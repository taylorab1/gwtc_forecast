# Executed validation for v0.5.0

## Bottom line

**75 tests passed. The complete default synthetic experiment and its separate repeated-training calibration ran. No real GW population result or continuous full-BBH training fit is claimed.**

The original supplied snapshot passed its 43 tests before modification. The final 75-test suite retains those regressions and adds matched-model normalization, exact zero-feature equality, joint spin-mixture normalization, PE/detection consistency, posterior-versus-truth separation, finite-prior training, saved/reloaded integration, chronological separation, predictive-support diagnostics, Jacobian checks, qualified iid bootstrap semantics, paired-error covariance, confidence-interval-aware power decisions and an optional-Bilby interface check using a stub (not installed Bilby).

## Actual execution

```
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q -p no:cacheprovider
# 75 passed (see examples/build_evidence/pytest.txt)

python -m gwtc_forecast feature-demo --output /mnt/data/refurbish_runs/release_demo_v05_attempt2
python -m gwtc_forecast feature-calibration --output /mnt/data/refurbish_runs/release_calibration_v05 --replicates 20
python -m gwtc_forecast study-audit --spec config/real_study.example.json
python -m gwtc_forecast audit-repo
python -m pip wheel . --no-deps --no-build-isolation -w /mnt/data/refurbish_build_wheel
```

The demo/calibration commands used OPENBLAS_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1 and PYTHONPATH=src. Paths above describe this build environment, not the scientist's laptop. The start-here notebook was executed with nbclient without error. The wheel was built successfully without fetching dependencies. Repository data guard passed; bulk simulated contracts and factor arrays remain outside the distributed code tree. The final archive is additionally checked by extraction and the test suite; that check is saved alongside the downloadable ZIP rather than changing the archive after testing it.

## Synthetic reference result

| Quantity | Result |
|---|---:|
| Training events | 40 |
| Held-out events | 24 in O4a + 24 in O4b |
| Reference feature-minus-continuum log score | 2.688071072694 |
| PE/injection score difference | 2.604435719894 |
| MC-minus-reference discrepancy | -0.083635352800 |
| Maximum joint/sequential discrepancy | 7.11e-15 |
| Maximum quadrature-doubling score change | 1.5e-12 |

The positive sign is not astronomical evidence: the synthetic generating model contains an excess by construction. The one-realization MC discrepancy is not an uncertainty estimate or a total precision qualification. Grid-node concentration is not sampling convergence.

The 20 conditional-power trials per direction had wrong-sign fractions 0.35 (continuum generation) and 0.30 (high-component generation). These tiny samples illustrate ambiguity; they do not qualify the real design or precisely estimate its power. A separate 20-per-direction repeated experiment re-simulated and refitted training and recorded randomized finite-prior SBC ranks. No rank-uniformity certification is claimed from this small sample.

Measured phases for the completed demo were approximately 0.62 s for generation/contract reload, 2.24 s for the continuum paths, 24.60 s for the feature paths and 0.30 s for conditional power; plotting overhead is additional. One earlier attempt timed out before completion and was not used as evidence. Runtime is environment-dependent and does not forecast a real catalog or Bilby fit.

## Environment and limits

Python 3.13.5; NumPy 2.3.5; SciPy 1.17.0; h5py 3.15.1; pandas 2.2.3 in the build environment. Full details are in examples/build_evidence/versions.json. The source is declared Python >=3.11 but the proposed Python 3.11 Conda environment was not created on the user's system in this build.

Bilby, GWPopulation and PESummary were not installed here. The optional training adapter's interface and likelihood linkage were tested with a stub only; an actual sampler invocation is a future qualification step. Ruff was unavailable, and network restrictions prevented installing it; no lint pass is claimed. Public-data priors, selection normalization, waveform choices and support remain unqualified. The real-study template correctly reports BLOCKED and defaults to no retrospective scoring authorization.

Scientific source code manifest: examples/build_evidence/source_manifest.sha256. Its digest is `000b587184ed084d2f5e40f4cbe50470d67b97553086a49a8a966560bd6c3df5`. This manifest describes the distributed code snapshot; tests ran after the final operational guard changes. The demo's statistical modules and scientific configuration were unchanged by those guard/documentation edits. No other project, cloud upload, laptop repository or external disk was modified.

## Documents and archive

The eight-page milestone PDF was rendered and visually checked. Its dates are proposals; later meetings are review/decision targets, not promised paper deadlines. Student learning criteria are separated from scientific investment gates. No fonts, raw public data, credentials or large simulation products are included.
