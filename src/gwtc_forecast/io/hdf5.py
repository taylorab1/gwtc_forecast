from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np


def _jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        if value.size <= 20:
            return [_jsonable(item) for item in value.tolist()]
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def inventory_hdf5(
    path: Path,
    *,
    max_nodes: int = 5000,
    max_depth: int = 12,
    include_attributes: bool = True,
) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)

    nodes: list[dict[str, Any]] = []
    truncated = False

    with h5py.File(path, "r") as handle:
        root_attributes = (
            {str(k): _jsonable(v) for k, v in handle.attrs.items()}
            if include_attributes
            else {}
        )

        def visitor(name: str, obj: h5py.Group | h5py.Dataset) -> None:
            nonlocal truncated
            if len(nodes) >= max_nodes:
                truncated = True
                return
            depth = len(Path(name).parts)
            if depth > max_depth:
                return
            entry: dict[str, Any] = {
                "path": f"/{name}",
                "kind": "dataset" if isinstance(obj, h5py.Dataset) else "group",
            }
            if isinstance(obj, h5py.Dataset):
                entry.update(
                    {
                        "shape": list(obj.shape),
                        "dtype": str(obj.dtype),
                        "size": int(obj.size),
                        "storage_bytes": int(obj.id.get_storage_size()),
                    }
                )
            if include_attributes and len(obj.attrs):
                entry["attributes"] = {
                    str(k): _jsonable(v) for k, v in obj.attrs.items()
                }
            nodes.append(entry)

        handle.visititems(visitor)

    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "root_attributes": root_attributes,
        "node_count": len(nodes),
        "truncated": truncated,
        "nodes": nodes,
    }


def candidate_tabular_groups(path: Path, *, minimum_rows: int = 10) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    with h5py.File(path, "r") as handle:
        groups: list[tuple[str, h5py.Group]] = [("/", handle)]

        def collect(name: str, obj: h5py.Group | h5py.Dataset) -> None:
            if isinstance(obj, h5py.Group):
                groups.append((f"/{name}", obj))
            elif (
                isinstance(obj, h5py.Dataset)
                and obj.ndim == 1
                and obj.dtype.names
                and len(obj) >= minimum_rows
            ):
                candidates.append(
                    {
                        "group": f"/{name}",
                        "row_count": len(obj),
                        "column_count": len(obj.dtype.names),
                        "storage": "compound_dataset",
                        "columns": [
                            {
                                "name": field,
                                "length": len(obj),
                                "dtype": str(obj.dtype.fields[field][0]),
                            }
                            for field in obj.dtype.names
                        ],
                    }
                )

        handle.visititems(collect)
        for group_path, group in groups:
            columns: list[dict[str, Any]] = []
            lengths: list[int] = []
            for name, obj in group.items():
                if not isinstance(obj, h5py.Dataset) or obj.ndim != 1:
                    continue
                if obj.dtype.kind not in "biufcSU":
                    continue
                lengths.append(len(obj))
                columns.append(
                    {"name": name, "length": len(obj), "dtype": str(obj.dtype)}
                )
            if not lengths or max(lengths) < minimum_rows:
                continue
            counts: dict[int, int] = {}
            for length in lengths:
                counts[length] = counts.get(length, 0) + 1
            modal_length = max(counts, key=counts.get)
            modal_columns = [column for column in columns if column["length"] == modal_length]
            if len(modal_columns) >= 2:
                candidates.append(
                    {
                        "group": group_path,
                        "row_count": modal_length,
                        "column_count": len(modal_columns),
                        "columns": modal_columns,
                    }
                )
    return sorted(candidates, key=lambda item: (-item["row_count"], item["group"]))


def write_inventory_json(path: Path, inventory: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(inventory, indent=2, sort_keys=True))
    tmp.replace(path)
