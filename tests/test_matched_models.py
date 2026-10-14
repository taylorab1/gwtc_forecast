import numpy as np
import pytest
from scipy.integrate import quad
from gwtc_forecast.populations.matched_mass import MatchedMass, MASS_KEY
from gwtc_forecast.populations.matched_bbh import MatchedBBH, mass_ratio_log_prob, spin_magnitude_log_prob, tilt_pair_log_prob, redshift_log_prob
from gwtc_forecast.experiments.feature_demo import load_demo_config

def hyper():
    c, _ = load_demo_config()
    return {**c['generating_parameters'], 'beta_q': 1.2, 'kappa': 2.0, 'spin_mean': 0.25, 'spin_concentration': 8.0, 'aligned_fraction': 0.3, 'tilt_sigma': 0.5}

@pytest.mark.parametrize('feature', [False, True])
def test_mass_density_normalized_independent_quad(feature):
    m = MatchedMass(feature)
    h = hyper()
    integral = quad(lambda x: np.exp(m.log_prob({MASS_KEY: np.array([x])}, h))[0], m.m_min, m.m_max, epsabs=1e-08)[0]
    assert integral == pytest.approx(1, abs=2e-06)

def test_feature_zero_identical_and_off_ignores_high_parameters():
    x = {MASS_KEY: np.geomspace(5, 160, 200)}
    h = hyper()
    h['f_high'] = 0
    assert np.array_equal(MatchedMass(False).log_prob(x, h), MatchedMass(True).log_prob(x, h))
    h['f_high'] = 0.9
    assert np.array_equal(MatchedMass(False).log_prob(x, h), MatchedMass(False).log_prob(x, {**h, 'mu_high': 60}))

@pytest.mark.parametrize('beta', [-2, -1, 0, 2])
def test_mass_ratio_normalization(beta):
    m1 = 36
    m2min = 3
    v = quad(lambda q: np.exp(mass_ratio_log_prob(q, m1, beta, m2min)), m2min / m1, 1)[0]
    assert v == pytest.approx(1, abs=1e-08)

def test_spin_and_tilt_pair_normalization():
    v = quad(lambda a: np.exp(spin_magnitude_log_prob(a, 0.25, 8)), 0, 1)[0]
    assert v == pytest.approx(1, abs=1e-08)
    n, w = np.polynomial.legendre.leggauss(80)
    c1, c2 = np.meshgrid(n, n, indexing='ij')
    p = np.exp(tilt_pair_log_prob(c1, c2, 0.3, 0.5))
    assert np.sum(p * w[:, None] * w[None, :]) == pytest.approx(1, abs=1e-08)

def test_redshift_normalization():
    z = np.linspace(0, 3, 8193)
    assert np.trapezoid(np.exp(redshift_log_prob(z, 2, 3, 0.3089)), z) == pytest.approx(1, abs=1e-06)

def test_joint_bbh_exact_ablation():
    samples = {MASS_KEY: np.array([10.0, 30.0, 90.0]), 'mass_ratio': np.array([0.5, 0.8, 0.4]), 'redshift': np.array([0.1, 0.4, 1.0]), 'a_1': np.array([0.2, 0.4, 0.6]), 'a_2': np.array([0.1, 0.2, 0.3]), 'cos_tilt_1': np.array([-0.5, 0, 0.5]), 'cos_tilt_2': np.array([-0.5, 0, 0.5])}
    h = hyper()
    h['f_high'] = 0
    assert np.allclose(MatchedBBH(False).log_prob(samples, h), MatchedBBH(True).log_prob(samples, h), atol=0, rtol=0)
    with pytest.raises(KeyError):
        MatchedBBH().log_prob({MASS_KEY: np.ones(3)}, h)

def test_density_support_and_bad_parameters():
    m = MatchedMass()
    h = hyper()
    assert np.isneginf(m.log_prob({MASS_KEY: np.array([1.0, 200.0])}, h)).all()
    with pytest.raises(ValueError):
        m.log_prob({MASS_KEY: np.array([20.0])}, {**h, 'break_width': 0})
