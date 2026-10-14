# GW Forecast Project

## Student research and implementation plan for catalog-to-catalog validation of binary-black-hole population models

**Project repository:** `gwtc_forecast`  
**Prepared for:** the SFSU gravitational-wave research team  
**Baseline reviewed:** repository package version `0.3.0`, archive dated 2026-08-21  
**Plan date:** 2026-08-27  
**Project decision:** **GO WITH A QUALIFICATION GATE**

---

## Executive summary

The purpose of this project is to test whether population structures inferred from an earlier gravitational-wave catalog actually predicted later detections.

The central scientific question is:

> **Which frozen GWTC-3 binary-black-hole population model assigned the larger selection-corrected predictive probability to the later O4 detections?**

The first comparison uses two population analyses released with GWTC-3:

1. `PowerLawPeak`, which contains a power-law continuum and a localized excess in the primary-mass distribution;
2. `PowerlawDipBreak`, which permits a dip and a change of slope or break.

The current repository is a strong starting point rather than a finished astrophysical analysis. It already implements the statistical algebra, immutable data contracts, toy population models, mock-catalog tests, numerical diagnostics, safe data downloads, and strict provenance controls. The remaining scientific work is to connect the public data products to that statistical core without guessing:

- identify the correct parameter-estimation result and reconstruct the exact single-event prior for each O4 event;
- reconstruct and independently verify the O4a and O4b selection-function normalization;
- map the released GWTC-3 hyperposterior samples and executable population densities;
- demonstrate through simulations that the two models are distinguishable with an O4-sized catalog;
- then apply the qualified pipeline to the official O4a+O4b population sample.

The five-event pilot is **not** the final scientific sample. It is a real-data integration test: a small collection that exercises the entire chain from public PE samples to a comparative predictive score. No population-level claim should be made from those five events.

The project is worth doing because prediction is a stricter scientific standard than retrospective fit. Many flexible models can describe the catalog used to construct them. A model earns stronger credibility if it gives high probability to observations that arrived later and were not used to tune it.

There is, however, an important limitation on the novelty claim. The official GWTC-4 population paper already performed a one-model held-out posterior-predictive check: it inferred a default mass model from GWTC-3 and compared the resulting detected-population predictions with O4a. Therefore, this project must not claim to be the first use of O4 as held-out data. Its defensible contribution is the combination of:

- **comparative proper scoring** of multiple frozen models;
- **full currently public O4a+O4b coverage**;
- **calibrated model-discrimination power**;
- **chronological, runwise, and eventwise predictive-regret decomposition**;
- **separate tests of relative preference and absolute model adequacy**;
- **catalog, PE, and selection Monte Carlo uncertainty control**;
- and, ideally, a **sealed prospective O4c forecast** before the next catalog release.

The project proceeds through hard gates. Passing a software test does not authorize a scientific result. Passing the five-event integration test does not authorize a full-catalog claim. Passing the simulation power gate authorizes the full O4 analysis, but not a particular conclusion. The final interpretation must depend on the data and on prespecified numerical criteria.

---

# 1. How to use this document

This document is both a research plan and an implementation specification. Students should use it in four ways:

1. **As a scientific map.** Each code task is tied to a scientific quantity and an explanation of why it is needed.
2. **As a project contract.** The primary models, data split, diagnostics, and stop rules must not be changed after looking at the real-data score unless a documented technical error requires correction.
3. **As an issue tracker.** Each work package can become one or more GitHub issues with explicit inputs, outputs, tests, and acceptance criteria.
4. **As a reading guide.** The references at the end are ordered so that students can learn the statistical framework while implementing it.

Students should not try to complete the entire document at once. The work is intentionally staged. A later stage begins only after the artifacts and gates of the previous stage have been reviewed and signed off.

---

# 2. The scientific idea

## 2.1 Why test prediction rather than fit another population model?

Suppose a model is built after inspecting a catalog. If the model is flexible enough, it may describe bumps, gaps, or correlations in that same catalog even when some of those structures are statistical fluctuations. This is the population-analysis version of overfitting.

A chronological forecast creates a more severe test:

\[
\text{infer from GWTC-3}
\quad\longrightarrow\quad
\text{freeze the model}
\quad\longrightarrow\quad
\text{score O4}.
\]

The later detections were not used to determine the earlier hyperposterior. A model that predicts them well has demonstrated something beyond in-sample flexibility.

An intuitive analogy is weather forecasting. A weather model should not be judged only by how well it reconstructs yesterday after yesterday's observations are known. It should be judged by the probability it assigned yesterday before the weather occurred. This project applies that logic to binary-black-hole populations.

## 2.2 Why the primary-mass distribution?

The first paper should emphasize masses, especially the structures around approximately \(10\,M_\odot\) and \(35\,M_\odot\), because:

- component masses are measured more informatively than many spin-orientation quantities;
- the public population products already contain the relevant released models;
- selection effects are significant but tractable with the released injection campaign;
- the physical interpretations are important and actively debated;
- a mass-first analysis is achievable for master's students without strain-level parameter estimation.

The current literature has evolved as the catalog has grown. GWTC-5 reports a feature near \(10\,M_\odot\) and a change of slope near \(35\,M_\odot\), while a catalog-variance study finds that the apparent \(35\,M_\odot\) peak is substantially weakened after resampling the finite catalog. This makes the predictive question timely: did a localized peak or a break-like model actually generalize better?

## 2.3 What result would matter?

Several scientifically useful outcomes are possible.

### Outcome A: one model predicts substantially better

For example:

> The frozen GWTC-3 break model assigned substantially greater predictive probability to O4a+O4b than the frozen peak model.

This would establish a historical forecast comparison. It would not, by itself, prove that a specific physical mechanism produced the mass feature because the released models differ in more than one assumption.

### Outcome B: one model wins relatively, but both fail adequacy checks

This may be more informative:

> The break model was less wrong than the peak model, but neither frozen GWTC-3 model adequately predicted the later detected population.

That result would expose model misspecification and motivate a more controlled next generation of models.

### Outcome C: a simpler model predicts as well as the elaborate models

This would warn that some in-sample structure was not predictively useful.

### Outcome D: the models cannot be distinguished at O4 sample size

This is a valid project-level no-go. It would mean that the proposed comparison is information-limited. The correct response would be to stop the astrophysical comparison, not to add models until something appears significant.

## 2.4 What this project must not claim

The initial released-model comparison does **not** isolate one physical ingredient. `PowerLawPeak` and `PowerlawDipBreak` can differ in continuum shape, support, tapering, redshift behavior, mass-ratio assumptions, spin assumptions, priors, and posterior uncertainty. Therefore:

- valid: “Released model A predicted O4 better than released model B.”
- not automatically valid: “O4 proves the \(35\,M_\odot\) feature is physically a break rather than a peak.”

A clean physical peak-versus-break statement requires a later **harmonized-model stage** in which nuisance assumptions are held fixed and only the targeted mass structure changes.

---

# 3. What is already present in the repository

The baseline repository should be presented to students as a scientific scaffold, not a blank coding exercise.

## 3.1 Implemented infrastructure

The repository already includes:

- resumable, checksum-verified downloads from pinned Zenodo records;
- safe archive extraction on the external disk;
- a mount guard that prevents large files from falling back onto the laptop;
- release inventories and lightweight HDF5 inspectors;
- readers for official PE summary tables;
- immutable processed HDF5 contracts for event posteriors, selection campaigns, and hyperposteriors;
- event-level hierarchical reweighting;
- run-conditioned selection correction;
- catalog predictive scores;
- chronological or prequential scoring;
- effective-sample-size and event-influence diagnostics;
- normalized toy smooth, peak, and break models;
- deterministic selection-biased mock-catalog validation;
- a generic five-event vertical-slice evaluator;
- machine-readable readiness reporting.

Students should reuse this machinery. Rewriting it would spend time without increasing scientific information.

## 3.2 Verified baseline tests

For the reviewed archive, the following command passed:

```bash
PYTHONPATH=src python -m pytest -q
```

with:

```text
22 passed
```

Python compilation also passed. This establishes that the implemented unit tests are green. It does **not** establish that the public releases have been mapped correctly or that the real-data score is scientifically valid.

## 3.3 What remains unresolved

Real-data scoring is deliberately disabled because three mappings remain scientifically incomplete:

1. **PE mapping:** the correct released result label and exact PE prior in population coordinates for every pilot event;
2. **selection mapping:** the O4a and O4b generated-count and wall-time mixture normalization, with independent reference checks;
3. **released-model mapping:** the exact hyperposterior files, weights, parameter names, supports, transformations, and executable population densities.

The repository's `config/science.toml` therefore keeps:

```toml
real_data_scoring_enabled = false
```

No student should change this flag merely because code runs. It can change only after every production gate has machine-verifiable evidence.

## 3.4 Existing numerical gates

The baseline already freezes the following minimum requirements:

```text
minimum event ESS                         100
minimum selection ESS                    1000
maximum joint/prequential discrepancy    1e-10
maximum MC sigma on Delta S               0.5 nat
maximum fractional MC error               0.2
```

These should be treated as lower-level numerical gates. Later sections add simulation-power and scientific-interpretability gates.

## 3.5 Important provenance issue before distribution

The reviewed ZIP contains no `.git/` directory. Thus its branch and commit cannot be reconstructed from the archive alone. Before students begin, the advisor should distribute the actual Git repository or deliberately create a new repository from the reviewed baseline and record:

- the archive SHA-256;
- the initial commit;
- a signed or annotated tag such as `student-baseline-v0.3.0`;
- the authoritative pilot manifest;
- the authoritative science configuration.

The reviewed archive SHA-256 is:

```text
f58768aa81b7b6f9005b3d3bd1b9d486580d711b626b94068abafbb0e1d60526
```

This is essential. Reproducibility starts by knowing exactly what code each student received.

---

# 4. Frozen scientific contract

The purpose of a frozen contract is to prevent the analysis from changing in response to an appealing or disappointing real-data result.

## 4.1 Training and test data

### Training information

Use the released GWTC-3 population hyperposteriors. Do not refit the initial models using O4.

### Held-out data

Use the official O4 population-analysis events, with O4a and O4b kept as separate observing runs because their selection functions and observing conditions differ.

### Pilot data

Use the five events in the authoritative `config/pilot_manifest.toml` only as an integration test. In the reviewed baseline these are:

