import numpy as np
import pytest
from gwtc_forecast.experiments.feature_demo import load_demo_config, build_pair, run_feature_demo
from gwtc_forecast.experiments.observation import Observation, posterior_for_observation, synthetic_injections, exact_log_factors, pe_log_factors
from gwtc_forecast.experiments.calibration import randomized_rank, run_repeated_calibration
from gwtc_forecast.statistics.objects import HyperPosterior

def test_pe_conditions_on_noisy_observation_and_detection():
    c, _ = load_demo_config()
    m, p = build_pair(c)
    obs = Observation('x', 'O4a', 10.0, np.log(35.0), 0.05)
    ev = posterior_for_observation(obs, m[0], rng=np.random.default_rng(1), sample_count=5000)
    assert abs(np.mean(np.log(ev.samples['mass_1_source'])) - np.log(35.0)) < 0.01
    assert abs(np.mean(np.log(ev.samples['mass_1_source'])) - np.log(obs.truth_mass)) > 1

def test_pe_ratio_agrees_with_independent_integral():
    c, _ = load_demo_config()
    models, _ = build_pair(c)
    h = c['generating_parameters']
    p = HyperPosterior({k: np.array([v]) for k, v in h.items()})
    obs = Observation('x', 'O4a', 30.0, np.log(31.0), 0.16)
    ev = posterior_for_observation(obs, models[0], rng=np.random.default_rng(2), sample_count=80000)
    sel = {'O4a': synthetic_injections(models[0], 'O4a', rng=np.random.default_rng(3), generated_count=150000)}
    exact = [exact_log_factors([obs], m, p)[0, 0] for m in models]
    mc = [pe_log_factors([obs], [ev], m, p, sel)[0, 0] for m in models]
    assert mc[1] - mc[0] == pytest.approx(exact[1] - exact[0], abs=0.035)

def tiny_config(path):
    ctext = 'schema_version=1\npurpose="synthetic_learning_and_implementation_reference_only"\nseed=20260904\ntraining_count=4\nheldout_count_per_run=2\nsigma_log_mass=0.2\nquadrature_nodes=256\nposterior_samples=150\ngenerated_injections=2000\npower_replicates_per_direction=2\n[mass_domain]\nm_min=5.0\nm_max=160.0\n[shared_fixed]\nalpha_high=5.0\nm_break=35.0\nbreak_width=0.18\nf_low=0.2\nmu_low=10.0\nsigma_low=1.8\n[shared_axes]\nalpha_low=[1.0,2.0]\n[feature_axes]\nf_high=[0.1,0.3]\nmu_high=[30.0]\nsigma_high=[3.0]\n[generating_parameters]\nalpha_low=2.0\nalpha_high=5.0\nm_break=35.0\nbreak_width=0.18\nf_low=0.2\nmu_low=10.0\nsigma_low=1.8\nf_high=0.1\nmu_high=30.0\nsigma_high=3.0\n'
    path.write_text(ctext)
    return path

def test_saved_reloaded_end_to_end_and_reproducibility(tmp_path):
    config = tiny_config(tmp_path / 'config.toml')
    r = run_feature_demo(tmp_path / 'a', config_path=config, make_plots=False)
    r2 = run_feature_demo(tmp_path / 'b', config_path=config, make_plots=False)
    assert r['reference_delta_log_score'] == r2['reference_delta_log_score']
    assert not r['production_qualified'] and (not r['real_data_analyzed'])
    assert all(r['implementation_checks'].values())
    assert (tmp_path / 'a/event_scores.csv').is_file()
    with pytest.raises(FileExistsError):
        run_feature_demo(tmp_path / 'a', config_path=config, make_plots=False)

def test_repeated_training_calibration_executes(tmp_path):
    config = tiny_config(tmp_path / 'config.toml')
    r = run_repeated_calibration(tmp_path / 'cal', config_path=config, replicates=2)
    assert not r['qualifies_real_data']
    for rows in r['directions'].values():
        assert len(rows) == 2
        assert all((0 <= v <= 1 for row in rows for v in row['randomized_sbc_ranks'].values()))

def test_randomized_discrete_sbc_rank():
    rng = np.random.default_rng(8)
    value = randomized_rank(np.array([1.0, 2.0, 2.0, 3.0]), np.log([0.1, 0.2, 0.3, 0.4]), 2.0, rng)
    assert 0.1 <= value <= 0.6
