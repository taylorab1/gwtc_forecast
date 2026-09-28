from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from ..models import NumericalGates
from ..populations.protocol import PopulationModel
from ..statistics.diagnostics import (
    leave_one_event_out_influence,
    summarize_ess,
)
from ..statistics.likelihood import CatalogLikelihoodEvaluation, catalog_log_likelihood
from ..statistics.numerics import logmeanexp
from ..statistics.objects import EventPosterior, HyperPosterior, SelectionCampaign
from ..statistics.predictive import PrequentialResult, predictive_log_score, prequential_score


@dataclass(frozen=True)
class ModelVerticalSlice:
    """In-memory result for one frozen model on one held-out catalog."""

    model_name: str
    hyperposterior: HyperPosterior
    evaluation: CatalogLikelihoodEvaluation
    prequential: PrequentialResult
    report: dict[str, Any]


@dataclass(frozen=True)
class ModelComparison:
    """Predictive score difference and finite-hyperposterior diagnostics."""

    left_model: str
    right_model: str
    delta_log_score: float
    bootstrap_mean: float
    bootstrap_standard_deviation: float
    bootstrap_fractional_error: float | None
    fractional_error_applicable: bool
    bootstrap_q05: float
    bootstrap_median: float
    bootstrap_q95: float
    numerical_gates: dict[str, bool]
    eventwise_prequential_delta: tuple[dict[str, Any], ...]

    @property
    def passed(self) -> bool:
        return all(self.numerical_gates.values())


def _ordered_events(
    events: Sequence[EventPosterior], chronological_order: Sequence[str]
) -> list[EventPosterior]:
    by_id = {event.event_id: event for event in events}
    if len(by_id) != len(events):
        raise ValueError("event IDs must be unique")
    order = [str(item) for item in chronological_order]
    if len(set(order)) != len(order):
        raise ValueError("chronological order contains duplicates")
    if set(order) != set(by_id):
        missing = sorted(set(by_id) - set(order))
        extra = sorted(set(order) - set(by_id))
        raise ValueError(
            f"chronological order does not match events; missing={missing}, extra={extra}"
        )
    return [by_id[event_id] for event_id in order]


def evaluate_model_vertical_slice(
    *,
    events: Sequence[EventPosterior],
    selections: Mapping[str, SelectionCampaign],
    model: PopulationModel,
    hyperposterior: HyperPosterior,
    chronological_order: Sequence[str],
    numerical_gates: NumericalGates,
    raise_on_failure: bool = True,
) -> ModelVerticalSlice:
    """Evaluate one frozen population model with all primary numerical gates.

    This function does not inspect public release files.  It consumes only
    validated, analysis-ready statistical objects, which keeps release parsing
    separate from the predictive calculation.
    """

    ordered = _ordered_events(events, chronological_order)
    evaluation = catalog_log_likelihood(ordered, selections, model, hyperposterior)
    prequential = prequential_score(
        ordered,
        evaluation,
        hyperposterior,
        tolerance=numerical_gates.maximum_joint_prequential_difference,
    )
    joint_score = predictive_log_score(evaluation.log_likelihood, hyperposterior)

    event_ess_by_id = {
        event_id: asdict(summarize_ess(item.effective_sample_size))
        for event_id, item in evaluation.events.items()
    }
    selection_ess_by_run = {
        run: asdict(summarize_ess(item.effective_sample_size))
        for run, item in evaluation.selections.items()
    }
    minimum_event_ess = min(item["minimum"] for item in event_ess_by_id.values())
    minimum_selection_ess = min(
        item["minimum"] for item in selection_ess_by_run.values()
    )
    influence = leave_one_event_out_influence(ordered, evaluation, hyperposterior)

    gates = {
        "all_catalog_log_likelihoods_finite": bool(
            np.isfinite(evaluation.log_likelihood).all()
        ),
        "joint_equals_prequential": (
            prequential.absolute_difference <= prequential.comparison_tolerance
        ),
        "minimum_event_ess": (
            minimum_event_ess >= numerical_gates.minimum_event_ess
        ),
        "minimum_selection_ess": (
            minimum_selection_ess >= numerical_gates.minimum_selection_ess
        ),
    }
    report = {
        "schema": "gwtc_forecast.model_vertical_slice.v1",
        "model_name": hyperposterior.model_name or getattr(model, "name", "unnamed"),
        "event_count": len(ordered),
        "chronological_order": [event.event_id for event in ordered],
        "joint_log_score": joint_score,
        "prequential_log_score": prequential.cumulative_log_score,
        "joint_prequential_absolute_difference": prequential.absolute_difference,
        "joint_prequential_comparison_tolerance": prequential.comparison_tolerance,
        "minimum_event_ess": minimum_event_ess,
        "minimum_selection_ess": minimum_selection_ess,
        "event_ess": event_ess_by_id,
        "selection_ess": selection_ess_by_run,
        "prequential_steps": [asdict(item) for item in prequential.steps],
        "leave_one_event_out_influence": [asdict(item) for item in influence],
        "numerical_gates": gates,
        "status": "PASS" if all(gates.values()) else "FAIL",
    }
    result = ModelVerticalSlice(
        model_name=str(report["model_name"]),
        hyperposterior=hyperposterior,
        evaluation=evaluation,
        prequential=prequential,
        report=report,
    )
    if raise_on_failure and report["status"] != "PASS":
        failed = [name for name, passed in gates.items() if not passed]
        raise RuntimeError(
            f"Numerical gates failed for {result.model_name}: {failed}"
        )
    return result


