from __future__ import annotations

import csv

import h5py
import numpy as np

from gwtc_forecast.io.pe_summary import read_pe_summary_table, write_pe_index_csv


def test_pe_summary_compound_table_is_indexed_without_astropy(tmp_path) -> None:
    path = tmp_path / "summary.hdf5"
    dtype = np.dtype(
        [
            ("result_label", "S80"),
            ("gw_name", "S20"),
            ("result_file_name", "S120"),
            ("result_samples_key", "S60"),
            ("mass_1_source_median", "f8"),
        ]
    )
    rows = np.zeros(3, dtype=dtype)
    rows[0] = (
        b"GW000001_000001-C00:WaveA",
        b"GW000001_000001",
        b"event-a.hdf5",
        b"C00:WaveA",
        35.0,
    )
    rows[1] = (
        b"GW000001_000001-C00:WaveB",
        b"GW000001_000001",
        b"event-a.hdf5",
        b"C00:WaveB",
        35.2,
    )
    rows[2] = (
        b"GW000002_000002-C00:WaveA",
        b"GW000002_000002",
        b"event-b.hdf5",
        b"C00:WaveA",
        12.0,
    )
    with h5py.File(path, "w") as handle:
        handle.create_dataset("__astropy_table__", data=rows)

    report = read_pe_summary_table(path, event_ids=["GW000001_000001"])
    assert report["storage"] == "compound_dataset"
    assert report["selected_row_count"] == 2
    assert report["events"]["GW000001_000001"]["candidate_labels"] == [
        "C00:WaveA",
        "C00:WaveB",
    ]
    assert report["consistency_errors"] == []
    assert not report["production_label_frozen"]

    output = tmp_path / "index.csv"
    write_pe_index_csv(output, report)
    with output.open(newline="") as stream:
        loaded = list(csv.DictReader(stream))
    assert len(loaded) == 2
    assert loaded[0]["result_file_name"] == "event-a.hdf5"
