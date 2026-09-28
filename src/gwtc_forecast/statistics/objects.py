from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from .numerics import (
    as_finite_1d,
    effective_sample_size_from_log_weights,
    normalize_log_weights,
)


def _validated_samples(
    samples: Mapping[str, np.ndarray], *, expected_length: int | None = None
) -> tuple[dict[str, np.ndarray], int]:
    if not samples:
        raise ValueError("sample mapping must not be empty")
    arrays = {str(name): np.asarray(value) for name, value in samples.items()}
    if any(value.ndim != 1 for value in arrays.values()):
        shapes = {name: value.shape for name, value in arrays.items()}
        raise ValueError(f"all sample arrays must be one-dimensional: {shapes}")
    lengths = {len(value) for value in arrays.values()}
    if len(lengths) != 1:
        raise ValueError(f"sample arrays have inconsistent lengths: {lengths}")
    length = lengths.pop()
    if expected_length is not None and length != expected_length:
        raise ValueError(f"sample length {length} != expected {expected_length}")
    if length == 0:
        raise ValueError("sample arrays must not be empty")
    return arrays, length


@dataclass(frozen=True)
class EventPosterior:
    """Analysis-ready posterior samples for one event.

    ``log_sample_weights`` describes how the stored rows represent the event
    posterior itself.  It is normalized on construction.  Equal-weight public
    products may omit it; the object then assigns every row weight ``1 / K``.
    These posterior-representation weights are distinct from the population
    reweighting ratio ``p(theta | Lambda) / pi_PE(theta)`` used later.

    The field is intentionally placed after ``metadata`` to preserve positional
    compatibility with the original v0.3 baseline.  New code should pass it by
    keyword.
    """

    event_id: str
    run: str
    samples: Mapping[str, np.ndarray]
    log_pe_prior: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)
    log_sample_weights: np.ndarray | None = None

    def __post_init__(self) -> None:
        if not str(self.event_id).strip():
            raise ValueError("event_id must not be empty")
        if not str(self.run).strip():
            raise ValueError("run must not be empty")

        log_prior = np.asarray(self.log_pe_prior, dtype=float)
        if log_prior.ndim != 1 or log_prior.size == 0:
            raise ValueError("log_pe_prior must be a non-empty one-dimensional array")
        if not np.isfinite(log_prior).all():
            raise ValueError("log_pe_prior contains non-finite values")
        samples, length = _validated_samples(
            self.samples, expected_length=log_prior.size
        )

        if self.log_sample_weights is None:
            log_sample_weights = np.full(length, -np.log(length), dtype=float)
        else:
            raw = as_finite_1d(
                self.log_sample_weights,
                name="log_sample_weights",
                allow_negative_infinity=True,
            )
            if raw.size != length:
                raise ValueError(
                    "event log_sample_weights have incompatible shape: "
                    f"{raw.shape} for {length} samples"
                )
            log_sample_weights = normalize_log_weights(raw)

        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "log_pe_prior", log_prior)
        object.__setattr__(self, "log_sample_weights", log_sample_weights)
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def sample_count(self) -> int:
        return len(self.log_pe_prior)

    @property
    def posterior_sample_ess(self) -> float:
        """Effective number of rows representing the stored event posterior."""

        return effective_sample_size_from_log_weights(self.log_sample_weights)


@dataclass(frozen=True)
class HyperPosterior:
    samples: Mapping[str, np.ndarray]
    log_weights: np.ndarray | None = None
    model_name: str = "unnamed"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        samples, length = _validated_samples(self.samples)
        if self.log_weights is None:
            log_weights = np.full(length, -np.log(length), dtype=float)
        else:
            raw = np.asarray(self.log_weights, dtype=float)
            if raw.ndim != 1 or len(raw) != length:
                raise ValueError("hyperposterior log_weights have incompatible shape")
            log_weights = normalize_log_weights(raw)
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "log_weights", log_weights)
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def draw_count(self) -> int:
        return len(self.log_weights)

    def draw(self, index: int) -> dict[str, float]:
        return {name: float(values[index]) for name, values in self.samples.items()}


@dataclass(frozen=True)
class SelectionCampaign:
    run: str
    samples: Mapping[str, np.ndarray]
    log_draw_density: np.ndarray
    log_base_weight: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not str(self.run).strip():
            raise ValueError("run must not be empty")
        log_draw = np.asarray(self.log_draw_density, dtype=float)
        log_base = np.asarray(self.log_base_weight, dtype=float)
        if log_draw.ndim != 1 or log_draw.size == 0:
            raise ValueError(
                "selection log_draw_density must be a non-empty one-dimensional array"
            )
        samples, length = _validated_samples(
            self.samples, expected_length=log_draw.size
        )
        if log_base.ndim != 1 or len(log_base) != length:
            raise ValueError("selection log arrays have incompatible shapes")
        if not np.isfinite(log_draw).all() or not np.isfinite(log_base).all():
            raise ValueError("selection log arrays contain non-finite values")
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "log_draw_density", log_draw)
        object.__setattr__(self, "log_base_weight", log_base)
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def injection_count(self) -> int:
        return len(self.log_draw_density)
