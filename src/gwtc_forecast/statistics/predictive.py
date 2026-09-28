from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.special import logsumexp

from .likelihood import CatalogLikelihoodEvaluation
from .numerics import (
    assert_close_joint_prequential,
    mixed_tolerance_limit,
    normalize_log_weights,
)
from .objects import EventPosterior, HyperPosterior


@dataclass(frozen=True)
class PrequentialStep:
    event_id: str
    run: str
    log_score_increment: float
    cumulative_log_score: float
    hyperposterior_ess: float


@dataclass(frozen=True)
class PrequentialResult:
    joint_log_score: float
    cumulative_log_score: float
    absolute_difference: float
    comparison_tolerance: float
    steps: tuple[PrequentialStep, ...]
    final_log_weights: np.ndarray


def predictive_log_score(
    catalog_log_likelihood: np.ndarray, hyperposterior: HyperPosterior
) -> float:
    values = np.asarray(catalog_log_likelihood, dtype=float)
    if values.shape != hyperposterior.log_weights.shape:
        raise ValueError("catalog likelihood and hyperposterior weights disagree")
    return float(logsumexp(hyperposterior.log_weights + values))


def prequential_score(
    events_in_order: Sequence[EventPosterior],
    evaluation: CatalogLikelihoodEvaluation,
    hyperposterior: HyperPosterior,
    *,
    tolerance: float = 1.0e-10,
) -> PrequentialResult:
    log_weights = np.array(hyperposterior.log_weights, copy=True)
    cumulative = 0.0
    steps: list[PrequentialStep] = []
    for event in events_in_order:
        event_eval = evaluation.events[event.event_id]
        selection_eval = evaluation.selections[event.run]
        log_increment_by_draw = (
            event_eval.log_likelihood - selection_eval.log_efficiency
        )
        increment = float(logsumexp(log_weights + log_increment_by_draw))
        cumulative += increment
        log_weights = normalize_log_weights(log_weights + log_increment_by_draw)
        ess = float(1.0 / np.sum(np.exp(log_weights) ** 2))
        steps.append(
            PrequentialStep(
                event_id=event.event_id,
                run=event.run,
                log_score_increment=increment,
                cumulative_log_score=cumulative,
                hyperposterior_ess=ess,
            )
        )

    joint = predictive_log_score(evaluation.log_likelihood, hyperposterior)
    assert_close_joint_prequential(joint, cumulative, tolerance)
    comparison_tolerance = mixed_tolerance_limit(
        joint,
        cumulative,
        absolute_tolerance=tolerance,
        relative_tolerance=1.0e-12,
    )
    return PrequentialResult(
        joint_log_score=joint,
        cumulative_log_score=cumulative,
        absolute_difference=abs(joint - cumulative),
        comparison_tolerance=comparison_tolerance,
        steps=tuple(steps),
        final_log_weights=log_weights,
    )
