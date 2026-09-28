from __future__ import annotations

import numpy as np

from gwtc_forecast.workflows.detected_power_gate import (
    PowerGateConfig,
    evaluate_detected_power_gate,
    seed_manifest,
)


def _config(*, final: int = 200) -> PowerGateConfig:
    return PowerGateConfig(
        master_seed=20260827,
        generating_models=("PowerLawPeak", "PowerlawDipBreak"),
        preliminary_replicates_per_direction=50,
        final_replicates_per_direction=final,
        bootstrap_replicates=80,
        minimum_median_signed_score=5.0,
        maximum_wrong_sign_probability=0.10,
        minimum_q05_signed_score=0.0,
        maximum_median_standard_error=0.25,
        maximum_wrong_sign_standard_error=0.03,
    )


def test_bidirectional_detected_power_gate_passes_only_after_final_sample() -> None:
    rng = np.random.default_rng(7)
    scores = {
        "PowerLawPeak": rng.normal(7.0, 0.5, 200),
        "PowerlawDipBreak": rng.normal(6.5, 0.5, 200),
    }
    result = evaluate_detected_power_gate(scores, config=_config())
    assert result["decision"] == "PASS_DETECTED_POWER_GATE"
    assert result["all_directions_pass"]


def test_detected_power_gate_is_bidirectional_and_can_no_go() -> None:
    rng = np.random.default_rng(8)
    scores = {
        "PowerLawPeak": rng.normal(7.0, 0.5, 200),
        "PowerlawDipBreak": rng.normal(-1.0, 0.5, 200),
    }
    result = evaluate_detected_power_gate(scores, config=_config())
    assert result["decision"] == "NO_GO_INSUFFICIENT_DETECTED_POWER"
    assert result["directions"]["PowerLawPeak"]["gates"]["q05_signed_score"]
    assert not result["directions"]["PowerlawDipBreak"]["gates"][
        "median_signed_score"
    ]


def test_preliminary_mock_sample_does_not_issue_final_decision() -> None:
    scores = {
        "PowerLawPeak": np.full(50, 7.0),
        "PowerlawDipBreak": np.full(50, 7.0),
    }
    result = evaluate_detected_power_gate(scores, config=_config(final=200))
    assert result["decision"] == "QUALIFICATION_INCOMPLETE_MORE_MOCKS_REQUIRED"


def test_seed_manifest_is_label_stable() -> None:
    first = seed_manifest(123, ["a", "b"])
    second = seed_manifest(123, ["b", "a"])
    assert first["a"] == second["a"]
    assert first["b"] == second["b"]
    assert first["a"] != first["b"]
