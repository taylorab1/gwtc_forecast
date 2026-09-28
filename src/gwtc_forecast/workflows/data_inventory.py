from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from ..io.hdf5 import inventory_hdf5
from ..io.hyperposterior import discover_hyperposterior_files
from ..io.injections import inspect_injection_file
from ..io.pesummary import inspect_pe_file
from ..models import PilotManifest, ProjectConfig
from ..paths import ProjectPaths
from .common import write_json_atomic
from .pe_release_index import build_pilot_pe_release_index

EVENT_RE = re.compile(r"\bGW\d{6}_\d{6}\b")
HDF_SUFFIXES = {".h5", ".hdf", ".hdf5"}


def _raw_path(paths: ProjectPaths, record_id: int, filename: str) -> Path:
    return paths.raw / f"zenodo_{record_id}" / filename


def _scan_event_list(root: Path) -> set[str]:
    found: set[str] = set()
    if not root.exists():
        return found
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 20 * 1024**2:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        found.update(EVENT_RE.findall(text))
    return found


def build_data_inventory(
    *,
    project: ProjectConfig,
    manifest: PilotManifest,
    paths: ProjectPaths,
    deep_pe: bool = False,
) -> dict[str, Any]:
    paths.create()
    file_rows: list[dict[str, Any]] = []
    hdf5_reports: dict[str, Any] = {}
    for spec in manifest.files:
        path = _raw_path(paths, spec.record_id, spec.filename)
        row = {
            "record_id": spec.record_id,
            "filename": spec.filename,
            "role": spec.role,
            "category": spec.category,
            "run": spec.run,
            "event_id": spec.event_id,
            "path": str(path),
            "present": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else None,
            "extract": spec.extract,
            "extract_subdir": spec.extract_subdir,
        }
        file_rows.append(row)
        if not path.is_file() or path.suffix.lower() not in HDF_SUFFIXES:
            continue
        if spec.category == "event_pe":
            hdf5_reports[spec.role] = inspect_pe_file(path, deep=deep_pe)
        elif spec.category == "selection":
            hdf5_reports[spec.role] = inspect_injection_file(path)
        else:
            hdf5_reports[spec.role] = inventory_hdf5(path)

    extracted_reports: dict[str, Any] = {}
    for spec in manifest.files:
        if not spec.extract or not spec.extract_subdir:
            continue
        target = paths.extracted / spec.extract_subdir
        if not target.exists():
            extracted_reports[spec.role] = {
                "path": str(target),
                "present": False,
            }
            continue
        files = [path for path in target.rglob("*") if path.is_file()]
        payload: dict[str, Any] = {
            "path": str(target),
            "present": True,
            "file_count": len(files),
            "total_bytes": sum(path.stat().st_size for path in files),
        }
        if spec.category == "hyperposterior":
            payload["hyperposterior_discovery"] = discover_hyperposterior_files(target)
        extracted_reports[spec.role] = payload

    expected_events = sorted(
        {spec.event_id for spec in manifest.files if spec.event_id is not None}
    )
    event_list_roots = [
        paths.extracted / spec.extract_subdir
        for spec in manifest.files
        if spec.role == "gwtc5_population_event_list" and spec.extract_subdir
    ]
    catalog_event_ids: set[str] = set()
    for root in event_list_roots:
        catalog_event_ids.update(_scan_event_list(root))

    missing_files = [row["role"] for row in file_rows if not row["present"]]
    pe_release_index = build_pilot_pe_release_index(
        manifest=manifest, paths=paths
    )

    report: dict[str, Any] = {
        "schema": "gwtc_forecast.data_inventory.v1",
        "pilot_name": manifest.name,
        "data_root": str(paths.root),
        "all_manifest_files_present": not missing_files,
        "missing_roles": missing_files,
        "files": file_rows,
        "hdf5_reports": hdf5_reports,
        "extracted": extracted_reports,
        "pe_release_index": pe_release_index,
        "event_list_audit": {
            "expected_pilot_events": expected_events,
            "catalog_event_ids_found": sorted(catalog_event_ids),
            "missing_expected_events": sorted(set(expected_events) - catalog_event_ids),
            "passed": bool(catalog_event_ids)
            and set(expected_events).issubset(catalog_event_ids),
        },
        "production_warnings": [
            "HDF5 discovery is descriptive and does not validate PE priors.",
            "Injection discovery is descriptive and does not validate run masks, "
            "draw densities, or normalization.",
            "Released hyperposterior files are discovered but not interpreted "
            "until a model-specific adapter is validated.",
        ],
    }

    output_dir = paths.results / "pilot" / "inventory"
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(output_dir / "data_inventory.json", report)
    with (output_dir / "file_inventory.csv").open("w", newline="") as stream:
        fieldnames = [
            "record_id",
            "filename",
            "role",
            "category",
            "run",
            "event_id",
            "path",
            "present",
            "size_bytes",
            "extract",
            "extract_subdir",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(file_rows)
    return report
