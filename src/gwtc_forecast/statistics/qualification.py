"""Uncertainty-aware investment decisions. Not astronomical discovery thresholds.

Implementation notes
--------------------
Interval-derived SE remains nonzero when no error was observed."""
from __future__ import annotations
import numpy as np
from scipy.stats import binom, norm

def wilson_interval(successes: int, trials: int, confidence: float=0.95):
    if not 0 <= successes <= trials or trials < 1 or (not 0 < confidence < 1):
        raise ValueError('invalid binomial inputs')
    z = norm.ppf((1 + confidence) / 2)
    p = successes / trials
    d = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / d
    half = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / d
    return (max(0.0, float(center - half)), min(1.0, float(center + half)))

def quantile_interval(values, q, confidence=0.95):
    """Conservative distribution-free order-statistic interval, continuous data.

    None denotes an unbounded endpoint. No asymptotic zero-error shortcut.
    """
    x = np.sort(np.asarray(values, float))
    if x.ndim != 1 or not len(x) or (not np.isfinite(x).all()) or (not 0 < q < 1):
        raise ValueError('invalid quantile inputs')
    if not 0 < confidence < 1:
        raise ValueError('confidence must lie between zero and one')
    tail = (1 - confidence) / 2
    lower_rank = int(binom.ppf(tail, len(x), q))
    upper_rank = int(binom.ppf(1 - tail, len(x), q)) + 1
    low = float(x[lower_rank - 1]) if lower_rank >= 1 else None
    high = float(x[upper_rank - 1]) if upper_rank <= len(x) else None
    return (low, high)

def assess_direction(values, *, final_count=2000, median_target=5.0, wrong_sign_limit=0.1, q05_target=0.0, maximum_median_se=0.25, maximum_wrong_sign_se=0.01, seed=20260904, bootstrap_replicates=1000):
    x = np.asarray(values, float)
    if x.ndim != 1 or len(x) < 2 or (not np.isfinite(x).all()):
        raise ValueError('all planned scores must be present, finite, and valid')
    if final_count < 2 or bootstrap_replicates < 2:
        raise ValueError('at least two planned and bootstrap replicates required')
    n = len(x)
    if n > final_count:
        raise ValueError('more scores than the frozen final count; review the design rather than adding trials to pass')
    p = float(np.mean(x <= 0))
    wrong_ci = wilson_interval(int(np.sum(x <= 0)), n)
    median_ci = quantile_interval(x, 0.5)
    q05_ci = quantile_interval(x, 0.05)
    rng = np.random.default_rng(seed)
    medians = np.array([np.median(x[rng.integers(0, n, n)]) for _ in range(bootstrap_replicates)])
    median_se = float(medians.std(ddof=1))
    wrong_se = (wrong_ci[1] - wrong_ci[0]) / (2 * norm.ppf(0.975))
    precision_ok = median_se <= maximum_median_se and wrong_se <= maximum_wrong_sign_se
    confidence_pass = median_ci[0] is not None and median_ci[0] >= median_target and (q05_ci[0] is not None) and (q05_ci[0] > q05_target) and (wrong_ci[1] <= wrong_sign_limit)
    confidence_fail = median_ci[1] is not None and median_ci[1] < median_target or (q05_ci[1] is not None and q05_ci[1] <= q05_target) or wrong_ci[0] > wrong_sign_limit
    if n < final_count:
        decision = 'INCOMPLETE'
    elif not precision_ok:
        decision = 'INCONCLUSIVE_NUMERICAL_PRECISION'
    elif confidence_pass:
        decision = 'PASS'
    elif confidence_fail:
        decision = 'NO_GO_FOR_THIS_DESIGN'
    else:
        decision = 'INCONCLUSIVE_THRESHOLD_OVERLAP'
    return {'decision': decision, 'replicates': n, 'median': float(np.median(x)), 'q05': float(np.quantile(x, 0.05)), 'wrong_sign_probability': p, 'median_95_interval': median_ci, 'q05_95_interval': q05_ci, 'wrong_sign_95_interval': wrong_ci, 'median_standard_error': median_se, 'wrong_sign_interval_derived_standard_error': float(wrong_se), 'precision_ok': bool(precision_ok), 'authorizes_production': False}

def assess_bidirectional(scores, *, expected_models, **kwargs):
    if set(scores) != set(expected_models) or len(expected_models) != 2:
        raise ValueError('require exactly the two prespecified generating models')
    reports = {name: assess_direction(scores[name], **kwargs) for name in expected_models}
    decisions = [r['decision'] for r in reports.values()]
    if all((d == 'PASS' for d in decisions)):
        decision = 'PASS_QUALIFICATION_CRITERIA'
    elif any((d == 'INCOMPLETE' for d in decisions)):
        decision = 'INCOMPLETE'
    elif any((d == 'NO_GO_FOR_THIS_DESIGN' for d in decisions)):
        decision = 'NO_GO_FOR_THIS_DESIGN'
    else:
        decision = 'INCONCLUSIVE'
    return {'decision': decision, 'directions': reports, 'authorizes_production': False}
