from __future__ import annotations

import numpy as np
from scipy.special import logsumexp


def as_finite_1d(values, *, name: str, allow_negative_infinity: bool = False) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional; got shape {array.shape}")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty")
    if np.isnan(array).any() or np.isposinf(array).any():
        raise ValueError(f"{name} contains NaN or +inf")
    if not allow_negative_infinity and np.isneginf(array).any():
        raise ValueError(f"{name} contains -inf")
    return array


def logmeanexp(values, axis=None):
    array = np.asarray(values, dtype=float)
    if axis is None:
        if array.size == 0:
            raise ValueError("logmeanexp requires at least one value")
        return logsumexp(array) - np.log(array.size)
    count = array.shape[axis]
    if count == 0:
        raise ValueError("logmeanexp requires a non-empty axis")
    return logsumexp(array, axis=axis) - np.log(count)


def normalize_log_weights(log_weights) -> np.ndarray:
    values = as_finite_1d(
        log_weights, name="log_weights", allow_negative_infinity=True
    )
    if np.isneginf(values).all():
        raise ValueError("all log weights are -inf")
    return values - logsumexp(values)


def effective_sample_size_from_log_weights(log_weights) -> float:
    normalized = normalize_log_weights(log_weights)
    return float(np.exp(-logsumexp(2.0 * normalized)))


def mixed_tolerance_limit(
    left: float,
    right: float,
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> float:
    """Return an absolute-plus-relative comparison threshold.

    The absolute term controls comparisons close to zero, where a fractional
    error is undefined or scientifically misleading.  The relative term avoids
    making the same fixed absolute threshold unrealistically strict for large
    log scores.
    """

    if absolute_tolerance < 0.0 or relative_tolerance < 0.0:
        raise ValueError("numerical tolerances must be non-negative")
    return float(
        absolute_tolerance
        + relative_tolerance * max(abs(float(left)), abs(float(right)))
    )


def values_are_numerically_close(
    left: float,
    right: float,
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> bool:
    if not np.isfinite([left, right]).all():
        return False
    difference = abs(float(left) - float(right))
    return difference <= mixed_tolerance_limit(
        left,
        right,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
    )


def assert_close_joint_prequential(
    joint: float,
    prequential: float,
    tolerance: float,
    *,
    relative_tolerance: float = 1.0e-12,
) -> None:
    """Require equivalent joint and sequential factorizations to agree.

    ``tolerance`` remains the absolute tolerance used by the v0.3 API.  A small
    relative term is added for scale awareness without changing behavior near
    a scientifically valid zero score difference.
    """

    difference = abs(float(joint) - float(prequential))
    limit = mixed_tolerance_limit(
        joint,
        prequential,
        absolute_tolerance=tolerance,
        relative_tolerance=relative_tolerance,
    )
    if not np.isfinite([joint, prequential]).all() or difference > limit:
        raise RuntimeError(
            f"Joint/prequential mismatch {difference:.3e} exceeds mixed "
            f"tolerance {limit:.3e} (abs={tolerance:.3e}, "
            f"rel={relative_tolerance:.3e})"
        )
