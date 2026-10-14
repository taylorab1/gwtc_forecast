# Matched models: equations, assumptions and implementation

This is a new candidate prescription, not a claim to reproduce an LVK released model. A comparison of unrelated released fits remains a whole-model comparison, not an ablation of one feature.

## Primary mass

Let x = log(m/m_b). The unnormalized smoothly bending continuum is

\[
C_*(m)=\exp[-\alpha_L x-(\alpha_H-\alpha_L)w\log(1+e^{x/w})].
\]

At masses well below/above the bend it approaches slopes -alpha_L/-alpha_H. Normalize in **dm**, not d log m, on the configured domain. The implementation uses Gauss-Legendre quadrature in log mass including its Jacobian, and tests normalization against independent adaptive integration.

With truncated, separately normalized Gaussians G_L and G_H:

\[
p_0(m)=(1-f_L)C(m)+f_LG_L(m),\qquad
p_1(m)=(1-f_H)p_0(m)+f_HG_H(m).
\]

At f_H=0 the two densities agree exactly, a tested structural check. A nonzero f_H denotes an excess component; it does not imply a local maximum of the total density. The shared continuum is allowed to bend so that a Gaussian is not automatically rewarded for compensating a rigid power law.

`populations/matched_mass.py` implements this family. The teaching grid fixes some parameters to make independent integration feasible. Grid weights are a finite discrete prior; use grid refinement before using it as a continuous-prior approximation. The current toy result makes no such approximation claim.

## Full BBH candidate

The real-study entry point uses the normalized density

\[
p(\theta\mid\Lambda)=p(m_1)\,p(q\mid m_1)\,p(z)\,p(a_1)p(a_2)\,p(c_1,c_2),
\]

in coordinates (source-frame m1, q, z, a1, a2, c1, c2), with c=cos(tilt). For fixed primary mass, q lies between m2_min/m1 and 1 and follows a normalized q^beta distribution; beta=-1 is handled with its logarithmic normalization.

The redshift shape is proportional to (dV_c/dz)(1+z)^(kappa-1), including source-time dilation. The implementation uses fixed flat-LambdaCDM geometry. Its overall H0 factor cancels in the normalized shape, but **H0 does not disappear from converting detector-frame masses and luminosity distance to source coordinates**. Record the actual conversion cosmology separately.

Spin magnitudes are independent beta distributions with common mean and concentration. Tilt cosines use a binary-level mixture

\[
p(c_1,c_2)=(1-\zeta)/4+\zeta T(c_1;\sigma_t)T(c_2;\sigma_t),
\]

where T is a normalized truncated normal centered at alignment. This is not the product of two independently mixed tilt distributions. Tests verify its marginal normalization and joint construction.

These factorization assumptions intentionally limit the first paper. A mass-spin correlation can masquerade as a mass preference through selection. Predeclare a small shared-model stress test using training evidence and physically motivated simulation; do not claim a physical peak solely because this factorized alternative wins.

## Development priors and support

`config/matched_bbh_priors.json` is the authoritative list of current candidate values, distributions and fixed parameters. It is marked `development_candidate_not_frozen_for_real_data`. Values include source-primary support 5–160 solar masses, a secondary-mass lower bound of 3, z<=3, a shared low feature, and a 20–50 solar-mass high-component location. These are starting values, not a universal BBH definition or an approved astrophysical prior.

Before freezing, verify training support, normalization over prior extremes, prior-predictive distributions and sensitivity to the common continuum/taper. A hard support edge should not cause an informative held-out event to be removed. Population support failure may be a scientific inadequacy; numerical undercoverage must first be excluded. Do not silently change support after viewing the score.

A full matched fit requires new through-O3 inference with these models. The inherited PowerLawPeak/PowerlawDipBreak posterior archives are not compatible by renaming their columns. See `REAL_DATA_WORKFLOW.md` for qualification and the optional Bilby adapter.
