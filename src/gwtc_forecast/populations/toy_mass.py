from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy.special import ndtr

MASS_KEY = "mass_1_source"


def _integral_power(alpha: float, low: float, high: float) -> float:
    if not 0 < low < high:
        raise ValueError(f"invalid bounds: {low}, {high}")
    if np.isclose(alpha, -1.0):
        return float(np.log(high / low))
    return float((high ** (alpha + 1.0) - low ** (alpha + 1.0)) / (alpha + 1.0))


def _sample_power(
    rng: np.random.Generator, size: int, alpha: float, low: float, high: float
) -> np.ndarray:
    u = rng.random(size)
    if np.isclose(alpha, -1.0):
        return low * np.exp(u * np.log(high / low))
    exponent = alpha + 1.0
    return (low**exponent + u * (high**exponent - low**exponent)) ** (1.0 / exponent)


def _mass(samples: Mapping[str, np.ndarray]) -> np.ndarray:
    if MASS_KEY not in samples:
        raise KeyError(f"population samples require {MASS_KEY!r}")
    return np.asarray(samples[MASS_KEY], dtype=float)


@dataclass(frozen=True)
class PowerLaw:
    name: str = "toy_power_law"

    def log_prob(self, samples, hyperparameters) -> np.ndarray:
        mass = _mass(samples)
        alpha = float(hyperparameters["alpha"])
        low = float(hyperparameters["m_min"])
        high = float(hyperparameters["m_max"])
        norm = _integral_power(alpha, low, high)
        result = np.full(mass.shape, -np.inf, dtype=float)
        support = (mass >= low) & (mass <= high)
        result[support] = alpha * np.log(mass[support]) - np.log(norm)
        return result

    def sample(self, rng, size: int, hyperparameters) -> np.ndarray:
        return _sample_power(
            rng,
            size,
            float(hyperparameters["alpha"]),
            float(hyperparameters["m_min"]),
            float(hyperparameters["m_max"]),
        )


@dataclass(frozen=True)
class PowerLawPlusPeak:
    name: str = "toy_power_law_plus_peak"

    def log_prob(self, samples, hyperparameters) -> np.ndarray:
        mass = _mass(samples)
        alpha = float(hyperparameters["alpha"])
        low = float(hyperparameters["m_min"])
        high = float(hyperparameters["m_max"])
        fraction = float(hyperparameters["peak_fraction"])
        mean = float(hyperparameters["peak_mean"])
        sigma = float(hyperparameters["peak_sigma"])
        if not 0.0 < fraction < 1.0:
            raise ValueError("peak_fraction must be strictly between zero and one")
        if sigma <= 0:
            raise ValueError("peak_sigma must be positive")

        power = PowerLaw().log_prob(samples, hyperparameters)
        z = (mass - mean) / sigma
        trunc_norm = ndtr((high - mean) / sigma) - ndtr((low - mean) / sigma)
        if trunc_norm <= 0:
            raise ValueError("invalid truncated Gaussian normalization")
        gaussian = -0.5 * z**2 - np.log(sigma * np.sqrt(2.0 * np.pi) * trunc_norm)
        gaussian[(mass < low) | (mass > high)] = -np.inf
        return np.logaddexp(np.log1p(-fraction) + power, np.log(fraction) + gaussian)

    def sample(self, rng, size: int, hyperparameters) -> np.ndarray:
        fraction = float(hyperparameters["peak_fraction"])
        choose_peak = rng.random(size) < fraction
        output = PowerLaw().sample(rng, size, hyperparameters)
        remaining = int(choose_peak.sum())
        low = float(hyperparameters["m_min"])
        high = float(hyperparameters["m_max"])
        mean = float(hyperparameters["peak_mean"])
        sigma = float(hyperparameters["peak_sigma"])
        accepted: list[float] = []
        while len(accepted) < remaining:
            candidates = rng.normal(mean, sigma, size=max(remaining, 32))
            accepted.extend(candidates[(candidates >= low) & (candidates <= high)].tolist())
        output[choose_peak] = np.asarray(accepted[:remaining])
        return output


@dataclass(frozen=True)
class BrokenPowerLaw:
    name: str = "toy_broken_power_law"

    @staticmethod
    def _segment_integrals(hyperparameters) -> tuple[float, float]:
        low = float(hyperparameters["m_min"])
        middle = float(hyperparameters["m_break"])
        high = float(hyperparameters["m_max"])
        if not low < middle < high:
            raise ValueError("require m_min < m_break < m_max")
        alpha_low = float(hyperparameters["alpha_low"])
        alpha_high = float(hyperparameters["alpha_high"])
        left = middle * _integral_power(alpha_low, low / middle, 1.0)
        right = middle * _integral_power(alpha_high, 1.0, high / middle)
        return left, right

    def log_prob(self, samples, hyperparameters) -> np.ndarray:
        mass = _mass(samples)
        low = float(hyperparameters["m_min"])
        middle = float(hyperparameters["m_break"])
        high = float(hyperparameters["m_max"])
        alpha_low = float(hyperparameters["alpha_low"])
        alpha_high = float(hyperparameters["alpha_high"])
        left, right = self._segment_integrals(hyperparameters)
        norm = left + right
        result = np.full(mass.shape, -np.inf, dtype=float)
        left_mask = (mass >= low) & (mass <= middle)
        right_mask = (mass > middle) & (mass <= high)
        result[left_mask] = alpha_low * np.log(mass[left_mask] / middle) - np.log(norm)
        result[right_mask] = alpha_high * np.log(mass[right_mask] / middle) - np.log(norm)
        return result

    def sample(self, rng, size: int, hyperparameters) -> np.ndarray:
        left, right = self._segment_integrals(hyperparameters)
        choose_left = rng.random(size) < left / (left + right)
        output = np.empty(size, dtype=float)
        low = float(hyperparameters["m_min"])
        middle = float(hyperparameters["m_break"])
        high = float(hyperparameters["m_max"])
        output[choose_left] = _sample_power(
            rng,
            int(choose_left.sum()),
            float(hyperparameters["alpha_low"]),
            low,
            middle,
        )
        output[~choose_left] = _sample_power(
            rng,
            int((~choose_left).sum()),
            float(hyperparameters["alpha_high"]),
            middle,
            high,
        )
        return output
