# Validation strategy

## Offline repository validation

```bash
make test
make lint
make audit
make science-smoke
```

The artifact build executed 22 offline tests after the final scientific-layer
changes. The tests cover configuration, external-storage guards, archive
safety, Zenodo metadata parsing, generic and compound HDF5 discovery, official
PE-summary indexing, documented O4 injection-schema discovery, immutable event,
selection, and hyperposterior contracts, normalized toy models, predictive and
prequential algebra, ESS/influence diagnostics, and the generic vertical-slice
model comparison.

## Live data validation

```bash
make plan
make download
make verify
make extract
make first-look
make readiness
```

## Statistical identities tested

- normalized toy mass PDFs integrate to one;
- selection importance sampling returns one when population and draw
  distributions are identical and detection is complete;
- event reweighting returns the expected result for a uniform toy problem;
- predictive scores are invariant to hyperposterior permutation;
- cumulative prequential score equals the joint score;
- processed event, selection, and hyperposterior contracts round-trip;
- the deterministic mock favors the generating peak model over a smooth model;
- the vertical-slice comparison returns the expected score sign and numerical
  diagnostics in a controlled analytic-density problem.

## Not validated in this artifact build environment

The multi-gigabyte Zenodo transfer and the actual public HDF5 payloads were not
executed here. `make plan` verifies live release metadata before transfer, and
`make first-look` audits the downloaded schemas on the user's machine.

Ruff was not installed in the artifact container, so `ruff check` was not run
here. It is part of the dedicated Conda environment and is executed by
`scripts/setup_conda.sh` and `make codex-preflight`.
