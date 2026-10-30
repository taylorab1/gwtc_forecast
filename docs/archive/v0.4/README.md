# GWTC catalog-to-catalog forecasting

This repository is the full starting point for a chronological, out-of-sample
Bayesian test of binary-black-hole population models:

> Which population structures inferred from GWTC-3 assigned the largest
> selection-corrected predictive probability to later O4 detections?

The first physical comparison is deliberately narrow:

1. the released GWTC-3 `PowerLawPeak` population analysis;
2. the released GWTC-3 `PowerlawDipBreak` population analysis;
3. five O4 PE files spanning O4a and O4b;
4. the released O4a+O4b injection campaign.

The repository separates code and data:

```text
Code on the laptop and synchronized through MEGA:
~/MEGA/GRAND_projects/gwtc_forecast

Public GW data, processed scientific products, large numerical caches,
temporary scientific files, and results:
/media/oamacias/LaCie/GW_Project_Data

Laptop-local Conda environment and package caches:
gwtc_forecast
```

The code refuses to write when `/media/oamacias/LaCie` is not a genuine mounted
filesystem. This prevents an unplugged external disk from silently redirecting
multi-gigabyte downloads to the laptop.

## What is already implemented

The repository goes substantially beyond downloading data. It includes:

- a resumable and checksum-verified Zenodo downloader;
- safe archive extraction entirely on the external disk;
- release and generic HDF5 inventory tools;
- a lightweight reader for the official O4 PE summary tables;
- pilot-event candidate-label and event-file consistency reports;
- a PESummary-aware combined-event inspector;
- an audit of the documented O4 injection fields, FAR columns, draw-density
  components, weights, attributes, and observing-run windows;
- immutable processed event, selection, and hyperposterior HDF5 contracts;
- backward-compatible weighted and equal-weight PE posterior contracts;
- tested event-level hierarchical reweighting;
- tested selection-efficiency importance sampling;
- bounded-memory chunked selection-contract evaluation;
- tested catalog predictive scores;
- tested chronological/prequential scoring;
- a generic vertical-slice evaluator with ESS, event influence, and score-
  difference Monte Carlo diagnostics;
- normalized toy smooth, peak, and break mass models;
- a deterministic selection-biased mock-catalog validation;
- a frozen, bidirectional detected-space power-gate decision contract;
- a machine-readable production-readiness report;
- strict Codex instructions in `AGENTS.md` and `CODEX_FIRST_CAMPAIGN.md`.

The statistical layer is usable now on mocks and on validated analysis-ready
objects. Real-data scoring is intentionally gated until the exact PE-prior,
O4a/O4b normalization, and released GWTC-3 model mappings have been independently
audited.

## 1. Install this full replacement

This ZIP is the entire repository, not an overlay. Keep the existing external
data directory, but replace the old code tree.

```bash
cd ~/MEGA/GRAND_projects
mv gwtc_forecast gwtc_forecast.pre_full_baseline
unzip /path/to/gwtc_forecast_drop_in_replacement.zip
cd gwtc_forecast
```

After the new baseline passes its checks, the backup code directory may be
removed. Do not copy `.venv`, Conda files, downloaded HDF5 files, caches, or
results into the new repository.

## 2. Create the dedicated Conda environment

The external disk is not required for software installation or unit tests:

```bash
cd ~/MEGA/GRAND_projects/gwtc_forecast
./scripts/setup_conda.sh
```

The environment and package caches remain in Conda's normal laptop-local
locations, not inside MEGA or on the LaCie disk. The setup script creates or
updates `gwtc_forecast`, installs this repository in editable mode, and runs the
offline validation suite. Connect the LaCie disk only before public-data,
processed-contract, large-temporary-file, or result operations.

For interactive work:

```bash
source scripts/activate_project.sh
```

For Codex or other non-interactive commands:

```bash
./scripts/run_in_env.sh pytest -q
./scripts/run_in_env.sh gwtc-forecast status
```

## 3. Inspect and download only the frozen pilot

First resolve the current Zenodo metadata and exact size. This is a dry run:

```bash
make status
make bootstrap
make plan
```