```text
O4a: GW230627_015337
O4a: GW230726_002940
O4a: GW230814_230901
O4b: GW240414_054515
O4b: GW240630_101703
```

The pilot events are not selected to be statistically representative. Their score must never be presented as the population result.

## 4.2 Initial model set

The first comparison is exactly:

```text
PowerLawPeak
PowerlawDipBreak
```

No third model is added before the released-model screen and simulation power gate are complete.

A smooth baseline can be introduced only in the later harmonized-model stage, where its role is to test whether either claimed feature improves out-of-sample prediction relative to a simpler continuum.

## 4.3 Primary estimand

For model \(M\), training data \(D_{\rm train}\), and later run data \(D_r\), the primary quantity is the shape-only posterior predictive probability conditioned on the observed count \(N_r\):

\[
p(D_r\mid D_{\rm train},M,N_r)
=
\int
p(D_r\mid\Lambda,M,N_r)
\,p(\Lambda\mid D_{\rm train},M)
\,d\Lambda.
\]

The primary comparison is the log-score difference

\[
\Delta S_r
=
\log p(D_r\mid D_{\rm train},M_1,N_r)
-
\log p(D_r\mid D_{\rm train},M_0,N_r).
\]

Interpretation:

- \(\Delta S_r>0\): model \(M_1\) assigned greater predictive probability to the later run;
- \(\Delta S_r<0\): model \(M_0\) did better;
- \(\Delta S_r\approx0\): the catalog does not meaningfully discriminate the models at the achieved numerical precision.

## 4.4 Why condition on the event count initially?

The number of detections depends on the merger rate, detector observing time, duty cycle, and detection efficiency. Those are scientifically important, but they can obscure the narrower first question: did the model predict **what kinds of binaries** were detected?

Conditioning on \(N_r\) separates shape from rate. A later extension can ask whether the model also predicted how many events occurred, but the first paper should not let rate uncertainty dominate the mass-structure comparison.

## 4.5 Relative comparison and absolute adequacy are different

A model can win a race between two poor models. Therefore the project must report both:

1. **relative prediction:** which frozen model has the higher held-out score?
2. **model adequacy:** could catalogs generated by that model plausibly resemble the observed O4 catalog?

The relative score is the primary ranking statistic. Posterior-predictive or data-level checks are required to determine whether either model is adequate.

## 4.6 Scope exclusions for the first paper

The first paper does not include:

- strain-level parameter estimation;
- new waveform inference;
- a broad spin-population campaign;
- merger-rate inference as a primary result;
- machine-learning models;
- GPU development;
- arbitrary new population families;
- post-hoc tuning after inspecting O4 scores.

These exclusions protect the scientific question from turning into an open-ended software project.

---

# 5. Statistical framework, explained intuitively

## 5.1 The single-event posterior is not a population draw

For one event \(i\), the PE analysis provides posterior samples

\[
\theta_i^k\sim p(\theta_i\mid d_i,\pi_i),
\]

where \(d_i\) is the detector data and \(\pi_i(\theta)\) is the PE prior.

Those samples contain both information from the data and assumptions from the PE prior. To ask how compatible the event is with a population model \(p(\theta\mid\Lambda,M)\), we must remove the PE-prior weighting and replace it with the population weighting.

The importance-sampling estimator is

\[
\widehat{\mathcal L}_i(\Lambda,M)
\propto
\frac{1}{K_i}
\sum_{k=1}^{K_i}
\frac{p(\theta_i^k\mid\Lambda,M)}{\pi_i(\theta_i^k)}.
\]

### Intuition

Imagine that the PE analysis deliberately sampled a map more heavily in some regions than others. Counting the samples directly would confuse that sampling strategy with the physical population. Dividing by the PE prior removes the sampling preference; multiplying by the population density asks how strongly the model values each possible source configuration.

### Consequence

A guessed or incomplete PE prior can create a convincing but false population preference. That is why the PE adapter is a scientific task, not simple file parsing.

## 5.2 Why selection effects enter

The detected population is not the astrophysical population. Massive, nearby, favorably oriented binaries are easier to detect. A model that places more probability in easy-to-detect regions would generate more detections even if its intrinsic rate were the same.

For run \(r\), define the detection efficiency

\[
\xi_r(\Lambda,M)
=
\int
P_{\rm det,r}(\theta)
\,p(\theta\mid\Lambda,M)
\,d\theta.
\]

The released injection campaign estimates this integral by importance sampling.

### Intuition

The observed catalog is like a wildlife survey with a camera that sees large animals more easily than small animals. A raw count of photographed animals is not the true forest population. The selection function describes the camera.

## 5.3 Run-conditioned catalog likelihood

Conditioning on the number of detections in each run gives, schematically,

\[
\widehat{\mathcal L}_{\rm cat}(\Lambda,M)
\propto
\prod_i \widehat{\mathcal L}_i(\Lambda,M)
\prod_r \xi_r(\Lambda,M)^{-N_r}.
\]

In log form,

\[
\log\widehat{\mathcal L}_{\rm cat}
=
\sum_i \log\widehat{\mathcal L}_i
-
\sum_r N_r\log\widehat{\xi}_r.
\]

The event terms reward a model for explaining the observed systems. The selection terms prevent the model from receiving unfair credit merely because it populates regions that are easy to detect.

## 5.4 Averaging over the earlier hyperposterior

GWTC-3 did not determine one exact population hyperparameter vector. It produced a posterior distribution

\[
p(\Lambda\mid D_{\rm GWTC3},M).
\]

The predictive score averages the later-catalog likelihood over this uncertainty:

\[
p(D_{\rm O4}\mid D_{\rm GWTC3},M)
=
\int
p(D_{\rm O4}\mid\Lambda,M)
\,p(\Lambda\mid D_{\rm GWTC3},M)
\,d\Lambda.
\]

### Intuition

A forecast should include everything the earlier data still allowed, not only the best-fit curve. A model with a broad and uncertain prediction spreads probability over many possible outcomes. The log predictive score rewards predictions that are both calibrated and sufficiently sharp.

## 5.5 Why use the logarithmic score?

The logarithmic score is

\[
S_M=\log p(D_{\rm test}\mid D_{\rm train},M).
\]

It is a proper scoring rule: in expectation, a forecaster maximizes the score by reporting its true predictive distribution rather than strategically distorting it.

Log scores also add across conditionally sequential observations, which makes chronological decomposition natural.

A difference of \(5\) nats corresponds to a predictive-density ratio of approximately

\[
e^5\simeq 148.
\]

This is not automatically a discovery threshold or a Bayes factor between newly fitted models. It is a practical scale for predictive separation that must be calibrated with simulations.

## 5.6 Joint versus prequential scoring

The same predictive probability can be written as a sequence:

\[
p(d_1,\ldots,d_N\mid D_{\rm train},M)
=
\prod_{i=1}^{N}
p(d_i\mid D_{\rm train},d_{<i},M).
\]

Taking logs gives eventwise increments:

\[
S_M=\sum_i s_{i,M}.
\]

The comparative cumulative score is

\[
\Delta S(n)
=
\sum_{i=1}^{n}
\left(s_{i,M_1}-s_{i,M_0}\right).
\]

### Intuition

The joint score answers, “How well did the model predict the whole later catalog?” The prequential view answers, “As detections arrived, when and why did one model begin to outperform the other?”

The implementation must update the shared hyperposterior after each event. Simply marginalizing each event independently and adding the results is generally not equivalent.

## 5.7 Important event-evidence caveat

The PE posterior reweighting estimator is typically known only up to an event-evidence constant that does not depend on the population model. These constants cancel when comparing two models on the **same events**.

Therefore the safe eventwise quantity is the comparative increment

\[
\Delta s_i=s_{i,M_1}-s_{i,M_0}.
\]

Students must not advertise a model-specific value such as

\[
-\log p(d_i\mid M)
\]

as an absolute “surprise” unless the event-evidence normalization has been restored and verified. Use the language **comparative predictive regret** or **event contribution to \(\Delta S\)**.

## 5.8 Effective sample size

Importance sampling fails when a few samples carry almost all the weight. A standard diagnostic is

\[
\mathrm{ESS}
=
\frac{\left(\sum_k w_k\right)^2}{\sum_k w_k^2}.
\]

A large nominal sample count does not help if the ESS is tiny.

The project monitors ESS for:

- every event under every retained hyperposterior draw;
- every run's selection estimate;
- the evolving hyperposterior after each chronological event.

ESS is necessary but not sufficient. Students must also test convergence under thinning, chunking, row shuffling, hyperposterior resampling, and injection resampling.

---

# 6. Data and software architecture

The intended data flow is:

```text
official immutable public releases
            |
            v
checksummed raw files on LaCie
            |
            v
lightweight inventory and schema audit
            |
            v
reviewed scientific mappings
  (PE prior, selection, released model)
            |
            v
immutable processed contracts
  EventPosterior / SelectionCampaign / HyperPosterior
            |
            v
existing statistical core
            |
            v
qualification diagnostics and decision artifacts
            |
            v
only after gates pass: scientific result
```

The separation is deliberate. File-reading code should not contain scientific likelihood algebra. Scientific model code should not silently choose a PE label. Workflows should consume validated contracts rather than reopen raw releases and make choices at run time.

## 6.1 Repository and external-disk separation

Code remains under:

```text
~/MEGA/GRAND_projects/gwtc_forecast
```

All raw data, processed products, caches, logs, figures, and results remain under:

```text
/media/oamacias/LaCie/GW_Project_Data
```

No file larger than 20 MiB may be committed. The mount guard must never be bypassed.

## 6.2 Source-of-truth files

Before changing scientific code, students must read:

```text
SCIENCE_CHARTER.md
KNOWN_GAPS.md
ROADMAP.md
AGENTS.md
CODEX_FIRST_CAMPAIGN.md
docs/OFFICIAL_RELEASE_SCHEMA_NOTES.md
docs/RELEASE_AUDIT_CHECKLIST.md
docs/STATISTICAL_CONVENTIONS.md
docs/DATA_CONTRACTS.md
config/science.toml
config/pilot_manifest.toml
config/pe_mapping.toml
config/injection_mapping.toml
config/released_model_mapping.toml
```

If two documents disagree, the disagreement is reported in an issue. Students must not choose silently.

## 6.3 Reusable core

Do not rewrite:

