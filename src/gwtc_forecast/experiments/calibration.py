"""Repeated train-and-test validation with randomized finite-prior SBC ranks.

This is distinct from the conditional-power experiment in feature_demo.py.
It is an executable reference under a correctly specified one-dimensional
synthetic likelihood, not GW instrument calibration.


Implementation notes
--------------------
One population draw shared by this replicate's training and test."""
from __future__ import annotations
import json
import numpy as np
from .feature_demo import load_demo_config, build_pair, _output_directory
from .observation import simulate_catalog, exact_log_factors, population_table
from ..inference.grid import fit_finite_prior, score_factors

def randomized_rank(values, log_weights, truth, rng):
    values = np.asarray(values, float)
    w = np.exp(log_weights)
    return float(w[values < truth].sum() + rng.random() * w[values == truth].sum())

def run_repeated_calibration(outdir, *, config_path=None, replicates=20, seed=20260905):
    if replicates < 2:
        raise ValueError('replicates must be >=2')
    config, text = load_demo_config(config_path)
    models, priors = build_pair(config)
    tables = [population_table(m, p, nodes=config['quadrature_nodes']) for m, p in zip(models, priors)]
    out = _output_directory(outdir)
    (out / 'feature_demo.toml').write_text(text)
    rng = np.random.default_rng(seed)
    directions = {}
    for gidx, (generator, prior) in enumerate(zip(models, priors)):
        rows = []
        for rep in range(replicates):
            ti = rng.choice(prior.draw_count, p=np.exp(prior.log_weights))
            truth = prior.draw(ti)
            train = simulate_catalog(generator, truth, rng=rng, count_by_run={'O3': config['training_count']}, sigma_log_mass=config['sigma_log_mass'], prefix=f'cal{gidx}_{rep}_train')
            test = simulate_catalog(generator, truth, rng=rng, count_by_run={'O4a': config['heldout_count_per_run'], 'O4b': config['heldout_count_per_run']}, sigma_log_mass=config['sigma_log_mass'], prefix=f'cal{gidx}_{rep}_test')
            fits = []
            scores = []
            for model, p, t in zip(models, priors, tables):
                fit = fit_finite_prior(p, exact_log_factors(train, model, p, table=t), training_ids=[o.event_id for o in train])
                fits.append(fit)
                scores.append(score_factors(fit.posterior, exact_log_factors(test, model, fit.posterior, table=t)))
            correct = fits[gidx].posterior
            rank_names = ['alpha_low', 'm_break', 'f_low'] + (['f_high'] if gidx else [])
            rows.append({'replicate': rep, 'truth': truth, 'signed_score': float((scores[1] - scores[0]) * (1 if gidx else -1)), 'randomized_sbc_ranks': {k: randomized_rank(correct.samples[k], correct.log_weights, truth[k], rng) for k in rank_names}})
        directions[generator.name] = rows
    report = {'scope': 'synthetic_prior_predictive_repeated_training_calibration', 'qualifies_real_data': False, 'seed': seed, 'replicates_per_direction': replicates, 'directions': directions, 'interpretation': 'SBC ranks should be uniform in repeated draws from the specified finite prior. Small samples are illustrative, not certification. Predictive classification can be weak despite calibrated inference.'}
    (out / 'calibration.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report
