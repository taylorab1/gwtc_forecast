"""Exact inference for a stated finite prior support (not a continuous sampler).

Finite grids provide transparent training and predictive reference answers.
A grid is not certified as a continuous-prior approximation without refinement.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Mapping
import numpy as np
from scipy.special import logsumexp
from ..statistics.objects import HyperPosterior

def cartesian_prior(axes: Mapping[str, list[float]], fixed: Mapping[str, float], *, model_name: str):
    if not axes or set(axes) & set(fixed):
        raise ValueError('nonempty axes must be disjoint from fixed parameters')
    names = list(axes)
    if any((len(axes[k]) == 0 for k in names)):
        raise ValueError('empty prior axis')
    rows = np.array(list(product(*(axes[k] for k in names))), float)
    samples = {k: rows[:, j] for j, k in enumerate(names)}
    samples.update({k: np.full(len(rows), float(v)) for k, v in fixed.items()})
    return HyperPosterior(samples, model_name=model_name, metadata={'representation': 'finite_discrete_prior', 'equal_probability_nodes': True, 'continuous_prior_validated': False})

@dataclass(frozen=True)
class GridFit:
    posterior: HyperPosterior
    log_evidence_up_to_common_constants: float
    log_likelihood: np.ndarray

def fit_finite_prior(prior: HyperPosterior, event_log_factors: np.ndarray, *, training_ids: list[str]):
    """Train only on supplied data; rows are events, columns prior support points."""
    factors = np.asarray(event_log_factors, float)
    if factors.ndim != 2 or factors.shape[1] != prior.draw_count or (not len(factors)):
        raise ValueError('training factors must be events x prior nodes')
    if len(training_ids) != len(factors) or len(set(training_ids)) != len(training_ids):
        raise ValueError('training IDs must be unique and match factors')
    if np.isnan(factors).any() or np.isposinf(factors).any():
        raise ValueError('invalid training log factors')
    loglike = factors.sum(axis=0)
    raw = prior.log_weights + loglike
    evidence = float(logsumexp(raw))
    if not np.isfinite(evidence):
        raise ValueError('training catalog has zero support')
    posterior = HyperPosterior(prior.samples, raw, prior.model_name, {**prior.metadata, 'representation': 'finite_discrete_posterior', 'trained_on': list(training_ids), 'training_only': True})
    return GridFit(posterior, evidence, loglike)

def score_factors(posterior: HyperPosterior, factors: np.ndarray):
    factors = np.asarray(factors, float)
    if factors.ndim != 2 or factors.shape[1] != posterior.draw_count:
        raise ValueError('score factors must be events x posterior nodes')
    if not np.isfinite(factors).all():
        raise ValueError('predictive factors must be finite')
    return float(logsumexp(posterior.log_weights + factors.sum(axis=0)))

def sequential_factors(posterior: HyperPosterior, factors: np.ndarray):
    factors = np.asarray(factors, float)
    joint = score_factors(posterior, factors)
    logw = posterior.log_weights.copy()
    increments, ess = ([], [])
    for row in factors:
        inc = float(logsumexp(logw + row))
        increments.append(inc)
        logw += row - inc
        ess.append(float(1 / np.sum(np.exp(2 * logw))))
    if not np.isclose(sum(increments), joint, atol=1e-10, rtol=1e-12):
        raise ArithmeticError('joint/sequential identity failed')
    return (np.asarray(increments), np.asarray(ess), logw)
