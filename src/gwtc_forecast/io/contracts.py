from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping

import h5py
import numpy as np

from ..statistics.objects import EventPosterior, HyperPosterior, SelectionCampaign

EVENT_SCHEMA_V1 = "gwtc_forecast.processed_event.v1"
EVENT_SCHEMA_V2 = "gwtc_forecast.processed_event.v2"
EVENT_SCHEMA = EVENT_SCHEMA_V2
SELECTION_SCHEMA = "gwtc_forecast.processed_selection.v1"
HYPERPOSTERIOR_SCHEMA = "gwtc_forecast.processed_hyperposterior.v1"


@dataclass(frozen=True)
class SelectionContractSummary:
    path: str
    run: str
    injection_count: int
    sample_names: tuple[str, ...]
    metadata: dict[str, object]


def _validate_destination(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() not in {".h5", ".hdf5"}:
        raise ValueError("Processed contracts must use .h5 or .hdf5")


def _write_mapping(group: h5py.Group, values: Mapping[str, np.ndarray]) -> None:
    for name, array in sorted(values.items()):
        group.create_dataset(
            name,
            data=np.asarray(array),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )


def _text_attribute(value: object) -> str:
    if isinstance(value, (bytes, np.bytes_)):
        return bytes(value).decode("utf-8")
    return str(value)


def _metadata(handle: h5py.File) -> dict[str, object]:
    raw = _text_attribute(handle.attrs.get("metadata_json", "{}"))
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("contract metadata_json must decode to a mapping")
    return value


def _replace_atomic(tmp: Path, destination: Path) -> None:
    try:
        tmp.replace(destination)
    finally:
        tmp.unlink(missing_ok=True)


def write_event_contract(path: Path, event: EventPosterior) -> None:
    path = Path(path)
    _validate_destination(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    try:
        with h5py.File(tmp, "w") as handle:
            handle.attrs["schema"] = EVENT_SCHEMA
            handle.attrs["event_id"] = event.event_id
            handle.attrs["run"] = event.run
            handle.attrs["metadata_json"] = json.dumps(event.metadata, sort_keys=True)
            _write_mapping(handle.create_group("samples"), event.samples)
            handle.create_dataset(
                "log_pe_prior",
                data=event.log_pe_prior,
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            handle.create_dataset(
                "log_sample_weights",
                data=event.log_sample_weights,
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
        _replace_atomic(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def read_event_contract(path: Path) -> EventPosterior:
    with h5py.File(path, "r") as handle:
        schema = _text_attribute(handle.attrs.get("schema", ""))
        if schema not in {EVENT_SCHEMA_V1, EVENT_SCHEMA_V2}:
            raise ValueError(f"Unexpected event contract schema in {path}: {schema}")
        samples = {name: dataset[...] for name, dataset in handle["samples"].items()}
        log_sample_weights = (
            handle["log_sample_weights"][...]
            if schema == EVENT_SCHEMA_V2 and "log_sample_weights" in handle
            else None
        )
        return EventPosterior(
            event_id=_text_attribute(handle.attrs["event_id"]),
            run=_text_attribute(handle.attrs["run"]),
            samples=samples,
            log_pe_prior=handle["log_pe_prior"][...],
            metadata=_metadata(handle),
            log_sample_weights=log_sample_weights,
        )


def write_selection_contract(path: Path, campaign: SelectionCampaign) -> None:
    path = Path(path)
    _validate_destination(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    try:
        with h5py.File(tmp, "w") as handle:
            handle.attrs["schema"] = SELECTION_SCHEMA
            handle.attrs["run"] = campaign.run
            handle.attrs["metadata_json"] = json.dumps(campaign.metadata, sort_keys=True)
            _write_mapping(handle.create_group("samples"), campaign.samples)
            handle.create_dataset(
                "log_draw_density",
                data=campaign.log_draw_density,
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
            handle.create_dataset(
                "log_base_weight",
                data=campaign.log_base_weight,
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
        _replace_atomic(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def selection_contract_summary(path: Path) -> SelectionContractSummary:
    """Validate the on-disk selection schema without loading all rows."""

    path = Path(path)
    with h5py.File(path, "r") as handle:
        schema = _text_attribute(handle.attrs.get("schema", ""))
        if schema != SELECTION_SCHEMA:
            raise ValueError(f"Unexpected selection contract schema in {path}: {schema}")
        if "samples" not in handle or not isinstance(handle["samples"], h5py.Group):
            raise ValueError(f"Selection contract has no samples group: {path}")
        required = ("log_draw_density", "log_base_weight")
        missing = [name for name in required if name not in handle]
        if missing:
            raise ValueError(f"Selection contract is missing datasets: {missing}")

        sample_group = handle["samples"]
        sample_names = tuple(sorted(sample_group.keys()))
        if not sample_names:
            raise ValueError("Selection contract contains no sample coordinates")
        lengths: dict[str, int] = {}
        for name in sample_names:
            dataset = sample_group[name]
            if not isinstance(dataset, h5py.Dataset) or dataset.ndim != 1:
                raise ValueError(f"Selection sample {name} must be a 1D dataset")
            lengths[f"samples/{name}"] = len(dataset)
        for name in required:
            dataset = handle[name]
            if not isinstance(dataset, h5py.Dataset) or dataset.ndim != 1:
                raise ValueError(f"Selection dataset {name} must be one-dimensional")
            lengths[name] = len(dataset)
        unique_lengths = set(lengths.values())
        if len(unique_lengths) != 1:
            raise ValueError(f"Selection contract row-count mismatch: {lengths}")
        injection_count = unique_lengths.pop()
        if injection_count == 0:
            raise ValueError("Selection contract must contain at least one row")
        return SelectionContractSummary(
            path=str(path.resolve()),
            run=_text_attribute(handle.attrs["run"]),
            injection_count=injection_count,
            sample_names=sample_names,
            metadata=_metadata(handle),
        )


def iter_selection_contract_chunks(
    path: Path, *, chunk_rows: int = 100_000
) -> Iterator[SelectionCampaign]:
    """Yield bounded in-memory chunks from a validated selection contract.

    The stored ``log_base_weight`` values retain their global normalization, so
    the yielded chunks may be combined with log-sum-exp accumulation.  A chunk
    is not itself an independently normalized injection campaign.
    """

    if chunk_rows <= 0:
        raise ValueError("chunk_rows must be positive")
    path = Path(path)
    summary = selection_contract_summary(path)
    with h5py.File(path, "r") as handle:
        samples_group = handle["samples"]
        for chunk_index, start in enumerate(
            range(0, summary.injection_count, chunk_rows)
        ):
            stop = min(start + chunk_rows, summary.injection_count)
            metadata = dict(summary.metadata)
            metadata.update(
                {
                    "contract_path": summary.path,
                    "chunk_index": chunk_index,
                    "chunk_start": start,
                    "chunk_stop": stop,
                    "full_injection_count": summary.injection_count,
                }
            )
            yield SelectionCampaign(
                run=summary.run,
                samples={
                    name: samples_group[name][start:stop]
                    for name in summary.sample_names
                },
                log_draw_density=handle["log_draw_density"][start:stop],
                log_base_weight=handle["log_base_weight"][start:stop],
                metadata=metadata,
            )


def read_selection_contract(path: Path) -> SelectionCampaign:
    summary = selection_contract_summary(path)
    with h5py.File(path, "r") as handle:
        samples = {name: dataset[...] for name, dataset in handle["samples"].items()}
        return SelectionCampaign(
            run=summary.run,
            samples=samples,
            log_draw_density=handle["log_draw_density"][...],
            log_base_weight=handle["log_base_weight"][...],
            metadata=summary.metadata,
        )


def write_hyperposterior_contract(path: Path, posterior: HyperPosterior) -> None:
    """Serialize an immutable released-model hyperposterior representation."""

    path = Path(path)
    _validate_destination(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.unlink(missing_ok=True)
    try:
        with h5py.File(tmp, "w") as handle:
            handle.attrs["schema"] = HYPERPOSTERIOR_SCHEMA
            handle.attrs["model_name"] = posterior.model_name
            handle.attrs["metadata_json"] = json.dumps(
                posterior.metadata, sort_keys=True
            )
            _write_mapping(handle.create_group("samples"), posterior.samples)
            handle.create_dataset(
                "log_weights",
                data=posterior.log_weights,
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            )
        _replace_atomic(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def read_hyperposterior_contract(path: Path) -> HyperPosterior:
    with h5py.File(path, "r") as handle:
        schema = _text_attribute(handle.attrs.get("schema", ""))
        if schema != HYPERPOSTERIOR_SCHEMA:
            raise ValueError(f"Unexpected hyperposterior contract schema in {path}")
        samples = {name: dataset[...] for name, dataset in handle["samples"].items()}
        return HyperPosterior(
            samples=samples,
            log_weights=handle["log_weights"][...],
            model_name=_text_attribute(handle.attrs["model_name"]),
            metadata=_metadata(handle),
        )
