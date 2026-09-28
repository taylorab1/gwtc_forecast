from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

import h5py
import numpy as np

REQUIRED_COLUMNS = (
    "result_label",
    "gw_name",
    "result_file_name",
    "result_samples_key",
)

# These lightweight summary quantities are useful for selecting a scientifically
# representative pilot and auditing that the expected event is being read.  They
# are not used in the hierarchical likelihood.
OPTIONAL_COLUMNS = (
    "superevent_id",
    "mass_1_source_median",
    "mass_1_source_lower",
    "mass_1_source_upper",
    "mass_2_source_median",
    "mass_2_source_lower",
    "mass_2_source_upper",
    "chirp_mass_source_median",
    "chirp_mass_source_lower",
    "chirp_mass_source_upper",
    "chi_eff_median",
    "chi_eff_lower",
    "chi_eff_upper",
    "redshift_median",
    "redshift_lower",
    "redshift_upper",
    "network_matched_filter_snr_median",
)


class PESummaryTableError(RuntimeError):
    """Raised when a public PE summary table is absent or ambiguous."""


def _decode(value: Any) -> Any:
    if np.ma.is_masked(value):
        return None
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        item = value.item()
        if isinstance(item, bytes):
            return item.decode("utf-8", errors="replace")
        if isinstance(item, float) and not np.isfinite(item):
            return None
        return item
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _compound_candidates(handle: h5py.File) -> list[tuple[str, h5py.Dataset]]:
    output: list[tuple[str, h5py.Dataset]] = []

    def visit(name: str, obj: h5py.Group | h5py.Dataset) -> None:
        if not isinstance(obj, h5py.Dataset) or obj.ndim != 1 or not obj.dtype.names:
            return
        fields = set(obj.dtype.names)
        if set(REQUIRED_COLUMNS).issubset(fields):
            output.append((f"/{name}", obj))

    handle.visititems(visit)
    return output


def _column_group_candidates(handle: h5py.File) -> list[tuple[str, h5py.Group]]:
    output: list[tuple[str, h5py.Group]] = []
    groups: list[tuple[str, h5py.Group]] = [("/", handle)]

    def collect(name: str, obj: h5py.Group | h5py.Dataset) -> None:
        if isinstance(obj, h5py.Group):
            groups.append((f"/{name}", obj))

    handle.visititems(collect)
    for path, group in groups:
        if not all(name in group for name in REQUIRED_COLUMNS):
            continue
        datasets = [group[name] for name in REQUIRED_COLUMNS]
        if not all(isinstance(item, h5py.Dataset) and item.ndim == 1 for item in datasets):
            continue
        lengths = {len(item) for item in datasets}
        if len(lengths) == 1:
            output.append((path, group))
    return output


def _select_table(
    handle: h5py.File,
) -> tuple[str, str, h5py.Dataset | h5py.Group, tuple[str, ...], int]:
    compound = _compound_candidates(handle)
    column_groups = _column_group_candidates(handle)
    candidates: list[
        tuple[str, str, h5py.Dataset | h5py.Group, tuple[str, ...], int]
    ] = []
    for path, dataset in compound:
        fields = tuple(str(name) for name in dataset.dtype.names or ())
        candidates.append((path, "compound_dataset", dataset, fields, len(dataset)))
    for path, group in column_groups:
        fields = tuple(str(name) for name in group.keys())
        candidates.append((path, "column_group", group, fields, len(group[REQUIRED_COLUMNS[0]])))

    if not candidates:
        raise PESummaryTableError(
            "No one-dimensional table containing result_label, gw_name, "
            "result_file_name, and result_samples_key was found"
        )
    # A public summary release should contain exactly one such table.  Prefer the
    # largest candidate only when nested Astropy metadata creates a harmless
    # duplicate view with the same row count and fields.
    candidates.sort(key=lambda item: (-item[4], item[0], item[1]))
    best = candidates[0]
    conflicting = [
        item
        for item in candidates[1:]
        if item[4] != best[4] or set(item[3]) != set(best[3])
    ]
    if conflicting:
        descriptions = [(item[0], item[1], item[4]) for item in candidates]
        raise PESummaryTableError(f"Ambiguous PE summary tables: {descriptions}")
    return best


