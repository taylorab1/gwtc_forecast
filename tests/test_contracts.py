from __future__ import annotations

import numpy as np

from gwtc_forecast.io.contracts import (
    read_event_contract,
    read_hyperposterior_contract,
    read_selection_contract,
    write_event_contract,
    write_hyperposterior_contract,
    write_selection_contract,
)
from gwtc_forecast.statistics.objects import (
    EventPosterior,
    HyperPosterior,
    SelectionCampaign,
)


def test_processed_contracts_round_trip(tmp_path) -> None:
    event = EventPosterior(
        event_id="GWTEST",
        run="O4a",
        samples={"mass_1_source": np.asarray([10.0, 11.0, 12.0])},
        log_pe_prior=np.asarray([-2.0, -2.0, -2.0]),
        metadata={"label": "frozen", "checksum": "abc"},
        log_sample_weights=np.log(np.asarray([0.6, 0.3, 0.1])),
    )
    event_path = tmp_path / "event.hdf5"
    write_event_contract(event_path, event)
    restored_event = read_event_contract(event_path)
    assert restored_event.event_id == event.event_id
    assert restored_event.metadata == event.metadata
    assert np.array_equal(
        restored_event.samples["mass_1_source"], event.samples["mass_1_source"]
    )
    assert np.allclose(restored_event.log_sample_weights, event.log_sample_weights)

    selection = SelectionCampaign(
        run="O4a",
        samples={"mass_1_source": np.asarray([20.0, 30.0, 40.0])},
        log_draw_density=np.asarray([-3.0, -3.0, -3.0]),
        log_base_weight=np.asarray([-5.0, -5.0, -5.0]),
        metadata={"generated": 1000},
    )
    selection_path = tmp_path / "selection.hdf5"
    write_selection_contract(selection_path, selection)
    restored_selection = read_selection_contract(selection_path)
    assert restored_selection.run == selection.run
    assert restored_selection.metadata == selection.metadata
    assert np.array_equal(
        restored_selection.log_base_weight, selection.log_base_weight
    )

    hyperposterior = HyperPosterior(
        samples={
            "alpha": np.asarray([-2.1, -2.0, -1.9]),
            "m_max": np.asarray([80.0, 85.0, 90.0]),
        },
        log_weights=np.log(np.asarray([0.2, 0.3, 0.5])),
        model_name="PowerLawPeak",
        metadata={"source_role": "released"},
    )
    hyper_path = tmp_path / "hyperposterior.hdf5"
    write_hyperposterior_contract(hyper_path, hyperposterior)
    restored_hyper = read_hyperposterior_contract(hyper_path)
    assert restored_hyper.model_name == "PowerLawPeak"
    assert restored_hyper.metadata == hyperposterior.metadata
    assert np.allclose(restored_hyper.log_weights, hyperposterior.log_weights)
