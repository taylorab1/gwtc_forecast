"""Implementation notes
--------------------
The selection integral is of order found/generated, not normalized to 1."""
import numpy as np
import pytest
import h5py
from gwtc_forecast.statistics.qualification import wilson_interval, assess_direction, assess_bidirectional
from gwtc_forecast.statistics.uncertainty import resample_event_iid, resample_selection_iid, summarize_paired_score_replicates
from gwtc_forecast.statistics.objects import EventPosterior, SelectionCampaign
from gwtc_forecast.io.coordinates import source_component_masses_to_primary_ratio, detector_component_masses_distance_to_source
from gwtc_forecast.io.standardize import event_from_structured_hdf5

def test_zero_wrong_sign_has_nonzero_uncertainty():
    lo, hi = wilson_interval(0, 20)
    assert lo == pytest.approx(0, abs=1e-15) and hi > 0.1
    r = assess_direction(np.full(20, 8.0), final_count=20, maximum_wrong_sign_se=1, bootstrap_replicates=50)
    assert r['decision'] != 'PASS'

def test_qualification_success_failure_and_incomplete():
    rng = np.random.default_rng(6)
    good = rng.normal(8, 0.4, 2000)
    bad = rng.normal(-2, 0.4, 2000)
    kw = {'bootstrap_replicates': 100}
    assert assess_direction(good, **kw)['decision'] == 'PASS'
    assert assess_direction(bad, **kw)['decision'] == 'NO_GO_FOR_THIS_DESIGN'
    assert assess_direction(good[:50], **kw)['decision'] == 'INCOMPLETE'
    r = assess_bidirectional({'a': good, 'b': bad}, expected_models=['a', 'b'], **kw)
    assert r['decision'] == 'NO_GO_FOR_THIS_DESIGN'
    assert not r['authorizes_production']

def test_paired_numerical_error_preserves_covariance():
    x = np.arange(30.0)
    r = summarize_paired_score_replicates(x, x + 0.1, scope='same injections and PE resampled for both models')
    assert r['sigma_delta'] < 1e-14
    assert r['score_covariance'] > 1

def test_resampling_semantics_and_unrecovered_trials():
    e = EventPosterior('x', 'O4a', {'m': np.arange(10.0)}, np.zeros(10))
    with pytest.raises(ValueError):
        resample_event_iid(e, np.random.default_rng(1))
    e = EventPosterior('x', 'O4a', {'m': np.arange(10.0)}, np.zeros(10), metadata={'posterior_rows': 'independent_equal_weight'})
    assert resample_event_iid(e, np.random.default_rng(1)).sample_count == 10
    s = SelectionCampaign('O4a', {'m': np.arange(10.0)}, np.zeros(10), np.full(10, -np.log(100)), metadata={'generated_count': 100, 'normalization': 'single_iid_campaign_generated_count'})
    ss = resample_selection_iid(s, np.random.default_rng(1))
    assert np.exp(ss.log_base_weight).sum() < 0.3

def test_source_mass_ratio_jacobian():
    samples, lp = source_component_masses_to_primary_ratio([30.0], [15.0], [0.0])
    assert samples['mass_ratio'][0] == 0.5
    assert lp[0] == pytest.approx(np.log(30))

def test_detector_to_source_jacobian_numerically():
    m1, q, z = (30.0, 0.6, 0.3)

    def forward(v):
        m, q, z = v
        return np.array([m * (1 + z), q * m * (1 + z), 1000 * z + 200 * z * z])
    center = np.array([m1, q, z])
    eps = 1e-05
    jac = np.column_stack([(forward(center + np.eye(3)[j] * eps) - forward(center - np.eye(3)[j] * eps)) / (2 * eps) for j in range(3)])
    native = forward(center)
    s, lp = detector_component_masses_distance_to_source([native[0]], [native[1]], [z], [1000 + 400 * z], [0.0])
    assert lp[0] == pytest.approx(np.log(abs(np.linalg.det(jac))), abs=1e-08)
    assert s['mass_1_source'][0] == pytest.approx(m1)

def test_explicit_hdf5_extraction_does_not_claim_validation(tmp_path):
    p = tmp_path / 'event.h5'
    with h5py.File(p, 'w') as h:
        h.create_dataset('label/posterior_samples', data=np.array([(30.0, 0.5), (31.0, 0.6)], dtype=[('m', 'f8'), ('q', 'f8')]))
    e = event_from_structured_hdf5(p, dataset='label/posterior_samples', columns={'mass_1_source': 'm', 'mass_ratio': 'q'}, event_id='x', run='O4a', log_prior_in_target_coordinates=np.zeros(2), analysis_label='label', prior_reference='analytic independent reference')
    assert not e.metadata['validated']
    assert e.sample_count == 2
