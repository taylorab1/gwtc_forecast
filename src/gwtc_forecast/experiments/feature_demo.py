"""A saved, reloadable train -> freeze -> predict -> qualify learning experiment.

Implementation notes
--------------------
A small explicit /tmp path is supported for learning only. The CLI's
default goes through the project's external-storage guard instead.
Same saved/reloaded contracts and statistical core used by real-data
adapters. Train anew for the MC path to include training MC effects."""
from __future__ import annotations
import csv
import hashlib
import json
import platform
import time
import tomllib
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path
import numpy as np
from ..inference.grid import cartesian_prior, fit_finite_prior, score_factors, sequential_factors
from ..io.contracts import write_event_contract, read_event_contract, write_selection_contract, read_selection_contract, write_hyperposterior_contract, read_hyperposterior_contract
from ..populations.matched_mass import MatchedMass, MASS_KEY
from .observation import simulate_catalog, posterior_for_observation, synthetic_injections, exact_log_factors, pe_log_factors, population_table

def load_demo_config(path=None):
    text = Path(path).read_text() if path else files('gwtc_forecast').joinpath('defaults', 'feature_demo.toml').read_text()
    c = tomllib.loads(text)
    if c.get('schema_version') != 1 or c.get('purpose') != 'synthetic_learning_and_implementation_reference_only':
        raise ValueError('not a supported synthetic demo configuration')
    for key in ('training_count', 'heldout_count_per_run', 'quadrature_nodes', 'posterior_samples', 'generated_injections'):
        if not isinstance(c[key], int) or c[key] < 2:
            raise ValueError(f'invalid {key}')
    return (c, text)

def build_pair(config):
    models = [MatchedMass(False, **config['mass_domain']), MatchedMass(True, **config['mass_domain'])]
    axes0 = config['shared_axes']
    axes1 = {**axes0, **config['feature_axes']}
    priors = [cartesian_prior(axes, config['shared_fixed'], model_name=model.name) for axes, model in zip((axes0, axes1), models)]
    return (models, priors)

def _output_directory(path):
    path = Path(path).expanduser().resolve()
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f'output is nonempty; choose a new attempt directory: {path}')
    path.mkdir(parents=True, exist_ok=True)
    return path

def _json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')

