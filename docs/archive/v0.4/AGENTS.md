# AGENTS.md

## Repository mission

This is a prediction-first gravitational-wave population project. The primary
objective is a selection-corrected, chronological held-out score of frozen
GWTC-3 BBH population models on O4 data.

## Storage rules

- Repository: `~/MEGA/GRAND_projects/gwtc_forecast`
- External mount: `/media/oamacias/LaCie`
- External root: `/media/oamacias/LaCie/GW_Project_Data`
- Never write raw data, processed data, figures, logs, caches, checkpoints, or
  scientific outputs inside the repository.
- Resolve output locations through `ProjectPaths` or exported `GWTC_*` paths.
- Never bypass the external mount guard.
- Never commit files larger than 20 MiB.

## Environment

Use:

```bash
./scripts/run_in_env.sh <command>
```

Do not create another environment unless a demonstrated dependency conflict is
documented. Do not place Conda environments inside MEGA.

## Read first

```text
SCIENCE_CHARTER.md
STUDENT_RESEARCH_PLAN.md
KNOWN_GAPS.md
CODEX_FIRST_CAMPAIGN.md
docs/OFFICIAL_RELEASE_SCHEMA_NOTES.md
docs/STATISTICAL_CONVENTIONS.md
docs/DATA_CONTRACTS.md
```

Then inspect the external reports produced by:

```bash
make first-look
```

## Scientific priority

1. PE label and exact prior mapping.
2. O4a/O4b injection normalization and reference validation.
3. Released GWTC-3 hyperposterior and density mapping.
4. Five-event integration score through the existing vertical-slice evaluator.
5. Numerical, influence, and Monte Carlo diagnostics.
6. Bidirectional detected-space power qualification before any full-catalog PE
   campaign.

Everything else is lower priority. The five-event result is not a title-level
population claim.

## Existing code to reuse

Do not rewrite the statistical core. Use:

```text
src/gwtc_forecast/statistics/
src/gwtc_forecast/workflows/vertical_slice.py
src/gwtc_forecast/io/contracts.py
```

The existing code already handles event reweighting, selection penalties,
hyperposterior marginalization, chronological updates, ESS summaries,
leave-one-event-out influence, and finite-hyperposterior score-difference
uncertainty.

## Real-data safety gate

`config/science.toml` keeps `real_data_scoring_enabled = false`. Do not switch it
to true until all readiness checks below are machine-verifiable:

- every event has a frozen analysis label;
- every event has an exact log PE prior in the population coordinates;
- every event's equal- or unequal-weight posterior-row semantics are frozen;
- O4a and O4b processed selection contracts exist;
- selection normalization has an independent fixed-point validation;
- both released models have tested probability-density adapters;
- all ESS and finite-value checks pass.

Filling a mapping file with plausible strings is not validation. Preserve test
points, source checksums, derivations, and independent comparisons in metadata.

## Coding standards

- Put reusable calculations in `src/`, not notebooks.
- Use explicit dataclasses and type hints.
- Use stable log-space calculations.
- Hard-fail on missing or ambiguous scientific metadata.
- Preserve source checksums and release identifiers in every processed object.
- Add unit tests for every scientific formula and coordinate transformation.
- Avoid global state and hard-coded repository-relative data paths.
- Never load arbitrary pickle files before auditing their origin and classes.

## Scope control

Do not add new population models, spin analysis, rate inference, ML, or GPU
acceleration before the five-event vertical slice passes. Do not launch the
full-catalog PE workflow before both the vertical slice and the bidirectional
detected-power qualification pass. A compact auditable result is preferred to
a broad framework.

## Required checks before every handoff

```bash
make test
make lint
make audit
make science-smoke
make mapping-status
make readiness
```

## Long jobs

Do not start jobs expected to exceed 15 minutes. Instead provide the exact
command, inputs, expected outputs, and stop criteria.
