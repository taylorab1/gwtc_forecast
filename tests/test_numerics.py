from __future__ import annotations

import numpy as np
import pytest

from gwtc_forecast.statistics.numerics import (
    effective_sample_size_from_log_weights,
    logmeanexp,
    mixed_tolerance_limit,
    normalize_log_weights,
    values_are_numerically_close,
)


def test_logmeanexp_and_normalization() -> None:
    values = np.log(np.asarray([1.0, 3.0]))
    assert np.isclose(logmeanexp(values), np.log(2.0))
    normalized = normalize_log_weights(values)
    assert np.isclose(np.exp(normalized).sum(), 1.0)
    assert np.isclose(effective_sample_size_from_log_weights(np.zeros(7)), 7.0)


def test_all_negative_infinity_weights_fail() -> None:
    with pytest.raises(ValueError, match="all log weights"):
        normalize_log_weights(np.full(4, -np.inf))


def test_mixed_tolerance_is_well_defined_near_zero_and_scale_aware() -> None:
    limit = mixed_tolerance_limit(0.0, 1.0e-12, absolute_tolerance=1.0e-10, relative_tolerance=1.0e-6)
    assert limit >= 1.0e-10
    assert values_are_numerically_close(0.0, 1.0e-12, absolute_tolerance=1.0e-10, relative_tolerance=0.0)
    assert values_are_numerically_close(1.0e8, 1.0e8 + 50.0, absolute_tolerance=1.0e-6, relative_tolerance=1.0e-6)
    assert not values_are_numerically_close(0.0, 1.0e-3, absolute_tolerance=1.0e-6, relative_tolerance=1.0e-6)