def _rows_from_compound(
    dataset: h5py.Dataset, selected_columns: tuple[str, ...]
) -> list[dict[str, Any]]:
    array = dataset.fields(selected_columns)[:]
    return [
        {name: _decode(row[name]) for name in selected_columns}
        for row in array
    ]


def _rows_from_group(
    group: h5py.Group, selected_columns: tuple[str, ...]
) -> list[dict[str, Any]]:
    columns = {name: group[name][:] for name in selected_columns}
    row_count = len(columns[selected_columns[0]])
    return [
        {name: _decode(columns[name][index]) for name in selected_columns}
        for index in range(row_count)
    ]


def read_pe_summary_table(
    path: Path,
    *,
    event_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Read the lightweight public PE release index without loading PE samples.

    The official O4 release notebooks describe four key fields: ``gw_name``,
    ``result_file_name``, ``result_samples_key``, and ``result_label``.  This
    reader deliberately uses only that index to discover candidates.  It does
    not choose a production label and does not reconstruct a PE prior.
    """

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    requested = None if event_ids is None else {str(item) for item in event_ids}

    with h5py.File(path, "r") as handle:
        table_path, storage, table, fields, row_count = _select_table(handle)
        available = set(fields)
        selected_columns = tuple(
            name for name in (*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS) if name in available
        )
        if storage == "compound_dataset":
            rows = _rows_from_compound(table, selected_columns)  # type: ignore[arg-type]
        else:
            rows = _rows_from_group(table, selected_columns)  # type: ignore[arg-type]

    if requested is not None:
        rows = [row for row in rows if str(row["gw_name"]) in requested]
    rows.sort(key=lambda row: (str(row["gw_name"]), str(row["result_samples_key"])))

    by_event: dict[str, list[dict[str, Any]]] = {}
    consistency_errors: list[str] = []
    for row in rows:
        event_id = str(row["gw_name"])
        by_event.setdefault(event_id, []).append(row)
        expected_label = f"{event_id}-{row['result_samples_key']}"
        if str(row["result_label"]) != expected_label:
            consistency_errors.append(
                f"{event_id}: result_label={row['result_label']!r} != {expected_label!r}"
            )

    missing = [] if requested is None else sorted(requested - set(by_event))
    return {
        "schema": "gwtc_forecast.pe_summary_index.v1",
        "path": str(path),
        "table_path": table_path,
        "storage": storage,
        "release_row_count": row_count,
        "available_columns": sorted(fields),
        "selected_row_count": len(rows),
        "requested_event_ids": sorted(requested) if requested is not None else None,
        "missing_requested_events": missing,
        "consistency_errors": consistency_errors,
        "events": {
            event_id: {
                "candidate_count": len(event_rows),
                "result_file_names": sorted(
                    {str(item["result_file_name"]) for item in event_rows}
                ),
                "candidate_labels": [
                    str(item["result_samples_key"]) for item in event_rows
                ],
                "rows": event_rows,
            }
            for event_id, event_rows in sorted(by_event.items())
        },
        "production_label_frozen": False,
        "production_warning": (
            "The summary table enumerates released analyses; it does not decide "
            "which analysis or mixture is appropriate for population inference."
        ),
    }


def write_pe_index_csv(path: Path, report: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for event_id, payload in report.get("events", {}).items():
        for row in payload.get("rows", []):
            rows.append({"event_id": event_id, **row})
    columns = ["event_id", *REQUIRED_COLUMNS]
    optional_present = [
        name
        for name in OPTIONAL_COLUMNS
        if any(name in row for row in rows)
    ]
    fieldnames = list(dict.fromkeys([*columns, *optional_present]))
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)
