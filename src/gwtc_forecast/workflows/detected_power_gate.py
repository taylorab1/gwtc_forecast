from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np


SCORES_SCHEMA = "gwtc_forecast.detected_power_scores.v1"
DECISION_SCHEMA = "gwtc_forecast.detected_power_decision.v1"


@dataclass(frozen=True)
class PowerGateConfig:
    master_seed: int
    generating_models: tuple[str, ...]
    preliminary_replicates_per_direction: int
    final_replicates_per_direction: int
    bootstrap_replicates: int
    minimum_median_signed_score: float
    maximum_wrong_sign_probability: float
    minimum_q05_signed_score: float
    maximum_median_standard_error: float
    maximum_wrong_sign_standard_error: float


@dataclass(frozen=True)
class DirectionSummary:
    generating_model: str
    replicates: int
    median_signed_score: float
    q05_signed_score: float
    q95_signed_score: float
    wrong_sign_probability: float
    median_standard_error: float
    wrong_sign_standard_error: float
    gates: dict[str, bool]

    @property
    def passed(self) -> bool:
        return all(self.gates.values())


def load_power_gate_config(path: Path) -> PowerGateConfig:
    path = Path(path)
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Power-gate configuration not found: {path}") from exc
    if int(data.get("schema_version", -1)) != 1:
        raise RuntimeError(f"Unsupported detected-power config schema in {path}")
    design = data["design"]
    thresholds = data["thresholds"]
    models = tuple(str(value) for value in design["generating_models"])
    if len(models) < 2 or len(set(models)) != len(models):
        raise ValueError("generating_models must contain at least two unique names")
    config = PowerGateConfig(
        master_seed=int(data["master_seed"]),
        generating_models=models,
        preliminary_replicates_per_direction=int(
            design["preliminary_replicates_per_direction"]
        ),
        final_replicates_per_direction=int(design["final_replicates_per_direction"]),
        bootstrap_replicates=int(design["bootstrap_replicates"]),
        minimum_median_signed_score=float(
            thresholds["minimum_median_signed_score"]
        ),
        maximum_wrong_sign_probability=float(
            thresholds["maximum_wrong_sign_probability"]
        ),
        minimum_q05_signed_score=float(thresholds["minimum_q05_signed_score"]),
        maximum_median_standard_error=float(
            thresholds["maximum_median_standard_error"]
        ),
        maximum_wrong_sign_standard_error=float(
            thresholds["maximum_wrong_sign_standard_error"]
        ),
    )
    if config.preliminary_replicates_per_direction < 2:
        raise ValueError("preliminary_replicates_per_direction must be at least two")
    if (
        config.final_replicates_per_direction
        < config.preliminary_replicates_per_direction
    ):
        raise ValueError("final replicate count must not be below preliminary count")
    if config.bootstrap_replicates < 2:
        raise ValueError("bootstrap_replicates must be at least two")
    return config


def _stable_child_seed(master_seed: int, label: str) -> int:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    label_words = np.frombuffer(digest[:16], dtype=np.uint32).tolist()
    sequence = np.random.SeedSequence([int(master_seed), *label_words])
    return int(sequence.generate_state(1, dtype=np.uint64)[0])


def seed_manifest(master_seed: int, labels: Sequence[str]) -> dict[str, int]:
    """Return deterministic, label-stable child seeds for artifact provenance."""

    unique = tuple(str(label) for label in labels)
    if len(set(unique)) != len(unique):
        raise ValueError("seed labels must be unique")
    return {label: _stable_child_seed(master_seed, label) for label in unique}


def _bootstrap_median_standard_error(
    scores: np.ndarray, *, seed: int, replicates: int
) -> float:
    rng = np.random.default_rng(seed)
    medians = np.empty(replicates, dtype=float)
    count = len(scores)
    for index in range(replicates):
        selected = rng.integers(0, count, size=count)
        medians[index] = float(np.median(scores[selected]))
    return float(np.std(medians, ddof=1))