```text
src/gwtc_forecast/statistics/
src/gwtc_forecast/workflows/vertical_slice.py
src/gwtc_forecast/io/contracts.py
```

Any proposed change to these modules requires:

- a demonstrated scientific or numerical defect;
- a minimal failing test;
- advisor approval;
- regression tests showing that existing behavior is preserved where appropriate.

---

# 7. Team workflow and reproducibility rules

## 7.1 Baseline preparation by the advisor

Before the repository is handed over:

1. confirm the external-disk path and storage policy;
2. confirm the authoritative five-event manifest;
3. create or verify the real Git history;
4. tag the exact baseline;
5. add this document to the repository root;
6. protect the default branch from direct pushes;
7. create initial issues corresponding to Work Packages 0–4 below.

## 7.2 Branch and pull-request policy

Recommended branches:

```text
student-a/pe-adapter-<issue>
student-b/selection-adapter-<issue>
integration/released-model-vertical-slice
qualification/detected-power-gate
analysis/full-o4-score
forecast/o4c-registration
```

Every pull request must include:

- the scientific question addressed;
- files changed;
- new tests;
- commands run;
- artifact paths;
- numerical results with uncertainty;
- known limitations;
- whether the change modifies a scientific contract.

## 7.3 Cross-audit requirement

Every scientifically consequential mapping is implemented by one student and independently audited by the other.

Examples:

- Student A derives a PE prior; Student B checks the release documentation, Jacobian, support, and normalization.
- Student B derives the selection weights; Student A reproduces fixed-point \(\xi_r\) values with independent code.

“Both students ran the same function” is not an independent audit.

## 7.4 Deterministic computation

Every stochastic workflow must record:

- a master seed;
- a deterministic seed tree, preferably through `numpy.random.SeedSequence`;
- input checksums;
- configuration hash;
- Git commit and dirty-tree status;
- package versions;
- exact command;
- wall time, CPU usage, peak memory, and output size.

## 7.5 Notebooks versus library code

Notebooks are allowed for:

- inspecting a release;
- explaining a derivation;
- reproducing a figure from already generated artifacts;
- student tutorials.

Notebooks are not allowed to contain the only implementation of:

- a prior density;
- a coordinate transformation;
- a selection estimator;
- a population density;
- a score calculation;
- a machine decision.

Reusable and testable calculations belong in `src/`.

## 7.6 AI-assisted coding policy

AI tools may assist with code, but students remain responsible for scientific correctness. Any AI-generated code must be:

- identified in the pull request;
- tested against an independent expectation;
- explainable line by line by the student;
- supported by primary literature or release documentation for scientific formulas.

AI output is not a scientific source.

---
# 8. Work-package roadmap

Each work package below includes a scientific objective, intuitive justification, implementation tasks, required tests, artifacts, and a decision gate.

---

## Work Package 0: Onboarding, baseline verification, and literature map

### Objective

Ensure that both students understand the scientific question, can run the repository, and can distinguish an implemented function from a validated scientific result.

### Why this comes first

A population pipeline can produce plausible numbers even when a coordinate, prior, or normalization is wrong. Students therefore need a shared conceptual model before they specialize.

### Tasks

1. Clone the tagged baseline and record the commit.
2. Verify the LaCie mount:

   ```bash
   findmnt /media/oamacias/LaCie
   df -h /media/oamacias/LaCie
   ```

3. Create or activate the existing Conda environment:

   ```bash
   ./scripts/setup_conda.sh
   source scripts/activate_project.sh
   ```

4. Run the baseline suite:

   ```bash
   make status
   make test
   make lint
   make audit
   make science-smoke
   make mapping-status
   make readiness
   ```

5. Read the scientific and repository source-of-truth files listed in Section 6.2.
6. Each student writes a two-page note deriving:
   - the event reweighting estimator;
   - the selection correction;
   - the hyperposterior predictive integral;
   - the distinction between joint and prequential scoring.
7. Build a shared literature matrix with columns:

   ```text
   reference | data used | model | in-sample or held-out |
   statistic | selection treatment | main result | limitation |
   relevance to our project
   ```

8. Reproduce the existing toy-validation outputs and explain every diagnostic.

### Required understanding check

Each student should be able to answer orally:

- Why do we divide by the PE prior?
- Why is O4a not allowed to use the O4b selection factor by default?
- Why can a relative score be meaningful when absolute event evidences are omitted?
- Why can two models be rankable even if both are inadequate?
- Why does a green unit test not validate the public-release mapping?

### Artifacts

```text
results/onboarding/<student>/baseline_report.md
results/onboarding/shared/literature_matrix.csv
results/onboarding/shared/statistical_derivation.md
```

### Gate WP0

**Pass** when:

- baseline tests are reproduced;
- the Git commit and environment are recorded;
- both derivations are reviewed;
- the students can explain the statistical chain without relying on code.

**Stop or repair** if the distributed repository cannot be tied to an exact commit or if the baseline suite fails for unexplained reasons.

---

## Work Package 1: Data provenance and release inventory

### Objective

Prove that every required public input is exactly identified, checksummed, and stored in the intended location before scientific mappings begin.

### Why this matters

A result cannot be reproduced if “the O4 PE file” could refer to several stable releases or labels. Provenance errors are especially dangerous because they may leave the numerical answer looking reasonable.

### Tasks

1. Perform a dry-run plan before any large download:

   ```bash
   make status
   make bootstrap
   make plan
   ```

2. Review record IDs, filenames, live sizes, expected checksums, and total storage.
3. Download only the frozen pilot and core release products:

   ```bash
   make download
   make verify
   make extract
   ```

4. Run the lightweight audit:

   ```bash
   make inventory
   make pe-index
   make selection-schema
   make discover
   make first-look
   ```

5. Compare the resulting inventory with `config/pilot_manifest.toml`.
6. Record the exact stable-release version for each O4 PE source.
7. Confirm that raw archives remain immutable and that extraction is idempotent.
8. Confirm that no large file appears inside the Git tree.

### Implementation principle

Do not begin by loading every multi-gigabyte array. First inspect metadata, shapes, field names, attributes, and sample labels. Large-array access should follow a specific scientific question.

### Required tests

- checksum mismatch causes a hard failure;
- path-traversal archive entries are rejected;
- unplugging or unmounting the LaCie disk causes a hard failure;
- rerunning extraction does not create inconsistent duplicates;
- the inventory is identical under repeated runs with unchanged inputs;
- every pilot event maps to exactly one expected combined PE file.

### Artifacts

```text
manifests/pilot_download_plan.json
manifests/pilot_download_plan.csv
results/pilot/inventory/data_inventory.json
results/pilot/inventory/file_inventory.csv
results/pilot/inventory/pe_release_index.json
results/pilot/inventory/o4ab_selection_schema.json
results/pilot/inventory/hyperposterior_discovery.json
results/pilot/provenance_review.md
```

### Gate WP1

**Pass** when every required input has an unambiguous source, file, checksum, and role.

**Pause** with an explicit provenance label if a release has drifted, a checksum fails, or two candidate files cannot be distinguished from official documentation.

---

## Work Package 2A: O4 event PE adapter and exact prior reconstruction

**Primary owner:** Student A  
**Independent auditor:** Student B

### Objective

For each pilot event, convert one documented public PE result into an immutable `EventPosterior` contract containing source-frame population coordinates and the exact log PE prior in those same coordinates.

### Why this is scientifically difficult

The posterior samples are not enough. The likelihood contribution uses

\[
\frac{p(\theta\mid\Lambda,M)}{\pi_{\rm PE}(\theta)}.
\]

A wrong denominator reshapes every event's contribution. Coordinate changes can also introduce Jacobian factors. For example, a prior uniform in detector-frame component masses and luminosity distance is not automatically uniform in source-frame masses and redshift.

### Inputs

- official O4a and O4b PE release documentation;
- combined event HDF5 files;
- PESummary label inventories;
- cosmology convention used by the released samples;
- population-model coordinates required by the two GWTC-3 models.

### Ordered tasks

1. **Enumerate labels without choosing one.**

   For each event, write a table of:

   - `result_samples_key`;
   - waveform family;
   - sampler;
   - calibration or glitch-treatment metadata;
   - parameter columns;
   - sample count;
   - whether the label is identified as default, mixed, or preferred by the release.

2. **Freeze the label-selection rule before extraction.**

   The rule should be based on official documentation, not on which label gives higher ESS or a preferred score. Examples of acceptable rules include “the release-designated default population-analysis result” or a documented mixture of specified waveform labels.

3. **Map coordinates.**

   At minimum audit:

   ```text
   mass_1_source
   mass_2_source
   mass_ratio
   redshift
   spin magnitudes and orientations required by the released model
   luminosity distance or detector-frame masses when needed for prior reconstruction
   ```

4. **Write every transformation algebraically.**

   For each transformation \(x\mapsto y\), document

   \[
   \pi_y(y)=\pi_x(x(y))\left|\frac{dx}{dy}\right|.
   \]

   Do not rely on column names to imply a prior.

5. **Reconstruct the joint PE prior.**

   Include supports, normalization constants, conditional factors, cosmology, and Jacobians. If part of the prior is unavailable, stop rather than substitute a common “standard prior.”

6. **Validate the prior independently.**

   Recommended checks:

   - evaluate at frozen hand-calculated test points;
   - compare with samples drawn directly from the documented prior when feasible;
   - check support boundaries exactly;
   - integrate low-dimensional marginals numerically;
   - compare the reconstructed prior with any release-provided prior samples or code;
   - verify invariance when computing the same density in two coordinate systems with the Jacobian included.

7. **Write the processed contract.**

   Use `write_event_contract` and store:

   - event ID and run;
   - frozen label and selection rule;
   - posterior arrays;
   - `log_pe_prior`;
   - parameter names and units;
   - transformations and cosmology;
   - waveform/sampler metadata;
   - source record, filename, checksum;
   - software commit and configuration hash.

8. **Repeat for all five events.**

### Proposed module

```text
src/gwtc_forecast/io/gwtc_pe.py
```

Possible supporting modules, only when needed:

```text
src/gwtc_forecast/coordinates.py
src/gwtc_forecast/priors/gwtc_pe.py
```

Do not create a large general-purpose prior framework unless the five adapters require it.

### Required tests

