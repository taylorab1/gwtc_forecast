# Codex first campaign

## Mission

Turn the downloaded five-event pilot into an auditable real-data vertical slice:

\[
\text{PE samples}
\rightarrow \mathcal L_i(\Lambda)
\rightarrow \xi_r(\Lambda)
\rightarrow S_M
\rightarrow \Delta S.
\]

Do not broaden the science case. The campaign ends when the five-event
integration score is computed with controlled diagnostics, or when an explicit
gate fails. A pass authorizes only the separate detected-space power campaign;
it is not a population-level peak-versus-break conclusion.

## Priority order

### Task 1: run and read the existing baseline

```bash
make codex-preflight
make first-look
```

Read:

- `SCIENCE_CHARTER.md`
- `KNOWN_GAPS.md`
- `docs/OFFICIAL_RELEASE_SCHEMA_NOTES.md`
- `$GWTC_RESULTS_ROOT/pilot/inventory/pe_release_index.json`
- `$GWTC_RESULTS_ROOT/pilot/inventory/o4ab_selection_schema.json`
- `$GWTC_RESULTS_ROOT/pilot/inventory/hyperposterior_discovery.json`
- the official notebooks and READMEs downloaded by the manifest.

Do not begin by opening all multi-gigabyte arrays. Use the lightweight indices
and inventories first.

### Task 2: PE mapping

Implement a release-specific adapter under:

```text
src/gwtc_forecast/io/gwtc_pe.py
```

The PE summary index already supplies candidate `result_samples_key` values and
checks the combined event filenames. The remaining work is scientific, not
file discovery.

Required outputs per event:

- frozen label and documented label-selection rule;
- source-frame posterior arrays in the released-model coordinates;
- exact log PE prior in those same coordinates;
- documented equal-weight status or explicit normalized posterior-row weights;
- every coordinate Jacobian and cosmology convention;
- waveform/sampler metadata;
- source record, filename, and checksum;
- sample count and parameter list.

Write each processed object with `write_event_contract`. Never silently
substitute a different label or a guessed prior.

### Task 3: injection mapping

Implement:

```text
src/gwtc_forecast/io/o4_injections.py
```

The baseline has already audited the documented `/events` table, intrinsic
fields, nine log-draw components, `weights`, search-specific FAR fields, and
O4a/O4b time windows. Do not repeat that discovery manually.

Required outputs per run:

- frozen time mask and FAR threshold;
- explicit handling of missing/infinite search FARs;
- injection parameter arrays;
- `log_draw_density`;
- `log_base_weight`, including the correct run-specific generated-count and
  wall-time mixture normalization;
- source provenance and column mapping.

Validate \(\xi_{\rm O4a}\) and \(\xi_{\rm O4b}\) against an independent public
implementation at representative fixed hyperparameters. Write one
`SelectionCampaign` contract per run only after that comparison passes.

### Task 4: released-model mapping

Implement:

```text
src/gwtc_forecast/io/gwtc3_hyperposteriors.py
src/gwtc_forecast/populations/released_gwtc3.py
```

Start only with `PowerLawPeak` and `PowerlawDipBreak`. Prefer executable released
model code over transcription from paper equations. Preserve all mass-ratio,
redshift, spin, support, taper, and normalization assumptions needed by the
released posterior.

Write validated hyperposteriors with `write_hyperposterior_contract`.

### Task 5: first real-data score

Add a thin workflow:

```text
src/gwtc_forecast/workflows/five_event_score.py
```

It should read only processed contracts, instantiate the two validated released
model adapters, and call:

```python
from gwtc_forecast.workflows.vertical_slice import (
    compare_vertical_slice_models,
    evaluate_model_vertical_slice,
)
```

Do not duplicate the likelihood or sequential algebra.

The final report must contain:

- score per model;
- score difference and finite-hyperposterior bootstrap uncertainty;
- eventwise increments and cumulative chronological difference;
- event PE ESS by event;
- selection ESS by run;
- hyperposterior ESS after every event;
- leave-one-event-out influence;
- joint/prequential discrepancy;
- numerical and provenance failure flags.

## Acceptance tests

1. A toy conjugate or importance-sampling problem matches an analytic result.
2. Event and hyperposterior ordering do not affect the joint score.
3. Joint and prequential scores agree to `1e-10` in deterministic tests.
4. Event, selection, and hyperposterior contracts round-trip exactly.
5. Unknown PE labels, missing priors, missing injection normalization, and
   insufficient ESS cause hard failures.
6. The two O4 selection factors agree with an independent implementation within
   `max(2 sigma_MC, 2%)` at frozen points.
7. One released GWTC-3 mass-spectrum result is reproduced before real scoring.
8. No file larger than 20 MiB appears in the repository.
9. Every generated result is under `GWTC_RESULTS_ROOT`.

## Forbidden shortcuts

- Do not use posterior samples as if they were population draws.
- Do not drop the PE-prior denominator.
- Do not use one cumulative O4 selection factor for both runs without explicit
  derivation and justification.
- Do not normalize injection weights by guesswork.
- Do not treat the tutorial waveform-priority example as a frozen population
  label policy.
- Do not tune bins, priors, or model variants after viewing eventwise scores.
- Do not download the entire O4 catalog during this campaign.
- Do not begin fitting new hyperposteriors.

## Compute policy

Fast local calculations and tests are authorized. Any inference or job expected
to exceed 15 minutes must stop and leave exact run instructions rather than
starting automatically.
