# Uncertainty-aware power decision

The default `power-gate` command now uses `statistics/qualification.py`. The v0.4 point-threshold implementation remains importable only for historical regression tests; it is not the recommended decision method.

The frozen configuration retains 250 preliminary and 2000 final independent catalogs per generating direction, with 1000 median-bootstrap repetitions. A signed score is positive when the model that generated the catalog wins. Retain all planned valid trials and account for every numerical failure; failed trials cannot simply be removed from a final input file.

Final investment targets are median>=5, wrong-sign probability<=0.10, fifth percentile>0, median SE<=0.25, and wrong-sign SE<=0.01. The enhanced assessor uses distribution-free order-statistic intervals and Wilson binomial intervals. It does not report zero uncertainty because no wrong classifications were seen. A threshold-overlapping confidence interval produces INCONCLUSIVE, not a pass. Extra trials beyond the frozen final count are rejected rather than interpreted as a new favorable stopping point.

Input remains the compatible small JSON format:

```json
{
  "schema": "gwtc_forecast.detected_power_scores.v1",
  "metadata": {
    "purpose": "REPLACE with the actual qualified experiment",
    "observation_model_reference": "REPLACE with inspected evidence",
    "all_planned_trials_accounted_for": false
  },
  "signed_scores_by_generating_model": {
    "matched_bbh_continuum": [],
    "matched_bbh_highpeak": []
  }
}
```

Empty scores correctly fail validation. Run `gwtc-forecast power-gate /path/to/scores.json --output /path/to/new_decision.json`. It preserves numeric thresholds from `config/detected_power_gate.toml`. Existing decision files are not overwritten. Statistical assessment does not independently establish the scientific validity of the input metadata; the relevant report must be reviewed.

PASS supports consideration of the next investment, not an astronomical detection. NO_GO is limited to this model pair/design/generating regime. INCOMPLETE, INCONCLUSIVE and invalid execution are distinct from NO_GO. The learning demo's 20 trials and finite one-dimensional grid cannot qualify real-data analysis.
