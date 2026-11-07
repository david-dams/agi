# Loading invariance: findings from the corrected run

Equal general-factor loading constraints measurably worsen the primary nine-indicator CFA beyond the variation seen in the specified equal-loading cluster null. This is evidence against that constrained measurement model. The eight-indicator and one-configuration sensitivities show the same directional deterioration, but estimation boundaries prevent equally strong uncertainty statements in every case. Neither the free nor partial models achieve adequate absolute fit.

The analysis retains the fixed coding-plus-academic residual covariance specification, free cohort residual covariances/variances and factor variances, and a GPQA marker. It compares source release cohorts 2025H1, 2025H2 and 2026H1 in the frozen July 2026 snapshot. No scalar invariance, latent mean or historical evaluation-date trajectory is fitted.

## Bootstrap Delta CFI

Delta CFI = equal minus free CFI. All cases use 2,000 attempted matched named-base cluster draws.

| Sample | Battery | Observed Delta CFI | Admissible | 95% admissible-fit range | Finite-fit sensitivity range, including boundaries |
|---|---|---:|---:|---|---|
| All configurations | Nine | −.0489 | 1,805/2,000 | [−.0771, −.0315] | [−.0771, −.0312] |
| All configurations | Eight | −.0318 | 1,659/2,000 | Withheld | [−.0603, −.0192] |
| One per named base | Nine | −.0512 | 1,478/2,000 | Withheld | [−.0828, −.0320] |
| One per named base | Eight | −.0329 | 1,048/2,000 | Withheld | [−.0641, −.0199] |

Intervals are withheld below the pre-set 90% admissibility threshold. Even the primary case only narrowly clears that threshold. Finite-fit sensitivity ranges are not substitutes for admissible-fit confidence statements. The complete distributions and statuses are in distributions.npz, with a histogram comparison in delta_cfi_distributions.png.

## Null calibration with within-base dependence

There are 500 matched null cluster draws per case. Each cohort's score vectors are linearly whitened and recolored so their covariance exactly equals its fitted equal-loading covariance, then complete named-base clusters are resampled. This preserves transformed empirical within-cluster dependence; it does not preserve original score margins/floors or prove that named bases capture broader ancestry.

For the primary nine-indicator case, 481/500 null fits are admissible and none produces deterioration as large as observed. The plus-one conditional calibrated p-value is .0021. Counting every inadmissible null fit as an exceedance gives .0399; counting none gives .0020. These bounds address fit-status uncertainty, not all model assumptions. The null's finite-fit 95th percentile deterioration is .0116 versus observed .0489. The likelihood-ratio statistic gives the same qualitative result: observed Delta chi-square 197.2 versus a null 95th percentile of 48.9.

The sensitivity cases have no null exceedances among any finite fits, but their boundary rates materially weaken calibration. Worst-case p upper bounds are .2156 for all/eight, .0938 for selected/nine and .5928 for selected/eight. Admissible-only null p-values are withheld below 90% admissibility. The selected/nine case clears the null-fit threshold but its worst-case p range crosses .05. We therefore do not claim uniformly robust rejection across all four cases. Five hundred null draws limit Monte Carlo resolution; upper exceedance-rate bounds are exported.

Recoloring imposes the entire equal-loading residual model and removes the observed covariance misspecification. The calibration is conditional on that model. It cannot distinguish noninvariance of g itself from an inadequate residual structure or other measurement artifacts.

## Loading diagnostics

All cohort-specific raw and standardized loadings, intervals and three pairwise cohort differences are exported. The report gives the full primary standardized-loading table.

- CritPt is the largest single-release contributor with all nine indicators: freeing its loading reduces chi-square by 76.4 (68.1 in the one-base sensitivity).
- Without CritPt, HLE is the largest: reductions of 52.3 and 38.6 respectively. HLE is also second in both nine-indicator samples.
- In the primary case, first-to-last GPQA-relative raw-loading differences for HLE, CritPt and Terminal-Bench Hard have nominal simultaneous bands excluding zero. These bands cover all benchmark/contrast diagnostics within that case, not all four overlapping robustness cases.

For illustration, primary standardized HLE loadings are .671, .802 and .890; CritPt loadings are .638, .611 and .663. The much larger CritPt raw-loading change reflects scaling and changing cohort factor/residual variances. Standardized loading changes alone do not test metric invariance. Raw loadings are relative to the chosen GPQA marker; alternate IFBench-anchored point loadings and a GPQA-release diagnostic are provided. Single-release gains are not additive or unique causal contributions.

## Partial invariance

Before the new fits, the candidate set was fixed to freeing AA-LCR, CritPt, or both, motivated by previously documented floors. It was not chosen from the new diagnostic ranking. This is transparent exploratory specification, not independent preregistration.

None passes either the descriptive relative screen (Delta CFI >= −.01 versus free loadings) or the separate absolute screen (CFI >= .95 and multi-group RMSEA <= .08). For all/nine, freeing both raises CFI from .8016 to .8251, still below free CFI .8504 and with RMSEA .250. For all/eight, freeing AA-LCR gives CFI .8919 versus free .9209. The selected-sample results are similar.

Other small release sets were not selected adaptively from the contribution rankings. Partial fits have no dedicated cluster/null calibration or held-out validation. Failure of this candidate set does not establish failure of every possible partial specification.

## Absolute fit, numerical validation and interpretation

The free-loading multi-group model has CFI .8504 / .9209 and RMSEA .2506 / .2038 for the primary nine/eight samples. Across cohorts, free-model RMSEA remains .234–.265 with CritPt and .167–.225 without CritPt. Improved relative fit therefore does not establish an adequate measurement model.

Validation identified a near-singular model-covariance likelihood problem in an initial numerical run. All draws were repeated using Cholesky likelihood evaluation, a numerical covariance-domain guard and projected-gradient convergence checks. The final run has no failed paired fits: 2,010/8,000 bootstrap case-pairs and 468/2,000 null case-pairs reach parameter boundaries. These boundary pairs are retained as labeled sensitivity outputs, not silently accepted as admissible. No sample covariance regularization was used. All 36 repository tests pass; source/code hashes, draw counts and distributions were checked.

The defensible conclusion is that equal loadings are a poor restriction for this exploratory benchmark measurement model, with strongest calibrated evidence in the primary nine-indicator analysis. It is not evidence that underlying general intelligence grew, weakened or changed its nature. Score floors, model/configuration composition, evaluation differences and residual misspecification remain alternative explanations.

[Full report](README.md) · [Delta CFI distributions](delta_cfi_distributions.png) · [Loading differences](loading_differences.png) · [Partial invariance](partial_invariance.png)
