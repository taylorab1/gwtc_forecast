from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .hdf5 import inventory_hdf5


class PEInspectionError(RuntimeError):
    """Raised when a PE release file cannot be read unambiguously."""


def _labels(samples_dict: Any) -> list[str]:
    labels = getattr(samples_dict, "labels", None)
    if labels is not None:
        return [str(label) for label in labels]
    if hasattr(samples_dict, "keys"):
        return [str(label) for label in samples_dict.keys()]
    raise PEInspectionError("PESummary samples object exposes no labels")


def inspect_pe_file(path: Path, *, deep: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "path": str(path),
        "generic_hdf5": inventory_hdf5(
            path, max_depth=4 if not deep else 10, max_nodes=1000 if not deep else 10000
        ),
        "pesummary_available": False,
        "pesummary_error": None,
        "labels": [],
    }
    if not deep:
        return report
    try:
        from pesummary.io import read

        result = read(str(path), package="gw")
        samples_dict = result.samples_dict
        labels = _labels(samples_dict)
        analyses: list[dict[str, Any]] = []
        for label in labels:
            samples = samples_dict[label]
            parameters = [str(key) for key in samples.keys()]
            sample_count = len(np.asarray(samples[parameters[0]])) if parameters else 0
            analyses.append(
                {
                    "label": label,
                    "sample_count": sample_count,
                    "parameters": parameters,
                }
            )
        priors = getattr(result, "priors", None)
        config = getattr(result, "config", None)
        report.update(
            {
                "pesummary_available": True,
                "labels": labels,
                "analyses": analyses,
                "prior_container_type": type(priors).__name__ if priors is not None else None,
                "config_container_type": type(config).__name__ if config is not None else None,
            }
        )
    except Exception as exc:  # Inspection must preserve the generic report.
        report["pesummary_error"] = f"{type(exc).__name__}: {exc}"
    return report


def read_posterior_samples(
    path: Path, *, label: str, parameters: Iterable[str] | None = None
) -> dict[str, np.ndarray]:
    try:
        from pesummary.io import read
    except ImportError as exc:
        raise PEInspectionError("PESummary is not installed") from exc

    result = read(str(path), package="gw")
    samples_dict = result.samples_dict
    labels = _labels(samples_dict)
    if label not in labels:
        raise PEInspectionError(
            f"Requested label {label!r} is absent. Available labels: {labels}"
        )
    samples = samples_dict[label]
    available = [str(key) for key in samples.keys()]
    chosen = available if parameters is None else [str(name) for name in parameters]
    missing = sorted(set(chosen) - set(available))
    if missing:
        raise PEInspectionError(
            f"Missing parameters for label {label!r}: {missing}. Available: {available}"
        )
    return {name: np.asarray(samples[name]) for name in chosen}


def reconstruct_log_pe_prior(*args: Any, **kwargs: Any) -> np.ndarray:
    raise PEInspectionError(
        "Production PE-prior reconstruction is deliberately not generic. "
        "Implement and validate a release-specific mapping before real-data scoring."
    )
