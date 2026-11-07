# AA general-factor loading invariance study

This is a covariance-only, exploratory multi-group CFA using the fixed coding-plus-academic residual specification. Delta CFI is equal-loading CFI minus free-loading CFI: negative values indicate relative deterioration. Absolute fit is evaluated separately. The same named-base cluster draws are matched across both batteries and both configuration samples.

2000 cluster-bootstrap draws and 500 covariance-null cluster draws were attempted for every case. Residual covariance blocks and variances, and factor variances, remain free by cohort. GPQA is the primary loading-scale marker. No means or scalar invariance constraints are fitted.

## Fit deterioration and cluster uncertainty

| Sample | Battery | Free CFI | Equal CFI | Delta CFI | Admissible / attempted | 95% admissible range | All finite-fit 95% sensitivity range |
|---|---|---:|---:|---:|---:|---|---|
| all | nine | 0.8504 | 0.8016 | -0.0489 | 1805/2000 | [-0.0771, -0.0315] | [-0.0771, -0.0312] |
| all | eight | 0.9209 | 0.8891 | -0.0318 | 1659/2000 | withheld | [-0.0603, -0.0192] |
| selected | nine | 0.8457 | 0.7946 | -0.0512 | 1478/2000 | withheld | [-0.0828, -0.0320] |
| selected | eight | 0.9230 | 0.8901 | -0.0329 | 1048/2000 | withheld | [-0.0641, -0.0199] |

Admissible ranges are withheld below 90% admissibility. Finite-fit sensitivity ranges include boundary fits and are deliberately labeled separately; they are not calibrated confidence intervals. Boundary filtering can select the distribution even when the threshold is met. A bootstrap distribution around observed data measures estimator variation, not a null hypothesis test.

## Null-calibrated comparison

| Sample | Battery | Null statistic | Admissible / attempted | Calibrated p (admissible) | p including finite boundaries | Worst-case p range for inadmissible draws | Null finite 95th percentile |
|---|---|---|---:|---:|---:|---|---:|
| all | nine | deterioration_cfi | 481/500 | 0.0021 | 0.0020 | [0.0020, 0.0399] | 0.0116 |
| all | nine | delta_chi2 | 481/500 | 0.0021 | 0.0020 | [0.0020, 0.0399] | 48.8807 |
| all | eight | deterioration_cfi | 393/500 | withheld | 0.0020 | [0.0020, 0.2156] | 0.0106 |
| all | eight | delta_chi2 | 393/500 | withheld | 0.0020 | [0.0020, 0.2156] | 44.0417 |
| selected | nine | deterioration_cfi | 454/500 | 0.0022 | 0.0020 | [0.0020, 0.0938] | 0.0102 |
| selected | nine | delta_chi2 | 454/500 | 0.0022 | 0.0020 | [0.0020, 0.0938] | 40.2833 |
| selected | eight | deterioration_cfi | 204/500 | withheld | 0.0020 | [0.0020, 0.5928] | 0.0094 |
| selected | eight | delta_chi2 | 204/500 | withheld | 0.0020 | [0.0020, 0.5928] | 34.7498 |

For each case/cohort, center and whiten its empirical score vectors and recolor them to the fitted equal-loading covariance. The transformed original sample exactly matches that null covariance. Then resample complete named-base clusters using the same global draws across cases. This retains transformed empirical within-family dependence, rather than inventing independent Gaussian observations. It does not preserve original marginal bounds, floor rates or numerical within-family correlations. Most named-base clusters are singletons, and broader model ancestry remains unresolved.

The null is the entire fitted equal-loading covariance model, including the selected residual structure. Recoloring removes the original covariance misspecification. Rejection can therefore be affected by residual-model misspecification and cannot isolate a change in the latent general factor. Reported null p-values use a plus-one correction; with 500 simulations their finest resolution is about .002. Monte Carlo upper exceedance-rate bounds are in null_tests.csv. Worst-case ranges count every inadmissible null fit as either exceeding or not exceeding the observed statistic.

## Loading diagnostics

Raw loadings are GPQA-relative coefficients in common pooled score units. Standardized loadings also depend on cohort factor and residual variances and can differ under metric invariance. GPQA is fixed at one in the raw diagnostics, so its noninvariance cannot be assessed from that coefficient. The exhaustive single-release diagnostic uses IFBench as anchor when freeing GPQA. Alternate IFBench-anchored point loadings are exported; no benchmark is assumed intrinsically invariant.

Primary all-configuration, nine-indicator standardized loadings (point estimate and nominal 95% admissible-fit range):

| Benchmark | 2025H1 | 2025H2 | 2026H1 |
|---|---|---|---|
| gpqa | 0.859 [0.7628, 0.9329] | 0.911 [0.8751, 0.9410] | 0.910 [0.8607, 0.9498] |
| hle | 0.671 [0.4745, 0.8490] | 0.802 [0.7395, 0.8567] | 0.890 [0.8573, 0.9173] |
| omniscience | 0.927 [0.8625, 0.9676] | 0.846 [0.7605, 0.8999] | 0.823 [0.7175, 0.8956] |
| tau2 | 0.789 [0.6336, 0.8886] | 0.749 [0.6524, 0.8239] | 0.638 [0.5205, 0.7464] |
| ifbench | 0.808 [0.6905, 0.9005] | 0.775 [0.6982, 0.8409] | 0.749 [0.6563, 0.8222] |
| lcr | 0.812 [0.6915, 0.8992] | 0.877 [0.8367, 0.9114] | 0.918 [0.8876, 0.9426] |
| scicode | 0.883 [0.7996, 0.9413] | 0.932 [0.8974, 0.9560] | 0.915 [0.8673, 0.9498] |
| critpt | 0.638 [0.5182, 0.7845] | 0.611 [0.5302, 0.6918] | 0.663 [0.6014, 0.7192] |
| terminalbenchHard | 0.894 [0.8141, 0.9484] | 0.890 [0.8395, 0.9238] | 0.929 [0.8962, 0.9551] |

