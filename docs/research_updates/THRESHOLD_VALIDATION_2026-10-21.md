# GWTC Forecast v0.5 — Synthetic Threshold Validation

Date: 2026-10-21

## Calibration

Slurm job: 51866
Seed: 20261025
Replicates per generating direction: 2000

Null 95th-percentile threshold:
Delta S = 1.172732

Calibration false-positive rate: 5.00%
Calibration detection power: 61.90%

## Independent validation

Slurm job: 51867
Seed: 20261026
Replicates per generating direction: 2000

Frozen threshold: 1.172732

False positives: 96/2000 (4.80%)
95% exact CI: [3.91%, 5.83%]

Detections: 1244/2000 (62.20%)
95% exact CI: [60.03%, 64.33%]

One-sided test of FPR > 5%:
p = 0.673462

## Interpretation

The independently measured false-positive rate is
consistent with the nominal 5% target.

The validation does not prove strict FPR control at
or below 5%.

Detection power is approximately 62% under the
specified synthetic prior-predictive experiment.

## Scientific restrictions

This threshold is specific to the current synthetic
models, priors, observation counts, and likelihood.

It is not a real-data detection threshold.

Real GWTC scoring remains disabled pending
separate scientific readiness checks.

## Next phase

Investigate detection power as a function of:
- Held-out event count
- High-mass feature strength
- Training catalog size

Do not retune the validated threshold using the
independent validation dataset.
