# Artifact build report

Build date: 2026-08-28

## Repository baseline

- Package version: `0.4.0`
- Target runtime: Python 3.11 in the dedicated `gwtc_forecast` Conda environment
- Expected repository: `~/MEGA/GRAND_projects/gwtc_forecast`
- External scientific-data/results root:
  `/media/oamacias/LaCie/GW_Project_Data`
- Real-data predictive scoring is disabled by default.
- Public-release detected-power calibration is not marked complete.

## Verified in the artifact environment

- 43 offline tests passed.
- Source and tests compiled successfully.
- 37 importable package modules loaded successfully.
- 14 shell scripts passed syntax validation.
- 11 TOML files parsed successfully.
- Four notebooks contain no saved outputs or execution counts.
- The repository data guard passed.
- A wheel built and imported from a clean target directory.
- A direct toy predictive-statistics run passed.
- The detected-power CLI produced the correct preliminary/incomplete status.

See `BASELINE_ENHANCEMENT_REPORT.md` for the complete change and verification
record.

## Not performed

- Ruff was unavailable in this artifact container.
- No live public-data download was run.
- No public PE, injection, or released-model mapping was declared validated.
- No O4-sized power calculation or real-data score was produced.
