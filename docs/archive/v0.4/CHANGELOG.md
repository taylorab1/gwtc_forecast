# Changelog

## 0.4.0 — 2026-08-28 student-baseline hardening

- Added normalized event-posterior row weights with backward-compatible v1
  event-contract reading.
- Corrected the event integral for unequal-weight PE products.
- Made score-difference Monte Carlo gates well-defined at a scientifically
  valid null \(\Delta S\simeq0\).
- Added mixed absolute/relative joint-versus-prequential comparison tolerance.
- Added bounded-memory selection-contract iteration and mathematically
  equivalent streamed efficiency/ESS accumulation.
- Added strict layout, manifest filename, download destination, and extraction
  target containment checks.
- Added archive member-count, expanded-size, expansion-ratio, duplicate-name,
  member-type, and free-space preflight.
- Kept Conda environments and package caches laptop-local; external storage is
  required only for scientific data and generated scientific products.
- Added the frozen bidirectional detected-space power decision and CLI.
- Corrected `mock_calibration_passed` to `false`; toy validation is not the
  public-release O4-sized qualification.
- Added `STUDENT_RESEARCH_PLAN.md` and aligned the compact roadmap and agent
  instructions with the vertical-slice-then-power-gate sequence.
- Expanded the offline regression suite from 22 to 43 tests.