| Sample | Battery | Largest single-release contributors (chi-square gain) |
|---|---|---|
| all | nine | critpt (76.4); hle (46.0); lcr (15.6) |
| all | eight | hle (52.3); terminalbenchHard (22.6); lcr (11.1) |
| selected | nine | critpt (68.1); hle (33.5); terminalbenchHard (16.6) |
| selected | eight | hle (38.6); terminalbenchHard (21.9); lcr (11.3) |

These gains are exhaustive exploratory attribution diagnostics, not independent tests or unique causal contributions; they are not additive. Their ranking was not used to select partial-invariance specifications.

Loading intervals and all three pairwise cohort differences are in loading_intervals.csv and loading_differences.csv. Within each case/scale, simultaneous bands use the bootstrap maximum standardized deviation across all benchmark × contrast diagnostics, scaled by fixed bootstrap standard errors and excluding the fixed marker coefficient. They are nominal bootstrap bands, not calibrated across the four overlapping cases. As with marginal intervals, simultaneous bands are withheld below 90% free-model admissibility.

| Sample | Battery | First-to-last raw-loading differences with nominal simultaneous bands excluding zero |
|---|---|---|
| all | nine | hle: +0.854 [+0.364, +1.343]; critpt: +0.956 [+0.274, +1.639]; terminalbenchHard: +0.535 [+0.045, +1.025] |
| all | eight | bands withheld |
| selected | nine | bands withheld |
| selected | eight | bands withheld |

## Partial invariance: fixed candidate set

Candidates release AA-LCR, CritPt, or both, where present. They were fixed before these fits because prior audits documented substantial floors. This uses prior observations from the same dataset and is not independent confirmatory preregistration. No candidate was chosen from the new contribution ranking. Partial fits are point-fit diagnostics; they have not received their own cluster-bootstrap/null calibration or out-of-sample validation.

| Sample | Battery | Freed loadings | CFI | Multi-group RMSEA | Delta CFI vs free | Relative screen | Absolute screen | Boundary |
|---|---|---|---:|---:|---:|---|---|---|
| all | nine | lcr | 0.8052 | 0.2607 | -0.0452 | False | False | False |
| all | nine | critpt | 0.8216 | 0.2495 | -0.0288 | False | False | False |
| all | nine | critpt+lcr | 0.8251 | 0.2501 | -0.0254 | False | False | False |
| all | eight | lcr | 0.8919 | 0.2131 | -0.0290 | False | False | False |
| selected | nine | lcr | 0.7988 | 0.2813 | -0.0469 | False | False | False |
| selected | nine | critpt | 0.8165 | 0.2687 | -0.0292 | False | False | False |
| selected | nine | critpt+lcr | 0.8207 | 0.2689 | -0.0251 | False | False | False |
| selected | eight | lcr | 0.8937 | 0.2229 | -0.0293 | False | False | False |

The descriptive relative screen is Delta CFI >= −.01. The separate absolute screen requires CFI >= .95 and multi-group RMSEA <= .08. These conventional screens are not universal calibrated cutoffs for bounded, clustered benchmark scores. Multi-group RMSEA uses the average group N−1 convention. Cohort-specific free-model RMSEA and residual RMS are in absolute_fit_by_cohort.csv. Better relative fit does not make an inadequate absolute model adequate.

## Interpretation and limitations

The estimand is stability of benchmark-to-factor loading relationships across release cohorts in a frozen July 2026 snapshot. Evidence against equal loadings concerns this measurement model. It does not establish that the underlying general capability changed, grew, weakened or acquired new dimensions. Residual misspecification, differing floors, model/configuration composition and evaluation conditions are alternative explanations. Scalar invariance, latent capability means and item-level measurement error remain untested.

fit_problems.csv records every boundary or failed fit, including whether the free model itself was admissible. distributions.npz stores delta-CFI/chi-square draws, loading draws and statuses without pickle. draws.jsonl retains each completed matched draw. gradient_diagnostics.csv exposes convergence gradients; optimizer convergence alone is not proof of a well-determined model. The finite-boundary analyses and conservative failure bounds are necessary sensitivity checks, not substitutes for valid interior fits.

Numerical validation found that an earlier inverse/log-determinant calculation could mis-evaluate near-singular model covariances. The final run uses Cholesky likelihood calculations, rejects numerically singular proposed model covariances (without regularizing sample covariances), and requires projected optimizer gradients below .1. All 2,000 bootstrap and 500 null draws were repeated with the corrected fitter. This numerical guard does not make boundary estimates statistically admissible.

The tested partial candidate set is deliberately limited; its failure does not prove that no other small set of releases could improve relative fit. Selecting such a set from these same diagnostic rankings would require separate validation.

## Reproduction

`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run aa_invariance_study.py --bootstrap 2000 --null 500 --workers 4`

`uv run aa_invariance_report.py`

Inputs, analysis code and fixed specification are hashed in metadata.json. Figures render from saved outputs; no refits are needed.
