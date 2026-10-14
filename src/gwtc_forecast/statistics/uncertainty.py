"""Focused numerical checks with explicitly limited sampling assumptions."""
from __future__ import annotations
import numpy as np
from scipy.special import logsumexp
from .objects import EventPosterior, HyperPosterior, SelectionCampaign

def predictive_support(posterior: HyperPosterior, catalog_log_factors):
    raw = posterior.log_weights + np.asarray(catalog_log_factors, float)
    if raw.shape != posterior.log_weights.shape or not np.isfinite(raw).any():
        raise ValueError('invalid predictive support')
    logc = raw - logsumexp(raw)
    c = np.exp(logc)
    initial = np.exp(posterior.log_weights)
    positive = c > 0
    return {'initial_weight_ess': float(1 / np.sum(initial ** 2)), 'predictive_contribution_ess': float(1 / np.sum(c ** 2)), 'maximum_predictive_contribution': float(c.max()), 'kl_updated_from_training_nats': float(np.sum(c[positive] * (logc[positive] - posterior.log_weights[positive]))), 'representation': posterior.metadata.get('representation', 'unspecified'), 'diagnostic_is_not_convergence_proof': True}

def resample_event_iid(event: EventPosterior, rng):
    """Ordinary bootstrap ONLY for independent equal-weight posterior rows."""
    if event.metadata.get('posterior_rows') != 'independent_equal_weight':
        raise ValueError('resampling requires certified independent equal-weight rows; use block/weighted design otherwise')
    if not np.allclose(event.log_sample_weights, -np.log(event.sample_count), atol=1e-12):
        raise ValueError('event rows are not equal weight')
    idx = rng.integers(0, event.sample_count, event.sample_count)
    return EventPosterior(event.event_id, event.run, {k: v[idx] for k, v in event.samples.items()}, event.log_pe_prior[idx], dict(event.metadata))

def resample_selection_iid(campaign: SelectionCampaign, rng):
    """Bootstrap ALL trials, including unobserved unrecovered trials.

    Only valid for a single IID campaign with base weight 1/N_generated.
    Recovered rows are not renormalized to the number recovered. Mixed or
    stratified official injection campaigns require release-specific resampling.
    """
    if campaign.metadata.get('normalization') != 'single_iid_campaign_generated_count':
        raise ValueError('release-specific mixed/stratified campaign resampling is required')
    n = int(campaign.metadata['generated_count'])
    k = campaign.injection_count
    if not n >= k or not np.allclose(campaign.log_base_weight, -np.log(n)):
        raise ValueError('inconsistent generated-count normalization')
    probabilities = np.r_[np.full(k, 1 / n), (n - k) / n]
    counts = rng.multinomial(n, probabilities)[:k]
    mask = counts > 0
    if not mask.any():
        raise ValueError('bootstrap campaign recovered no injections')
    return SelectionCampaign(campaign.run, {key: value[mask] for key, value in campaign.samples.items()}, campaign.log_draw_density[mask], np.log(counts[mask]) - np.log(n), {**campaign.metadata, 'bootstrap_weighted_rows': True})

def summarize_paired_score_replicates(scores_a, scores_b, *, scope):
    """Preserve shared-sample covariance; caller must state what was rerun."""
    a, b = (np.asarray(scores_a, float), np.asarray(scores_b, float))
    if a.ndim != 1 or a.shape != b.shape or len(a) < 3 or (not np.isfinite(a + b).all()):
        raise ValueError('need >=3 valid paired numerical replicates')
    if not scope.strip():
        raise ValueError('scope must state PE/injection/training/sampler components included')
    delta = a - b
    return {'replicates': len(a), 'scope': scope, 'mean_delta': float(delta.mean()), 'sigma_delta': float(delta.std(ddof=1)), 'q025_q975_delta': np.quantile(delta, [0.025, 0.975]).tolist(), 'score_covariance': float(np.cov(a, b, ddof=1)[0, 1]), 'not_catalog_variance': True, 'not_automatically_total_numerical_error': True}
