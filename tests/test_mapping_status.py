from __future__ import annotations

from pathlib import Path

from gwtc_forecast.config import load_science_config
from gwtc_forecast.workflows.mapping_status import inspect_mapping_status


def test_mapping_templates_deliberately_keep_real_data_gated() -> None:
    science = load_science_config()
    report = inspect_mapping_status(science=science, config_dir=Path("config"))
    assert not report["all_mappings_ready"]
    assert set(report["pe"]["unvalidated_events"]) == set(science.events)
    assert set(report["injections"]["unvalidated_runs"]) == set(science.runs)
    assert set(report["released_models"]["unvalidated_models"]) == set(
        science.models
    )


def test_pe_mapping_cannot_be_ready_without_row_weight_semantics(tmp_path) -> None:
    import shutil

    science = load_science_config()
    shutil.copy("config/injection_mapping.toml", tmp_path / "injection_mapping.toml")
    shutil.copy(
        "config/released_model_mapping.toml", tmp_path / "released_model_mapping.toml"
    )
    rows = ["schema_version = 1", 'status = "TEST"', 'notes = "test"', ""]
    for event_id in science.events:
        rows.extend(
            [
                "[[events]]",
                f'event_id = "{event_id}"',
                'run = "O4a"',
                'frozen_label = "label"',
                'prior_adapter = "adapter"',
                'coordinates = ["x"]',
                "validated = true",
                "",
            ]
        )
    (tmp_path / "pe_mapping.toml").write_text("\n".join(rows))
    report = inspect_mapping_status(science=science, config_dir=tmp_path)
    assert not report["pe"]["ready"]
    assert set(report["pe"]["unvalidated_events"]) == set(science.events)
