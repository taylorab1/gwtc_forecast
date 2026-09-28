from __future__ import annotations

import numpy as np

from gwtc_forecast.models import NumericalGates
from gwtc_forecast.statistics.objects import (
    EventPosterior,
    HyperPosterior,
    SelectionCampaign,
)
from gwtc_forecast.workflows.vertical_slice import (
    compare_vertical_slice_models,
    evaluate_model_vertical_slice,
)


class LinearPopulation:
    name = "linear"

    def log_prob(self, samples, hyperparameters):
        x = np.asarray(samples["x"], dtype=float)
        beta = float(hyperparameters["beta"])
        density = 1.0 + beta * (2.0 * x - 1.0)
        result = np.full(x.shape, -np.inf)
        support = (x >= 0.0) & (x <= 1.0) & (density > 0.0)
        result[support] = np.log(density[support])
        return result


def test_vertical_slice_orchestrator_and_model_comparison() -> None:
    posterior = np.linspace(0.65, 0.98, 400)
    event = EventPosterior(
        event_id="GWTEST",
        run="O4a",
        samples={"x": posterior},
        log_pe_prior=np.zeros(len(posterior)),
    )
    injections = np.linspace(0.0005, 0.9995, 2000)
    selection = SelectionCampaign(
        run="O4a",
        samples={"x": injections},
        log_draw_density=np.zeros(len(injections)),
        log_base_weight=np.full(len(injections), -np.log(len(injections))),
    )
    gates = NumericalGates(
        minimum_event_ess=20.0,
        minimum_selection_ess=20.0,
        maximum_joint_prequential_difference=1.0e-12,
        maximum_mc_sigma_delta_s=0.1,
        maximum_fractional_mc_error=0.2,
    )
    left = evaluate_model_vertical_slice(
        events=[event],
        selections={"O4a": selection},
        model=LinearPopulation(),
        hyperposterior=HyperPosterior(
            samples={"beta": np.asarray([0.5])}, model_name="positive_slope"
        ),
        chronological_order=["GWTEST"],
        numerical_gates=gates,
    )
    right = evaluate_model_vertical_slice(
        events=[event],
        selections={"O4a": selection},
        model=LinearPopulation(),
        hyperposterior=HyperPosterior(
            samples={"beta": np.asarray([-0.5])}, model_name="negative_slope"
        ),
        chronological_order=["GWTEST"],
        numerical_gates=gates,
    )
    comparison = compare_vertical_slice_models(
        left,
        right,
        numerical_gates=gates,
        rng=np.random.default_rng(123),
        bootstrap_replicates=20,
    )
    assert left.report["status"] == "PASS"
    assert comparison.delta_log_score > 0.0
    assert comparison.passed
    assert comparison.eventwise_prequential_delta[0]["event_id"] == "GWTEST"


def test_zero_score_difference_is_scientific_null_not_fractional_error_failure() -> None:
    posterior = np.linspace(0.1, 0.9, 200)
    event = EventPosterior(
        event_id="NULL",
        run="O4a",
        samples={"x": posterior},
        log_pe_prior=np.zeros(len(posterior)),
    )
    injections = np.linspace(0.001, 0.999, 1000)
    selection = SelectionCampaign(
        run="O4a",
        samples={"x": injections},
        log_draw_density=np.zeros(len(injections)),
        log_base_weight=np.full(len(injections), -np.log(len(injections))),
    )
    gates = NumericalGates(
        minimum_event_ess=20.0,
        minimum_selection_ess=20.0,
        maximum_joint_prequential_difference=1.0e-12,
        maximum_mc_sigma_delta_s=0.1,
        maximum_fractional_mc_error=0.2,
    )
    kwargs = dict(
        events=[event],
        selections={"O4a": selection},
        model=LinearPopulation(),
        chronological_order=["NULL"],
        numerical_gates=gates,
    )
    left = evaluate_model_vertical_slice(
        **kwargs,
        hyperposterior=HyperPosterior(
            samples={"beta": np.asarray([0.2])}, model_name="same-left"
        ),
    )
    right = evaluate_model_vertical_slice(
        **kwargs,
        hyperposterior=HyperPosterior(
            samples={"beta": np.asarray([0.2])}, model_name="same-right"
        ),
    )
    comparison = compare_vertical_slice_models(
        left,
        right,
        numerical_gates=gates,
        rng=np.random.default_rng(99),
        bootstrap_replicates=20,
    )
    assert np.isclose(comparison.delta_log_score, 0.0)
    assert comparison.bootstrap_fractional_error is None
    assert not comparison.fractional_error_applicable
    assert comparison.passed
