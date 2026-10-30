from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

from .config import load_pilot_manifest, load_project_config, load_science_config
from .downloader import download_plan, remaining_bytes
from .extract import extract_plan
from .io.hdf5 import inventory_hdf5, write_inventory_json
from .io.hyperposterior import discover_hyperposterior_files
from .io.injections import inspect_injection_file
from .io.pesummary import inspect_pe_file
from .paths import ProjectPaths
from .planner import plan_total_bytes, resolve_plan, write_resolved_plan
from .repo_guard import audit_repository, repository_code_size
from .storage import (
    assert_external_storage,
    bootstrap_storage,
    free_bytes,
    human_bytes,
)
from .verify import verify_files
from .workflows.common import write_json_atomic
from .workflows.data_inventory import build_data_inventory
from .workflows.detected_power_gate import (
    load_power_gate_config,
    load_score_payload,
    write_power_decision,
)
from .workflows.mapping_status import inspect_mapping_status
from .workflows.pe_release_index import build_pilot_pe_release_index
from .workflows.pilot_readiness import build_readiness_report
from .workflows.toy_validation import run_toy_validation


def _new_output(args, subdir, *, small_synthetic=False):
    from datetime import datetime, timezone
    if getattr(args, "output", None) is not None:
        out = args.output.expanduser().resolve()
        if small_synthetic:
            # Explicit small teaching output outside the repository is allowed.
            cwd = Path.cwd().resolve()
            candidates = [cwd, *cwd.parents, Path(__file__).resolve().parents[2]]
            roots = [p for p in candidates if (p / "pyproject.toml").exists()
                     and (p / "src" / "gwtc_forecast").is_dir()]
            if any(out.is_relative_to(root) for root in roots):
                raise CommandError("Put synthetic output outside the repository, e.g. /tmp/gwtc-demo-attempt1")
            return out
    project = load_project_config(getattr(args, "project_config", None))
    paths = bootstrap_storage(project)
    if getattr(args, "output", None) is not None:
        out = args.output.expanduser().resolve()
        if not out.is_relative_to(paths.results.resolve()):
            raise CommandError("Real fit/score output must be below the configured external results directory")
        return out
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    return paths.results / subdir / stamp


def command_feature_demo(args):
    from .experiments.feature_demo import run_feature_demo
    out = _new_output(args, "synthetic/feature_demo", small_synthetic=True)
    report = run_feature_demo(out, config_path=args.demo_config,
                              power_replicates=args.power_replicates,
                              make_plots=not args.no_plots,
                              progress=lambda message: print(message, flush=True))
    print(f"Synthetic report: {out / 'report.md'}")
    print(f"Reference delta log score: {report['reference_delta_log_score']:.6f}")
    print("Synthetic development only. No real GW claim or production qualification.")
    return 0 if all(report["implementation_checks"].values()) else 1


def command_feature_calibration(args):
    from .experiments.calibration import run_repeated_calibration
    out = _new_output(args, "synthetic/repeated_calibration", small_synthetic=True)
    run_repeated_calibration(out, config_path=args.demo_config,
                             replicates=args.replicates, seed=args.seed)
    print(f"Synthetic repeated-training calibration: {out / 'calibration.json'}")
    return 0


def command_study_audit(args):
    from .inference.study import audit_study
    report = audit_study(args.spec)
    print(json.dumps(report, indent=2))
    return 0  # Reporting deliberate missing inputs is a successful audit.


def command_study_fit(args):
    from .inference.study import fit_study
    out = _new_output(args, "training")
    fit_study(args.spec, feature=args.model == "highpeak", outdir=out,
              seed=args.seed, nlive=args.nlive)
    print(f"Training result, not yet sampler-qualified: {out}")
    return 0


def command_study_score(args):
    from .inference.study import score_study
    out = _new_output(args, "retrospective_scoring")
    report = score_study(args.spec, outdir=out)
    print(f"Candidate frozen comparison: {out}")
    print(f"Feature-minus-continuum score: {report['delta_feature_minus_continuum']}")
    return 0


