from __future__ import annotations

import json

from gwtc_forecast.workflows.toy_validation import run_toy_validation


def test_toy_vertical_slice_passes_and_writes_report(tmp_path) -> None:
    report = run_toy_validation(output_dir=tmp_path)
    assert report["status"] == "PASS"
    assert report["comparisons"]["delta_peak_minus_smooth"] > 2.0
    loaded = json.loads((tmp_path / "toy_validation.json").read_text())
    assert loaded["acceptance"]["joint_equals_prequential"]
