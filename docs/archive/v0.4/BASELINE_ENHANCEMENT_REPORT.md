# Baseline enhancement and verification report

Build date: 2026-08-28  
Package version: `0.4.0`

## Purpose

This repository is a hardened drop-in replacement for the supplied v0.3
student baseline. It preserves the original hierarchical predictive-statistics
architecture and adds only changes that remove a realistic scientific or
operational failure mode for the planned GWTC-3-to-O4 project.

The repository still contains no validated public-release PE adapter, no
validated O4a/O4b selection normalization, no executable released GWTC-3 model
adapter, and no real-data population result. Those are the students' research
tasks, not claims of this baseline.

## Changes with scientific consequences

### 1. Unequal-weight event posterior products

`EventPosterior` now stores normalized `log_sample_weights`. When omitted, the
rows remain equal weight. The event estimator is

\[
\widehat{\mathcal L}_i(\Lambda) \propto
\sum_k q_{ik}
\frac{p(\theta_{ik}\mid\Lambda)}{\pi_i(\theta_{ik})},
\]

rather than always assuming `1/K`. Processed event contracts are now v2 and v1
contracts remain readable as equal-weight products.

### 2. A valid null score is no longer a numerical failure

The original comparison required a fractional Monte Carlo error even when
`delta S` was zero. The replacement always requires the frozen absolute MC
precision and applies the fractional criterion only once the score difference
is larger than that absolute numerical scale. Joint-versus-prequential
agreement also uses a mixed absolute-plus-relative tolerance.

### 3. Large selection contracts can be evaluated in bounded memory

`iter_selection_contract_chunks` validates all stored row counts and yields
bounded slices. `selection_log_efficiency_chunked` combines global efficiency
and ESS using log-space accumulation of `sum(w)` and `sum(w**2)`. Regression
tests verify agreement with the original in-memory calculation.

### 4. Path and archive handling is fail-closed

The replacement rejects parent traversal and absolute paths in project-layout,
manifest, download-destination, and extraction-target inputs. Archive preflight
rejects links and special members, duplicate normalized names, excessive member
counts, excessive expanded size, excessive expansion ratio, and insufficient
free space before extraction.

### 5. Development no longer requires the external disk

Conda environments and package caches remain laptop-local. Unit tests, linting,
documentation, and code development can run without the LaCie disk. Public-data
and scientific-result commands retain the independent Python storage guard and
fail closed when the configured external filesystem is not safely mounted.

### 6. The detected-space investment gate is executable

`config/detected_power_gate.toml`,
`src/gwtc_forecast/workflows/detected_power_gate.py`, and the
`gwtc-forecast power-gate` command implement the frozen bidirectional decision
rule from the student plan. The code evaluates completed mock scores; it does
not fabricate the public-release mock generator.

### 7. Readiness state corrected

`mock_calibration_passed` is now `false`. The existing toy smoke test validates
algebra and software behavior only; it is not the O4-sized released-model power
qualification.

## Added regression coverage

The suite now tests:

- equal- and unequal-weight event posterior rows;
- v1-to-v2 event-contract compatibility;
- invalid posterior-row weights;
- streamed versus in-memory selection efficiency and ESS;
- full-dataset row-count validation;
- mixed-run chunk rejection;
- null-safe score-difference diagnostics;
- mixed absolute/relative numerical tolerance;
- layout and manifest path containment;
- archive expansion and duplicate-member rejection;
- bidirectional power-gate pass, no-go, and incomplete states;
- deterministic label-stable seed derivation.

## Verification performed in the artifact environment

- `43` offline tests passed.
- Every Python source and test file compiled successfully.
- `37` importable package modules loaded successfully, excluding the executable
  `__main__` module.
- All `14` shell scripts passed `bash -n` syntax validation.
- All `11` TOML files parsed successfully.
- All `4` notebooks were valid nbformat-4 JSON with no saved outputs or
  execution counts.
- The repository data guard passed.
- The package built as `gwtc_forecast-0.4.0-py3-none-any.whl` and imported from
  a clean target directory.
- The direct toy workflow returned `PASS`.
- The detected-power CLI was smoke-tested on a preliminary score payload and
  correctly returned `QUALIFICATION_INCOMPLETE_MORE_MOCKS_REQUIRED`.

Ruff was not installed in the artifact container, so Ruff itself was not run
here. It remains installed by `environment.yml` and is run by
`scripts/setup_conda.sh` and `make lint` on the target machine.

## Deliberately not executed

- Multi-gigabyte public data downloads.
- Interpretation of the actual public PE or injection payloads.
- Released GWTC-3 population-density mapping.
- O4-sized detected mock generation.
- A real-data predictive score.

## Recommended first commands after installation

Software-only checks, with or without the external disk:

```bash
./scripts/setup_conda.sh
./scripts/run_in_env.sh pytest -q
./scripts/run_in_env.sh python -m compileall -q src tests
```

After connecting the external disk:

```bash
make bootstrap
make status
make plan
make first-look
```

Read `STUDENT_RESEARCH_PLAN.md`, `ROADMAP.md`, and
`docs/DETECTED_POWER_GATE.md` before beginning release-specific adapters.