def run_feature_demo(output_dir, *, config_path=None, power_replicates=None, make_plots=True, progress=None):
    start = time.perf_counter()
    notify = progress if progress is not None else (lambda message: None)
    phase_timings = {}
    config, config_text = load_demo_config(config_path)
    if power_replicates is not None:
        if power_replicates < 0:
            raise ValueError('power_replicates must be nonnegative')
        config['power_replicates_per_direction'] = int(power_replicates)
    out = _output_directory(output_dir)
    (out / 'feature_demo.toml').write_text(config_text)
    _json(out / 'effective_config.json', config)
    seed = int(config['seed'])
    streams = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(5)]
    rng_train, rng_test, rng_pe, rng_inj, rng_power = streams
    models, priors = build_pair(config)
    notify("Generating independent synthetic training and held-out observations.")
    truth = config['generating_parameters']
    kwargs = dict(sigma_log_mass=config['sigma_log_mass'])
    train = simulate_catalog(models[1], truth, rng=rng_train, count_by_run={'O3': config['training_count']}, prefix='train', **kwargs)
    heldout = simulate_catalog(models[1], truth, rng=rng_test, count_by_run={'O4a': config['heldout_count_per_run'], 'O4b': config['heldout_count_per_run']}, prefix='heldout', **kwargs)
    _json(out / 'observations.json', {'synthetic': True, 'training': [asdict(o) for o in train], 'heldout': [asdict(o) for o in heldout]})
    events = []
    for obs in train + heldout:
        event = posterior_for_observation(obs, models[0], rng=rng_pe, sample_count=config['posterior_samples'])
        path = out / 'contracts' / f'{event.event_id}.h5'
        write_event_contract(path, event)
        events.append(read_event_contract(path))
    selections = {}
    for run in ('O3', 'O4a', 'O4b'):
        selection = synthetic_injections(models[0], run, rng=rng_inj, generated_count=config['generated_injections'])
        path = out / 'contracts' / f'selection_{run}.h5'
        write_selection_contract(path, selection)
        selections[run] = read_selection_contract(path)
    exact_scores, mc_scores, posterior_list, exact_factors_list = ([], [], [], [])
    model_reports = {}
    phase_timings["generate_and_reload_contracts"] = time.perf_counter() - start
    for model, prior in zip(models, priors):
        phase_start = time.perf_counter()
        notify(f"Fitting and scoring {model.name} against quadrature and PE/injection paths.")
        table = population_table(model, prior, nodes=config['quadrature_nodes'])
        tf = exact_log_factors(train, model, prior, table=table)
        fit = fit_finite_prior(prior, tf, training_ids=[o.event_id for o in train])
        path = out / 'contracts' / f'training_posterior_{model.name}.h5'
        write_hyperposterior_contract(path, fit.posterior)
        posterior = read_hyperposterior_contract(path)
        hf = exact_log_factors(heldout, model, posterior, table=table)
        score = score_factors(posterior, hf)
        inc, ess, finalw = sequential_factors(posterior, hf)
        n_a = config['heldout_count_per_run']
        score_a = score_factors(posterior, hf[:n_a])
        score_b_independent = score_factors(posterior, hf[n_a:])
        loo_scores = np.array([score_factors(posterior, np.delete(hf, i, axis=0)) for i in range(len(heldout))])
        fine_tf = exact_log_factors(train, model, prior, nodes=2 * config['quadrature_nodes'])
        fine_fit = fit_finite_prior(prior, fine_tf, training_ids=[o.event_id for o in train])
        fine_hf = exact_log_factors(heldout, model, fine_fit.posterior, nodes=2 * config['quadrature_nodes'])
        fine_score = score_factors(fine_fit.posterior, fine_hf)
        mc_tf = pe_log_factors(train, events[:len(train)], model, prior, selections)
        mc_fit = fit_finite_prior(prior, mc_tf, training_ids=[o.event_id for o in train])
        mc_hf = pe_log_factors(heldout, events[len(train):], model, mc_fit.posterior, selections)
        mc_score = score_factors(mc_fit.posterior, mc_hf)
        np.savez_compressed(out / f'factors_{model.name}.npz', training=tf, heldout=hf, training_log_weights=posterior.log_weights, mc_training=mc_tf, mc_heldout=mc_hf)
        model_reports[model.name] = {'reference_joint_log_score': score, 'run_O4a_log_score': score_a, 'run_O4b_given_O4a_log_score': score - score_a, 'run_O4b_independently_marginalized_log_score': score_b_independent, 'joint_minus_sum_independent_run_scores': score - score_a - score_b_independent, 'joint_prequential_difference': float(abs(score - inc.sum())), 'quadrature_doubling_score_change': fine_score - score, 'prior_nodes': prior.draw_count, 'training_node_ess': float(1 / np.sum(np.exp(2 * posterior.log_weights))), 'updated_node_ess': float(1 / np.sum(np.exp(2 * finalw))), 'node_ess_interpretation': 'discrete probability concentration, NOT Monte Carlo ESS or convergence proof', 'increments': inc.tolist(), 'leave_one_out_scores': loo_scores.tolist(), 'training_evidence_up_to_common_constants': fit.log_evidence_up_to_common_constants}
        exact_scores.append(score)
        mc_scores.append(mc_score)
        posterior_list.append(posterior)
        exact_factors_list.append(hf)
        phase_timings[model.name] = time.perf_counter() - phase_start
    delta = exact_scores[1] - exact_scores[0]
    mc_delta = mc_scores[1] - mc_scores[0]
    delta_inc = np.array(model_reports[models[1].name]['increments']) - np.array(model_reports[models[0].name]['increments'])
    loo_delta = np.array(model_reports[models[1].name]['leave_one_out_scores']) - np.array(model_reports[models[0].name]['leave_one_out_scores'])
    with (out / 'event_scores.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['event_id', 'run', 'delta_prequential', 'delta_cumulative', 'delta_leave_one_out', 'full_minus_loo_delta'])
        for i, obs in enumerate(heldout):
            writer.writerow([obs.event_id, obs.run, delta_inc[i], delta_inc[:i + 1].sum(), loo_delta[i], delta - loo_delta[i]])
    phase_start = time.perf_counter()
    notify("Evaluating small conditional synthetic power sample.")
    power = conditional_power(models, posterior_list, config, rng_power, replicates=config['power_replicates_per_direction'])
    phase_timings['conditional_power'] = time.perf_counter() - phase_start
    _json(out / 'conditional_power.json', power)
    report = {'phase_seconds': phase_timings, 'status': 'SYNTHETIC_DEVELOPMENT_COMPLETE', 'real_data_analyzed': False, 'production_qualified': False, 'seed': seed, 'effective_config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(), 'python': platform.python_version(), 'numpy': np.__version__, 'comparison': 'high_feature_minus_common_continuum', 'reference_delta_log_score': delta, 'pe_injection_delta_log_score': mc_delta, 'mc_minus_reference_delta': mc_delta - delta, 'models': model_reports, 'power': power, 'implementation_checks': {'joint_sequential_identity': all((r['joint_prequential_difference'] < 1e-10 for r in model_reports.values())), 'quadrature_doubling_each_score_below_1e_3': all((abs(r['quadrature_doubling_score_change']) < 0.001 for r in model_reports.values()))}, 'limitations': ['One-dimensional synthetic likelihood and explicit toy detection mechanism, not real GW response.', 'Finite discrete priors, not qualified continuous population fits.', 'One PE/injection realization is a comparison, not a total numerical uncertainty estimate.', 'Power is conditional on this realized training catalog and uses both fixed competing posteriors.', 'Small demo power counts never qualify a real-data campaign or a publication.', 'A Gaussian excess component is not by itself a physical formation channel or even a local maximum.'], 'elapsed_seconds': time.perf_counter() - start}
    _json(out / 'report.json', report)
    (out / 'report.md').write_text(_report_markdown(report))
    if make_plots:
        _plots(out, models, posterior_list, config, delta_inc, power)
    return report

def conditional_power(models, posteriors, config, rng, *, replicates):
    """Conditional forecast power, one hyperparameter draw per mock catalog.

    Reuse the SAME training posterior for both directions. A full repeated-
    experiment calibration must independently simulate AND refit training.
    """
    result = {'scope': 'conditional_synthetic_forecast_power', 'qualifies_real_data': False, 'replicates_per_direction': replicates, 'directions': {}}
    tables = [population_table(m, p, nodes=config['quadrature_nodes']) for m, p in zip(models, posteriors)]
    for generator_index, (generator, generating_posterior) in enumerate(zip(models, posteriors)):
        signed = []
        for j in range(replicates):
            k = rng.choice(generating_posterior.draw_count, p=np.exp(generating_posterior.log_weights))
            obs = simulate_catalog(generator, generating_posterior.draw(k), rng=rng, count_by_run={'O4a': config['heldout_count_per_run'], 'O4b': config['heldout_count_per_run']}, sigma_log_mass=config['sigma_log_mass'], prefix=f'power{generator_index}_{j}')
            scores = [score_factors(p, exact_log_factors(obs, m, p, table=t)) for m, p, t in zip(models, posteriors, tables)]
            signed.append((scores[1] - scores[0]) * (1 if generator_index == 1 else -1))
        result['directions'][generator.name] = {'signed_scores': signed, 'median_signed_score': float(np.median(signed)) if signed else None, 'wrong_sign_fraction': float(np.mean(np.asarray(signed) <= 0)) if signed else None}
    return result

def _report_markdown(r):
    return f"# Matched-feature demonstration (synthetic only)\n\n**No real GW population conclusion and no production authorization.**\n\nReference held-out feature-minus-continuum log score: {r['reference_delta_log_score']:.6f}.\nPE/injection estimate, including an independent training fit: {r['pe_injection_delta_log_score']:.6f}.\nDifference from quadrature: {r['mc_minus_reference_delta']:.6f} (one realization, not an error bar).\n\nThe generating model contains a high-mass component by construction. The sign\nof this demonstration is not evidence for a peak in astronomical observations.\nSee `event_scores.csv`, `conditional_power.json`, and the detailed `report.json`.\n\n## What to explain at the meeting\n\nExplain the model difference, selection correction, why the training posterior\nis not a best-fit point, and why independent O4a/O4b scores do not add to the\njoint score. Compare saved/reloaded PE contracts to the quadrature reference.\nRead node ESS as finite-grid concentration, not sampler convergence.\n\n## Limitations\n\n" + '\n'.join(('- ' + x for x in r['limitations'])) + '\n'

def _plots(out, models, posteriors, config, delta_inc, power):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    mass = np.geomspace(config['mass_domain']['m_min'], config['mass_domain']['m_max'], 500)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for model, p in zip(models, posteriors):
        density = np.stack([np.exp(model.log_prob({MASS_KEY: mass}, p.draw(k))) for k in range(p.draw_count)])
        mean = np.exp(p.log_weights) @ density
        ax.plot(mass, mean, label=model.name)
    ax.set(xlabel='Primary mass (solar masses)', ylabel='Intrinsic density', title='SYNTHETIC: training-only predictive mass distributions')
    ax.set_xscale('log')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / 'training_prediction.png', dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(np.arange(1, len(delta_inc) + 1), np.cumsum(delta_inc))
    ax.axhline(0, linestyle=':')
    ax.axvline(config['heldout_count_per_run'] + 0.5, linestyle='--')
    ax.set(xlabel='Chronological held-out event', ylabel='Cumulative feature-minus-continuum log score', title='SYNTHETIC: frozen-training-posterior prediction')
    fig.tight_layout()
    fig.savefig(out / 'chronological_score.png', dpi=180)
    plt.close(fig)
    if power['replicates_per_direction']:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for name, direction in power['directions'].items():
            ax.hist(direction['signed_scores'], bins=12, histtype='step', label=name)
        ax.axvline(0, linestyle=':')
        ax.set(xlabel='Signed log score (positive means generating model wins)', ylabel='Mock catalogs', title='SYNTHETIC: conditional discrimination, not a qualification gate')
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / 'conditional_power.png', dpi=180)
        plt.close(fig)
