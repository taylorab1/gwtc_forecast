from __future__ import annotations

from typing import Any

from ..io.pe_summary import read_pe_summary_table, write_pe_index_csv
from ..models import PilotManifest
from ..paths import ProjectPaths
from .common import write_json_atomic


def build_pilot_pe_release_index(
    *,
    manifest: PilotManifest,
    paths: ProjectPaths,
) -> dict[str, Any]:
    """Index candidate PE analyses for the frozen pilot without choosing labels."""

    event_specs = [item for item in manifest.files if item.category == "event_pe"]
    summary_specs = [item for item in manifest.files if item.role.endswith("_pe_summary")]
    releases: dict[str, Any] = {}
    all_missing: list[str] = []
    file_mismatches: list[dict[str, Any]] = []

    for summary in summary_specs:
        relevant_events = [item for item in event_specs if item.record_id == summary.record_id]
        event_ids = [str(item.event_id) for item in relevant_events if item.event_id]
        path = paths.raw / f"zenodo_{summary.record_id}" / summary.filename
        release_key = summary.run or summary.role.removesuffix("_pe_summary")
        if not path.is_file():
            releases[release_key] = {
                "path": str(path),
                "present": False,
                "requested_event_ids": sorted(event_ids),
            }
            all_missing.extend(event_ids)
            continue

        report = read_pe_summary_table(path, event_ids=event_ids)
        releases[release_key] = {"present": True, **report}
        all_missing.extend(report["missing_requested_events"])

        expected_files = {str(item.event_id): item.filename for item in relevant_events}
        for event_id, payload in report["events"].items():
            observed = set(payload["result_file_names"])
            expected = expected_files[event_id]
            if observed != {expected}:
                file_mismatches.append(
                    {
                        "event_id": event_id,
                        "record_id": summary.record_id,
                        "expected_manifest_file": expected,
                        "summary_table_files": sorted(observed),
                    }
                )

        output_dir = paths.results / "pilot" / "inventory"
        write_pe_index_csv(output_dir / f"{release_key}_pe_candidates.csv", report)

    combined = {
        "schema": "gwtc_forecast.pilot_pe_release_index.v1",
        "pilot_name": manifest.name,
        "releases": releases,
        "missing_pilot_events": sorted(set(all_missing)),
        "manifest_file_mismatches": file_mismatches,
        "ready_for_label_audit": bool(releases)
        and not all_missing
        and not file_mismatches
        and all(item.get("present", False) for item in releases.values()),
        "production_labels_frozen": False,
        "next_step": (
            "Audit the candidate labels, prior/configuration metadata, and the "
            "population-analysis label policy; then freeze one explicit mapping "
            "per event in config/pe_mapping.toml."
        ),
    }
    output = paths.results / "pilot" / "inventory" / "pe_release_index.json"
    write_json_atomic(output, combined)
    return combined
