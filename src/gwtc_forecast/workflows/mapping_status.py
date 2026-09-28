from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from ..models import ScienceConfig


def _read(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream), None
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"




def _pe_weight_mapping_ready(row: dict[str, Any]) -> bool:
    mode = str(row.get("sample_weight_mode", "")).strip().lower()
    if mode == "equal":
        return True
    if mode in {"weights", "log_weights"}:
        return bool(str(row.get("sample_weight_field", "")).strip())
    return False

def inspect_mapping_status(
    *, science: ScienceConfig, config_dir: Path
) -> dict[str, Any]:
    config_dir = Path(config_dir)
    pe_path = config_dir / "pe_mapping.toml"
    injection_path = config_dir / "injection_mapping.toml"
    model_path = config_dir / "released_model_mapping.toml"

    pe, pe_error = _read(pe_path)
    injection, injection_error = _read(injection_path)
    models, model_error = _read(model_path)

    pe_rows = [] if pe is None else list(pe.get("events", []))
    pe_by_id = {str(row.get("event_id")): row for row in pe_rows}
    pe_missing = sorted(set(science.events) - set(pe_by_id))
    pe_unvalidated = sorted(
        event_id
        for event_id in science.events
        if event_id in pe_by_id
        and not (
            bool(pe_by_id[event_id].get("validated", False))
            and str(pe_by_id[event_id].get("frozen_label", "")).strip()
            and str(pe_by_id[event_id].get("prior_adapter", "")).strip()
            and _pe_weight_mapping_ready(pe_by_id[event_id])
        )
    )
    pe_ready = pe_error is None and not pe_missing and not pe_unvalidated

    run_tables = {} if injection is None else dict(injection.get("runs", {}))
    injection_missing = sorted(set(science.runs) - set(run_tables))
    injection_unvalidated = sorted(
        run
        for run in science.runs
        if run in run_tables
        and not (
            bool(run_tables[run].get("validated", False))
            and str(run_tables[run].get("found_mask_expression", "")).strip()
            and str(run_tables[run].get("parameter_group", "")).strip()
            and str(run_tables[run].get("log_draw_density_expression", "")).strip()
            and str(run_tables[run].get("log_base_weight_expression", "")).strip()
            and int(run_tables[run].get("generated_count", 0)) > 0
        )
    )
    injection_ready = (
        injection_error is None and not injection_missing and not injection_unvalidated
    )

    model_tables = {} if models is None else dict(models.get("models", {}))
    model_missing = sorted(set(science.models) - set(model_tables))
    model_unvalidated = sorted(
        name
        for name in science.models
        if name in model_tables
        and not (
            bool(model_tables[name].get("validated", False))
            and str(model_tables[name].get("posterior_file", "")).strip()
            and str(model_tables[name].get("parameter_mapping", "")).strip()
        )
    )
    models_ready = model_error is None and not model_missing and not model_unvalidated

    return {
        "schema": "gwtc_forecast.mapping_status.v1",
        "config_dir": str(config_dir),
        "pe": {
            "path": str(pe_path),
            "error": pe_error,
            "missing_events": pe_missing,
            "unvalidated_events": pe_unvalidated,
            "ready": pe_ready,
        },
        "injections": {
            "path": str(injection_path),
            "error": injection_error,
            "missing_runs": injection_missing,
            "unvalidated_runs": injection_unvalidated,
            "ready": injection_ready,
        },
        "released_models": {
            "path": str(model_path),
            "error": model_error,
            "missing_models": model_missing,
            "unvalidated_models": model_unvalidated,
            "ready": models_ready,
        },
        "all_mappings_ready": pe_ready and injection_ready and models_ready,
    }
