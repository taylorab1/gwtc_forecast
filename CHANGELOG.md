# Changelog

## 0.5.0 (4 September 2026)

Replaced the primary confounded released-model screening pair with a matched bending-continuum/extra-high-component design. Archived the original charter and long plan; preserved data/storage safety, core weighted statistical objects and regression tests.

Added normalized matched one-dimensional and full candidate BBH populations; true finite-prior training and frozen prediction; noisy-observation generation with consistent toy detection/PE; saved/reloaded integration; independent quadrature comparisons; conditional power and separately repeated-training randomized SBC.

Added prior-coordinate Jacobians, explicit HDF5 standardization, optional training-only Bilby likelihood/fitting entry points, frozen catalog checks and score output, support diagnostics, guarded iid uncertainty helpers and a confidence-interval-aware power consumer. New candidate scientific priors remain unfrozen. No real-catalog result is asserted.

Added a minimal local setup route, updated commands, student ownership/meeting instructions, milestone/report templates, literature positioning, migration notes and executed build evidence. Default downloads no longer include unrelated released-model posteriors; a legacy manifest preserves them. Real through-O3 release qualification remains explicit work.

The v0.4 regression implementation of the old power assessor remains for compatibility, but the CLI now uses the uncertainty-aware assessor. Old published build claims are archived rather than attributed to this code.