1. Unknown or ambiguous label fails explicitly.
2. Missing prior metadata fails explicitly.
3. Samples outside prior support yield `-inf` and a diagnostic count.
4. Coordinate round trips agree to numerical tolerance.
5. Analytic Jacobian tests pass at frozen points.
6. Prior normalization or marginal checks pass where calculable.
7. Contract write/read round trip is exact.
8. Reordering posterior samples does not change the event likelihood.
9. Thinning by independent random subsets gives compatible likelihood estimates within Monte Carlo uncertainty.
10. A deliberately omitted Jacobian makes a test fail, demonstrating that the test is sensitive to the error.

### Artifacts per event

```text
processed/events/<event_id>.hdf5
results/qualification/pe/<event_id>/label_audit.csv
results/qualification/pe/<event_id>/prior_derivation.md
results/qualification/pe/<event_id>/fixed_points.json
results/qualification/pe/<event_id>/validation.json
```

### Gate WP2A

**Pass for one event** when:

- label selection is documented;
- the exact prior is derived in population coordinates;
- all support and Jacobian tests pass;
- the other student independently reproduces selected fixed-point values.

**Pass for the work package** only when all five events pass.

**Pause** if the official release does not provide enough information to reconstruct the prior. Do not guess.

---

## Work Package 2B: O4a/O4b selection-function adapter

**Primary owner:** Student B  
**Independent auditor:** Student A

### Objective

Construct one validated `SelectionCampaign` contract for O4a and one for O4b, preserving the released injection draw density, mixture weighting, observing-run mask, found criterion, and normalization.

### Why this is central

The selection factor is raised to the number of detections:

\[
\xi_r(\Lambda)^{-N_r}.
\]

A small bias in \(\xi_r\) can therefore become a large catalog-level bias. Monte Carlo error in selection estimation is already known to be a limiting factor in gravitational-wave population inference.

### Inputs

- the official O4a+O4b injection HDF5 release;
- its documentation and attributes;
- time boundaries for O4a and O4b;
- search-specific FAR fields;
- the released draw-density components and mixture weights;
- an independent public implementation or release script for fixed-point comparison.

### Ordered tasks

1. **Map the schema.**

   Freeze the names and meanings of:

   - source parameters;
   - injection time;
   - search FAR columns;
   - found/not-found fields or derived criterion;
   - all log draw-density components;
   - mixture `weights`;
   - generated-count and wall-time metadata.

2. **Define run masks exactly.**

   O4a and O4b must use their documented time intervals. Boundary conventions must be tested.

3. **Define the found criterion.**

   Specify:

   - the FAR threshold consistent with the population event selection;
   - how several search pipelines are combined;
   - how missing or infinite FAR values are treated;
   - whether an injection is found if any eligible pipeline crosses threshold.

4. **Reconstruct the draw density.**

   Combine all documented components in log space. Preserve the mixture normalization. Do not infer a convenient normalization by matching the desired answer.

5. **Derive `log_base_weight`.**

   Include run-specific generated counts and wall-time mixture factors exactly as documented.

6. **Implement the estimator.**

   The estimator should be chunkable so that the large injection file does not require unbounded memory.

7. **Validate fixed points independently.**

   Select at least ten frozen hyperparameter points spanning:

   - low, central, and high primary masses;
   - broad and narrow mass distributions;
   - representative mass-ratio and redshift settings;
   - both released model families;
   - both O4a and O4b.

   Compare \(\xi_r\) against independent release or public reference code.

8. **Study Monte Carlo stability.**

   Repeat under:

   - injection subsampling;
   - deterministic data chunks;
   - row shuffling;
   - bootstrap resampling;
   - five-fold partitions;
   - alternative but documented search-pipeline combinations, when relevant.

9. **Write immutable contracts.**

   Each run contract contains arrays, masks, weights, source columns, thresholds, provenance, checksums, and validation metadata.

### Proposed module

```text
src/gwtc_forecast/io/o4_injections.py
```

### Required tests

1. O4a/O4b boundary tests.
2. Missing and infinite FAR handling.
3. Correct “found by any eligible search” logic.
4. Log draw density equals the sum of the documented components.
5. Mixture normalization is invariant to chunking.
6. Row reordering leaves \(\xi_r\) unchanged.
7. Contract round trip is exact.
8. Fixed-point agreement is within

   \[
   \max(2\sigma_{\rm MC},2\%).
   \]

9. Selection ESS and likelihood-estimator variance are reported for every hyperdraw.
10. Deliberately wrong run normalization causes the reference test to fail.

### Numerical gates

For the pilot:

```text
selection ESS >= 1000
fixed-point discrepancy <= max(2 sigma_MC, 2%)
all values finite within model support
```

For the full analysis, use the stronger qualification target:

```text
likelihood-estimator variance <= 0.25 for at least 95% of retained draws
hard ceiling on variance <= 1 for every retained draw
selection ESS >= max(1000, 4*N_run) for at least 99% of draws
no retained draw with ESS < 4*N_run
```

The variance thresholds are project qualification criteria, informed by current Monte Carlo-accuracy literature and recent LVK practice. They are not universal laws and must be reported as prespecified design choices.

### Artifacts

```text
processed/selection/o4a.hdf5
processed/selection/o4b.hdf5
results/qualification/selection/schema_mapping.json
results/qualification/selection/found_rule.md
results/qualification/selection/normalization_derivation.md
results/qualification/selection/fixed_point_comparison.csv
results/qualification/selection/convergence.json
```

### Gate WP2B

**Pass** only when both run-specific estimators agree with independent reference calculations and satisfy the numerical gates.

**Pause** if the generated-count or wall-time normalization cannot be established from official products.

---

## Work Package 3: Released GWTC-3 hyperposterior and population-density adapters

**Shared implementation with separate model ownership**

### Objective

Evaluate the exact released `PowerLawPeak` and `PowerlawDipBreak` population densities and read their hyperposterior samples and weights without replacing them with toy approximations.

### Why this is more than reading a CSV

A hyperposterior sample is meaningful only with the same model definition, supports, tapers, cosmology, and nuisance assumptions used to generate it. Transcribing only the primary-mass formula while ignoring mass ratio, redshift, or spins can make the event and selection integrals inconsistent.

### Ordered tasks

1. **Audit archive contents before executing code.**

   Inventory file types, modules, serialization formats, requirements, and object provenance. Never load arbitrary pickles before understanding their classes and origin.

2. **Identify hyperposterior samples and weights.**

   Determine whether samples are equally weighted. If not, preserve the weights exactly.

3. **Map every hyperparameter.**

   Create a table:

   ```text
   release name | internal name | definition | unit | support |
   prior | model component | transformation
   ```

4. **Prefer released executable code.**

   Wrap the official model implementation when feasible rather than rewriting equations. If dependency incompatibility requires transcription, document every formula and compare at frozen points.

5. **Preserve full nuisance structure.**

   Audit and implement all dimensions that enter either event likelihoods or selection estimates:

   - primary and secondary masses or mass ratio;
   - redshift and rate evolution as required by the shape density;
   - spin variables and their distributions if they differ or do not cancel;
   - supports and smoothing tapers;
   - cosmology and source/detector-frame transformations;
   - normalization.

6. **Test density normalization.**

   At representative hyperdraws, numerically verify the normalized density or normalized conditional factors. The project target is an error no larger than \(10^{-3}\) where the integral can be evaluated reliably.

7. **Reproduce a released result.**

   Reproduce at least one machine-readable mass-spectrum curve, numerical table, or released figure panel for each model. The comparison must be quantitative, not only visual.

8. **Write `HyperPosterior` contracts.**

   Preserve samples, log weights, parameter names, release identifiers, checksums, and adapter version.

### Proposed modules

```text
src/gwtc_forecast/io/gwtc3_hyperposteriors.py
src/gwtc_forecast/populations/released_gwtc3.py
```

### Required tests

1. Hyperposterior weights normalize correctly in log space.
2. Equal-weight and unequal-weight synthetic cases recover analytic expectations.
3. All support boundaries are exact.
4. Density values match release code at frozen test points.
5. Normalization checks pass at representative hyperdraws.
6. Parameter name mapping is complete and one-to-one.
7. Missing nuisance coordinates cause a hard failure.
8. Source-frame and detector-frame transformations agree with documented cosmology.
9. Hyperposterior contract round trip is exact.
10. Reproduced release curve/table agrees within

   \[
   \max(2\sigma_{\rm reference},2\%).
   \]

### Artifacts

```text
processed/hyperposteriors/powerlaw_peak.hdf5
processed/hyperposteriors/powerlaw_dip_break.hdf5
results/qualification/models/archive_inventory.json
results/qualification/models/parameter_mapping.csv
results/qualification/models/fixed_points.json
results/qualification/models/normalization.json
results/qualification/models/release_reproduction.csv
results/qualification/models/release_reproduction.png
```

### Gate WP3

**Pass** only when both released models have validated executable densities, hyperposterior weights, and a quantitative release reproduction.

**Pause** if no machine-readable reference can be reproduced or if an essential nuisance dimension is unavailable.

---

## Work Package 4: Five-event real-data vertical slice

### Objective

Run the complete real-data chain on the five pilot events using only validated processed contracts and the existing statistical core.

### Why this stage exists

The pilot catches interface errors that toy tests cannot:

- real PE labels and priors;
- real coordinate conventions;
- real O4a/O4b selection data;
- real released hyperposteriors;
- realistic importance-weight degeneracy;
- provenance across several public releases.

It is a systems test, not the paper result.

### Workflow

Add a thin orchestrator:

```text
src/gwtc_forecast/workflows/five_event_score.py
```

It should:

1. read the five `EventPosterior` contracts;
2. read the O4a and O4b `SelectionCampaign` contracts;
3. read the two `HyperPosterior` contracts;
4. instantiate the two released population adapters;
5. call the existing vertical-slice evaluator;
6. write a complete run manifest and diagnostics.

It must not reimplement likelihood algebra.

### Required outputs

For each model:

- joint predictive score;
- prequential predictive score;
- eventwise increments;
- chronological cumulative score;
- event PE ESS;
- selection ESS by run;
- evolving hyperposterior ESS;
- leave-one-event-out influence;
- finite-hyperposterior bootstrap uncertainty;
- joint/prequential discrepancy;
- support and nonfinite counts.

For the comparison:

- \(\Delta S\);
- Monte Carlo uncertainty on \(\Delta S\);
- eventwise \(\Delta s_i\);
- cumulative \(\Delta S(n)\);
- result after removing each event in turn.

