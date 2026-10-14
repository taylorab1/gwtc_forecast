"""Matched mass-feature ablation with a common, bendable continuum.

This is a project reference model, NOT a byte-for-byte LVK implementation.
All defaults are development choices. See docs/MODELS_AND_PRIORS.md.
Density is with respect to dm_1_source, not dlog(m_1).


Implementation notes
--------------------
p(m) approaches m**(-alpha_low/high), and is smooth at mb."""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.special import ndtr, logsumexp
MASS_KEY = 'mass_1_source'

@lru_cache(maxsize=16)
def mass_quadrature(low: float, high: float, n: int=512):
    """Gauss-Legendre nodes in log mass, returning weights for dm."""
    if not 0 < low < high or n < 16:
        raise ValueError('invalid mass integration domain or resolution')
    from scipy.special import roots_legendre
    u, w = roots_legendre(n)
    half = 0.5 * np.log(high / low)
    x = half * u + 0.5 * np.log(low * high)
    m = np.exp(x)
    return (m, w * half * m)

def _truncated_gaussian(m, mu, sigma, low, high):
    if sigma <= 0 or not low < mu < high:
        raise ValueError('Gaussian mean/width outside allowed domain')
    z = ndtr((high - mu) / sigma) - ndtr((low - mu) / sigma)
    if not z > 0:
        raise ValueError('unresolved Gaussian normalization')
    return np.exp(-0.5 * ((m - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi) * z)

@dataclass(frozen=True)
class MatchedMass:
    """Common low-mass component + smooth broken continuum +/- high-mass excess.

    p_base = (1 - f_low) C + f_low G_low
    p_on   = (1 - f_high) p_base + f_high G_high

    Both models therefore have the same conditional low-peak fraction among
    objects outside the added high-mass component. At f_high=0 they agree
    exactly. A positive high-component weight need not create a local maximum.
    """
    feature: bool = False
    m_min: float = 5.0
    m_max: float = 160.0
    normalization_nodes: int = 512

    def __post_init__(self):
        if not 0 < self.m_min < self.m_max or self.normalization_nodes < 16:
            raise ValueError('invalid mass domain/quadrature')

    @property
    def name(self):
        return 'continuum_lowpeak_highpeak' if self.feature else 'continuum_lowpeak'

    def log_prob(self, samples: Mapping[str, np.ndarray], hyperparameters: Mapping[str, float]):
        if MASS_KEY not in samples:
            raise KeyError(f'missing {MASS_KEY}')
        m = np.asarray(samples[MASS_KEY], dtype=float)
        if m.ndim != 1 or not np.isfinite(m).all():
            raise ValueError('masses must be finite one-dimensional arrays')
        h = hyperparameters
        alpha_low, alpha_high = (float(h['alpha_low']), float(h['alpha_high']))
        mb, width = (float(h['m_break']), float(h['break_width']))
        flow = float(h['f_low'])
        fhigh = float(h.get('f_high', 0.0)) if self.feature else 0.0
        vals = [alpha_low, alpha_high, mb, width, flow, fhigh]
        if not np.isfinite(vals).all() or not 0 < width <= 2:
            raise ValueError('nonfinite parameters or invalid log-mass break width')
        if not self.m_min < mb < self.m_max:
            raise ValueError('m_break must lie within mass support')
        if not 0 <= flow <= 1 or not 0 <= fhigh <= 1:
            raise ValueError('mixture fractions must be in [0,1]')

        def log_cont(mass):
            x = np.log(mass / mb)
            return -alpha_low * x - (alpha_high - alpha_low) * width * np.logaddexp(0, x / width)
        nodes, weights = mass_quadrature(self.m_min, self.m_max, self.normalization_nodes)
        log_norm = logsumexp(log_cont(nodes) + np.log(weights))
        out = np.full(m.shape, -np.inf)
        ok = (m >= self.m_min) & (m <= self.m_max)
        mm = m[ok]
        continuum = np.exp(log_cont(mm) - log_norm)
        low = _truncated_gaussian(mm, float(h['mu_low']), float(h['sigma_low']), self.m_min, self.m_max)
        p = (1 - flow) * continuum + flow * low
        if self.feature:
            high = _truncated_gaussian(mm, float(h['mu_high']), float(h['sigma_high']), self.m_min, self.m_max)
            p = (1 - fhigh) * p + fhigh * high
        with np.errstate(divide='ignore'):
            out[ok] = np.log(p)
        return out

    def sample(self, rng: np.random.Generator, size: int, hyperparameters: Mapping[str, float]):
        """Inverse-CDF numerical generator, on a grid independent of quadrature.

        This is a convergent numerical approximation, not an exact sampler.
        Refinement checks are required in a power study.
        """
        if size < 0:
            raise ValueError('size must be nonnegative')
        x = np.linspace(np.log(self.m_min), np.log(self.m_max), 8193)
        m = np.exp(x)
        p_x = np.exp(self.log_prob({MASS_KEY: m}, hyperparameters)) * m
        cdf = np.r_[0.0, cumulative_trapezoid(p_x, x)]
        cdf /= cdf[-1]
        return np.exp(np.interp(rng.random(size), cdf, x))