class CommandError(RuntimeError):
    """Raised for user-facing command failures."""


def _add_config_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-config", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--science-config", type=Path)


def _add_resolution_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh cached Zenodo record metadata.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Require cached Zenodo metadata and make no metadata request.",
    )


def _load(args: argparse.Namespace):
    project = load_project_config(getattr(args, "project_config", None))
    manifest = load_pilot_manifest(getattr(args, "manifest", None))
    science = load_science_config(getattr(args, "science_config", None))
    return project, manifest, science, ProjectPaths.from_config(project)


def _resolved(args: argparse.Namespace):
    project, manifest, science, paths = _load(args)
    files = resolve_plan(
        config=project,
        manifest=manifest,
        paths=paths,
        refresh=bool(getattr(args, "refresh", False)),
        offline=bool(getattr(args, "offline", False)),
    )
    return project, manifest, science, paths, files


def _print_plan(files, *, free: int) -> None:
    print("\nSelected pilot files")
    print("=" * 88)
    for item in files:
        print(
            f"{human_bytes(item.remote.size_bytes):>11}  "
            f"Zenodo {item.remote.record_id:<8}  {item.spec.role}"
        )
        print(f"             {item.remote.filename}")
    total = plan_total_bytes(files)
    missing = sum(remaining_bytes(item) for item in files)
    recommended = int(missing * 1.10 + 2 * 1024**3)
    print("=" * 88)
    print(f"Selected total:       {human_bytes(total)}")
    print(f"Still missing:        {human_bytes(missing)}")
    print(f"External free space:  {human_bytes(free)}")
    print(f"Recommended free:     {human_bytes(recommended)}")
    if free < recommended:
        raise CommandError(
            "The external data filesystem does not have the recommended free space."
        )


def command_bootstrap(args: argparse.Namespace) -> int:
    project, _, _, _ = _load(args)
    paths = bootstrap_storage(project)
    print(f"External project tree ready: {paths.root}")
    return 0


def command_status(args: argparse.Namespace) -> int:
    project, manifest, science, paths = _load(args)
    assert_external_storage(project, write_test=False)
    print(f"Repository:                {Path.cwd().resolve()}")
    print(f"External mount:            {project.storage.external_mount}")
    print(f"External data root:        {paths.root}")
    print(f"External free space:       {human_bytes(free_bytes(project))}")
    print(f"Repository code size:      {human_bytes(repository_code_size(Path.cwd()))}")
    print(f"Pilot manifest files:      {len(manifest.files)}")
    print(f"Pilot events:              {len(science.events)}")
    print(f"Real-data scoring enabled: {science.real_data_scoring_enabled}")
    return 0


def command_paths(args: argparse.Namespace) -> int:
    project, _, _, paths = _load(args)
    assert_external_storage(project, write_test=False)
    for key, value in paths.as_environment().items():
        print(f"export {key}={shlex.quote(value)}")
    return 0


