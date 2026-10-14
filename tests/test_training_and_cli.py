"""Check the optional adapter interface without pretending Bilby was installed."""
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from gwtc_forecast.cli import main
from gwtc_forecast.experiments.feature_demo import load_demo_config, build_pair
from gwtc_forecast.experiments.observation import (
    Observation, posterior_for_observation, synthetic_injections,
)
from gwtc_forecast.inference.training import make_bilby_likelihood, training_log_likelihood
from gwtc_forecast.inference.frozen import compare_frozen_pair
from gwtc_forecast.statistics.objects import HyperPosterior
from gwtc_forecast.statistics.qualification import assess_direction


def small_inputs():
    c, _ = load_demo_config()
    models, _ = build_pair(c)
    pars = c['generating_parameters']
    rng = np.random.default_rng(707)
    events = [posterior_for_observation(
        Observation(f'e{i}', run, mass, np.log(mass), 0.2), models[0],
        rng=rng, sample_count=150,
    ) for i, (run, mass) in enumerate([('O4a', 30.), ('O4b', 18.)])]
    selections = {run: synthetic_injections(models[0], run, rng=rng,
                  generated_count=3000) for run in ['O4a', 'O4b']}
    return models, pars, events, selections


def test_bilby_interface_matches_direct_likelihood():
    models, pars, events, selections = small_inputs()
    class StubLikelihood:
        def __init__(self, parameters):
            self.parameters = parameters
    fake = SimpleNamespace(Likelihood=StubLikelihood)
    likelihood = make_bilby_likelihood(fake, parameter_names=pars,
                 events=events, selections=selections, model=models[1])
    direct = training_log_likelihood(pars, events=events,
             selections=selections, model=models[1])
    likelihood.parameters.update(pars)
    assert likelihood.log_likelihood() == pytest.approx(direct)
    assert likelihood.log_likelihood(parameters=pars) == pytest.approx(direct)


def test_frozen_comparison_is_joint_and_not_a_validity_flag():
    models, pars, events, selections = small_inputs()
    posteriors = [HyperPosterior(
        {k: np.array([v, v]) for k, v in pars.items()},
        model_name=m.name, metadata={'trained_on': ['training_event']},
    ) for m in models]
    result = compare_frozen_pair(events, selections, models, posteriors)
    assert np.sum(result['eventwise_delta']) == pytest.approx(
        result['delta_feature_minus_continuum'])
    assert all(not m['scientifically_validated'] for m in result['models'])
    assert len(result['delta_without_each_event']) == 2


def test_primary_cli_power_uses_uncertainty_and_refuses_overwrite(tmp_path):
    root = Path(__file__).resolve().parents[1]
    payload = {
        'schema': 'gwtc_forecast.detected_power_scores.v1',
        'metadata': {'synthetic_unit_test': True},
        'signed_scores_by_generating_model': {
            'matched_bbh_continuum': [8.] * 20,
            'matched_bbh_highpeak': [8.] * 20,
        },
    }
    scores = tmp_path / 'scores.json'
    output = tmp_path / 'decision.json'
    scores.write_text(json.dumps(payload))
    args = ['power-gate', str(scores), '--gate-config',
            str(root / 'config/detected_power_gate.toml'), '--output', str(output)]
    assert main(args) == 0
    result = json.loads(output.read_text())
    assert result['decision'] == 'INCOMPLETE'
    assert not result['authorizes_production']
    assert main(args) != 0


def test_extra_power_trials_need_a_design_decision():
    with pytest.raises(ValueError, match='more scores'):
        assess_direction(np.full(21, 8.), final_count=20)
