from __future__ import annotations

import h5py
import numpy as np

from gwtc_forecast.io.injections import (
    DOCUMENTED_INTRINSIC_FIELDS,
    DOCUMENTED_LOG_DRAW_FIELDS,
    inspect_injection_file,
)


def test_documented_o4_injection_schema_is_discovered(tmp_path) -> None:
    path = tmp_path / "injections.hdf"
    fields = [
        *(name for name in DOCUMENTED_INTRINSIC_FIELDS),
        *(name for name in DOCUMENTED_LOG_DRAW_FIELDS),
        "weights",
        "time_geocenter",
        "gstlal_far",
        "pycbc_far",
    ]
    dtype = np.dtype([(name, "f8") for name in fields])
    rows = np.zeros(120, dtype=dtype)
    rows["weights"] = 1.0
    with h5py.File(path, "w") as handle:
        handle.attrs["gps_start"] = 1366933504
        handle.attrs["gps_end"] = 1422403072
        handle.attrs["total_analysis_time"] = 1.0
        handle.attrs["total_generated"] = 1000000
        handle.attrs["num_accepted"] = 120
        handle.attrs["searches"] = np.asarray([b"gstlal", b"pycbc"])
        handle.attrs["date"] = "test"
        handle.create_dataset("events", data=rows)

    report = inspect_injection_file(path)
    schema = report["documented_schema"]
    assert schema["events_dataset_present"]
    assert schema["schema_names_match_documentation"]
    assert schema["missing_required_fields"] == []
    assert schema["search_far_fields_missing"] == []
    assert not report["production_mapping_complete"]
