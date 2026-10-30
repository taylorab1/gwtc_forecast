# Matched-feature demonstration (synthetic only)

**No real GW population conclusion and no production authorization.**

Reference held-out feature-minus-continuum log score: 2.688071.
PE/injection estimate, including an independent training fit: 2.604436.
Difference from quadrature: -0.083635 (one realization, not an error bar).

The generating model contains a high-mass component by construction. The sign
of this demonstration is not evidence for a peak in astronomical observations.
See `event_scores.csv`, `conditional_power.json`, and the detailed `report.json`.

## What to explain at the meeting

Explain the model difference, selection correction, why the training posterior
is not a best-fit point, and why independent O4a/O4b scores do not add to the
joint score. Compare saved/reloaded PE contracts to the quadrature reference.
Read node ESS as finite-grid concentration, not sampler convergence.

## Limitations

- One-dimensional synthetic likelihood and explicit toy detection mechanism, not real GW response.
- Finite discrete priors, not qualified continuous population fits.
- One PE/injection realization is a comparison, not a total numerical uncertainty estimate.
- Power is conditional on this realized training catalog and uses both fixed competing posteriors.
- Small demo power counts never qualify a real-data campaign or a publication.
- A Gaussian excess component is not by itself a physical formation channel or even a local maximum.
