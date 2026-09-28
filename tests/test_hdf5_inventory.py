from __future__ import annotations

import h5py
import numpy as np

from gwtc_forecast.io.hdf5 import candidate_tabular_groups, inventory_hdf5


def test_hdf5_inventory_and_table_discovery(tmp_path) -> None:
    path = tmp_path / "sample.hdf5"
    with h5py.File(path, "w") as handle:
        handle.attrs["release"] = "test"
        table = handle.create_group("table")
        table.create_dataset("mass_1_source", data=np.arange(100.0))
        table.create_dataset("redshift", data=np.linspace(0.0, 1.0, 100))
        handle.create_dataset("matrix", data=np.zeros((3, 4)))
        structured = np.zeros(50, dtype=[("mass", "f8"), ("far", "f8")])
        handle.create_dataset("structured", data=structured)

    report = inventory_hdf5(path)
    assert report["root_attributes"]["release"] == "test"
    assert any(node["path"] == "/table/mass_1_source" for node in report["nodes"])
    candidates = candidate_tabular_groups(path)
    by_group = {item["group"]: item for item in candidates}
    assert by_group["/table"]["row_count"] == 100
    assert by_group["/structured"]["storage"] == "compound_dataset"
