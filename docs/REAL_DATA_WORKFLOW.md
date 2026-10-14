# From the synthetic experiment to a defensible real-data comparison

## 1. Lock down the data domain before a large download

Start with the official GWOSC release documentation, not guessed filenames. The supplied manifest preserves the five-event integration pilot and existing reference/sensitivity products; it is not a complete through-O3 training manifest. The old released-model hyperposterior downloads have been removed from the default primary route and preserved in `config/legacy_reference_manifest.toml`.

Agree on through-O3 BBH membership, event identities, search/FAR definitions, observing-period boundaries, and treatment of ambiguous events. Record reprocessed versions and whether they supersede earlier products. O4a/O4b scoring here is explicitly retrospective. A corrected PE release may be the right statistical choice, but it is not an as-of-training-era forecast.

Use `plan`, then a limited `download`, file verification and inventory commands. Do not begin by fetching every event. The external disk defaults and configuration guards remain active. Students need legitimate access to that disk or their own approved data configuration before a deadline requiring real products.

## 2. Make one event scientifically usable

Identify the exact PE analysis label, waveform, sample weights, sampled variables, conditional/marginalized nuisance conventions, bounds and generating prior. Save source locators and checksums. Reconstruct the prior in the model coordinates and check at selected samples against released/trusted code or an independently derived expression. Do not infer a prior from a histogram of posterior samples.

`io/standardize.py` accepts an explicit structured HDF5 dataset/column map and an already evaluated target-coordinate log prior. It writes no claim of validation and invents no LVK-specific expression. `io/coordinates.py` supplies tested Jacobian operations, not cosmological inference. Build one explicit adapter per genuinely different convention, sharing common code where valid.

Write an EventPosterior using `io/contracts.py`, reload it and repeat the numerical check. Set metadata `validated=true` only after documenting the independent check. Missing required prior factors remain a blocker, not an invitation to use a convenient approximate prior.

## 3. Make one selection campaign scientifically usable

Record proposal density, generated-trial normalization, recovered mask, search combination, redshift/source-time conventions and any mixed-campaign weights. Reproduce a documented released efficiency or compare to an independent integral where possible. Inspect parameter support against the candidate model, including tails.

A `SelectionCampaign` stores recovered samples, log_draw_density, log_base_weight and run. For single iid generated trials, log_base_weight=-log(N_generated). For a mixed release, use its documented estimator. Write and reload the contract. A successful HDF5 read is not normalization validation. The O4 campaign does not stand in for O3 sensitivity.

## 4. Approve training-only model development

Compare prior-predictive distributions, evaluate independent density normalizations at representative prior extremes, and inspect through-O3 fit behavior. The candidate prior file lists all fixed and variable quantities; copy it into the study workspace, record the chosen values, then change its status to `frozen_for_training` only after this review.

Freeze shared structure identically in both models. Do not tune high-feature location, width, support or continuum flexibility after examining O4 score preference. Because the design was informed by published O4 analyses, label the ultimate study retrospective even when its implementation avoids further tuning.

## 5. Fit both models to through-O3

Copy `config/real_study.example.json` to a small external study workspace. All relative paths are relative to that JSON. Fill explicit training-event paths, held-out paths, per-run selection contracts, prior file and an inspectable qualification report. Add inputs incrementally; do not invent dummy contracts merely to clear the audit.

```bash
gwtc-forecast study-audit --spec /absolute/path/to/study.json
gwtc-forecast study-fit --spec /absolute/path/to/study.json --model continuum
gwtc-forecast study-fit --spec /absolute/path/to/study.json --model highpeak
```

Commands without explicit outputs use new attempt directories below the configured external results tree. `--output` must also be below that tree for real fits/scores. Model training refuses O4/future training runs and requires validated inputs, frozen prior status and a qualification-report file. The optional Bilby adapter was implemented but not exercised against installed Bilby in the distribution build; first qualify its likelihood through a small trusted case in the documented science environment. `nlive=500` is a starting sampler setting, not demonstrated convergence.

Check independent sampler runs/settings, likelihood precision over relevant posterior support, parameter/derived distributions and stability of the final predictive integral. The exported posterior initially has `sampler_qualified=false`. A report file's existence and metadata flags are not proof; a researcher must inspect the evidence before changing qualification metadata. Do not use two agents calling the same code as an independent implementation.

## 6. Run the five-event producer-to-report test

Provide the two training-posterior paths in the study JSON. Set `allow_retrospective_scoring=true` only after the explicit review authorizing this pilot calculation; it defaults to false. The old `science.toml` flags describe the retained legacy readiness workflow, not a substitute for this study specification. Ensure both record the same training identities and prior-file hash and have their training qualification completed. Run `study-score` on the pilot with its release-specific selections. Verify joint/sequential agreement, run accounting, coordinate conventions and saved/reloaded reproducibility.

The returned result is a candidate comparison, not final production qualification. Estimate the cost and support limitations of the full catalog before expanding. Pilot score signs must not be used to choose a more favorable design; retain the pilot as an exposed integration subset in the retrospective disclosure.

## 7. Qualify power, adequacy and total numerical precision

Before a full-catalog claim, supply a measurement-aware mock-observation process independently checked for the chosen population question. That component is not asserted complete in this release. A bounded detected-true-parameter study can identify obviously inadequate power, but cannot certify realistic power in the presence of measurement degeneracies.

The conditional power experiment and repeated-training SBC prototype give concrete statistical references. Extend them using the qualified real-data observation strategy; do not rename their toy selection as an instrument response. Include a small training-motivated out-of-family stress test to determine whether shared-model misspecification could favor the added mass component. Freeze its scope before examining held-out model preference.

Use the predeclared 250/2000-per-direction study and the uncertainty-aware decision consumer described in `DETECTED_POWER_GATE.md`. Benchmark one full replicate before a long campaign, persist ordinary checkpoints, inspect failures and preserve them in the report. Do not add trials to force a favorable decision.

## 8. Complete the retrospective comparison

Only after qualification and an agreed resource budget, score the complete selected O4a/O4b catalog. Report joint delta with numerical uncertainty, conditional period increments, event influence, failure/support diagnostics and qualified discriminating power. Report adequacy separately from relative preference. Numerical precision, finite-catalog variability, and model sensitivity are different quantities.

Package a small report and decisive arrays/figures for review; leave bulk public data on external storage. No additional model family, spin project or future observing-run campaign is automatic. A valid no-go or restricted claim is an acceptable endpoint.
