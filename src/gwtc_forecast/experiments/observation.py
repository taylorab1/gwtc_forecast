"""Explicit synthetic observation model used ONLY for development/calibration.

An independent detection flag is sampled conditional on true mass. Conditional
on detection, y=ln(m_true)+Normal(0,sigma). Real GW selection and likelihoods
are not modeled by this experiment. Training and test noise are independent.


Implementation notes
--------------------
Noise is drawn about truth, then PE below is centered on this datum.
PE conditions on the complete observed toy data: y AND detection flag.
Its likelihood is Normal(y|ln(m),sig) * p_det(m). This lets the ordinary
GW event reweighting code work unchanged, without double selection.
PE prior is uniform in x, therefore pi(m)=1/(m ln(mmax/mmin)).
Scaling each observed likelihood avoids underflow for extreme y."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from scipy.stats import truncnorm
from ..populations.matched_mass import MatchedMass, mass_quadrature, MASS_KEY
from ..statistics.objects import EventPosterior, SelectionCampaign, HyperPosterior
RUN_SETTINGS = {'O3': (0.04, 0.9, 25.0, 11.0), 'O4a': (0.08, 0.9, 19.0, 12.0), 'O4b': (0.12, 0.86, 14.0, 14.0)}

def detection_probability(mass, run):
    if run not in RUN_SETTINGS:
        raise ValueError(f'unknown synthetic run {run!r}')
    floor, amplitude, midpoint, width = RUN_SETTINGS[run]
    return floor + amplitude * expit((np.asarray(mass) - midpoint) / width)

@dataclass(frozen=True)
class Observation:
    event_id: str
    run: str
    truth_mass: float
    log_mass_observed: float
    sigma_log_mass: float

def simulate_catalog(model: MatchedMass, hyperparameters, *, rng, count_by_run, sigma_log_mass=0.16, prefix='sim'):
    if sigma_log_mass <= 0 or not np.isfinite(sigma_log_mass):
        raise ValueError('sigma_log_mass must be positive')
    observations = []
    for run, count in count_by_run.items():
        if not isinstance(count, (int, np.integer)) or count < 0:
            raise ValueError('run counts must be nonnegative integers')
        masses = []
        attempts = 0
        while len(masses) < count:
            n = max(64, 3 * (count - len(masses)))
            proposals = model.sample(rng, n, hyperparameters)
            accepted = proposals[rng.random(n) < detection_probability(proposals, run)]
            masses.extend(accepted.tolist())
            attempts += n
            if attempts > max(100000, count * 1000):
                raise RuntimeError('synthetic detection rejection sampler exhausted')
        for i, mass in enumerate(masses[:count]):
            y = float(np.log(mass) + rng.normal(0, sigma_log_mass))
            observations.append(Observation(f'{prefix}_{run}_{i:04d}', run, mass, y, sigma_log_mass))
    return observations

def posterior_for_observation(observation, model, *, rng, sample_count=512):
    if sample_count < 2:
        raise ValueError('sample_count must be >=2')
    lo, hi = (np.log(model.m_min), np.log(model.m_max))
    y, sig = (observation.log_mass_observed, observation.sigma_log_mass)
    accepted = []
    attempts = 0
    while len(accepted) < sample_count:
        n = max(64, 3 * (sample_count - len(accepted)))
        x = truncnorm.rvs((lo - y) / sig, (hi - y) / sig, loc=y, scale=sig, size=n, random_state=rng)
        proposals = np.exp(x)
        accepted.extend(proposals[rng.random(n) < detection_probability(proposals, observation.run)].tolist())
        attempts += n
        if attempts > sample_count * 1000:
            raise RuntimeError('toy event posterior rejection sampler exhausted')
    m = np.asarray(accepted[:sample_count])
    return EventPosterior(observation.event_id, observation.run, {MASS_KEY: m}, -np.log(m) - np.log(hi - lo), metadata={'synthetic': True, 'coordinates': [MASS_KEY], 'analysis_label': 'joint_log_mass_normal_and_detection_log_uniform_prior', 'log_mass_observed': y, 'sigma_log_mass': sig, 'posterior_rows': 'independent_equal_weight', 'not_real_gw_measurement_model': True})

def synthetic_injections(model, run, *, rng, generated_count=50000):
    if generated_count < 10:
        raise ValueError('generated_count too small')
    x = rng.uniform(np.log(model.m_min), np.log(model.m_max), generated_count)
    mass = np.exp(x)
    kept = mass[rng.random(generated_count) < detection_probability(mass, run)]
    if not len(kept):
        raise RuntimeError('no recovered synthetic injections')
    return SelectionCampaign(run, {MASS_KEY: kept}, -np.log(kept) - np.log(np.log(model.m_max / model.m_min)), np.full(len(kept), -np.log(generated_count)), metadata={'synthetic': True, 'generated_count': generated_count, 'normalization': 'single_iid_campaign_generated_count'})

def population_table(model, support: HyperPosterior, *, nodes=512):
    mass, dm = mass_quadrature(model.m_min, model.m_max, nodes)
    logp = np.stack([model.log_prob({MASS_KEY: mass}, support.draw(j)) for j in range(support.draw_count)])
    return (mass, dm, logp)

def exact_log_factors(observations, model, support, *, nodes=512, table=None):
    """Quadrature reference for p(y|det,Lambda), on stated finite prior nodes.

    p_det occurs inside this reference numerator as part of the joint toy
    likelihood for (y,det=1). The toy PE posterior includes this factor already.
    Neither real nor toy PE reweighting multiplies by p_det a second time.
    """
    if table is None:
        table = population_table(model, support, nodes=nodes)
    mass, dm, logp = table
    output = np.empty((len(observations), support.draw_count))
    for run in {o.run for o in observations}:
        idx = [i for i, o in enumerate(observations) if o.run == run]
        obs = [observations[i] for i in idx]
        y = np.array([o.log_mass_observed for o in obs])[:, None]
        sig = np.array([o.sigma_log_mass for o in obs])[:, None]
        loglike = -0.5 * ((y - np.log(mass)) / sig) ** 2 - np.log(sig * np.sqrt(2 * np.pi))
        offset = loglike.max(axis=1)
        like = np.exp(loglike - offset[:, None])
        weights = np.exp(logp) * detection_probability(mass, run) * dm
        numerator = like @ weights.T
        if (numerator <= 0).any():
            raise ArithmeticError('unresolved observation integral; increase quadrature')
        output[idx] = np.log(numerator) + offset[:, None] - np.log(weights.sum(axis=1))
    return output

def pe_log_factors(observations, events, model, support, selections):
    """Use the production statistical core on these synthetic PE contracts.

    The PE likelihood already includes the observed detection flag. The usual
    PE reweighting numerator must NOT contain an extra selection factor.
    Results omit event evidence constants which cancel between models.
    """
    from ..statistics.likelihood import catalog_log_likelihood
    if [o.event_id for o in observations] != [e.event_id for e in events]:
        raise ValueError('observation/event order mismatch')
    evaluation = catalog_log_likelihood(events, selections, model, support)
    return np.stack([evaluation.events[e.event_id].log_likelihood - evaluation.selections[e.run].log_efficiency for e in events])