### Existing numerical gates

```text
minimum event ESS                         100
minimum selection ESS                    1000
maximum joint/prequential discrepancy    1e-10
maximum MC sigma on Delta S               0.5 nat
maximum fractional MC error               0.2
```

### Additional interpretation rule

Even if all gates pass, the five-event result is labeled:

```text
PASS_REAL_DATA_VERTICAL_SLICE
```

not:

```text
SCIENTIFIC_PEAK_OR_BREAK_RESULT
```

### Artifacts

```text
results/qualification/five_event/<run_id>/RUN_MANIFEST.json
results/qualification/five_event/<run_id>/scores.json
results/qualification/five_event/<run_id>/event_increments.csv
results/qualification/five_event/<run_id>/ess.csv
results/qualification/five_event/<run_id>/leave_one_out.csv
results/qualification/five_event/<run_id>/figures/
results/qualification/five_event/<run_id>/COMPLETION_REPORT.md
```

### Gate WP4

**Pass** when the five-event chain completes reproducibly, all numerical gates pass, and results are unchanged within uncertainty under reasonable thinning and chunking.

**Fail technically** if any mapping, support, ESS, or convergence criterion fails. Repair only the identified issue; do not tune the scientific model to make the score stable.

A pass authorizes the detected-space power experiment. It does not yet authorize downloading and analyzing the full O4 PE sample.

---

## Work Package 5: Detected-space discrimination and power qualification

### Objective

Determine whether the two frozen released models are distinguishable at the size and sensitivity of the O4a+O4b catalog even under idealized parameter measurement.

### Why this must precede the expensive full-catalog PE campaign

Suppose the two models predict almost the same detected distribution. Processing hundreds of event-level PE files cannot create information that the models do not provide. The power gate is therefore a best-case test of identifiability.

If the models cannot be distinguished when every source parameter is known exactly, measurement uncertainty will not rescue the comparison.

### Hypothesis

For an O4-sized catalog generated from either model, the generating model should usually receive the larger held-out predictive score.

### Minimum inputs

- validated released-model adapters and hyperposteriors;
- validated O4a/O4b injection campaign;
- official O4a and O4b event counts under the frozen population-selection rule;
- no event-level PE files beyond the pilot.

### Mock-catalog construction

For generating model \(M_g\):

1. draw one hyperparameter vector per mock catalog,

   \[
   \Lambda_g\sim p(\Lambda\mid D_{\rm GWTC3},M_g);
   \]

2. for each run \(r\), draw exactly the official count \(N_r\) from the detected distribution

   \[
   p_{\rm det}(\theta\mid\Lambda_g,r)
   \propto
   p(\theta\mid\Lambda_g)P_{\rm det,r}(\theta);
   \]

3. score the ideal source parameters under both posterior-predictive models;
4. preserve O4a and O4b as separate selection terms;
5. repeat under each generating model.

### Preventing injection leakage

If the same finite injection rows are used both to generate mock events and to estimate the score's selection normalization, accidental correlations can make performance look better than it is.

Use deterministic five-fold cross-fitting:

- generate events from one fold;
- estimate selection from the complementary folds;
- rotate the generation fold evenly;
- prove by test that no row is used in both roles for the same mock.

### Signed recovery statistic

Define

\[
T=
\begin{cases}
S_{\rm PLP}-S_{\rm PDB}, & M_g={\rm PLP},\\
S_{\rm PDB}-S_{\rm PLP}, & M_g={\rm PDB}.
\end{cases}
\]

Positive \(T\) means the generating model wins.

### Preliminary and final mock counts

1. Run **250 mocks per generating model** as a qualification screen.
2. Continue to **at least 2,000 mocks per generating model** only if the preliminary interval could satisfy the pass criteria.
3. Before a run longer than 15 minutes, report the benchmarked event rate, expected wall time, RAM, scratch space, command, checkpoints, and stop conditions.

### Prespecified power gate

Both generating directions must satisfy:

\[
\operatorname{median}(T)\ge5\ \text{nats},
\]

\[
P(T\le0)\le0.10,
\]

and

\[
q_{0.05}(T)>0.
\]

In words:

- the typical correct-model advantage is at least 5 nats;
- the wrong model wins in no more than 10% of mocks;
- even the 5th percentile remains on the correct side.

These are strict project investment thresholds, not universal discovery criteria. They are chosen to ensure that a costly real-data campaign has a meaningful chance of producing an interpretable answer.

### Monte Carlo gates

```text
SE of median T                         <= 0.25 nat
SE of wrong-sign probability          <= 0.01
change when sampling is doubled:
    |change in median T|              <= 0.5 nat
    |change in wrong-sign probability| <= 0.03
same qualitative decision in all five injection folds
```

### Robustness checks

- remove the most influential mock event;
- vary retained hyperposterior sample count;
- vary injection subsample size;
- shuffle injection order;
- verify supports and maximum normalized weights;
- require unsupported detected mass below 0.5% for each model/run comparison;
- inspect runwise contributions, not only combined O4.

### Proposed files

```text
config/detected_power_gate.toml
src/gwtc_forecast/workflows/detected_power_gate.py
tests/test_detected_power_gate.py
```

### Artifacts

```text
results/qualification/detected_power/<run_id>/
    RUN_MANIFEST.json
    RESOLVED_CONFIG.toml
    INJECTION_FOLD_MANIFEST.json
    mock_scores.hdf5
    power_summary.json
    convergence.json
    resource_usage.json
    figures/
    DECISION.json
    COMPLETION_REPORT.md
```

### Gate WP5

If both directions pass:

```text
PASS_DETECTED_POWER_GATE
```

This authorizes the full O4 PE campaign.

If either direction fails:

```text
NO_GO_INSUFFICIENT_DETECTED_POWER
```

Stop the released-model astrophysical comparison. Do not weaken the threshold, add models, or fall back to interpreting the five-event pilot.

If an adapter or reference check fails, use a technical pause label rather than a scientific no-go.

---
## Work Package 6: Freeze the official O4a+O4b analysis sample

### Objective

Construct a machine-readable event-selection contract for the full held-out catalog before calculating any full-catalog model score.

### Why this is a separate scientific task

A forecast score depends on which events count as the test sample. Choosing events after inspecting their score contributions would be a form of post-selection. The event rule must come from the official population-analysis criteria, not from convenience or the visual quality of PE samples.

### Tasks

1. Read the official GWTC-5 event list and population-analysis scripts.
2. Reconstruct the exact binary-black-hole inclusion rule used for the chosen analysis:
   - observing run;
   - FAR threshold;
   - source-class or mass cuts;
   - availability and version of PE results;
   - treatment of ambiguous neutron-star or mass-gap systems;
   - treatment of duplicate or updated event releases.
3. Decide whether the primary sample exactly follows the official GWTC-5 population sample or a narrower frozen BBH subset. The advisor approves this before scores are computed.
4. Assign every candidate one of:

   ```text
   INCLUDE_O4A
   INCLUDE_O4B
   EXCLUDE_<DOCUMENTED_REASON>
   PAUSE_AMBIGUOUS
   ```

5. Cross-check the counts against the official population publication and scripts.
6. Freeze the chronological order using event GPS times.
7. Freeze the PE stable-release version and label rule globally, with documented event-specific exceptions only when the release requires them.

### Required artifact

```text
processed/catalogs/o4_population_count_contract.json
```

It must contain:

- event ID;
- GPS time;
- observing run;
- inclusion status;
- every selection field used;
- exclusion reason;
- PE source record and stable-release version;
- checksum of the official source list;
- final O4a and O4b counts;
- configuration and Git hash.

### Tests

- event IDs are unique;
- chronological ordering is deterministic;
- every official candidate receives a status;
- included events have an available PE file under the frozen release;
- counts reproduce the official selection or every difference is explained;
- changing an event field used by the rule changes the expected classification in a unit test.

### Gate WP6

The sample is frozen and reviewed **before** the full PE download plan is approved.

---

## Work Package 7: Full O4a+O4b event-contract campaign

### Objective

Apply the validated PE adapter to every event in the frozen O4 population sample, producing compact event contracts with standardized coordinates and full provenance.

### Why this begins only now

The full PE campaign may involve many files and substantial storage. It is justified only after:

- the five-event adapter works on real releases;
- the selection and model adapters pass;
- the detected-space power gate shows that the comparison is identifiable.

### Tasks

1. Generate a dry-run full-O4 download plan from the frozen event contract.
2. Report exact live size, free-space reserve, estimated download time, and extraction requirements.
3. Download sequentially with checksum verification.
4. Process events in deterministic batches, for example by observing run and GPS time.
5. For every event:
   - apply the frozen label rule;
   - reconstruct the PE prior through the validated adapter;
   - write the standardized contract;
   - calculate summary diagnostics;
   - hard-fail on ambiguity.
6. Create a catalog-level status table.
7. Do not silently omit an event because its ESS is poor. Mark it as a scientific/numerical blocker and investigate.

### Batch safeguards

- checkpoint after every event;
- never overwrite a valid contract with a different mapping without versioning;
- store failed-event reports separately;
- make reruns idempotent;
- do not keep unnecessary copies of large posterior arrays;
- preserve raw public files unchanged.

### Required status table

```text
event_id | run | PE record | label | sample count |
minimum ESS across frozen test points | support fraction |
contract status | failure reason | checksum
```

### Gate WP7

Every included event must have a valid contract or a documented blocking decision. A full-catalog score is not computed from an opportunistic subset unless that subset was defined prospectively as a separate analysis.

---

## Work Package 8: Full O4a+O4b comparative predictive score

### Objective

Compute the primary scientific result: the selection-corrected predictive score of each frozen GWTC-3 model on O4a, O4b, and their chronological combination.

### Primary outputs

Compute:

\[
S_{\rm PLP}^{\rm O4a},\quad
S_{\rm PDB}^{\rm O4a},\quad
\Delta S_{\rm O4a},
\]

\[
S_{\rm PLP}^{\rm O4b},\quad
S_{\rm PDB}^{\rm O4b},\quad
\Delta S_{\rm O4b},
\]

and the sequential combined result

\[
\Delta S_{\rm O4a+O4b}.
\]

The O4b analysis should be reported in two logically distinct ways:

