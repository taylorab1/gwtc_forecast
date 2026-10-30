# GWTC forecast: do population features earn their predictive complexity?

**Version 0.5.0 | refurbished scientific and student-development baseline | 4 September 2026**

This repository asks whether an additional high-mass excess improves predictions of later binary-black-hole observations over a matched, smoothly bending population without that excess. It fits a training population, preserves its posterior uncertainty, and evaluates new observations using their measurement uncertainty and observing-period selection functions.

**Run the complete synthetic experiment now. Qualify the real-data interfaces before making an astronomical claim.** No public-event population fit or production calibration was executed when building this release. Its new candidate priors are not a frozen scientific prescription.

## Start here (students)

From this directory, in an existing suitable Python >=3.11 environment:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m gwtc_forecast feature-demo --output /tmp/gwtc-feature-attempt1
python -m gwtc_forecast feature-calibration --output /tmp/gwtc-calibration-attempt1 --replicates 20
python -m gwtc_forecast study-audit --spec config/real_study.example.json
```

Choose a new output directory for each attempt. The first installation needs Internet access; the synthetic commands and tests do not. `study-audit` deliberately reports BLOCKED with concrete missing inputs; that is a successful inventory, not a broken installation. Setting `OPENBLAS_NUM_THREADS=1` can avoid excessive thread use for small exercises.

For a dedicated Conda environment instead, run `bash scripts/setup_student.sh`, then `conda activate gwtc_forecast`. This preserves an already-existing environment rather than pruning it. The optional larger `environment.yml` and `setup_conda.sh` retain the previous research dependencies; use them only when reaching the Bilby/release-analysis milestones. An installation failure is an environment task, not an excuse to suspend all reading, analytical work, or small Python exercises.

Read, in order: `STUDENT_RESEARCH_PLAN.md`, `SCIENCE_CHARTER.md`, `docs/STATISTICAL_CONVENTIONS.md`, and `STUDENT_MEETING_MILESTONES.md`. Use `notebooks/00_start_here.ipynb` for a short guided entry. The archived 90-kB plan is historical, not your current assignment.

## What is different from v0.4?

The primary comparison is now a matched model pair, not PowerLawPeak versus PowerlawDipBreak. Both models share a bending continuum, a low-mass component, mass-ratio prescription, spin prescription, redshift prescription, support, and shared priors. Only the additional high-mass component differs. We therefore target its incremental predictive value rather than attributing every difference between unrelated models to a peak.

The new demo really simulates noisy observations, fits both training posteriors, writes and reloads the event/selection/posterior contracts, and evaluates a later two-period catalog. Its quadrature calculation provides an independent numerical reference for the posterior-sample/injection route. A separate repeated-training experiment distinguishes simulation-based calibration from power conditional on one training catalog. Neither is a real GW response simulation.

## Executable workflow

| Stage | Entry point | What it establishes |
|---|---|---|
| Learning and integration | `feature-demo` | Complete synthetic inference and held-out scoring with reference checks |
| Repeated synthetic calibration | `feature-calibration` | Finite-prior posterior-rank reference with fresh training each replicate |
| Real input inventory | `study-audit --spec …` | Missing paths and unfrozen design, not scientific validity |
| Through-O3 training | `study-fit --spec … --model continuum` and `--model highpeak` | Optional Bilby fit from explicit, validated contracts |
| Frozen comparison | `study-score --spec …` | Candidate held-out score after training-sampler qualification |
| Investment decision | `power-gate scores.json` | Uncertainty-aware assessment of already-produced mock scores |

The last three commands do not substitute for the independent checks in `docs/REAL_DATA_WORKFLOW.md`. The real-data mock-observation generator, public PE-prior adapters, and release-specific injection normalization are still qualification work. A template with blank input paths is deliberate; no released field is guessed.

## Outputs to bring to a meeting

The demo produces `report.md`, `report.json`, `event_scores.csv`, three labeled synthetic figures, the effective configuration, simulated observations, saved HDF5 contracts, and numerical factor arrays. Bring one figure and one quantitative check, not a folder listing. Small reference reports from the build are included under `examples/validated_demo/`; bulk contracts are regenerated outside the repository.

## Storage and replacement

Code belongs on the laptop, normally `~/MEGA/GRAND_projects/gwtc_forecast`. Real data, caches, fits and generated results belong under `/media/oamacias/LaCie/GW_Project_Data`. `config/project.toml` preserves that default and its mount/separate-device guards. Conda packages remain local. Explicit small `/tmp` synthetic output is allowed without an external disk.

Extract this complete replacement into a sibling directory first. Back up your existing code/Git history and compare any local changes and custom configuration before renaming directories. Do not overwrite your only working copy, copy raw data into this ZIP, or delete the external data tree. Existing v1 event/selection/posterior contracts remain supported. Old released hyperposteriors remain useful reference products, but are not the new matched training posteriors.

## Scientific scope

The real target is a retrospective, through-O3-to-O4a/O4b comparison, conditional on the selected event count in each period. It is not a merger-rate forecast, and it is not an as-of-2021 forecast when using corrected later PE products. A prospective extension needs an explicit exposure record and freeze before access to its held-out information. GWTC-6 is a catalog label; O6 is an observing run.

Read `docs/PAPER_STRATEGY.md` for what could be novel, what is already in the literature, and when to stop or narrow. Strong claims and citation counts are not promised. `VALIDATION.md` records the evidence actually executed for this release. `KNOWN_GAPS.md` identifies the work that remains.