def _bootstrap_delta(
    left: ModelVerticalSlice,
    right: ModelVerticalSlice,
    *,
    rng: np.random.Generator,
    replicates: int,
) -> np.ndarray:
    if replicates < 2:
        raise ValueError("bootstrap replicates must be at least two")
    left_values = left.evaluation.log_likelihood
    right_values = right.evaluation.log_likelihood
    left_prob = np.exp(left.hyperposterior.log_weights)
    right_prob = np.exp(right.hyperposterior.log_weights)
    values = np.empty(replicates, dtype=float)
    for index in range(replicates):
        left_index = rng.choice(
            left.hyperposterior.draw_count,
            size=left.hyperposterior.draw_count,
            replace=True,
            p=left_prob,
        )
        right_index = rng.choice(
            right.hyperposterior.draw_count,
            size=right.hyperposterior.draw_count,
            replace=True,
            p=right_prob,
        )
        values[index] = float(
            logmeanexp(left_values[left_index])
            - logmeanexp(right_values[right_index])
        )
    return values


def compare_vertical_slice_models(
    left: ModelVerticalSlice,
    right: ModelVerticalSlice,
    *,
    numerical_gates: NumericalGates,
    rng: np.random.Generator,
    bootstrap_replicates: int = 500,
    raise_on_failure: bool = True,
) -> ModelComparison:
    """Compare two frozen models with a score-difference MC diagnostic."""

    left_order = [item.event_id for item in left.prequential.steps]
    right_order = [item.event_id for item in right.prequential.steps]
    if left_order != right_order:
        raise ValueError("model evaluations use different chronological event orders")

    delta = float(
        left.report["joint_log_score"] - right.report["joint_log_score"]
    )
    bootstrap = _bootstrap_delta(
        left,
        right,
        rng=rng,
        replicates=bootstrap_replicates,
    )
    q05, median, q95 = np.quantile(bootstrap, [0.05, 0.5, 0.95])
    sigma = float(np.std(bootstrap, ddof=1))
    # A fractional error is not meaningful when the scientifically correct
    # score difference is close to zero.  Require absolute Monte Carlo control
    # everywhere, and add the relative gate only once |delta| is larger than
    # that absolute numerical scale.
    fractional_applicable = (
        abs(delta) > numerical_gates.maximum_mc_sigma_delta_s
    )
    fractional = sigma / abs(delta) if fractional_applicable else None
    gates = {
        "left_model_numerically_valid": left.report["status"] == "PASS",
        "right_model_numerically_valid": right.report["status"] == "PASS",
        "mc_sigma_delta_s": sigma <= numerical_gates.maximum_mc_sigma_delta_s,
        "fractional_mc_error": (
            not fractional_applicable
            or fractional <= numerical_gates.maximum_fractional_mc_error
        ),
    }
    eventwise = tuple(
        {
            "event_id": left_step.event_id,
            "run": left_step.run,
            "left_increment": left_step.log_score_increment,
            "right_increment": right_step.log_score_increment,
            "delta_increment": (
                left_step.log_score_increment - right_step.log_score_increment
            ),
            "cumulative_delta": (
                left_step.cumulative_log_score - right_step.cumulative_log_score
            ),
        }
        for left_step, right_step in zip(
            left.prequential.steps, right.prequential.steps, strict=True
        )
    )
    result = ModelComparison(
        left_model=left.model_name,
        right_model=right.model_name,
        delta_log_score=delta,
        bootstrap_mean=float(np.mean(bootstrap)),
        bootstrap_standard_deviation=sigma,
        bootstrap_fractional_error=(
            float(fractional) if fractional is not None else None
        ),
        fractional_error_applicable=fractional_applicable,
        bootstrap_q05=float(q05),
        bootstrap_median=float(median),
        bootstrap_q95=float(q95),
        numerical_gates=gates,
        eventwise_prequential_delta=eventwise,
    )
    if raise_on_failure and not result.passed:
        failed = [name for name, passed in gates.items() if not passed]
        raise RuntimeError(
            f"Comparison numerical gates failed for {left.model_name} versus "
            f"{right.model_name}: {failed}"
        )
    return result
