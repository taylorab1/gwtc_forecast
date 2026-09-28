from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import PilotManifest, ScienceConfig
from ..paths import ProjectPaths
from .common import write_json_atomic
from .mapping_status import inspect_mapping_status


def _json_status(path: Path, *, pass_values: tuple[str, ...] = ("PASS",)) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "present": False, "passed": False}
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return {
            "path": str(path),
            "present": True,
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    status = str(payload.get("status", ""))
    return {
        "path": str(path),
        "present": True,
        "passed": status in pass_values,
        "status": status or None,
    }


def build_readiness_report(
    *,
    science: ScienceConfig,
    manifest: PilotManifest,
    paths: ProjectPaths,
    config_dir: Path,
) -> dict[str, Any]:
    verification_path = paths.manifests / "pilot_verification_report.json"
    inventory_path = paths.results / "pilot" / "inventory" / "data_inventory.json"
    smoke_path = paths.results / "pilot" / "toy_validation" / "toy_validation.json"

    verification = _json_status(verification_path)
    inventory: dict[str, Any]
    if inventory_path.is_file():
        payload = json.loads(inventory_path.read_text())
        inventory = {
            "path": str(inventory_path),
            "present": True,
            "all_manifest_files_present": bool(
                payload.get("all_manifest_files_present", False)
            ),
            "event_list_audit_passed": bool(
                payload.get("event_list_audit", {}).get("passed", False)
            ),
        }
    else:
        inventory = {
            "path": str(inventory_path),
            "present": False,
            "all_manifest_files_present": False,
            "event_list_audit_passed": False,
        }
    smoke = _json_status(smoke_path)

    extraction_markers: dict[str, bool] = {}
    for spec in manifest.files:
        if spec.extract and spec.extract_subdir:
            marker = paths.extracted / spec.extract_subdir / ".extraction_complete.json"
            extraction_markers[spec.role] = marker.is_file()

    mapping_status = inspect_mapping_status(science=science, config_dir=config_dir)
    production = science.production_gates
    declared_gates = {
        "pe_labels_frozen": production.pe_labels_frozen,
        "pe_priors_validated": production.pe_priors_validated,
        "injection_mapping_validated": production.injection_mapping_validated,
        "selection_reference_validated": production.selection_reference_validated,
        "released_models_validated": production.released_models_validated,
        "mock_calibration_passed": production.mock_calibration_passed,
    }
    effective_gates = {
        "pe_labels_frozen": production.pe_labels_frozen
        and mapping_status["pe"]["ready"],
        "pe_priors_validated": production.pe_priors_validated
        and mapping_status["pe"]["ready"],
        "injection_mapping_validated": production.injection_mapping_validated
        and mapping_status["injections"]["ready"],
        "selection_reference_validated": production.selection_reference_validated,
        "released_models_validated": production.released_models_validated
        and mapping_status["released_models"]["ready"],
        "mock_calibration_passed": production.mock_calibration_passed
        and smoke["passed"],
    }
    data_ready = bool(
        verification["passed"]
        and inventory["all_manifest_files_present"]
        and inventory["event_list_audit_passed"]
        and all(extraction_markers.values())
    )
    statistics_ready = bool(smoke["passed"])
    real_data_allowed = bool(
        science.real_data_scoring_enabled
        and all(effective_gates.values())
        and data_ready
        and statistics_ready
    )
    next_actions: list[str] = []
    if not data_ready:
        next_actions.append(
            "Complete plan/download/verify/extract/inventory on the external disk."
        )
    if not statistics_ready:
        next_actions.append("Fix the deterministic toy predictive-statistics smoke test.")
    if not mapping_status["pe"]["ready"]:
        next_actions.append(
            "Audit labels and exact priors for every event; complete config/pe_mapping.toml."
        )
    if not mapping_status["injections"]["ready"]:
        next_actions.append(
            "Map O4 run masks, draw density, generated count, and base weights; "
            "complete config/injection_mapping.toml."
        )
    if not production.selection_reference_validated:
        next_actions.append(
            "Match selection efficiency to GWPopulation/release code at frozen points."
        )
    if not mapping_status["released_models"]["ready"]:
        next_actions.append(
            "Map the two released hyperposteriors and complete "
            "config/released_model_mapping.toml."
        )
    if not science.real_data_scoring_enabled:
        next_actions.append(
            "Keep real_data_scoring_enabled=false until every production gate is reviewed."
        )

    report: dict[str, Any] = {
        "schema": "gwtc_forecast.readiness.v1",
        "science_name": science.name,
        "primary_question": science.primary_question,
        "baseline_statistics_ready": statistics_ready,
        "pilot_data_ready": data_ready,
        "real_data_scoring_enabled": science.real_data_scoring_enabled,
        "real_data_scoring_allowed": real_data_allowed,
        "verification": verification,
        "inventory": inventory,
        "extraction_markers": extraction_markers,
        "mapping_status": mapping_status,
        "toy_validation": smoke,
        "declared_production_gates": declared_gates,
        "effective_production_gates": effective_gates,
        "next_actions_in_priority_order": next_actions,
        "status": (
            "REAL_DATA_READY"
            if real_data_allowed
            else "BASELINE_READY_REAL_DATA_GATED"
            if statistics_ready
            else "BASELINE_NOT_READY"
        ),
    }
    output = paths.results / "pilot" / "readiness.json"
    write_json_atomic(output, report)
    return report
