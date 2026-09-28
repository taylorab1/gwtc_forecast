from __future__ import annotations

import numpy as np

from gwtc_forecast.populations.toy_mass import (
    BrokenPowerLaw,
    PowerLaw,
    PowerLawPlusPeak,
)


def _integral(model, hyperparameters) -> float:
    grid = np.linspace(hyperparameters["m_min"], hyperparameters["m_max"], 20001)
    density = np.exp(model.log_prob({"mass_1_source": grid}, hyperparameters))
    return float(np.trapezoid(density, grid))


def test_all_toy_mass_models_are_normalized() -> None:
    smooth = {"alpha": -2.0, "m_min": 5.0, "m_max": 90.0}
    peak = {
        **smooth,
        "peak_fraction": 0.25,
        "peak_mean": 35.0,
        "peak_sigma": 3.0,
    }
    broken = {
        "alpha_low": -1.0,
        "alpha_high": -3.0,
        "m_min": 5.0,
        "m_break": 35.0,
        "m_max": 90.0,
    }
    assert np.isclose(_integral(PowerLaw(), smooth), 1.0, atol=2e-6)
    assert np.isclose(_integral(PowerLawPlusPeak(), peak), 1.0, atol=2e-6)
    assert np.isclose(_integral(BrokenPowerLaw(), broken), 1.0, atol=2e-6)


def test_toy_sampling_respects_support() -> None:
    rng = np.random.default_rng(4)
    hyper = {
        "alpha": -2.0,
        "m_min": 5.0,
        "m_max": 90.0,
        "peak_fraction": 0.4,
        "peak_mean": 35.0,
        "peak_sigma": 3.0,
    }
    sample = PowerLawPlusPeak().sample(rng, 2000, hyper)
    assert np.all((sample >= 5.0) & (sample <= 90.0))
