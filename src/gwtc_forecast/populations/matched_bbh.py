"""Normalized seven-dimensional reference BBH family with shared nuisance terms.

The mass-feature ablation is the ONLY family difference. This implementation
is a candidate for qualification, not an official release model or a qualified
real-data analysis. Normalization is for dm1 dq dz da1 da2 dcos(t1) dcos(t2).


Implementation notes
--------------------
Common constants, including (c/H0)^3, cancel from the normalized shape."""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.special import betaln, ndtr
from .matched_mass import MatchedMass

@lru_cache(maxsize=16)
def redshift_geometry(z_max: float, omega_m: float, nodes: int=4097):
    if z_max <= 0 or not 0 < omega_m < 1 or nodes < 16:
        raise ValueError('invalid flat-LCDM geometry')
    z = np.linspace(0, z_max, nodes)
    e = np.sqrt(omega_m * (1 + z) ** 3 + 1 - omega_m)
    distance = np.r_[0.0, cumulative_trapezoid(1 / e, z)]
    return (z, distance ** 2 / e)

def redshift_log_prob(z, kappa: float, z_max: float, omega_m: float):
    z = np.asarray(z, dtype=float)
    grid, geometry = redshift_geometry(z_max, omega_m)
    unnormalized = geometry * (1 + grid) ** (kappa - 1)
    norm = np.trapezoid(unnormalized, grid)
    values = np.interp(z, grid, unnormalized, left=0, right=0) / norm
    with np.errstate(divide='ignore'):
        return np.log(values)

def mass_ratio_log_prob(q, m1, beta: float, m2_min: float):
    q, m1 = np.broadcast_arrays(np.asarray(q, float), np.asarray(m1, float))
    low = m2_min / m1
    support = (m1 > m2_min) & (q >= low) & (q <= 1)
    out = np.full(q.shape, -np.inf)
    exponent = beta + 1.0
    if abs(exponent) < 1e-08:
        norm = -np.log(low[support])
    else:
        norm = -np.expm1(exponent * np.log(low[support])) / exponent
    out[support] = beta * np.log(q[support]) - np.log(norm)
    return out

def spin_magnitude_log_prob(a, mean: float, concentration: float):
    if not 0 < mean < 1 or concentration <= 0:
        raise ValueError('invalid beta spin distribution')
    a = np.asarray(a, float)
    aa, bb = (mean * concentration, (1 - mean) * concentration)
    out = np.full(a.shape, -np.inf)
    ok = (a > 0) & (a < 1)
    out[ok] = (aa - 1) * np.log(a[ok]) + (bb - 1) * np.log1p(-a[ok]) - betaln(aa, bb)
    return out

def tilt_pair_log_prob(c1, c2, aligned_fraction: float, sigma: float):
    """Binary-level mixture: both tilts isotropic OR both alignment-centered.

    Not a product of two independent mixture densities.
    """
    if not 0 <= aligned_fraction <= 1 or sigma <= 0:
        raise ValueError('invalid tilt mixture')
    c1, c2 = np.broadcast_arrays(np.asarray(c1, float), np.asarray(c2, float))
    out = np.full(c1.shape, -np.inf)
    ok = (abs(c1) <= 1) & (abs(c2) <= 1)
    norm = sigma * np.sqrt(2 * np.pi) * (ndtr(0) - ndtr(-2 / sigma))
    aligned = -0.5 * (((c1[ok] - 1) / sigma) ** 2 + ((c2[ok] - 1) / sigma) ** 2) - 2 * np.log(norm)
    with np.errstate(divide='ignore'):
        out[ok] = np.logaddexp(np.log1p(-aligned_fraction) - np.log(4), np.log(aligned_fraction) + aligned)
    return out

@dataclass(frozen=True)
class MatchedBBH:
    feature: bool = False
    m_min: float = 5.0
    m_max: float = 160.0
    m2_min: float = 3.0
    z_max: float = 3.0
    omega_m: float = 0.3089

    def __post_init__(self):
        if not 0 < self.m2_min < self.m_min < self.m_max:
            raise ValueError('require 0 < m2_min < m_min < m_max')
        if not self.z_max > 0 or not 0 < self.omega_m < 1:
            raise ValueError('invalid redshift domain/cosmology')

    @property
    def name(self):
        return 'matched_bbh_highpeak' if self.feature else 'matched_bbh_continuum'

    def log_prob(self, samples, hyperparameters):
        keys = ('mass_1_source', 'mass_ratio', 'redshift', 'a_1', 'a_2', 'cos_tilt_1', 'cos_tilt_2')
        missing = set(keys) - set(samples)
        if missing:
            raise KeyError(f'Missing BBH coordinates: {sorted(missing)}')
        arrays = [np.asarray(samples[key], float) for key in keys]
        if any((a.ndim != 1 or not np.isfinite(a).all() for a in arrays)):
            raise ValueError('BBH arrays must be finite and one-dimensional')
        if len({a.size for a in arrays}) != 1:
            raise ValueError('BBH array lengths disagree')
        if not all((np.isfinite(float(v)) for v in hyperparameters.values())):
            raise ValueError('nonfinite population hyperparameters')
        m1, q, z, a1, a2, c1, c2 = arrays
        h = hyperparameters
        lp = MatchedMass(self.feature, self.m_min, self.m_max).log_prob(samples, h)
        lp += mass_ratio_log_prob(q, m1, float(h['beta_q']), self.m2_min)
        lp += redshift_log_prob(z, float(h['kappa']), self.z_max, self.omega_m)
        for a in (a1, a2):
            lp += spin_magnitude_log_prob(a, float(h['spin_mean']), float(h['spin_concentration']))
        lp += tilt_pair_log_prob(c1, c2, float(h['aligned_fraction']), float(h['tilt_sigma']))
        return lp
