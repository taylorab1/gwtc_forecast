# Statistical conventions and checks

Primary references: Mandel, Farr & Gair (2019), arXiv:1809.02063; Talbot & Golomb (2023), arXiv:2304.06138. Full source locators and literature/design distinctions are in `LITERATURE.md`.

## Event likelihoods, selection and the frozen forecast

Write the event PE prior as pi_i(theta) and its normalized posterior sample weights as w_ij. For one population parameter vector:

\[
A_i(\Lambda)=\sum_j w_{ij}\,p(\theta_{ij}\mid\Lambda)/\pi_i(\theta_{ij}).
\]

This estimates the population-weighted event likelihood divided by the PE evidence. The omitted PE evidence cancels in a model comparison using exactly the same event and PE convention. Raw posterior medians discard information; raw posterior draws without dividing their generating prior also give the wrong calculation.

In coordinates used by the model, evaluate both densities with the same measure. For (m1_source,m2_source)->(m1_source,q), multiply a density by m1_source. For (m1_detector,m2_detector,dL)->(m1_source,q,z), the absolute Jacobian is m1_source*(1+z)^2*|dDL/dz|. `io/coordinates.py` implements these transformations and tests them. They do not reconstruct the released prior or choose a cosmology for you. Marginalizing PE nuisance variables requires checking that their assumed conditional distributions are compatible; merely dropping columns is not a general prior transformation.

Selection efficiency for period r is xi_r(Lambda)=integral p_det,r(theta)p(theta|Lambda)dtheta. For a genuinely single iid injection campaign with N_generated trials and proposal g,

\[
\widehat\xi_r=\frac1{N_{\rm generated}}\sum_{k\in\mathrm{found}}p(\theta_k|\Lambda)/g(\theta_k).
\]

Real releases can combine campaigns and supply additional weights. The general contract stores log proposal density and log base integration weight separately. Do not replace the base weight with 1/N_found or assume every release is a single iid campaign.

For the selected count N_r in each period, the training likelihood is proportional to product_i A_i / product_r xi_r^N_r. Rate and count information are conditioned away. The held-out score is

\[
S_M=\log E_{p(\Lambda|D_T,M)}[\prod_r\prod_{i\in r} A_i(\Lambda)/\xi_r(\Lambda)].
\]

No best-fit plug-in. No division by selection twice. Standard detected GW PE uses the likelihood of the observed data; the selection probability belongs in the catalog denominator, not as an extra factor multiplying each event's likelihood.

## Joint and sequential prediction

Integrate the catalog product over a single shared population, not each event independently. A sequential calculation updates integration weights with each factor and must reproduce the joint score. Thus S(O4a+O4b)=S(O4a)+S(O4b|O4a), generally not S(O4a)+S(O4b) with two independently marginalized forecasts. Frozen models/priors do not forbid this algebraic weight update. Reusing later events for model redesign would be different.

Per-event increments depend on order; the final joint sum does not. Freeze chronological ordering, and use leave-one-out changes to assess influential events without deleting them from the primary catalog. Influence does not imply the event is bad data. A prior/support/model problem should be diagnosed on its merits.

## How the synthetic observation process avoids a subtle bias

The toy first draws true mass from the population, draws an independent Bernoulli detection using the run's toy p_det(m), then measures y=log(m)+Normal(0,sigma). Its observed event is (detected=1,y), so its likelihood contains p_det(m)Normal(y|log m). Its PE posterior is generated conditional on BOTH detection and y with a log-uniform PE prior. Reweighting this PE posterior uses the unchanged standard catalog core and does not add p_det again.

The independent exact reference integrates p(m)p_det(m)Normal(y|log m) and divides by xi. This explicit likelihood is a controlled learning model, not a representation of how LIGO detection/PE actually work. In particular, normal errors in log mass with fixed width do not model real mass-ratio/redshift/spin degeneracies.

Truth masses are saved only for simulation diagnostics. PE samples are generated from the noisy y, not from the known truth. Training uses a different simulated catalog from held-out prediction.

## Numerical validity, calibration and power

Finite-grid node ESS is concentration, not MCMC convergence or sample-size adequacy. Exact joint/sequential agreement does not prove importance-sampling support. Use `predictive_support` to report final contribution concentration and inspect support directly. A collapse onto a few training posterior draws can require a separately justified numerical integration strategy that preserves the target, not a refit of scientific choices to the held-out catalog.

Compare independent resolutions/samples and quantify uncertainty in delta=S_feature-S_continuum with paired resampling when inputs are shared. The included iid event bootstrap rejects weighted/correlated samples; the selection bootstrap includes missed injections in the generated count and rejects unqualified mixed campaigns. These helpers are not a public-release bootstrap recipe. The new paired summary is not a complete automated total-error calculation.

Population-posterior resampling alone omits event-PE and injection uncertainty, including effects on the training fit. A single MC-minus-quadrature discrepancy is not an estimated standard error. For N events, selection errors can accumulate through -N log xi. Assess final score stability, not only per-event ESS floors.

`feature-demo` measures toy forecast discrimination conditional on one training realization. `feature-calibration` independently simulates and fits training in every replicate and saves randomized discrete-prior SBC ranks. Correctly specified SBC is a posterior-calibration reference; it is not an out-of-family adequacy test. Small rank samples cannot certify uniformity. Power and calibration must both be assessed at a scale adequate to their intended claims.
