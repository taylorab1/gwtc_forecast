import numpy as np
import pytest
from scipy.special import logsumexp
from gwtc_forecast.statistics.objects import HyperPosterior, EventPosterior
from gwtc_forecast.inference.grid import fit_finite_prior, score_factors, sequential_factors, cartesian_prior
from gwtc_forecast.inference.frozen import validate_train_test_identity
from gwtc_forecast.inference.training import load_prior_spec
from gwtc_forecast.inference.study import audit_study
from gwtc_forecast.statistics.uncertainty import predictive_support

def test_grid_training_matches_enumeration_and_sequential():
    prior = HyperPosterior({'a': np.array([0.0, 1.0])})
    f = np.log([[0.2, 0.7], [0.4, 0.5]])
    fit = fit_finite_prior(prior, f, training_ids=['a', 'b'])
    expected = np.array([0.2 * 0.4, 0.7 * 0.5])
    expected /= expected.sum()
    assert np.allclose(np.exp(fit.posterior.log_weights), expected)
    heldout = np.log([[0.6, 0.2], [0.3, 0.9]])
    score = score_factors(fit.posterior, heldout)
    assert score == pytest.approx(np.log(expected @ np.prod(np.exp(heldout), axis=0)))
    inc, ess, w = sequential_factors(fit.posterior, heldout)
    assert sum(inc) == pytest.approx(score)
    assert logsumexp(w) == pytest.approx(0, abs=1e-12)
    independent = sum((score_factors(fit.posterior, x[None, :]) for x in heldout))
    assert abs(score - independent) > 0.001

def test_invalid_grid_inputs():
    with pytest.raises(ValueError):
        cartesian_prior({'a': [1]}, {'a': 2}, model_name='x')
    with pytest.raises(ValueError):
        fit_finite_prior(HyperPosterior({'a': np.array([0.0, 1.0])}), np.zeros((2, 2)), training_ids=['x', 'x'])

def event(name, run):
    return EventPosterior(name, run, {'mass_1_source': np.array([20.0, 21.0])}, np.zeros(2))

def test_overlap_and_missing_provenance_rejected():
    p = HyperPosterior({'a': np.array([1.0, 2.0])}, metadata={'trained_on': ['TRAIN']})
    validate_train_test_identity(p, [event('TEST', 'O4a')])
    with pytest.raises(ValueError):
        validate_train_test_identity(p, [event('TRAIN', 'O4a')])
    with pytest.raises(ValueError):
        validate_train_test_identity(p, [event('x', 'O4b'), event('y', 'O4a')])
    with pytest.raises(ValueError):
        validate_train_test_identity(HyperPosterior({'a': np.array([1.0])}), [event('x', 'O4a')])

def test_predictive_collapse_is_visible():
    p = HyperPosterior({'a': np.arange(100.0)})
    r = predictive_support(p, np.r_[100.0, np.zeros(99)])
    assert r['predictive_contribution_ess'] < 1.01
    assert r['maximum_predictive_contribution'] > 0.99

def test_development_study_is_blocked():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    r = audit_study(root / 'config/real_study.example.json')
    assert r['status'] == 'BLOCKED'
    assert 'priors are development candidates, not frozen' in r['missing']
    spec = load_prior_spec(root / 'config/matched_bbh_priors.json')
    assert set(spec['shared']).isdisjoint(spec['feature_only'])
