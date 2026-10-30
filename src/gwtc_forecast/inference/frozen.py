"""Frozen-training comparison and chronology checks, on analysis-ready objects.

Implementation notes
--------------------
Exact within-run order is supplied by the frozen event manifest. Do not
sort IDs here: IDs are labels, not guaranteed timestamps."""
from __future__ import annotations
import numpy as np
from .grid import score_factors, sequential_factors
from ..statistics.likelihood import catalog_log_likelihood
from ..statistics.uncertainty import predictive_support

def validate_train_test_identity(posterior, heldout_events, *, require_provenance=True):
    ids = [e.event_id for e in heldout_events]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('held-out events must be nonempty and unique')
    training = posterior.metadata.get('trained_on')
    if require_provenance and (not training):
        raise ValueError('training-event provenance is missing')
    if set(ids) & set(training or []):
        raise ValueError('training/held-out overlap detected')
    if any((e.run not in {'O4a', 'O4b', 'O4c'} for e in heldout_events)):
        raise ValueError('this study reserves through-O3 runs for training')
    order = {'O4a': 0, 'O4b': 1, 'O4c': 2}
    if [order[e.run] for e in heldout_events] != sorted((order[e.run] for e in heldout_events)):
        raise ValueError('run blocks must be chronological')

def score_frozen_model(events, selections, model, posterior):
    validate_train_test_identity(posterior, events)
    evaluation = catalog_log_likelihood(events, selections, model, posterior)
    factors = np.stack([evaluation.events[e.event_id].log_likelihood - evaluation.selections[e.run].log_efficiency for e in events])
    joint = score_factors(posterior, factors)
    inc, _, _ = sequential_factors(posterior, factors)
    independent = {}
    conditional = {}
    for run in dict.fromkeys((e.run for e in events)):
        index = [i for i, e in enumerate(events) if e.run == run]
        independent[run] = score_factors(posterior, factors[index])
        conditional[run] = float(inc[index].sum())
    loo = np.array([score_factors(posterior, np.delete(factors, i, axis=0)) for i in range(len(events))])
    return {'model': model.name, 'joint_log_score_up_to_event_constants': joint, 'increments': inc.tolist(), 'run_conditional_scores': conditional, 'run_independent_scores': independent, 'leave_one_out_scores': loo.tolist(), 'minimum_event_ess': float(min((v.effective_sample_size.min() for v in evaluation.events.values()))), 'minimum_selection_ess': float(min((v.effective_sample_size.min() for v in evaluation.selections.values()))), 'predictive_support': predictive_support(posterior, evaluation.log_likelihood), 'chronological_ids': [e.event_id for e in events], 'scientifically_validated': False}

def compare_frozen_pair(events, selections, models, posteriors):
    if len(models) != 2 or len(posteriors) != 2:
        raise ValueError('exactly two prespecified models required')
    if set(posteriors[0].metadata.get('trained_on', [])) != set(posteriors[1].metadata.get('trained_on', [])):
        raise ValueError('both models must use the same training events')
    shared_ids = [p.metadata.get('prior_spec_sha256') for p in posteriors]
    if all(shared_ids) and shared_ids[0] != shared_ids[1]:
        raise ValueError('both models must use the same frozen matched prior specification')
    reports = [score_frozen_model(events, selections, m, p) for m, p in zip(models, posteriors)]
    a, b = reports
    delta = b['joint_log_score_up_to_event_constants'] - a['joint_log_score_up_to_event_constants']
    return {'scope': 'candidate_frozen_comparison_requires_numerical_qualification', 'delta_feature_minus_continuum': delta, 'models': reports, 'eventwise_delta': (np.array(b['increments']) - np.array(a['increments'])).tolist(), 'delta_without_each_event': (np.array(b['leave_one_out_scores']) - np.array(a['leave_one_out_scores'])).tolist(), 'does_not_establish': 'absolute model adequacy, a formation channel, or production validity'}
