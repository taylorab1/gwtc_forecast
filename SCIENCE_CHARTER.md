# Scientific charter: matched feature predictive audit

Status: the scientist's request for a refurbished, more impactful pipeline authorizes this redesign and the code/instruction development. It does not authorize automatic production runs, use of protected data, or acceptance of the numerical prior candidates without scientific review. This charter replaces v0.4; the old charter is archived.

## Primary question and claim

Does an additional localized high-mass excess improve the joint prediction of subsequently detected binary black holes, after allowing the baseline to describe broad mass-spectrum curvature and marginalizing the same nuisance population structure?

The claim is about **incremental predictive utility for the specified model pair and data domain**. An excess component need not produce a local maximum. A local maximum need not identify a formation channel. A model can win against a worse alternative and still be inadequate. These distinctions must appear in reports and any paper.

## Adopted direction

Use a matched shared smoothly broken continuum plus low-mass component, with and without an extra high-mass Gaussian. Match mass-ratio, spin, redshift, coordinate, selection and shared-prior prescriptions. Fit each model to the same selected through-O3 training catalog (O1/O2 included where prescribed), then freeze the model, priors, training posterior, input versions, cuts and scoring convention. O3-only is not an interchangeable label.

The primary statistic is the feature-minus-continuum joint log predictive score for the held-out catalog, conditional on each run's count. Report O4a and O4b as chronological blocks; the O4b conditional increment follows O4a, whereas an independently marginalized O4b score is a different estimand. No ranking by overlap of credible bands, posterior medians, or best-fit parameter likelihoods.

The candidate full population factorizes mass, mass ratio conditional on primary mass, redshift, and a joint spin distribution. These are scientific assumptions, not implementation truths. The baseline includes neither mass-dependent spin/redshift correlations nor rate information. Sensitivity of the conclusion to plausible shared-model inadequacy must be assessed before a feature-specific interpretation.

## Choices still requiring training-only development and freeze

The new JSON prior file is explicitly a **development candidate**. Its support, high-tail treatment, low-mass smoothing, continuum flexibility, parameter priors, event inclusion, FAR threshold and search union, PE analyses, cosmology and injection weights need a short scientific approval based on training data, release documentation, and simulations. Do not inspect held-out score signs while choosing them.

The same shared prior distribution must be used in both models; their fitted shared posteriors need not be equal. The extra-component prior must be proper. A continuous prior with support near zero is not a spike at zero. The discrete toy grid is a learning reference, not the continuous scientific prior.

The five inherited pilot events are for data-interface integration only, not a population conclusion. Through-O3 event-level PE and selection inputs must be added explicitly; no released hyperposterior from a different model is silently reused as a matched fit.

## Qualification and investment

First validate population normalization, coordinate/prior recovery, selection normalization and held-out factorization on analytical or independently implemented examples. Then qualify real released inputs, training inference and total numerical score precision. The fixed event/injection ESS floors (100/1000) are screening diagnostics, not sufficient accuracy guarantees.

Retain the previous final investment criteria: 2,000 mocks per generating direction after a 250-per-direction preliminary study; median signed score >=5; wrong-sign fraction <=0.10; fifth percentile >0; median SE <=0.25; wrong-sign SE <=0.01. The revised assessor also exposes 95% intervals and reports threshold overlap as inconclusive. These are investment criteria, not calibrated astronomical significance levels. Tiny synthetic tests do not open them.

For the actual discriminating experiment, incorporate an independently checked observation/measurement process consistent with detection. True-parameter-only detected catalogs provide at most an optimistic screen. A real-data generator is not supplied as if validated. Draw one set of population parameters per mock catalog, not per event. Conditional power uses one realized training posterior; repeated-experiment calibration re-simulates and refits training. Both are useful but answer different questions.

Retain the target score Monte Carlo sigma <=0.5 and fractional sigma <=0.2 away from zero. Close to zero the absolute requirement applies; division by nearly zero is not meaningful. Assess uncertainty in the difference with paired shared inputs, and separately address event PE, injection and training-posterior contributions. Numerical error is not astrophysical catalog variance.

## Outcomes and limits

Favorable and unfavorable valid evidence both complete an experiment. Low qualified power means stop or narrow this design, not disprove the feature. Invalid integration, poor sampler support, or incomplete jobs are not negative science. Do not weaken gates, discard problematic events, alter seeds, add trials beyond the planned total, or switch models after a failure to manufacture a pass.

O4a/O4b are retrospective. Published results informed this project design. A prospective O4c or other extension requires documented non-exposure to the relevant information and a timestamped freeze before access, not merely before the next population paper. Do not wait for observing run O6 to deliver a thesis contribution.

No long campaign is automatically launched by this repository. Benchmark the actual producer-to-report path first and obtain the appropriate resource/scientific authorization. Reuse validated inputs after operational repairs. AI assistance is optional; scientific ownership and independent checks are required.
