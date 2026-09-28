# Statistical conventions

## Primary estimand

The primary score conditions on the number of detections in each run and tests
population **shape**. For event posterior rows \(\theta_i^k\) obtained under PE
prior \(\pi_i\), let \(q_i^k\) be the normalized probability weight carried by
each stored row. Then

\[
\mathcal L_i(\Lambda) \propto
\sum_k q_i^k
\frac{p(\theta_i^k\mid\Lambda)}{\pi_i(\theta_i^k)}.
\]

For an equal-weight posterior product, \(q_i^k=1/K_i\), recovering the usual
sample mean. PE row weights and population importance ratios are distinct
objects and must be audited separately.

For run-specific detection efficiency \(\xi_r(\Lambda)\),

\[
\log \mathcal L_{\rm cat}(\Lambda)
= \sum_i \log \mathcal L_i(\Lambda)
- \sum_r N_r\log\xi_r(\Lambda).
\]

For frozen training-catalog hyperposterior draws \(\Lambda_j\) with normalized
weights \(w_j\),

\[
S_M = \log\sum_j w_j\,\mathcal L_{\rm cat}(\Lambda_j).
\]

The code carries all of these calculations in log space.

## Selection estimator contract

A processed `SelectionCampaign` contains only found injections. For each found
injection \(j\), `log_base_weight[j]` must already contain the released
normalization and any mixture/run weight that does not depend on the population
model. The estimator is

\[
\widehat\xi_r(\Lambda)=
\sum_{j\in\mathrm{found},r}
\exp\left[
  \log w^{\rm base}_j
  + \log p(\theta_j\mid\Lambda)
  - \log p_{\rm draw}(\theta_j)
\right].
\]

The statistical core intentionally does not guess `log_base_weight`. Large
campaigns may be evaluated in bounded chunks, but a chunk is never treated as
an independently normalized injection set.

## Event contract

A processed `EventPosterior` must contain posterior arrays, the exact
`log_pe_prior` evaluated in the same coordinates, and explicit normalized row
weights when the selected public product is not equal weight. Constants
independent of the population model may be omitted, but this omission must be
identical for every model compared on the same event.

## Joint and prequential scores

The sequential implementation updates hyperposterior weights after every event.
Its cumulative score must equal the joint catalog score to a mixed absolute and
relative numerical tolerance. A naive sum of independently marginalized event
scores is not allowed because events share the same hyperparameters.

## Score-difference Monte Carlo control near zero

A scientifically valid result may be \(\Delta S\simeq0\). Fractional uncertainty
is undefined in that limit, so the comparison gate always requires a frozen
absolute Monte Carlo precision and applies the fractional criterion only when
\(|\Delta S|\) is larger than that absolute numerical scale. A stable null result
is therefore not mislabeled as a computational failure.

## Numerical diagnostics

Every production evaluation must report:

- event importance-sampling ESS for every hyperposterior draw;
- PE posterior-row ESS when source rows are unequally weighted;
- selection importance-sampling ESS for every run and hyperposterior draw;
- hyperposterior ESS after every sequential event;
- joint/prequential discrepancy and comparison tolerance;
- finite-value and support failures;
- absolute and, when applicable, fractional resampling uncertainty on score
  differences.
