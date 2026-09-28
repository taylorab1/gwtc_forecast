from __future__ import annotations

import numpy as np

from gwtc_forecast.statistics.likelihood import catalog_log_likelihood
from gwtc_forecast.statistics.objects import (
    EventPosterior,
    HyperPosterior,
    SelectionCampaign,
)
from gwtc_forecast.statistics.predictive import predictive_log_score, prequential_score


class UniformPopulation:
    name = "uniform"

    def log_prob(self, samples, hyperparameters):
        del hyperparameters
        values = np.asarray(samples["x"])
        return np.full(values.shape, -np.log(2.0))


def test_uniform_problem_has_zero_shape_log_likelihood() -> None:
    sample = np.linspace(0.01, 1.99, 500)
    event_a = EventPosterior(
        event_id="A",
        run="run",
        samples={"x": sample},
        log_pe_prior=np.full(len(sample), -np.log(2.0)),
    )
    event_b = EventPosterior(
        event_id="B",
        run="run",
        samples={"x": sample[::-1]},
        log_pe_prior=np.full(len(sample), -np.log(2.0)),
    )
    generated = 2000
    campaign = SelectionCampaign(
        run="run",
        samples={"x": np.linspace(0.001, 1.999, generated)},
        log_draw_density=np.full(generated, -np.log(2.0)),
        log_base_weight=np.full(generated, -np.log(generated)),
    )
    hyperposterior = HyperPosterior(samples={"dummy": np.arange(4.0)})
    evaluation = catalog_log_likelihood(
        [event_a, event_b],
        {"run": campaign},
        UniformPopulation(),
        hyperposterior,
    )
    assert np.allclose(evaluation.log_likelihood, 0.0, atol=1e-12)
    joint = predictive_log_score(evaluation.log_likelihood, hyperposterior)
    sequential = prequential_score(
        [event_a, event_b], evaluation, hyperposterior, tolerance=1e-12
    )
    assert np.isclose(joint, 0.0, atol=1e-12)
    assert np.isclose(sequential.cumulative_log_score, joint, atol=1e-12)
    assert all(step.hyperposterior_ess == 4.0 for step in sequential.steps)


def test_event_order_changes_steps_but_not_joint_score() -> None:
    sample = np.linspace(0.01, 1.99, 200)
    events = [
        EventPosterior(
            event_id=name,
            run="run",
            samples={"x": sample + offset},
            log_pe_prior=np.full(len(sample), -np.log(2.0)),
        )
        for name, offset in (("A", 0.0), ("B", 0.0))
    ]
    campaign = SelectionCampaign(
        run="run",
        samples={"x": np.linspace(0.001, 1.999, 1000)},
        log_draw_density=np.full(1000, -np.log(2.0)),
        log_base_weight=np.full(1000, -np.log(1000)),
    )
    hp = HyperPosterior(samples={"dummy": np.arange(3.0)})
    evaluation = catalog_log_likelihood(
        events, {"run": campaign}, UniformPopulation(), hp
    )
    first = prequential_score(events, evaluation, hp)
    second = prequential_score(list(reversed(events)), evaluation, hp)
    assert np.isclose(first.joint_log_score, second.joint_log_score)
