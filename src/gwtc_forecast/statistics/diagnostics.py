from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .likelihood import CatalogLikelihoodEvaluation
from .numerics import logmeanexp
from .objects import EventPosterior, HyperPosterior
from .predictive import predictive_log_score


@dataclass(frozen=True)
class ESSSummary:
    minimum: float
    q05: float
    median: float
    q95: float
    maximum: float


@dataclass(frozen=True)
class BootstrapSummary:
    replicates: int
    mean: float
    standard_deviation: float
    q05: float
    median: float
    q95: float


@dataclass(frozen=True)
class EventInfluence:
    event_id: str
    run: str
    full_log_score: float
    leave_one_out_log_score: float
    full_minus_leave_one_out: float


def summarize_ess(values: np.ndarray) -> ESSSummary:
    array = np.asarray(values, dtype=float).ravel()
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError("ESS values must be non-empty and finite")
    quantiles = np.quantile(array, [0.05, 0.5, 0.95])
    return ESSSummary(
        minimum=float(np.min(array)),
        q05=float(quantiles[0]),
        median=float(quantiles[1]),
        q95=float(quantiles[2]),
        maximum=float(np.max(array)),
    )


def bootstrap_predictive_score(
    catalog_log_likelihood: np.ndarray,
    hyperposterior: HyperPosterior,
    *,
    rng: np.random.Generator,
    replicates: int = 500,
) -> BootstrapSummary:
    """Estimate finite-hyperposterior-draw uncertainty by weighted resampling.

    This quantifies Monte Carlo uncertainty from the stored hyperposterior draws.
    It is not catalog variance and does not include PE or injection resampling.
    """

    values = np.asarray(catalog_log_likelihood, dtype=float)
    if values.shape != hyperposterior.log_weights.shape:
        raise ValueError("catalog likelihood and hyperposterior weights disagree")
    if replicates < 2:
        raise ValueError("replicates must be at least two")
    probabilities = np.exp(hyperposterior.log_weights)
    draw_count = hyperposterior.draw_count
    scores = np.empty(replicates, dtype=float)
    for index in range(replicates):
        selected = rng.choice(draw_count, size=draw_count, replace=True, p=probabilities)
        scores[index] = float(logmeanexp(values[selected]))
    quantiles = np.quantile(scores, [0.05, 0.5, 0.95])
    return BootstrapSummary(
        replicates=replicates,
        mean=float(np.mean(scores)),
        standard_deviation=float(np.std(scores, ddof=1)),
        q05=float(quantiles[0]),
        median=float(quantiles[1]),
        q95=float(quantiles[2]),
    )


def leave_one_event_out_influence(
    events: Sequence[EventPosterior],
    evaluation: CatalogLikelihoodEvaluation,
    hyperposterior: HyperPosterior,
) -> tuple[EventInfluence, ...]:
    """Return the change in joint predictive score after removing each event.

    Removing an event also removes one run-specific selection penalty.  These
    values are influence diagnostics, not independently marginalized event
    scores and not a substitute for the chronological prequential increments.
    """

    full = predictive_log_score(evaluation.log_likelihood, hyperposterior)
    output: list[EventInfluence] = []
    for event in events:
        event_eval = evaluation.events[event.event_id]
        selection_eval = evaluation.selections[event.run]
        leave_one_out_log_likelihood = (
            evaluation.log_likelihood
            - event_eval.log_likelihood
            + selection_eval.log_efficiency
        )
        leave_one_out = predictive_log_score(
            leave_one_out_log_likelihood, hyperposterior
        )
        output.append(
            EventInfluence(
                event_id=event.event_id,
                run=event.run,
                full_log_score=full,
                leave_one_out_log_score=leave_one_out,
                full_minus_leave_one_out=full - leave_one_out,
            )
        )
    return tuple(output)
