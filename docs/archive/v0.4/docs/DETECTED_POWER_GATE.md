# Detected-space power qualification contract

This document specifies the machine decision that sits between the five-event
real-data integration slice and the expensive full-O4 PE campaign.

## Scientific role

For a mock catalog generated under model \(M_g\), define a signed score

\[
T = S_{M_g}-S_{M_{\rm alternative}}.
\]

Positive \(T\) means that the generating model won. Scores must be supplied in
both generating directions. A model that wins regardless of which model
created the data has not demonstrated bidirectional identifiability.

The power gate is a best-case detected-space qualification. It is not a
real-data result, an absolute model-adequacy test, or permission to claim that a
physical peak or break has been isolated.

## Input schema

`gwtc-forecast power-gate` consumes JSON of the form

```json
{
  "schema": "gwtc_forecast.detected_power_scores.v1",
  "signed_scores_by_generating_model": {
    "PowerLawPeak": [6.2, 7.1, 5.8],
    "PowerlawDipBreak": [5.9, 6.5, 7.0]
  },
  "metadata": {
    "run_contract": "O4a+O4b conditioned counts",
    "code_commit": "<commit>",
    "injection_folds": 5
  }
}
```

The short arrays above are illustrative only. The final gate requires the
replicate count frozen in `config/detected_power_gate.toml`.

## Frozen thresholds

For each generating direction:

- median signed score at least 5 nats;
- wrong-sign probability at most 0.10;
- fifth percentile strictly above zero;
- bootstrap standard error of the median at most 0.25 nat;
- binomial standard error of the wrong-sign probability at most 0.01;
- at least 2,000 completed qualified mocks.

These are project investment thresholds, not general discovery standards.
Changing them after examining mock or real-data results is forbidden.

## Command

```bash
gwtc-forecast power-gate \
  /path/to/detected_power_scores.json \
  --gate-config config/detected_power_gate.toml \
  --output /path/to/detected_power_decision.json
```

or

```bash
make power-gate SCORES=/path/to/detected_power_scores.json
```

## Terminal states

- `QUALIFICATION_INCOMPLETE_MORE_MOCKS_REQUIRED`: at least the preliminary
  sample exists, but a final pass/no-go is not authorized.
- `PASS_DETECTED_POWER_GATE`: both generating directions pass all frozen gates.
- `NO_GO_INSUFFICIENT_DETECTED_POWER`: the final mock sample is complete and at
  least one generating direction fails.

Technical problems such as an invalid schema, missing model direction, or
nonfinite score produce an explicit command failure rather than a scientific
no-go.

## What a pass authorizes

A pass authorizes preparation of a separately reviewed, prespecified full-O4 PE
campaign. It does not turn on `real_data_scoring_enabled`, validate the public
release adapters, establish model adequacy, or support a peak-versus-break
physical conclusion.
