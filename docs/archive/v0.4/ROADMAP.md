# Ruthlessly prioritized roadmap

The full student-facing scientific and implementation plan is in
`STUDENT_RESEARCH_PLAN.md`. This file is the compact repository decision tree.

## Stage 0: repository and storage safety (implemented software baseline)

- Dedicated laptop-local `gwtc_forecast` Conda environment.
- Code in MEGA; public GW data and generated scientific products on LaCie.
- Mount-point guard and repository data guard.
- Pinned pilot manifest, resumable downloader, checksum verification, and
  bounded archive preflight.

The repository contains the machinery, not evidence that the external downloads
have already been executed on the student's machine.

**Exit:** offline tests, compilation, and repository audit pass; the external
mount passes separately before data operations.

## Stage 1: release inventory (implemented baseline)

- Inventory the released GWTC-3 archives.
- Index candidate PE labels from the official lightweight summary tables.
- Inventory each combined PE HDF5 file without choosing a label.
- Audit the documented O4 injection table, draw-density fields, FAR columns,
  weights, and run windows while leaving normalization gated.
- Record all labels, parameters, dimensions, attributes, and source checksums.

**Exit:** a machine-readable inventory exists and every required file is
unambiguous.

## Stage 2: statistical algebra (implemented baseline)

- Equal- or unequal-weight event-posterior reweighting.
- Selection-efficiency importance sampling, including bounded-memory chunks.
- Run-conditioned catalog likelihood.
- Hyperposterior-marginalized predictive score.
- Chronological/prequential update.
- Toy smooth, peak, and break population models.
- Mock recovery and joint/prequential consistency tests.
- A generic vertical-slice orchestrator with ESS, influence, chronological, and
  finite-hyperposterior score-difference diagnostics.
- Null-safe absolute/relative Monte Carlo precision logic.
- Immutable event, selection, and hyperposterior contracts.
- A deterministic bidirectional detected-power decision contract.

**Exit:** `make science-smoke` and all offline tests pass.

## Stage 3: PE adapter

For each of the five PE files:

1. list all PESummary labels;
2. freeze one documented mixed/default label;
3. determine whether the stored rows are equal or unequal weight;
4. extract the required source-frame parameters and row weights;
5. reconstruct and test the exact PE prior density;
6. write a compact processed-event v2 contract;
7. hard-fail when a prior, row weight, or Jacobian is unresolved.

**Exit:** prior-reweighting tests pass and the same mapping is independently
audited by both students.

## Stage 4: injection adapter

1. identify O4a and O4b masks;
2. identify generated and found injections;
3. reconstruct the injection draw density and mixture weights;
4. define the estimator normalization explicitly;
5. compare fixed-hyperparameter \(\xi_r\) values with GWPopulation or released
   reference code;
6. write compact processed-selection contracts;
7. demonstrate full versus streamed evaluation agreement.

**Exit:** agreement within `max(2 sigma_MC, 2%)` at representative points.

## Stage 5: released hyperposterior adapter

1. map the extracted GWTC-3 release tree;
2. identify posterior files and model metadata;
3. read equal or unequal hyperposterior weights correctly;
4. map released parameter names to each complete population density;
5. preserve mass ratio, redshift, spin, support, taper, and cosmology assumptions;
6. evaluate detected-space model densities at fixed test points.

**Exit:** one machine-readable released GWTC-3 mass-spectrum reference is
reproduced within a frozen quantitative tolerance.

## Stage 6: five-event real-data vertical slice

Compute for both released models:

- event-level \(\log \mathcal L_i(\Lambda)\);
- O4a/O4b \(\log \xi_r(\Lambda)\);
- joint predictive score;
- chronological eventwise score increments;
- posterior and selection ESS;
- bootstrap/Monte Carlo uncertainty;
- leave-one-event-out influence.

**Exit:** `PASS_REAL_DATA_VERTICAL_SLICE` means that authentic release adapters
work together. It is not a population-level peak-versus-break result.

## Stage 7: bidirectional detected-space power qualification

Generate O4-sized detected mock catalogs under each frozen released model and
form a signed score that is positive when the generating model wins. Use
`config/detected_power_gate.toml` and the machine decision implemented by
`gwtc-forecast power-gate`.

The final gate requires in both generating directions:

- median signed score at least 5 nats;
- wrong-sign probability at most 0.10;
- fifth percentile above zero;
- frozen Monte Carlo standard-error thresholds;
- at least 2,000 completed mocks per direction.

**Exit:** `PASS_DETECTED_POWER_GATE` authorizes a separately reviewed full-O4 PE
campaign. `NO_GO_INSUFFICIENT_DETECTED_POWER` stops the two-model paper rather
than triggering additional model families or weaker thresholds.

## Stage 8: full O4a+O4b predictive audit

Freeze the official population event-count contract, process the prespecified
PE sample, and score O4a, O4b, and their chronological combination. Report
comparative score increments rather than model-specific absolute event
surprises when event evidences are absent.

**Investment gate:** a stable, calibrated, and scientifically interpretable
released-model result is required before harmonized refits.

## Stage 9: full uncertainty and model adequacy

Propagate PE posterior, injection, shared-score covariance, catalog variance,
waveform/label alternatives, run splits, and event influence. Test each model's
adequacy separately: a relative winner may still be a poor model.

## Stage 10: harmonized physical comparison and sealed O4c forecast

Only after the historical released-model audit contains stable information may
the team fit smooth, peak, and break models with identical nuisance structure.
Freeze a timestamped O4c/GWTC-6 prediction before the relevant official catalog
is inspected or used for tuning.