def command_plan(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    bootstrap_storage(project)
    files = resolve_plan(
        config=project,
        manifest=manifest,
        paths=paths,
        refresh=args.refresh,
        offline=args.offline,
    )
    output = write_resolved_plan(manifest=manifest, files=files, paths=paths)
    _print_plan(files, free=free_bytes(project))
    print(f"\nResolved plan: {output}")
    print("Dry run complete. No large file was downloaded.")
    return 0


def command_download(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    bootstrap_storage(project)
    files = resolve_plan(
        config=project,
        manifest=manifest,
        paths=paths,
        refresh=args.refresh,
        offline=args.offline,
    )
    write_resolved_plan(manifest=manifest, files=files, paths=paths)
    _print_plan(files, free=free_bytes(project))
    if args.dry_run:
        print("Dry run requested; no files downloaded.")
        return 0
    download_plan(files, project.download)
    print("\nAll selected downloads completed and passed file-level verification.")
    return 0


def command_verify(args: argparse.Namespace) -> int:
    project, _, _, paths, files = _resolved(args)
    assert_external_storage(project, write_test=True)
    report = verify_files(files, paths)
    print(f"Pilot raw files verified: {report}")
    return 0


def command_extract(args: argparse.Namespace) -> int:
    project, _, _, paths, files = _resolved(args)
    assert_external_storage(project, write_test=True)
    extract_plan(files, paths)
    print(f"Required archives extracted below: {paths.extracted}")
    return 0


def command_inventory(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    assert_external_storage(project, write_test=True)
    report = build_data_inventory(
        project=project,
        manifest=manifest,
        paths=paths,
        deep_pe=args.deep_pe,
    )
    output = paths.results / "pilot" / "inventory" / "data_inventory.json"
    print(f"Inventory written: {output}")
    print(f"All manifest files present: {report['all_manifest_files_present']}")
    print(f"Event-list audit passed:   {report['event_list_audit']['passed']}")
    return 0


def command_inspect_hdf5(args: argparse.Namespace) -> int:
    report = inventory_hdf5(
        args.path.expanduser().resolve(),
        max_depth=args.max_depth,
        max_nodes=args.max_nodes,
        include_attributes=not args.no_attributes,
    )
    if args.output:
        write_inventory_json(args.output.expanduser().resolve(), report)
        print(f"HDF5 inventory written: {args.output.expanduser().resolve()}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def command_inspect_pe(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    assert_external_storage(project, write_test=False)
    matches = [spec for spec in manifest.files if spec.event_id == args.event_id]
    if len(matches) != 1:
        raise CommandError(
            f"Expected exactly one manifest entry for {args.event_id}; found {len(matches)}"
        )
    spec = matches[0]
    path = paths.raw / f"zenodo_{spec.record_id}" / spec.filename
    if not path.is_file():
        raise CommandError(f"PE file is absent: {path}")
    report = inspect_pe_file(path, deep=args.deep)
    output = (
        paths.results
        / "pilot"
        / "inventory"
        / f"pe_{args.event_id}_{'deep' if args.deep else 'shallow'}.json"
    )
    write_json_atomic(output, report)
    print(f"PE inspection written: {output}")
    if report.get("labels"):
        print("Analysis labels:")
        for label in report["labels"]:
            print(f"  {label}")
    elif args.deep:
        print(f"PESummary inspection error: {report.get('pesummary_error')}")
    return 0


def command_pe_index(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    assert_external_storage(project, write_test=True)
    report = build_pilot_pe_release_index(manifest=manifest, paths=paths)
    output = paths.results / "pilot" / "inventory" / "pe_release_index.json"
    print(f"PE release index written: {output}")
    print(f"Ready for label audit: {report['ready_for_label_audit']}")
    for release, payload in report["releases"].items():
        if not payload.get("present", False):
            print(f"  {release}: summary table absent")
            continue
        print(f"  {release}: {payload['selected_row_count']} candidate rows")
        for event_id, event in payload["events"].items():
            labels = ", ".join(event["candidate_labels"])
            print(f"    {event_id}: {labels}")
    return 0


def command_inspect_selection(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    assert_external_storage(project, write_test=True)
    matches = [spec for spec in manifest.files if spec.category == "selection"]
    if len(matches) != 1:
        raise CommandError(
            f"Expected exactly one pilot selection file; found {len(matches)}"
        )
    spec = matches[0]
    path = paths.raw / f"zenodo_{spec.record_id}" / spec.filename
    if not path.is_file():
        raise CommandError(f"Selection file is absent: {path}")
    report = inspect_injection_file(path)
    output = paths.results / "pilot" / "inventory" / "o4ab_selection_schema.json"
    write_json_atomic(output, report)
    documented = report["documented_schema"]
    print(f"Selection schema audit written: {output}")
    print(
        "Documented field names present: "
        f"{documented['schema_names_match_documentation']}"
    )
    print("Production mapping complete: False")
    return 0


def command_discover_hyperposteriors(args: argparse.Namespace) -> int:
    project, manifest, _, paths = _load(args)
    assert_external_storage(project, write_test=False)
    reports: dict[str, Any] = {}
    for spec in manifest.files:
        if spec.category != "hyperposterior" or not spec.extract_subdir:
            continue
        root = paths.extracted / spec.extract_subdir
        reports[spec.role] = (
            discover_hyperposterior_files(root)
            if root.exists()
            else {"root": str(root), "present": False}
        )
    output = paths.results / "pilot" / "inventory" / "hyperposterior_discovery.json"
    write_json_atomic(output, reports)
    print(f"Hyperposterior discovery report: {output}")
    return 0


def command_science_smoke(args: argparse.Namespace) -> int:
    project, _, science, paths = _load(args)
    assert_external_storage(project, write_test=True)
    report = run_toy_validation(
        output_dir=paths.results / "pilot" / "toy_validation",
        seed=args.seed,
        count_per_run=args.count_per_run,
        posterior_samples=args.posterior_samples,
        hyperposterior_draws=args.hyperposterior_draws,
        generated_injections_per_run=args.generated_injections,
        tolerance=science.numerical_gates.maximum_joint_prequential_difference,
    )
    print(f"Toy validation: {report['status']}")
    for name, item in report["models"].items():
        print(f"  {name:>7}: log predictive score = {item['joint_log_score']:.6f}")
    print(
        "  peak - smooth = "
        f"{report['comparisons']['delta_peak_minus_smooth']:.6f}"
    )
    print(
        "Report: "
        f"{paths.results / 'pilot' / 'toy_validation' / 'toy_validation.json'}"
    )
    return 0



def command_power_gate(args: argparse.Namespace) -> int:
    from dataclasses import asdict
    from .statistics.qualification import assess_bidirectional
    config = load_power_gate_config(args.gate_config.expanduser().resolve())
    scores, input_metadata = load_score_payload(args.scores.expanduser().resolve())
    decision = assess_bidirectional(
        scores, expected_models=config.generating_models,
        final_count=config.final_replicates_per_direction,
        median_target=config.minimum_median_signed_score,
        wrong_sign_limit=config.maximum_wrong_sign_probability,
        q05_target=config.minimum_q05_signed_score,
        maximum_median_se=config.maximum_median_standard_error,
        maximum_wrong_sign_se=config.maximum_wrong_sign_standard_error,
        bootstrap_replicates=config.bootstrap_replicates,
        seed=config.master_seed,
    )
    decision["config"] = asdict(config)
    decision["input_score_file"] = str(args.scores.expanduser().resolve())
    decision["input_metadata"] = input_metadata
    decision["scope"] = "Numerical investment criteria only. Input scientific validity must be established separately."
    output = (args.output.expanduser().resolve() if args.output is not None
              else args.scores.expanduser().resolve().with_name("detected_power_decision.json"))
    if output.exists():
        raise CommandError("Decision output exists; use a new attempt output instead of overwriting evidence")
    write_power_decision(output, decision)
    print(f"Detected-power decision: {decision['decision']}")
    for model, summary in decision["directions"].items():
        print(f"  {model}: median={summary['median']:.6f}, "
              f"q05={summary['q05']:.6f}, "
              f"wrong-sign={summary['wrong_sign_probability']:.4f}, "
              f"replicates={summary['replicates']}")
    print(f"Decision artifact: {output}")
    print("No automatic scientific validation or production authorization.")
    return 0


def command_mapping_status(args: argparse.Namespace) -> int:
    _, _, science, _ = _load(args)
    report = inspect_mapping_status(
        science=science,
        config_dir=args.config_dir.expanduser().resolve(),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def command_readiness(args: argparse.Namespace) -> int:
    project, manifest, science, paths = _load(args)
    assert_external_storage(project, write_test=True)
    report = build_readiness_report(
        science=science, manifest=manifest, paths=paths, config_dir=Path.cwd() / "config"
    )
    print(f"Readiness status: {report['status']}")
    print(f"Pilot data ready: {report['pilot_data_ready']}")
    print(f"Statistics ready: {report['baseline_statistics_ready']}")
    print(f"Real-data scoring allowed: {report['real_data_scoring_allowed']}")
    print("Next actions:")
    for index, action in enumerate(report["next_actions_in_priority_order"], start=1):
        print(f"  {index}. {action}")
    print(f"Report: {paths.results / 'pilot' / 'readiness.json'}")
    return 0


def command_audit_repository(args: argparse.Namespace) -> int:
    project = load_project_config(args.project_config)
    root = args.root.expanduser().resolve()
    violations = audit_repository(root, project.guards.max_repository_file_mib)
    if violations:
        print("Repository data guard failed:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1
    print(
        f"Repository data guard passed: {root} "
        f"({human_bytes(repository_code_size(root))})"
    )
    return 0


def command_versions(args: argparse.Namespace) -> int:
    packages = [
        "gwtc-forecast",
        "numpy",
        "scipy",
        "pandas",
        "h5py",
        "bilby",
        "gwpopulation",
        "pesummary",
        "popsummary",
        "zenodo-get",
    ]
    payload = {
        "python": sys.version,
        "executable": sys.executable,
        "packages": {},
    }
    for name in packages:
        try:
            payload["packages"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            payload["packages"][name] = None
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gwtc-forecast",
        description=(
            "Guarded data management and prediction-first statistics for the "
            "GWTC catalog-to-catalog forecasting project."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("feature-demo", help="Run the matched train/freeze/predict synthetic experiment")
    demo.add_argument("--output", type=Path)
    demo.add_argument("--project-config", type=Path)
    demo.add_argument("--demo-config", type=Path)
    demo.add_argument("--power-replicates", type=int)
    demo.add_argument("--no-plots", action="store_true")
    demo.set_defaults(func=command_feature_demo)

    calibration = subparsers.add_parser("feature-calibration", help="Repeat independent synthetic training and test catalogs")
    calibration.add_argument("--output", type=Path)
    calibration.add_argument("--project-config", type=Path)
    calibration.add_argument("--demo-config", type=Path)
    calibration.add_argument("--replicates", type=int, default=20)
    calibration.add_argument("--seed", type=int, default=20260905)
    calibration.set_defaults(func=command_feature_calibration)

    sa = subparsers.add_parser("study-audit", help="List missing real-study inputs without scoring events")
    sa.add_argument("--spec", type=Path, default=Path("config/real_study.example.json"))
    sa.set_defaults(func=command_study_audit)

    sf = subparsers.add_parser("study-fit", help="Fit validated through-O3 contracts with a frozen matched model")
    sf.add_argument("--spec", type=Path, required=True)
    sf.add_argument("--model", choices=["continuum", "highpeak"], required=True)
    sf.add_argument("--output", type=Path)
    sf.add_argument("--project-config", type=Path)
    sf.add_argument("--seed", type=int, default=20260904)
    sf.add_argument("--nlive", type=int, default=500)
    sf.set_defaults(func=command_study_fit)

    ss = subparsers.add_parser("study-score", help="Score qualified frozen posteriors on explicit held-out contracts")
    ss.add_argument("--spec", type=Path, required=True)
    ss.add_argument("--output", type=Path)
    ss.add_argument("--project-config", type=Path)
    ss.set_defaults(func=command_study_score)

    bootstrap = subparsers.add_parser("bootstrap", help="Create the external data tree")
    _add_config_options(bootstrap)
    bootstrap.set_defaults(func=command_bootstrap)

    status = subparsers.add_parser("status", help="Report storage and project status")
    _add_config_options(status)
    status.set_defaults(func=command_status)

    paths = subparsers.add_parser("paths", help="Print shell exports for external paths")
    _add_config_options(paths)
    paths.set_defaults(func=command_paths)

    plan = subparsers.add_parser("plan", help="Resolve and size the pilot download")
    _add_config_options(plan)
    _add_resolution_options(plan)
    plan.set_defaults(func=command_plan)

    download = subparsers.add_parser("download", help="Download only the pinned pilot")
    _add_config_options(download)
    _add_resolution_options(download)
    download.add_argument("--dry-run", action="store_true")
    download.set_defaults(func=command_download)

    verify = subparsers.add_parser("verify", help="Verify all pilot raw files")
    _add_config_options(verify)
    _add_resolution_options(verify)
    verify.set_defaults(func=command_verify)

    extract = subparsers.add_parser("extract", help="Safely extract required archives")
    _add_config_options(extract)
    _add_resolution_options(extract)
    extract.set_defaults(func=command_extract)

    inventory = subparsers.add_parser(
        "inventory", help="Inspect downloaded releases without interpreting them"
    )
    _add_config_options(inventory)
    inventory.add_argument(
        "--deep-pe",
        action="store_true",
        help="Use PESummary to enumerate every PE analysis label and parameter.",
    )
    inventory.set_defaults(func=command_inventory)

    hdf5 = subparsers.add_parser("inspect-hdf5", help="Inventory an arbitrary HDF5 file")
    hdf5.add_argument("path", type=Path)
    hdf5.add_argument("--output", type=Path)
    hdf5.add_argument("--max-depth", type=int, default=8)
    hdf5.add_argument("--max-nodes", type=int, default=10000)
    hdf5.add_argument("--no-attributes", action="store_true")
    hdf5.set_defaults(func=command_inspect_hdf5)

    pe = subparsers.add_parser("inspect-pe", help="Inspect one selected event PE file")
    _add_config_options(pe)
    pe.add_argument("event_id")
    pe.add_argument("--deep", action="store_true")
    pe.set_defaults(func=command_inspect_pe)

    pe_index = subparsers.add_parser(
        "pe-index",
        help="Index candidate analysis labels from the lightweight PE summary tables",
    )
    _add_config_options(pe_index)
    pe_index.set_defaults(func=command_pe_index)

    selection = subparsers.add_parser(
        "inspect-selection",
        help="Audit the documented O4 injection table fields without loading it",
    )
    _add_config_options(selection)
    selection.set_defaults(func=command_inspect_selection)

    hp = subparsers.add_parser(
        "discover-hyperposteriors",
        help="List safe candidate files in extracted GWTC-3 analyses",
    )
    _add_config_options(hp)
    hp.set_defaults(func=command_discover_hyperposteriors)

    smoke = subparsers.add_parser(
        "science-smoke",
        help="Validate event, selection, predictive, and prequential statistics on mocks",
    )
    _add_config_options(smoke)
    smoke.add_argument("--seed", type=int, default=20260821)
    smoke.add_argument("--count-per-run", type=int, default=10)
    smoke.add_argument("--posterior-samples", type=int, default=600)
    smoke.add_argument("--hyperposterior-draws", type=int, default=32)
    smoke.add_argument("--generated-injections", type=int, default=50000)
    smoke.set_defaults(func=command_science_smoke)


    power_gate = subparsers.add_parser(
        "power-gate",
        help="Evaluate frozen bidirectional detected-space mock-score thresholds",
    )
    power_gate.add_argument("scores", type=Path)
    power_gate.add_argument(
        "--gate-config", type=Path, default=Path("config/detected_power_gate.toml")
    )
    power_gate.add_argument("--output", type=Path)
    power_gate.set_defaults(func=command_power_gate)

    mapping = subparsers.add_parser(
        "mapping-status", help="Report unresolved PE, injection, and model mappings"
    )
    _add_config_options(mapping)
    mapping.add_argument("--config-dir", type=Path, default=Path("config"))
    mapping.set_defaults(func=command_mapping_status)

    readiness = subparsers.add_parser(
        "readiness", help="Report whether real-data scoring gates are open"
    )
    _add_config_options(readiness)
    readiness.set_defaults(func=command_readiness)

    audit = subparsers.add_parser(
        "audit-repo", help="Reject large data/results accidentally placed in Git"
    )
    audit.add_argument("--project-config", type=Path)
    audit.add_argument("--root", type=Path, default=Path.cwd())
    audit.set_defaults(func=command_audit_repository)

    versions = subparsers.add_parser("versions", help="Print runtime package versions")
    versions.set_defaults(func=command_versions)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        if os.environ.get("GWTC_FORECAST_DEBUG") == "1":
            raise
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
