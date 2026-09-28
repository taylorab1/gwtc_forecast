from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np

from .hdf5 import candidate_tabular_groups, inventory_hdf5

# Official O4 observing-run intervals documented with the public injection file.
# They are discovery/audit values here, not an assertion that a simple row split
# alone supplies the correct run-specific normalization.
DOCUMENTED_RUN_WINDOWS = {
    "O4a": {"gps_start": 1368975618, "gps_end": 1389456018},
    "O4b": {"gps_start": 1396969218, "gps_end": 1422118818},
}

DOCUMENTED_ROOT_ATTRIBUTES = (
    "gps_start",
    "gps_end",
    "total_analysis_time",
    "total_generated",
    "num_accepted",
    "searches",
    "date",
)

DOCUMENTED_INTRINSIC_FIELDS = (
    "mass1_source",
    "mass2_source",
    "mass1_detector",
    "mass2_detector",
    "q",
    "eta",
    "z",
    "spin1_magnitude",
    "spin1_polar_angle",
    "spin1_azimuthal_angle",
    "spin2_magnitude",
    "spin2_polar_angle",
    "spin2_azimuthal_angle",
)

# The official release example builds the population draw density for a
# mass-spin-redshift model from this sum.  Extrinsic parameters are deliberately
# not included in that example because the target population uses the released
# extrinsic draw distributions.
DOCUMENTED_LOG_DRAW_FIELDS = (
    "lnpdraw_mass1_source",
    "lnpdraw_mass2_source_GIVEN_mass1_source",
    "lnpdraw_z",
    "lnpdraw_spin1_magnitude",
    "lnpdraw_spin1_polar_angle",
    "lnpdraw_spin1_azimuthal_angle",
    "lnpdraw_spin2_magnitude",
    "lnpdraw_spin2_polar_angle",
    "lnpdraw_spin2_azimuthal_angle",
)

DOCUMENTED_WEIGHT_FIELD = "weights"
DOCUMENTED_TIME_FIELD = "time_geocenter"

KEYWORDS = (
    "mass",
    "redshift",
    "distance",
    "far",
    "pastro",
    "found",
    "weight",
    "draw",
    "sampling",
    "o4a",
    "o4b",
    "run",
)


def _decode(value: Any) -> Any:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, np.ndarray):
        return [_decode(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _decode(value.item())
    return value


def _search_names(value: Any) -> list[str]:
    decoded = _decode(value)
    if decoded is None:
        return []
    if isinstance(decoded, str):
        # HDF attributes may be a single search or a serialized list.
        return [decoded]
    if isinstance(decoded, Iterable):
        return [str(item) for item in decoded]
    return [str(decoded)]


def inspect_injection_file(path: Path) -> dict[str, Any]:
    """Audit the documented O4 sensitivity schema without loading the table.

    Matching the documented names is necessary but not sufficient for
    production.  In particular, the O4a/O4b denominator and wall-time mixture
    normalization still require an independent fixed-point comparison before
    processed ``SelectionCampaign`` objects may be used in real-data scoring.
    """

    path = Path(path)
    inventory = inventory_hdf5(path, max_depth=8, max_nodes=10000)
    tables = candidate_tabular_groups(path, minimum_rows=100)
    keyword_hits: list[dict[str, str]] = []
    for node in inventory["nodes"]:
        name = node["path"].lower()
        for keyword in KEYWORDS:
            if keyword in name:
                keyword_hits.append({"keyword": keyword, "path": node["path"]})
                break

    schema: dict[str, Any] = {
        "events_dataset_present": False,
        "events_storage": None,
        "row_count": None,
        "available_fields": [],
        "root_attributes": {},
        "searches": [],
        "far_fields_from_searches": [],
        "available_far_fields": [],
    }
    with h5py.File(path, "r") as handle:
        attrs = {str(key): _decode(value) for key, value in handle.attrs.items()}
        schema["root_attributes"] = attrs
        searches = _search_names(attrs.get("searches"))
        schema["searches"] = searches
        schema["far_fields_from_searches"] = [f"{name}_far" for name in searches]
        if "events" in handle and isinstance(handle["events"], h5py.Dataset):
            events = handle["events"]
            fields = tuple(str(name) for name in (events.dtype.names or ()))
            schema.update(
                {
                    "events_dataset_present": True,
                    "events_storage": "compound_dataset",
                    "row_count": len(events),
                    "available_fields": sorted(fields),
                    "available_far_fields": sorted(
                        name for name in fields if name.endswith("_far")
                    ),
                }
            )

    attributes = set(schema["root_attributes"])
    fields = set(schema["available_fields"])
    required_fields = {
        *DOCUMENTED_INTRINSIC_FIELDS,
        *DOCUMENTED_LOG_DRAW_FIELDS,
        DOCUMENTED_WEIGHT_FIELD,
        DOCUMENTED_TIME_FIELD,
    }
    far_fields = set(schema["available_far_fields"])
    requested_far = set(schema["far_fields_from_searches"])
    documented_match = (
        schema["events_dataset_present"]
        and not (set(DOCUMENTED_ROOT_ATTRIBUTES) - attributes)
        and not (required_fields - fields)
        and bool(far_fields)
    )

    report = {
        "schema": "gwtc_forecast.o4_injection_schema_audit.v1",
        "path": str(path),
        "inventory": inventory,
        "candidate_tables": tables,
        "keyword_hits": keyword_hits,
        "documented_schema": {
            **schema,
            "required_root_attributes": list(DOCUMENTED_ROOT_ATTRIBUTES),
            "missing_root_attributes": sorted(
                set(DOCUMENTED_ROOT_ATTRIBUTES) - attributes
            ),
            "required_intrinsic_fields": list(DOCUMENTED_INTRINSIC_FIELDS),
            "required_log_draw_fields": list(DOCUMENTED_LOG_DRAW_FIELDS),
            "weight_field": DOCUMENTED_WEIGHT_FIELD,
            "time_field": DOCUMENTED_TIME_FIELD,
            "missing_required_fields": sorted(required_fields - fields),
            "search_far_fields_missing": sorted(requested_far - far_fields),
            "run_windows": DOCUMENTED_RUN_WINDOWS,
            "schema_names_match_documentation": documented_match,
        },
        "candidate_population_log_draw_expression": " + ".join(
            DOCUMENTED_LOG_DRAW_FIELDS
        ),
        "candidate_found_mask_expression": (
            "minimum finite FAR across the released search-specific *_far fields "
            "is below the frozen FAR threshold"
        ),
        "candidate_combined_campaign_base_weight_expression": (
            "log(weights) - log(total_generated) after applying the found mask"
        ),
        "production_mapping_complete": False,
        "unresolved_production_questions": [
            "Freeze the exact FAR threshold and treatment of unavailable searches.",
            "Establish the correct O4a- and O4b-specific generated-count/mixture "
            "normalization after splitting by time_geocenter.",
            "Validate both selection efficiencies against an independent public "
            "implementation at fixed population hyperparameters.",
        ],
        "required_next_step": (
            "Use the documented /events compound table and the concrete field "
            "inventory to build separate O4a/O4b contracts; keep real-data scoring "
            "disabled until run normalization and fixed-point checks pass."
        ),
    }
    return report
