# Known gaps and non-claims

The replacement is a runnable development baseline, not a finished public-catalog analysis.

**Real released inputs:** A complete through-O3 PE/selection manifest, exact event-level PE prior adapters, final analysis labels and weighted-sample conventions, and independently verified O3/O4 injection normalization are not supplied as validated. Five inherited pilot events remain for integration. Generic HDF5/coordinate helpers do not solve release-specific statistical semantics.

**Scientific prescription:** The matched density is implemented and normalization-tested, but its full candidate priors, support/tapers, shared continuum flexibility and population factorization still need training-only review. No continuous full-BBH training fit has been performed here. The optional Bilby adapter has only interface/likelihood tests in this build, not an actual installed-Bilby/Dynesty run.

**Realistic observations:** The executable one-dimensional noisy-mass detector is synthetic. A public-data-relevant measurement-aware mock strategy remains a research task. Its correctly specified finite-grid SBC does not demonstrate robustness to misspecification, realistic degeneracies or public-release systematics.

**Numerical precision:** The example compares one Monte Carlo realization with quadrature. Its discrepancy is not an error bar. There are paired-summary and guarded iid-resampling helpers, not a validated total public-data PE+injection+training-posterior error estimator. Importance-weight support and independent training-inference stability need qualification at actual scale.

**Runtime/environment:** Tests and the synthetic CLI were run in the build environment; the user's Linux/Conda/external-disk environment was not accessed or changed. The optional inherited science environment was not solved here. Ruff was unavailable and could not be installed in this network-restricted environment; no lint pass is claimed. See `VALIDATION.md` for exact executed evidence.

**Authorization:** Input path existence, metadata booleans, passing tests or a numeric power pass do not constitute scientific authorization. No real population conclusion, rate measurement, prospective forecast, formation-channel identification, future observing-run schedule or citation forecast is delivered.
