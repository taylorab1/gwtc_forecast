from __future__ import annotations

import numpy as np

from gwtc_forecast.statistics.diagnostics import (
    bootstrap_predictive_score,
    leave_one_event_out_influence,
    summarize_ess,
)
from gwtc_forecast.statistics.likelihood import catalog_log_likelihood
from gwtc_forecast.statistics.objects import (
    EventPosterior,
    HyperPosterior,
    SelectionCampaign,
)


class UniformPopulation:
    name = "uniform"

    def log_prob(self, samples, hyperparameters):
        del hyperparameters
        return np.full(len(samples["x"]), -np.log(2.0))


def _problem():
    event = EventPosterior(
        event_id="A",
        run="run",
        samples={"x": np.linspace(0.01, 1.99, 300)},
        log_pe_prior=np.full(300, -np.log(2.0)),
    )
    selection = SelectionCampaign(
        run="run",
        samples={"x": np.linspace(0.001, 1.999, 1000)},
        log_draw_density=np.full(1000, -np.log(2.0)),
        log_base_weight=np.full(1000, -np.log(1000)),
    )
    hp = HyperPosterior(samples={"dummy": np.arange(5.0)})
    evaluation = catalog_log_likelihood(
        [event], {"run": selection}, UniformPopulation(), hp
    )
    return event, hp, evaluation


def test_ess_summary() -> None:
    summary = summarize_ess(np.asarray([1.0, 2.0, 3.0, 4.0]))
    assert summary.minimum == 1.0
    assert summary.maximum == 4.0
    assert summary.median == 2.5


def test_bootstrap_and_influence_for_uniform_problem() -> None:
    event, hp, evaluation = _problem()
    bootstrap = bootstrap_predictive_score(
        evaluation.log_likelihood,
        hp,
        rng=np.random.default_rng(10),
        replicates=50,
    )
    assert np.isclose(bootstrap.mean, 0.0, atol=1e-12)
    assert np.isclose(bootstrap.standard_deviation, 0.0, atol=1e-12)
    influence = leave_one_event_out_influence([event], evaluation, hp)
    assert len(influence) == 1
    assert np.isclose(influence[0].full_minus_leave_one_out, 0.0, atol=1e-12)
