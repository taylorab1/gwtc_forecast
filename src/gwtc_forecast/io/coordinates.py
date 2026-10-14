"""Explicit, small Jacobian helpers. These do not reconstruct a released PE prior.

Implementation notes
--------------------
|d(m1,m2)/d(m1,q)| = m1."""
from __future__ import annotations
import numpy as np

def source_component_masses_to_primary_ratio(m1, m2, log_density_dm1_dm2):
    m1, m2, lp = np.broadcast_arrays(np.asarray(m1, float), np.asarray(m2, float), np.asarray(log_density_dm1_dm2, float))
    if not np.isfinite(m1 + m2 + lp).all() or (m2 <= 0).any() or (m1 < m2).any():
        raise ValueError('require finite ordered source-frame component masses')
    return ({'mass_1_source': m1, 'mass_ratio': m2 / m1}, lp + np.log(m1))

def detector_component_masses_distance_to_source(m1_detector, m2_detector, redshift, d_luminosity_distance_dz, log_density_dm1det_dm2det_dDL):
    """Transform density from detector component masses and D_L to m1,q,z.

    The caller must obtain z and dD_L/dz from the SAME fixed cosmology as PE and
    the study. H0 units must match the native D_L prior. No cosmology is guessed.
    """
    a, b, z, deriv, lp = np.broadcast_arrays(*[np.asarray(x, float) for x in (m1_detector, m2_detector, redshift, d_luminosity_distance_dz, log_density_dm1det_dm2det_dDL)])
    if not np.isfinite(a + b + z + deriv + lp).all() or (b <= 0).any() or (a < b).any() or (z < 0).any() or (deriv <= 0).any():
        raise ValueError('invalid detector/source coordinate inputs')
    m1 = a / (1 + z)
    log_jacobian = np.log(m1) + 2 * np.log1p(z) + np.log(deriv)
    return ({'mass_1_source': m1, 'mass_ratio': b / a, 'redshift': z}, lp + log_jacobian)