1. **GWTC-3 forecast of O4b:** retain the original GWTC-3 hyperposterior throughout;
2. **rolling update:** update each model with O4a, then forecast O4b.

The first is the clean historical model test. The second asks whether each model can learn sequentially. They must not be conflated.

### Workflow

Add a workflow that reads only frozen contracts:

```text
src/gwtc_forecast/workflows/full_o4_score.py
config/full_o4_score.toml
```

It should produce:

- joint and prequential scores;
- chronological \(\Delta S(n)\);
- runwise contributions;
- eventwise comparative increments \(\Delta s_i\);
- leave-one-out and leave-one-run-out results;
- event and selection ESS;
- support diagnostics;
- finite-hyperposterior Monte Carlo uncertainty;
- convergence under hyperposterior and PE sample changes.

### Interpretation categories

The machine report should distinguish:

```text
DECISIVE_RELATIVE_PREFERENCE
MODEST_RELATIVE_PREFERENCE
INDISTINGUISHABLE_AT_CURRENT_PRECISION
NUMERICALLY_UNRESOLVED
SUPPORT_DOMINATED
ONE_EVENT_DOMINATED
```

These labels describe diagnostics; final astrophysical language remains an advisor decision.

### Suggested score scales

Use simulations, not a universal Jeffreys-style table, for final calibration. For project triage, the following descriptive scales can be reported:

```text
|Delta S| < 1 nat       negligible predictive separation
1 <= |Delta S| < 2.5    small
2.5 <= |Delta S| < 5    moderate
|Delta S| >= 5          substantial for project-level interpretation
```

These are descriptive, not discovery thresholds.

### No-single-event rule

Report the fraction of the total score difference supplied by the most influential event:

\[
f_{\max}=\frac{\max_i|\Delta s_i|}{|\Delta S|}.
\]

A result with \(f_{\max}>0.5\) is flagged as one-event dominated. It may still be scientifically meaningful, but the paper must then center on that event and demonstrate waveform/PE robustness rather than advertise a generic population preference.

### Gate WP8

Proceed to a paper-level interpretation only if:

- all numerical gates pass;
- the sign and broad magnitude are stable under the uncertainty program in WP9;
- the result is not an unsupported-boundary artifact;
- the eventwise pattern is physically interpretable or the null result is decisively calibrated.

---

## Work Package 9: Uncertainty, calibration, and model adequacy

### Objective

Determine whether the observed score difference is stable and whether either model provides an acceptable description of O4.

### Why the baseline bootstrap is not enough

The current finite-hyperposterior bootstrap quantifies uncertainty from storing a finite number of GWTC-3 hyperposterior draws. It does not include:

- finite PE posterior samples;
- finite injection samples;
- finite realization of the astrophysical catalog;
- waveform/PE label choices;
- possible model misspecification.

A publishable result needs a layered uncertainty budget.

### 9.1 Hyperposterior Monte Carlo uncertainty

Repeat the score under:

- independent hyperposterior subsamples;
- increasing retained sample counts;
- weighted bootstrap or appropriate resampling of hyperposterior draws;
- common random numbers across the two models where scientifically valid.

Report convergence of \(\Delta S\), not only each absolute score.

### 9.2 PE Monte Carlo uncertainty

For each event:

- repeat with independent posterior subsamples;
- bootstrap posterior samples with care for sampler correlations when relevant;
- study thinning versus retained-sample count;
- calculate contribution to score variance.

If available labels represent meaningful waveform alternatives rather than redundant samplings, treat their spread as a systematic sensitivity, not as ordinary Monte Carlo noise.

### 9.3 Selection Monte Carlo uncertainty

Use:

- injection bootstrap;
- deterministic injection folds;
- segment-aware resampling when the released campaign structure supports it;
- convergence with injection sample count;
- variance estimates for the catalog log likelihood.

Selection uncertainty can be correlated between the two model scores because both use the same injection campaign. Estimate the uncertainty of the **difference** with paired resampling rather than adding two independent error bars.

### 9.4 Catalog variance

The observed O4 catalog is one finite realization. To assess sensitivity to that realization:

- perform event bootstrap or block bootstrap consistent with the catalog design;
- resample corresponding injection information or observing segments when required;
- compare with leave-one-out and delete-group jackknife diagnostics;
- report how often the sign of \(\Delta S\) changes.

Do not use the bootstrap to manufacture a new independent data set. Its purpose is to quantify how catalog-specific the conclusion is.

### 9.5 Prior and support sensitivity

Vary only prespecified, scientifically defensible choices:

- exact PE label alternatives documented by the release;
- numerical support truncation well outside posterior mass;
- hyperposterior thinning and weight treatment;
- event inclusion near an official threshold, reported as a secondary sensitivity analysis.

Do not retune model priors after seeing the preferred result.

### 9.6 Model adequacy

Relative scoring asks which model predicts better. Adequacy asks whether a model can plausibly generate data resembling O4.

At minimum implement detected-space posterior-predictive checks for:

- primary mass;
- secondary mass or mass ratio;
- redshift or luminosity-distance proxy as supported;
- selected two-dimensional summaries near the disputed feature;
- runwise counts in prespecified mass intervals, conditional on total count.

Recommended discrepancy statistics include:

- empirical CDF distance;
- binned or kernel two-sample discrepancy with bins frozen before O4 scoring;
- maximum gap in primary mass;
- counts in \(8<m_1/M_\odot<12\);
- counts in \(30<m_1/M_\odot<40\);
- high-mass tail count;
- a data-level or observable-space check when feasible.

Traditional event-posterior PPCs can have low power for poorly measured parameters because the single-event prior can dominate. For masses they are more useful than for spin tilts, but students should still compare event-level and more data-level summaries where possible.

### 9.7 Calibration of the observed score

Use the power simulations to calculate:

- probability of a score at least as extreme as observed under each generating model;
- expected distribution of eventwise concentration;
- distribution of run-to-run changes;
- probability that one event contributes the observed fraction of \(\Delta S\).

This turns a raw number into a calibrated statement.

### Required uncertainty table

```text
source of uncertainty | estimator | sigma(Delta S) |
changes sign? | changes category? | caveat
```

### Gate WP9

A result is stable when:

- Monte Carlo uncertainty is comfortably smaller than the claimed separation;
- the sign does not depend on arbitrary thinning or chunking;
- no unresolved support problem remains;
- catalog resampling does not make a strong claim look typical under both models;
- adequacy checks are reported for both models.

If the sign changes under reasonable, prespecified variants, report the models as indistinguishable and stop the strong astrophysical claim.

---

## Work Package 10: Harmonized peak-versus-break experiment

### Objective

If the released-model comparison is informative, construct a controlled comparison in which the competing models share the same nuisance assumptions and differ only in the mass structure under study.

### Why this is a later stage

The released-model screen answers a historical question: which published GWTC-3 analysis generalized better? It is faster because the hyperposteriors already exist.

A harmonized refit answers a cleaner physical question but requires new inference, more validation, and additional choices. It should be attempted only after the forecast machinery has demonstrated information content.

### Model design

Use no more than three frozen families:

1. **Smooth continuum:** a common tapered or broken continuum without localized excess;
2. **Localized peak:** the same nuisance model plus a Gaussian-like excess;
3. **Break model:** the same nuisance model plus a slope change, without the localized high-mass excess.

All three must share:

- mass-ratio model;
- redshift evolution;
- spin model;
- cosmology;
- mass support and taper convention where possible;
- event set;
- selection estimator;
- hyperpriors on common parameters;
- inference code and convergence criteria.

### Critical anti-hindsight rule

Model equations, priors, supports, and stopping rules are frozen before computing their O4 held-out scores. GWTC-3 may be used for training and internal validation. O4 must not be used to choose the number, width, or position of features.

### Training procedure

1. Reproduce a published GWTC-3 result with the chosen inference framework.
2. Fit the three harmonized models to GWTC-3 only.
3. validate sampler convergence and hyperposterior Monte Carlo accuracy;
4. generate posterior-predictive detected catalogs;
5. rerun the bidirectional power gate;
6. only then score O4.

### Physical localization

To support a statement about the \(35\,M_\odot\) structure, compute a prespecified regional decomposition. One option is to compare score changes when the population density is evaluated with masked or conditional primary-mass regions, taking care that the resulting quantities remain properly normalized. A simpler and safer approach is to report the eventwise contributions and the posterior probability that influential events occupy prespecified mass intervals.

Do not create bins after viewing the cumulative score curve.

### Gate WP10

Proceed only if the released-model phase shows stable discrimination or a clear adequacy failure worth isolating. If the released models are information-indistinguishable, a new refit is unlikely to be the highest-value next move unless simulations show a harmonized design with much greater power.

---

## Work Package 11: Sealed O4c forecast

### Objective

Create a timestamped, immutable forecast before the O4c catalog is released.

### Why this is strategically important

O4a+O4b is now a retrospective holdout because those data are public. O4c remains unreleased. A sealed forecast removes ambiguity about hindsight and raises the project from a retrospective methods analysis to a genuine prospective scientific test.

### Preconditions

- the full O4a+O4b pipeline is qualified;
- the model set is frozen;
- the event-selection rule for the future catalog is prespecified;
- the forecast can be generated without seeing O4c candidate properties.

### Forecast contents

At minimum archive:

1. the predictive distribution of the future comparative score \(\Delta S_{\rm O4c}\);
2. the probability that each model will win;
3. predictive distributions for prespecified counts, for example:

   \[
   N(8<m_1/M_\odot<12),
   \]

   \[
   N(30<m_1/M_\odot<40),
   \]

   \[
   N(m_1>45M_\odot),
   \]

   conditional on the future total count or with a separately documented rate model;
4. the predicted primary-mass CDF and uncertainty band;
5. the future event-inclusion rule;
6. all models, priors, data versions, code, thresholds, and seeds;
7. the scoring procedure to be run after release;
8. explicit handling of events lacking PE results or lying near thresholds.

A spin-related forecast should be included only if a spin extension has independently passed its own PE-information and power gates.

### Registration mechanism

Create:

- an immutable Git tag;
- a Zenodo DOI or equivalent timestamped archive;
- a human-readable forecast document;
- machine-readable predictive samples;
- cryptographic hashes of all files.

### No-change rule after registration

After registration, any correction is versioned and explained publicly. The original forecast remains accessible. Changes motivated by seeing O4c data invalidate the prospective status of the changed forecast.

