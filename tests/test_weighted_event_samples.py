from __future__ import annotations

import h5py
import numpy as np
import pytest

from gwtc_forecast.io.contracts import (
    EVENT_SCHEMA_V1,
    read_event_contract,
    write_event_contract,
)
from gwtc_forecast.statistics.likelihood import event_log_likelihood
from gwtc_forecast.statistics.objects import EventPosterior, HyperPosterior


class TabulatedPopulation:
    name = "tabulated"

    def log_prob(self, samples, hyperparameters):
        del hyperparameters
        x = np.asarray(samples["x"], dtype=float)
        return np.log(1.0 + 2.0 * x)


def test_unequal_posterior_sample_weights_enter_event_integral() -> None:
    event = EventPosterior(
        event_id="weighted",
        run="O4a",
        samples={"x": np.asarray([0.0, 1.0])},
        log_pe_prior=np.zeros(2),
        log_sample_weights=np.log(np.asarray([0.9, 0.1])),
    )
    hp = HyperPosterior(samples={"dummy": np.asarray([0.0])})
    result = event_log_likelihood(event, TabulatedPopulation(), hp)
    assert np.isclose(result.log_likelihood[0], np.log(0.9 * 1.0 + 0.1 * 3.0))
    assert np.isclose(np.exp(event.log_sample_weights).sum(), 1.0)
    assert np.isclose(event.posterior_sample_ess, 1.0 / (0.9**2 + 0.1**2))


def test_weighted_rows_match_explicit_equal_weight_replication() -> None:
    weighted = EventPosterior(
        event_id="weighted",
        run="O4a",
        samples={"x": np.asarray([0.0, 1.0])},
        log_pe_prior=np.zeros(2),
        log_sample_weights=np.log(np.asarray([0.9, 0.1])),
    )
    replicated = EventPosterior(
        event_id="replicated",
        run="O4a",
        samples={"x": np.asarray([0.0] * 9 + [1.0])},
        log_pe_prior=np.zeros(10),
    )
    hp = HyperPosterior(samples={"dummy": np.asarray([0.0])})
    left = event_log_likelihood(weighted, TabulatedPopulation(), hp)
    right = event_log_likelihood(replicated, TabulatedPopulation(), hp)
    assert np.allclose(left.log_likelihood, right.log_likelihood)


@pytest.mark.parametrize(
    "weights,match",
    [
        (np.asarray([-np.inf, -np.inf]), "all log weights"),
        (np.asarray([0.0, np.nan]), "NaN"),
        (np.asarray([0.0]), "incompatible shape"),
    ],
)
def test_invalid_event_log_sample_weights_fail(weights, match) -> None:
    with pytest.raises(ValueError, match=match):
        EventPosterior(
            event_id="bad",
            run="O4a",
            samples={"x": np.asarray([0.0, 1.0])},
            log_pe_prior=np.zeros(2),
            log_sample_weights=weights,
        )


def test_event_contract_v2_preserves_weights_and_v1_reads_as_uniform(tmp_path) -> None:
    event = EventPosterior(
        event_id="GWTEST",
        run="O4a",
        samples={"x": np.asarray([0.0, 1.0])},
        log_pe_prior=np.zeros(2),
        log_sample_weights=np.log(np.asarray([0.8, 0.2])),
    )
    path = tmp_path / "event_v2.h5"
    write_event_contract(path, event)
    restored = read_event_contract(path)
    assert np.allclose(restored.log_sample_weights, event.log_sample_weights)

    old = tmp_path / "event_v1.h5"
    with h5py.File(old, "w") as handle:
        handle.attrs["schema"] = EVENT_SCHEMA_V1
        handle.attrs["event_id"] = "OLD"
        handle.attrs["run"] = "O4a"
        handle.attrs["metadata_json"] = "{}"
        handle.create_group("samples").create_dataset("x", data=np.asarray([0.0, 1.0]))
        handle.create_dataset("log_pe_prior", data=np.zeros(2))
    restored_old = read_event_contract(old)
    assert np.allclose(np.exp(restored_old.log_sample_weights), [0.5, 0.5])
