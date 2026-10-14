# Known gaps and deliberate stops

This repository is a strong baseline, not a completed astrophysical analysis.
The following gaps are intentional and must not be hidden.

## 1. PE-prior reconstruction is not yet release-specific

The lightweight summary-table index now enumerates every candidate label and
checks the event-file mapping, while the PESummary reader can inspect posterior
columns. The code still does not guess the correct mixed/default label or
reconstruct every event's exact prior and coordinate Jacobian. Production
scoring remains disabled until this is implemented and tested for all five
events.

## 2. O4 run-specific injection normalization is not yet validated

The repository now knows the documented `/events` table, source parameters,
log-draw components, search FAR fields, mixture-weight column, and official O4a
and O4b time windows. The core `SelectionCampaign` object implements the
importance-sampling algebra once normalized `log_base_weight` is supplied. The
remaining hard problem is deriving the separate O4a/O4b generated-count and
wall-time mixture normalization and validating it against independent code.

## 3. Released GWTC-3 model adapters are not yet implemented

The downloader and discovery tools expose the extracted products. The toy
smooth/peak/break models validate statistical machinery only. They are not a
replacement for the released multidimensional GWTC-3 models.

## 4. No real-data predictive score is produced by the baseline

That is a feature. Producing a number before the three mappings above are
validated would create a convincing but scientifically unreliable result.

## 5. The pilot is not the final event sample

Five events test the software chain and numerical information content. Any
catalog-level astrophysical conclusion requires the frozen official O4
population event list and all corresponding PE files.

## 6. Count/rate prediction is postponed

The initial score conditions on the observed count and focuses on population
shape. Merger-rate and observing-time uncertainties are a separate extension.

## 7. PE row-weight semantics are not yet frozen for public products

The processed event v2 contract can represent unequal posterior-row weights,
and equal-weight v1 files remain readable. The release adapter must still
document whether each selected PE label is equal weight and identify the exact
source weight field when it is not. The baseline never infers this from column
names alone.

## 8. The detected-space power gate is implemented but not executed

`config/detected_power_gate.toml` and `gwtc-forecast power-gate` provide a frozen
bidirectional decision rule. They do not generate public-release mock catalogs.
The released-model and injection adapters must pass first, and at least 2,000
qualified mocks per generating direction are required before a final pass or
no-go decision. Accordingly, `mock_calibration_passed` remains `false`.