### Future scoring

When O4c is released:

1. apply the prespecified event rule;
2. process events through the frozen adapters;
3. report the score with no model tuning;
4. compare the observed statistics with the sealed predictive distributions;
5. distinguish forecast failure from data-product or mapping failure.

---

# 9. Division of work between two students

The division below gives each student a primary technical domain while ensuring that both learn the full statistical chain.

## Student A: Event data and PE-prior lead

Primary responsibilities:

- PE release inventory and label audit;
- coordinate definitions and Jacobians;
- exact PE-prior reconstruction;
- event contracts;
- full O4 event-processing campaign;
- event-level ESS and waveform-label sensitivity;
- independent audit of the selection implementation.

Core learning outcomes:

- Bayesian parameter estimation versus hierarchical inference;
- importance sampling;
- coordinate transformations;
- public GW data products;
- numerical diagnostics for posterior reweighting.

## Student B: Selection, population-model, and forecast lead

Primary responsibilities:

- O4a/O4b injection masks and found criteria;
- draw-density and mixture normalization;
- selection contracts and fixed-point validation;
- released GWTC-3 hyperposterior and density adapters;
- detected-space mock catalogs and power analysis;
- independent audit of PE prior fixed points.

Core learning outcomes:

- survey selection effects;
- hierarchical population models;
- posterior predictive distributions;
- Monte Carlo accuracy;
- experimental design and power.

## Shared responsibilities

Both students participate in:

- mathematical derivations;
- five-event integration;
- full-catalog scoring;
- uncertainty decomposition;
- interpretation and paper writing;
- O4c preregistration;
- code review and independent reproduction.

## Rotation checkpoints

At the end of WP2 and WP3, each student gives a tutorial to the other:

- Student A teaches the PE prior and event estimator.
- Student B teaches the injection estimator and population adapters.

At the end of WP5, they exchange ownership for one week and reproduce the other student's primary result from artifacts and documentation alone. This is a practical reproducibility test.

---

# 10. Suggested semester-scale timeline

The schedule below is illustrative. Gates, not calendar dates, authorize progression.

| Weeks | Milestone | Primary output |
|---:|---|---|
| 1–2 | WP0 onboarding and derivations | baseline report and literature matrix |
| 3 | WP1 provenance and inventories | frozen input manifest |
| 4–7 | WP2A and WP2B in parallel | one validated event adapter and both run selection prototypes |
| 8–9 | Complete all pilot events and selection fixed points | five event contracts and two selection contracts |
| 10–11 | WP3 released-model adapters | two hyperposterior contracts and release reproduction |
| 12 | WP4 five-event integration | qualified vertical-slice report |
| 13–15 | WP5 detected-space power gate | pass/no-go decision |
| 16 | Research review and next-semester decision | advisor/student project review |

A second semester, conditional on WP5 passing:

| Weeks | Milestone | Primary output |
|---:|---|---|
| 1–3 | WP6–7 event sample and full contracts | frozen O4 catalog and event-contract set |
| 4–6 | WP8 full predictive score | O4a/O4b score artifacts |
| 7–9 | WP9 uncertainty and adequacy | calibrated result and robustness matrix |
| 10–12 | paper figures and draft | first manuscript draft |
| 13–15 | WP10 harmonized experiment, only if justified | controlled peak/break result |
| parallel | WP11 O4c registration | timestamped prospective forecast |

Do not compress a failed scientific gate merely to preserve this schedule.

---

# 11. Required validation matrix

A stage is not complete until the relevant rows below are satisfied.

| Validation level | Question | Example evidence |
|---|---|---|
| Unit | Does one formula or transformation behave correctly? | analytic toy, fixed-point Jacobian test |
| Contract | Can data be written and read without loss or ambiguity? | exact HDF5 round trip |
| Integration | Do validated objects pass through the existing workflow? | five-event vertical slice |
| Release reproduction | Does the adapter match an official published/released result? | fixed-point \(\xi_r\), mass-spectrum curve |
| Numerical convergence | Is the answer stable as Monte Carlo effort changes? | thinning/subsampling curves |
| Simulation calibration | Does the method favor the truth with known mocks? | signed \(T\) distribution |
| Identifiability | Can the target models be distinguished at actual sample size? | bidirectional power gate |
| Adequacy | Can either model plausibly generate O4-like data? | detected-space PPC/data-level check |
| Systematics | Does the conclusion survive documented alternatives? | waveform label and threshold sensitivity |
| Provenance | Can every number be traced to code, config, and data? | run manifest and checksums |
| Scientific authorization | Does the result satisfy prespecified interpretation gates? | decision artifact reviewed by advisor |

---

# 12. Expected paper-level outputs

A strong final paper should be designed around a small number of interpretable figures rather than a large gallery of internal diagnostics.

## Figure 1: Scientific setup

A schematic:

```text
GWTC-3 hyperposteriors -> frozen predictions -> O4a -> O4b -> O4c forecast
```

This establishes the chronological design.

## Figure 2: Detected-space predictions before seeing O4 scores

For each model, show posterior-predictive detected primary-mass distributions for O4a and O4b, including uncertainty. Overlay the held-out events only after the predictive bands are fixed.

## Figure 3: Power calibration

Show the distribution of signed \(T\) under each generating model, with wrong-sign probability and the observed O4 value.

## Figure 4: Cumulative chronological comparative score

Plot \(\Delta S(n)\) against event time. Mark O4a/O4b boundaries and label only prespecified or clearly influential events.

## Figure 5: Eventwise contributions

Plot \(\Delta s_i\) with PE/Monte Carlo uncertainty and posterior primary-mass summaries. This reveals which mass regions drive the comparison.

## Figure 6: Model adequacy

Detected-space PPC or data-level discrepancy plots for both models. This prevents a relative winner from being mistaken for an adequate model.

## Figure 7: Robustness and catalog variance

Show the distribution of \(\Delta S\) under catalog/injection resampling and the leave-one-out results.

## Figure 8, if available before submission: sealed O4c forecast

Display registered predictive intervals, not post-release tuning.

## Core tables

1. frozen data and model contract;
2. numerical and power gates with pass/fail status;
3. O4a, O4b, and combined score differences;
4. uncertainty budget;
5. most influential events and leave-one-out changes;
6. registered O4c forecast quantities.

Internal figures such as every prior histogram or chunk-convergence trace belong in supplementary material or the reproducibility archive unless they expose a scientific issue.

---

# 13. Decision tree and explicit stop rules

```text
Baseline and provenance valid?
    no -> PAUSE_MISSING_PROVENANCE
    yes
      |
PE, selection, and model adapters independently reproduced?
    no -> PAUSE_MAPPING_OR_REFERENCE_FAILURE
    yes
      |
Five-event vertical slice numerically stable?
    no -> TECHNICAL_BLOCKER_VERTICAL_SLICE
    yes
      |
Bidirectional O4-sized power gate passes?
    no -> NO_GO_INSUFFICIENT_DETECTED_POWER
    yes
      |
Full official O4 event contracts complete?
    no -> PAUSE_EVENT_CONTRACT_BLOCKER
    yes
      |
Full O4 relative score stable under MC and support checks?
    no -> NUMERICALLY_UNRESOLVED / SUPPORT_DOMINATED
    yes
      |
Either clear relative preference, clear joint failure, or meaningful simple-model result?
    no -> STOP_ASTROPHYSICAL_PAPER; preserve benchmark
    yes
      |
Paper-level interpretation + sealed O4c forecast
```

## Rules that may not be changed after viewing O4 scores

- model names and released hyperposteriors;
- primary event-selection rule;
- O4a/O4b split;
- primary score definition;
- pilot versus final-sample distinction;
- ESS and numerical thresholds;
- power-gate thresholds;
- prespecified mass intervals used for forecast summaries;
- rule that relative preference and adequacy are reported separately.

A correction to a demonstrable error is allowed, but it must create a new version with a written change log and rerun all relevant tests.

---

# 14. Risk register

| Risk | Why it matters | Early diagnostic | Mitigation or stop rule |
|---|---|---|---|
| PE prior cannot be reconstructed | biases every event weight | missing release metadata or failed normalization | pause; do not guess |
| O4 selection normalization ambiguous | catalog score biased by \(N_r\log\xi_r\) | fixed-point disagreement | pause until independently resolved |
| Released model code is incompatible or opaque | cannot claim exact historical forecast | failure to reproduce reference curve | wrap audited code, transcribe with fixed-point tests, or pause |
| Models differ in many nuisance assumptions | weakens physical peak/break interpretation | score contributions outside target mass region | describe as released-model comparison; use later harmonized models |
| Low event ESS | reweighting dominated by few samples | ESS and max-weight diagnostics | seek documented alternative PE samples or stop affected analysis |
| Low selection ESS/high variance | score may be numerically biased | fold and subsample instability | increase valid injection support if available; otherwise stop |
| One event dominates | population claim may really be event-specific | leave-one-out and \(f_{\max}\) | reframe and study that event's PE/systematics |
| Models have little detected-space separation | full campaign cannot answer question | WP5 power failure | no-go; do not add models post hoc |
| Both models are inadequate | relative winner can be misleading | PPC/data-level failure | report both failure and relative ranking |
| Catalog variance changes conclusion | result tied to one finite realization | bootstrap sign instability | weaken claim or report indistinguishable |
| O4c released before forecast registration | loses prospective opportunity | release timeline monitoring | prioritize minimal sealed forecast after qualification |
| Project becomes software-generalization exercise | delays scientific decision | growing modules without new gate evidence | enforce minimum scientifically complete change |
| Students specialize too narrowly | poor reproducibility and training | inability to explain other pipeline half | cross-audits and ownership exchange |

---

# 15. Definition of done

## A code module is done when

- its scientific formula is documented;
- public inputs and assumptions are identified;
- unit and failure tests pass;
- it is type-annotated and uses stable log-space calculations;
- it creates no unauthorized files;
- another student can reproduce its fixed points.

## A mapping is done when

- it is based on official documentation or audited release code;
- every coordinate and support is explicit;
- source record and checksum are stored;
- an independent implementation agrees within a frozen tolerance;
- ambiguity causes failure rather than fallback.

## A workflow is done when

- it consumes processed contracts rather than making new scientific choices;
- it records config, seed, commit, inputs, resources, and outputs;
- rerunning it is deterministic within specified stochastic uncertainty;
- all acceptance gates are machine evaluated;
- failure labels explain what stopped.