The manifest pins release record IDs, exact filenames, and expected MD5
checksums. Metadata drift or a checksum mismatch is a hard stop.

Download and prepare the pilot:

```bash
make download
make verify
make extract
```

The pilot is expected to be roughly 6.5 GB compressed, but `make plan` reports
the live byte count before any large transfer. All files are stored below
`/media/oamacias/LaCie/GW_Project_Data/raw`; extraction is also performed on the
external disk.

## 4. Begin the scientific audit immediately

After the files are present:

```bash
make inventory
make pe-index
make selection-schema
make discover
make science-smoke
make readiness
```

Or run the non-destructive first-look sequence:

```bash
make first-look
```

Important outputs are written under:

```text
/media/oamacias/LaCie/GW_Project_Data/results/pilot/
├── inventory/
│   ├── data_inventory.json
│   ├── file_inventory.csv
│   ├── pe_release_index.json
│   ├── o4a_pe_candidates.csv
│   ├── o4b_pe_candidates.csv
│   ├── o4ab_selection_schema.json
│   └── hyperposterior_discovery.json
├── toy_validation/
│   ├── toy_validation.json
│   └── toy_events.csv
└── readiness.json
```

`pe_release_index.json` connects each pilot event to every released
`result_samples_key` without freezing a label. `o4ab_selection_schema.json`
checks the actual public HDF5 against the documented field names but leaves the
run-specific normalization unresolved. This distinction is deliberate.

Read the complete student-facing implementation and experiment plan first:

```text
STUDENT_RESEARCH_PLAN.md
```

Then read the release and statistical contracts before changing any mapping:

```text
docs/OFFICIAL_RELEASE_SCHEMA_NOTES.md
docs/RELEASE_AUDIT_CHECKLIST.md
docs/STATISTICAL_CONVENTIONS.md
docs/DATA_CONTRACTS.md
docs/DETECTED_POWER_GATE.md
```

## 5. Start the Codex campaign

Run:

```bash
make codex-preflight
```

Then direct Codex to read `AGENTS.md` and `CODEX_FIRST_CAMPAIGN.md`. The first
campaign is tightly bounded:

1. freeze and validate one PE label/prior adapter per pilot event;
2. derive and independently validate separate O4a/O4b selection contracts;
3. map the two released GWTC-3 hyperposteriors and executable densities;
4. feed those objects into the existing vertical-slice evaluator;
5. produce the five-event integration score only after every numerical and
   provenance gate passes;
6. run the bidirectional detected-space power qualification before authorizing
   the expensive full-catalog PE campaign.

The five events are an integration slice, not the paper's population sample.
No new model family, spin extension, full-catalog download, or new inference is
authorized before the vertical slice and power qualification succeed.

## Core commands

```bash
make help
make setup
make status
make plan
make download
make verify
make extract
make inventory
make pe-index
make selection-schema
make discover
make science-smoke
make mapping-status
make readiness
make power-gate SCORES=/path/to/detected_power_scores.json
make first-look
make test
make lint
make audit
make lock
make codex-preflight
make jupyter
```

## External directory layout

```text
/media/oamacias/LaCie/GW_Project_Data/
├── raw/          # Immutable Zenodo downloads
├── extracted/    # Safely extracted release archives
├── processed/    # Compact analysis-ready contracts
├── results/      # Tables, reports, figures, scores
├── cache/        # Zenodo metadata and scientific numerical caches
├── manifests/    # Resolved data/software provenance
├── logs/         # Logs
└── tmp/          # All large temporary work
```

## Release records

- GWTC-3 population release: DOI `10.5281/zenodo.11254021`
- O4a+O4b sensitivity estimates: DOI `10.5281/zenodo.19500064`
- GWTC-4.1 O4a PE release: DOI `10.5281/zenodo.20275769`
- GWTC-5 O4b PE Part 1: DOI `10.5281/zenodo.20348005`
- GWTC-5 population products: DOI `10.5281/zenodo.20292639`

See `SCIENCE_CHARTER.md`, `ROADMAP.md`, and `KNOWN_GAPS.md` before changing scope.
