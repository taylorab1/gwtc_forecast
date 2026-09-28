from __future__ import annotations

import h5py
import numpy as np
import pytest

from gwtc_forecast.io.contracts import (
    iter_selection_contract_chunks,
    selection_contract_summary,
    write_selection_contract,
)
from gwtc_forecast.statistics.likelihood import (
    selection_log_efficiency,
    selection_log_efficiency_chunked,
)
from gwtc_forecast.statistics.objects import HyperPosterior, SelectionCampaign


class LinearPopulation:
    name = "linear"

    def log_prob(self, samples, hyperparameters):
        x = np.asarray(samples["x"], dtype=float)
        beta = float(hyperparameters["beta"])
        return np.log1p(beta * x)


def test_chunked_selection_evaluation_matches_in_memory(tmp_path) -> None:
    count = 103
    campaign = SelectionCampaign(
        run="O4b",
        samples={"x": np.linspace(0.0, 1.0, count)},
        log_draw_density=np.zeros(count),
        log_base_weight=np.full(count, -np.log(count)),
        metadata={"global_normalization": True},
    )
    path = tmp_path / "selection.h5"
    write_selection_contract(path, campaign)
    summary = selection_contract_summary(path)
    assert summary.injection_count == count

    hp = HyperPosterior(samples={"beta": np.asarray([0.0, 0.3, 0.8])})
    full = selection_log_efficiency(campaign, LinearPopulation(), hp)
    streamed = selection_log_efficiency_chunked(
        iter_selection_contract_chunks(path, chunk_rows=17),
        LinearPopulation(),
        hp,
    )
    assert np.allclose(streamed.log_efficiency, full.log_efficiency, atol=1e-14)
    assert np.allclose(streamed.effective_sample_size, full.effective_sample_size)


def test_streaming_contract_validates_all_dataset_lengths(tmp_path) -> None:
    path = tmp_path / "broken.h5"
    with h5py.File(path, "w") as handle:
        handle.attrs["schema"] = "gwtc_forecast.processed_selection.v1"
        handle.attrs["run"] = "O4a"
        handle.attrs["metadata_json"] = "{}"
        handle.create_group("samples").create_dataset("x", data=np.arange(5.0))
        handle.create_dataset("log_draw_density", data=np.zeros(5))
        handle.create_dataset("log_base_weight", data=np.zeros(4))
    with pytest.raises(ValueError, match="row-count mismatch"):
        selection_contract_summary(path)


def test_chunked_selection_rejects_mixed_runs() -> None:
    chunks = [
        SelectionCampaign(
            run=run,
            samples={"x": np.asarray([0.5])},
            log_draw_density=np.zeros(1),
            log_base_weight=np.zeros(1),
        )
        for run in ("O4a", "O4b")
    ]
    hp = HyperPosterior(samples={"beta": np.asarray([0.0])})
    with pytest.raises(ValueError, match="multiple runs"):
        selection_log_efficiency_chunked(chunks, LinearPopulation(), hp)