## The five-event phase is done when

- the real-data chain works end to end;
- all numerical gates pass;
- no astrophysical population claim is attached to the five-event score.

## The full project is scientifically done when

one of the following is established with calibrated uncertainty:

1. one frozen model predicts O4 substantially better and the conclusion is not support-, event-, or Monte Carlo-dominated;
2. both models demonstrably fail to predict important aspects of O4 despite adequate discrimination power;
3. a simpler harmonized model predicts as well as or better than the feature-rich alternatives;
4. the models are demonstrably non-identifiable at O4 size, closing the proposed comparison;
5. a prospective O4c forecast is sealed and later evaluated according to its frozen rules.

A large amount of code is not a definition of completion.

---

# 16. Recommended meeting and reporting structure

## Weekly group meeting

Each student reports only:

1. the scientific question tested that week;
2. the exact artifact produced;
3. the most important quantitative result;
4. the gate status;
5. the largest unresolved risk;
6. the next smallest test capable of changing the decision.

Avoid progress reports consisting mainly of lines of code, files opened, or hours spent.

## Biweekly reproducibility review

The non-owner reproduces one result from:

- the tagged commit;
- the run manifest;
- the configuration;
- the input checksums;
- the documented command.

Failures become issues immediately.

## Monthly scientific review

The advisor and students revisit:

- whether the target remains identifiable;
- whether recent literature changes the novelty claim;
- whether the next stage is still the highest-information use of time;
- whether a stop condition has been reached.

The scientific model set is not changed merely because the result appears weak.

---

# 17. Reading sequence for students

## Stage A: Bayesian and hierarchical foundations

1. **Thrane & Talbot (2019/2020)** for a pedagogical introduction to Bayesian inference, model selection, and hierarchical models in gravitational-wave astronomy.
2. **Mandel, Farr & Gair (2019)** for uncertain observations and selection biases.
3. **Gneiting & Raftery (2007)** for proper scoring rules and why probabilistic forecasts should be evaluated by the probability assigned to realized outcomes.

Suggested exercise: derive the event reweighting estimator from Bayes' theorem and verify it with a one-dimensional Gaussian toy problem.

## Stage B: GWTC-3 population science and released models

4. **LVK GWTC-3 population paper (2023)** for the scientific meaning of `PowerLawPeak`, break/dip models, and the catalog selection.
5. **GWTC-3 population data release** and its tutorial for the exact public products used in this project.

Suggested exercise: reproduce one released primary-mass curve from stored hyperposterior samples.

## Stage C: Selection and numerical accuracy

6. **Talbot & Golomb (2023)** for Monte Carlo uncertainty in event and selection integrals.
7. The official O4a+O4b sensitivity-release documentation.

Suggested exercise: estimate a toy selection efficiency analytically and with injections; study bias and variance as the proposal distribution becomes poorly matched.

## Stage D: Current population results and novelty

8. **GWTC-4 population paper**, especially the held-out O4a posterior-predictive check in Appendix D.7/Figure 23.
9. **GWTC-5 population paper** for the current evidence around \(10\,M_\odot\), the slope change near \(35\,M_\odot\), and mass-dependent spin structure.
10. **Corelli et al. (2026)** for catalog variance and the instability of the \(35\,M_\odot\) peak.
11. **Miller et al. (2026)** for limitations of standard GW population PPCs and the value of more data-level diagnostics.
12. **Wolfe et al. (2026)** for sequential population updating, which is adjacent to but distinct from comparative predictive scoring.
13. **Toubiana et al. (2025)** for model comparison in observable space.

Suggested exercise: write a one-page comparison of posterior fitting, posterior-predictive checking, sequential updating, and held-out proper scoring.

---

# 18. Reference list

The references below should be cited in student notes, code documentation, and the eventual manuscript where relevant. Students should consult the latest versions and journal publications when available.

1. **Abbott, R. et al. (LIGO Scientific Collaboration, Virgo Collaboration, KAGRA Collaboration).** “Population of Merging Compact Binaries Inferred Using Gravitational Waves through GWTC-3.” *Physical Review X* **13**, 011048 (2023). arXiv:2111.03634. DOI: 10.1103/PhysRevX.13.011048.

2. **LIGO Scientific Collaboration, Virgo Collaboration, KAGRA Collaboration.** “GWTC-3 Population Data Release.” Zenodo record 11254021. DOI: 10.5281/zenodo.11254021.

3. **Abac, A. G. et al. (LIGO Scientific Collaboration, Virgo Collaboration, KAGRA Collaboration).** “GWTC-4.0: Population Properties of Merging Compact Binaries.” arXiv:2508.18083; published version should be used where available. See especially Appendix D.7 and Figure 23 for the GWTC-3-to-O4a held-out posterior-predictive comparison.

4. **LIGO Scientific Collaboration, Virgo Collaboration, KAGRA Collaboration.** “GWTC-5.0: Population Properties of Merging Compact Binaries.” arXiv:2605.27226 (2026).

5. **LIGO Scientific Collaboration, Virgo Collaboration, KAGRA Collaboration.** “GWTC-5.0 Data Release Documentation.” GW Open Science Center, including the O4b PE releases, event list, and population products.

6. **Mandel, I., Farr, W. M., & Gair, J. R.** “Extracting distribution parameters from multiple uncertain observations with selection biases.” *Monthly Notices of the Royal Astronomical Society* **486**, 1086–1093 (2019). arXiv:1809.02063.

7. **Thrane, E. & Talbot, C.** “An introduction to Bayesian inference in gravitational-wave astronomy: parameter estimation, model selection, and hierarchical models.” *Publications of the Astronomical Society of Australia* **36**, e010 (2019), with corrigendum. arXiv:1809.02293.

8. **Gneiting, T. & Raftery, A. E.** “Strictly Proper Scoring Rules, Prediction, and Estimation.” *Journal of the American Statistical Association* **102**, 359–378 (2007). DOI: 10.1198/016214506000001437.

9. **Talbot, C. & Golomb, J.** “Growing Pains: Understanding the Impact of Likelihood Uncertainty on Hierarchical Bayesian Inference for Gravitational-Wave Astronomy.” *Monthly Notices of the Royal Astronomical Society* **526**, 3495–3506 (2023). arXiv:2304.06138.

10. **Corelli, A., Gerosa, D., Mould, M., & Fabbri, C. M.** “Variance of gravitational-wave populations.” arXiv:2603.00239 (2026).

11. **Miller, S. J., Winney, S., Chatziioannou, K., & Meyers, P. M.** “Posterior Predictive Checks for Gravitational-wave Populations: Limitations and Improvements.” arXiv:2604.06090 (2026).

12. **Wolfe, N. E., Mould, M., Veitch, J., & Vitale, S.** “Neural Bayesian updates to populations with growing gravitational-wave catalogs.” arXiv:2602.20277 (2026).

13. **Toubiana, A. et al.** “Comparing gravitational-wave population models and observations in observable space.” arXiv:2507.13249 (2025). Use the final title and publication metadata from the current version.

14. **Moore, C. J. & Gerosa, D.** “Population-informed priors in gravitational-wave astronomy.” *Physical Review D* **104**, 083008 (2021). arXiv:2108.02462. Relevant for leave-one-out population-informed distributions and avoiding double use of an event.

15. **Essick, R. & Farr, W. M.** Work on precision requirements for Monte Carlo population likelihoods, including arXiv:2204.00461. Students should use the final bibliographic metadata and connect its criteria explicitly to the project's selection-variance gates.

16. **Official O4a+O4b search-sensitivity estimates.** Zenodo record 19500064. DOI: 10.5281/zenodo.19500064.

17. **Official GWTC-5 population release.** Zenodo record 20292639. DOI: 10.5281/zenodo.20292639.

18. **Official GWTC-4.1 and GWTC-5 PE releases.** Use the stable Zenodo records frozen in `config/pilot_manifest.toml` and record the stable-release version and checksums in every processed contract.

---

# 19. Final student checklist

Before claiming that a stage is complete, answer every relevant question below.

## Scientific definition

- What exact hypothesis did we test?
- What observation or simulation could have falsified it?
- Was the model and threshold frozen before the relevant data score was viewed?
- Are we answering relative prediction, absolute adequacy, or both?

## Data

- Is every input an official public product?
- Are record, version, filename, and checksum stored?
- Is the event-selection rule frozen and machine-readable?
- Are O4a and O4b treated with their own selection contracts?

## PE adapter

- Is the label-selection rule documented?
- Is the exact PE prior evaluated in the same coordinates as the population density?
- Are all Jacobians, supports, and cosmology assumptions explicit?
- Did the other student reproduce fixed-point values independently?

## Selection adapter

- Is the found criterion exact?
- Is the run-specific normalization derived rather than guessed?
- Does an independent implementation agree at frozen points?
- Are ESS and likelihood-estimator variance acceptable?

## Population adapter

- Are the full released assumptions preserved?
- Are hyperposterior weights correct?
- Does the density normalize?
- Is a released result quantitatively reproduced?

## Numerical control

- Are event, selection, and hyperposterior ESS reported?
- Is the result stable under sample count, chunking, and order?
- Do joint and prequential scores agree?
- Is Monte Carlo uncertainty smaller than the claimed effect?
- Are support failures and nonfinite values zero or explicitly resolved?

## Scientific interpretation

- Did the bidirectional power gate pass?
- Does one event dominate?
- Do both models pass adequacy checks?
- Does catalog variance change the sign or category?
- Are we careful not to interpret a released-model preference as proof of a single physical ingredient?

## Reproducibility

- Is the Git commit recorded and tree clean?
- Is the resolved config archived?
- Are seeds and input hashes stored?
- Are exact commands and resource usage recorded?
- Can the other student reproduce the result from the artifacts alone?

## Publication value

- Can the central result be stated in one sentence without referring primarily to software?
- Is that sentence distinct from the GWTC-4 held-out PPC and the GWTC-5 in-sample population result?
- Would the null result still teach the field something calibrated and reusable?
- Is the O4c forecast sealed before release?

---

# 20. One-sentence project goal

> **Build and qualify an auditable model-falsification pipeline that uses frozen GWTC-3 population posteriors to score later O4 binary-black-hole detections, identifies which population structures genuinely generalized, and registers a prospective prediction for the unreleased O4c catalog.**

