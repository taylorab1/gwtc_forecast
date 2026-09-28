from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.special import logsumexp

from ..populations.protocol import PopulationModel
from .numerics import effective_sample_size_from_log_weights
from .objects import EventPosterior, HyperPosterior, SelectionCampaign


@dataclass(frozen=True)
class EventLikelihoodEvaluation:
    event_id: str
    run: str
    log_likelihood: np.ndarray
    effective_sample_size: np.ndarray


@dataclass(frozen=True)
class SelectionEvaluation:
    run: str
    log_efficiency: np.ndarray
    effective_sample_size: np.ndarray


@dataclass(frozen=True)
class CatalogLikelihoodEvaluation:
    log_likelihood: np.ndarray
    events: dict[str, EventLikelihoodEvaluation]
    selections: dict[str, SelectionEvaluation]


def event_log_likelihood(
    event: EventPosterior,
    model: PopulationModel,
    hyperposterior: HyperPosterior,
) -> EventLikelihoodEvaluation:
    """Evaluate one event for every population-hyperposterior draw.

    For normalized event-posterior row weights ``q_k`` the estimator is

    ``sum_k q_k * p(theta_k | Lambda) / pi_PE(theta_k)``.

    Equal-weight products recover the original arithmetic mean exactly.
    """

    log_likelihood = np.empty(hyperposterior.draw_count, dtype=float)
    ess = np.empty(hyperposterior.draw_count, dtype=float)
    for index in range(hyperposterior.draw_count):
        log_population = np.asarray(
            model.log_prob(event.samples, hyperposterior.draw(index)), dtype=float
        )
        if log_population.shape != event.log_pe_prior.shape:
            raise ValueError(
                f"model returned shape {log_population.shape} for event {event.event_id}; "
                f"expected {event.log_pe_prior.shape}"
            )
        log_terms = (
            event.log_sample_weights + log_population - event.log_pe_prior
        )
        if np.isnan(log_terms).any() or np.isposinf(log_terms).any():
            raise ValueError(f"invalid event weights for {event.event_id}")
        if np.isneginf(log_terms).all():
            raise ValueError(
                f"all posterior samples have zero population support for {event.event_id}"
            )
        log_likelihood[index] = logsumexp(log_terms)
        ess[index] = effective_sample_size_from_log_weights(log_terms)
    return EventLikelihoodEvaluation(
        event_id=event.event_id,
        run=event.run,
        log_likelihood=log_likelihood,
        effective_sample_size=ess,
    )


def _selection_log_terms(
    campaign: SelectionCampaign,
    model: PopulationModel,
    hyperparameters: Mapping[str, float],
) -> np.ndarray:
    log_population = np.asarray(
        model.log_prob(campaign.samples, hyperparameters), dtype=float
    )
    if log_population.shape != campaign.log_draw_density.shape:
        raise ValueError(
            f"model returned shape {log_population.shape} for {campaign.run}; "
            f"expected {campaign.log_draw_density.shape}"
        )
    log_terms = campaign.log_base_weight + log_population - campaign.log_draw_density
    if np.isnan(log_terms).any() or np.isposinf(log_terms).any():
        raise ValueError(f"invalid selection weights for {campaign.run}")
    return log_terms


def selection_log_efficiency(
    campaign: SelectionCampaign,
    model: PopulationModel,
    hyperposterior: HyperPosterior,
) -> SelectionEvaluation:
    log_efficiency = np.empty(hyperposterior.draw_count, dtype=float)
    ess = np.empty(hyperposterior.draw_count, dtype=float)
    for index in range(hyperposterior.draw_count):
        log_terms = _selection_log_terms(
            campaign, model, hyperposterior.draw(index)
        )
        if np.isneginf(log_terms).all():
            raise ValueError(
                f"all injections have zero population support for {campaign.run}"
            )
        log_efficiency[index] = logsumexp(log_terms)
        ess[index] = effective_sample_size_from_log_weights(log_terms)
    return SelectionEvaluation(
        run=campaign.run,
        log_efficiency=log_efficiency,
        effective_sample_size=ess,
    )


def selection_log_efficiency_chunked(
    campaign_chunks: Iterable[SelectionCampaign],
    model: PopulationModel,
    hyperposterior: HyperPosterior,
) -> SelectionEvaluation:
    """Evaluate a selection campaign in bounded-memory chunks.

    Each chunk must contain slices of the same globally normalized campaign.
    The function accumulates both ``sum(w)`` and ``sum(w**2)`` in log space, so
    the returned efficiency and ESS are mathematically identical to evaluating
    a single in-memory ``SelectionCampaign`` up to floating-point roundoff.
    """

    log_sum_weights = np.full(hyperposterior.draw_count, -np.inf, dtype=float)
    log_sum_squared_weights = np.full(
        hyperposterior.draw_count, -np.inf, dtype=float
    )
    run: str | None = None
    chunk_count = 0
    for campaign in campaign_chunks:
        chunk_count += 1
        if run is None:
            run = campaign.run
        elif campaign.run != run:
            raise ValueError(
                f"selection chunks contain multiple runs: {run!r} and {campaign.run!r}"
            )
        for index in range(hyperposterior.draw_count):
            log_terms = _selection_log_terms(
                campaign, model, hyperposterior.draw(index)
            )
            if np.isneginf(log_terms).all():
                continue
            log_sum_weights[index] = np.logaddexp(
                log_sum_weights[index], logsumexp(log_terms)
            )
            log_sum_squared_weights[index] = np.logaddexp(
                log_sum_squared_weights[index], logsumexp(2.0 * log_terms)
            )

    if chunk_count == 0 or run is None:
        raise ValueError("selection_log_efficiency_chunked requires at least one chunk")
    unsupported = np.isneginf(log_sum_weights)
    if unsupported.any():
        indices = np.flatnonzero(unsupported).tolist()
        raise ValueError(
            f"all injections have zero population support for {run} at "
            f"hyperposterior draws {indices[:10]}"
        )
    ess = np.exp(2.0 * log_sum_weights - log_sum_squared_weights)
    return SelectionEvaluation(
        run=run,
        log_efficiency=log_sum_weights,
        effective_sample_size=ess,
    )


def catalog_log_likelihood(
    events: Sequence[EventPosterior],
    selections: Mapping[str, SelectionCampaign],
    model: PopulationModel,
    hyperposterior: HyperPosterior,
) -> CatalogLikelihoodEvaluation:
    if not events:
        raise ValueError("catalog must contain at least one event")
    required_runs = {event.run for event in events}
    missing_runs = required_runs - set(selections)
    if missing_runs:
        raise KeyError(f"missing selection campaigns for runs: {sorted(missing_runs)}")

    selection_evaluations = {
        run: selection_log_efficiency(selections[run], model, hyperposterior)
        for run in sorted(required_runs)
    }
    event_evaluations = {
        event.event_id: event_log_likelihood(event, model, hyperposterior)
        for event in events
    }
    if len(event_evaluations) != len(events):
        raise ValueError("event IDs must be unique")
    total = np.zeros(hyperposterior.draw_count, dtype=float)
    counts: dict[str, int] = {}
    for event in events:
        total += event_evaluations[event.event_id].log_likelihood
        counts[event.run] = counts.get(event.run, 0) + 1
    for run, count in counts.items():
        total -= count * selection_evaluations[run].log_efficiency

    return CatalogLikelihoodEvaluation(
        log_likelihood=total,
        events=event_evaluations,
        selections=selection_evaluations,
    )
