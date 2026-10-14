# Science charter

## Primary question

Did a localized high-mass peak or a slope break inferred from GWTC-3 assign the
larger selection-corrected predictive probability to later O4 BBH events?

## Primary estimand

For model \(M\), earlier data \(D_{\rm GWTC3}\), and held-out run \(D_r\),

\[
S_{r,M}=\log p(D_r\mid D_{\rm GWTC3},M,N_r).
\]

The primary analysis conditions on the observed count in each run and evaluates
population shape. O4a and O4b retain separate selection factors.

For two models,

\[
\Delta S_r=S_{r,M_1}-S_{r,M_0}.
\]

## Frozen first comparison

- `PowerLawPeak`
- `PowerlawDipBreak`

The released analyses are a screening comparison, not yet the final harmonized
peak-versus-break tournament. They may differ in more than one modeling choice.
A harmonized refit is authorized only if the released-model screen contains
stable predictive information.

## First real-data vertical slice

Five events only:

- O4a: `GW230627_015337`
- O4a: `GW230726_002940`
- O4a: `GW230814_230901`
- O4b: `GW240414_054515`
- O4b: `GW240630_101703`

The pilot is an implementation and information-content test, not a title-level
astrophysical claim.

## Non-negotiable statistical requirements

1. Each PE file has one frozen analysis label.
2. The event-level PE prior is evaluated in the same coordinates used in the
   population density, including every required Jacobian.
3. The posterior-row representation is frozen as equal weight or encoded with
   explicit normalized row weights.
4. O4a and O4b selection normalizations are explicit.
5. Posterior-sample and injection effective sample sizes are reported.
6. Joint and prequential scores agree numerically.
7. Monte Carlo uncertainty satisfies the frozen absolute threshold; a
   fractional threshold is additionally required only when the score difference
   is materially nonzero.
8. No model or prior is changed after inspecting eventwise real-data scores.

## Explicitly out of scope for the first campaign

- spin correlations;
- merger-rate/count prediction;
- full GWTC-5 population refits;
- a new flexible mass model;
- raw strain or new event-level PE;
- machine learning;
- GPU acceleration;
- O4c alert-driven tuning;
- production claims from the simplified one-dimensional toy models.

## Kill gates

The project stops or narrows if:

- a published GWTC-3 population product cannot be reproduced within understood
  numerical differences;
- the selection estimator disagrees with a public reference implementation;
- mock O4-sized catalogs cannot distinguish the relevant models;
- score ordering changes under reasonable posterior/injection resampling;
- one event supplies essentially the entire result without a physically clear
  and PE-robust explanation;
- the released-model screen has \(|\Delta S|<2\) and simulations show little
  prospective power.

## Full-catalog investment gate

The five-event vertical slice is an integration test. Before processing the
full O4 event posterior catalog, O4-sized detected mock catalogs generated under
each released model must pass the bidirectional gate in
`config/detected_power_gate.toml`. A failure stops the two-model paper and does
not authorize weaker thresholds or additional model families.

## Prospective requirement

Before the official GWTC-6 population products are available, a timestamped
O4c/GWTC-6 forecast must freeze models, priors, code, predictive arrays, scoring
rules, and sensitivity scenarios. Public low-latency alerts must not be used to
tune the forecast.