def _direction_summary(
    model: str, scores: Sequence[float], *, config: PowerGateConfig
) -> DirectionSummary:
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or values.size < config.preliminary_replicates_per_direction:
        raise ValueError(
            f"{model} requires at least "
            f"{config.preliminary_replicates_per_direction} signed scores"
        )
    if not np.isfinite(values).all():
        raise ValueError(f"{model} signed scores contain non-finite values")
    q05, median, q95 = np.quantile(values, [0.05, 0.5, 0.95])
    wrong = float(np.mean(values <= 0.0))
    wrong_se = float(np.sqrt(wrong * (1.0 - wrong) / values.size))
    median_se = _bootstrap_median_standard_error(
        values,
        seed=_stable_child_seed(config.master_seed, f"median-bootstrap:{model}"),
        replicates=config.bootstrap_replicates,
    )
    gates = {
        "median_signed_score": float(median)
        >= config.minimum_median_signed_score,
        "wrong_sign_probability": wrong
        <= config.maximum_wrong_sign_probability,
        "q05_signed_score": float(q05) > config.minimum_q05_signed_score,
        "median_standard_error": median_se
        <= config.maximum_median_standard_error,
        "wrong_sign_standard_error": wrong_se
        <= config.maximum_wrong_sign_standard_error,
    }
    return DirectionSummary(
        generating_model=model,
        replicates=int(values.size),
        median_signed_score=float(median),
        q05_signed_score=float(q05),
        q95_signed_score=float(q95),
        wrong_sign_probability=wrong,
        median_standard_error=median_se,
        wrong_sign_standard_error=wrong_se,
        gates=gates,
    )


def evaluate_detected_power_gate(
    signed_scores_by_generating_model: Mapping[str, Sequence[float]],
    *,
    config: PowerGateConfig,
) -> dict[str, object]:
    """Apply the frozen bidirectional model-discrimination investment gate.

    Each input score must be positive when the generating model wins.  The
    function does not generate mocks and does not interpret real data; it only
    turns completed mock results into a deterministic project decision.
    """

    missing = set(config.generating_models) - set(signed_scores_by_generating_model)
    extra = set(signed_scores_by_generating_model) - set(config.generating_models)
    if missing or extra:
        raise ValueError(
            f"power-score model mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    summaries = {
        model: _direction_summary(
            model,
            signed_scores_by_generating_model[model],
            config=config,
        )
        for model in config.generating_models
    }
    final_sample_complete = all(
        summary.replicates >= config.final_replicates_per_direction
        for summary in summaries.values()
    )
    all_directions_pass = all(summary.passed for summary in summaries.values())
    if not final_sample_complete:
        decision = "QUALIFICATION_INCOMPLETE_MORE_MOCKS_REQUIRED"
    elif all_directions_pass:
        decision = "PASS_DETECTED_POWER_GATE"
    else:
        decision = "NO_GO_INSUFFICIENT_DETECTED_POWER"

    return {
        "schema": DECISION_SCHEMA,
        "decision": decision,
        "scientific_scope": (
            "Best-case detected-space distinguishability of the two frozen models; "
            "not a real-data result and not production authorization."
        ),
        "config": asdict(config),
        "seed_manifest": seed_manifest(
            config.master_seed,
            [f"median-bootstrap:{model}" for model in config.generating_models],
        ),
        "directions": {model: asdict(summary) for model, summary in summaries.items()},
        "final_sample_complete": final_sample_complete,
        "all_directions_pass": all_directions_pass,
        "authorizes": (
            ["prepare separately reviewed full-O4 PE campaign"]
            if decision == "PASS_DETECTED_POWER_GATE"
            else []
        ),
        "does_not_authorize": [
            "real-data scoring",
            "production execution",
            "a peak-versus-break physical conclusion",
            "weakening thresholds or adding model families after failure",
        ],
    }


def load_score_payload(path: Path) -> tuple[dict[str, Sequence[float]], dict[str, object]]:
    path = Path(path)
    payload = json.loads(path.read_text())
    if payload.get("schema") != SCORES_SCHEMA:
        raise ValueError(f"Unexpected detected-power score schema in {path}")
    scores = payload.get("signed_scores_by_generating_model")
    if not isinstance(scores, dict):
        raise ValueError("signed_scores_by_generating_model must be a mapping")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("score metadata must be a mapping")
    return scores, metadata


def write_power_decision(path: Path, decision: Mapping[str, object]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(decision, indent=2, sort_keys=True))
    tmp.replace(path)
