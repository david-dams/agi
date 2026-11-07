# Shared-PC1 null test: findings

The first-to-last PC1 rotations exceed the variation produced by the specified shared-axis cluster nulls. This holds with and without CritPt, with one configuration per named base, under two covariance-null constructions, and under both exact-size and variable-size cluster resampling. The result concerns changes in observed covariance geometry in a fixed benchmark metric, not changes in latent intelligence or benchmark discrimination.

## Primary result: exact cohort sizes, projected shared-axis covariance

Every null comparison has 2,000 admissible draws. The observed angle is compared with the upper tail of its null distribution; calibrated p-values use a plus-one correction.

| Sample | Battery | First-to-last observed rotation | Null 95th percentile | Null 99th percentile | Exceedances | Pairwise calibrated p | Joint max-angle adjusted p |
|---|---|---:|---:|---:|---:|---:|---:|
| All configurations | Nine | 30.82° | 14.94° | 20.63° | 0/2,000 | .00050 | .00050 |
| All configurations | Eight | 21.35° | 12.41° | 17.06° | 0/2,000 | .00050 | .00100 |
| One per named base | Nine | 30.32° | 15.48° | 21.23° | 0/2,000 | .00050 | .00050 |
| One per named base | Eight | 20.61° | 12.58° | 16.59° | 1/2,000 | .00100 | .00100 |

The omnibus maximum-angle test across all three cohort pairs gives p=.00050 with nine indicators and p=.00100 with eight, for both configuration samples. This tests the complete shared-axis hypothesis, rather than selecting the largest observed pair and treating it as unselected.

For the primary all-configuration first-to-last tests, zero exceedances gives a 95% exact Monte Carlo exceedance-probability interval [0, .00184]. The reported p=.00050 is finite-simulation resolution, not proof of a zero tail probability. These Monte Carlo intervals do not account for uncertainty in the estimated null-generating model.

## Adjacent cohorts: more qualified evidence

For all configurations, primary pairwise p-values for 2025H1/2025H2 are .0315 with CritPt and .0260 without. Max-angle adjustments under the joint null give .0585 and .0395. The one-base sensitivity gives adjusted p=.0930 and .0675, respectively.

For 2025H2/2026H1, primary all-configuration adjusted p-values are .0105 with CritPt and .0490 without. In the selected sample they are .0140 and .0555. Thus the strongest and most robust result is the first-to-last rotation; not every adjacent comparison is clearly distinguishable after adjustment. These are joint-null max-statistic adjustments, not asserted strong familywise control for arbitrary mixtures of true and false pairwise hypotheses. The overlapping battery/sample sensitivities are not separately multiplicity-adjusted.

## What was simulated

One fixed common benchmark metric is reused from the PCA study: pooled mean and sample standard deviation of all 387 complete configurations, with cohort centering. Neither null construction nor simulated samples are restandardized by cohort.

For each case, the common unit axis u is the sample-size-minus-one weighted chordal consensus of the observed PC1 axes: the leading eigenvector of sum((n_g−1) v_g v_g^T). It is estimated once as a plug-in nuisance parameter.

Primary null: for cohort covariance S and P=I−uu^T, use S0=(u^T S u)uu^T+PSP. This eliminates covariance between the common axis and its complement, while allowing the leading eigenvalue and all covariance within the complement to differ by cohort. It preserves total cohort variance but can change individual eigenvalues. It is a fixed-axis block projection, not a Gaussian maximum-likelihood shared-principal-component fit. Every target is checked to have u as its unique leading eigenvector; no eigenvalues are inflated to force that condition.

Sensitivity null: minimally rotate each covariance to align its observed PC1 with u. This preserves every observed eigenvalue and spectral gap, while letting the remaining eigenvectors differ across cohorts. It also preserves within-cohort distances between transformed score vectors. It imposes a particular orthogonal rotation of the remaining covariance, rather than leaving it numerically unchanged.

The projected null uses centered empirical score vectors whitened and recolored to its target covariance. The spectral null uses an orthogonal rotation of those score vectors. The transformed empirical covariance matches its target before resampling. Whole named-base configuration blocks are resampled, retaining their transformed dependence; this is not an independent Gaussian-row simulation.

## Robustness to null and sample-size assumptions

All first-to-last pairwise calibrated p-values across the 16 null-construction × sampling × sample × battery designs lie between .00050 and .00200; their max-angle adjusted values are also in that range. Spectral-null first-to-last null 95th percentiles are 9.9–11.5°, below those of the projected null (12.4–16.1°). Thus preserving the original eigenvalues does not explain away the observed rotations.

The exact-size bootstrap samples whole bases within their cohort/configuration-count strata. It preserves 59/176/152 all-configuration rows and 49/127/103 selected rows, plus the number of bases per cohort. Two singleton strata in 2026H1 hold one four-configuration base and one five-configuration base fixed in this design. This conditions on the observed cluster-size distribution and understates uncertainty about those particular identities.

The global-cluster sensitivity relaxes that conditioning and allows cohort sizes to vary. Its central 95% all-configuration count ranges are 44–75, 150–203 and approximately 125–181. The first-to-last projected-null p-values remain .0010–.0020 across the four cases. These conditional and unconditional-size designs share assumptions about the named-base mapping; neither accounts for unrecorded broader ancestry.

## Spectral and numerical validation

- All 24 target covariance matrices are positive definite and have the common axis as PC1; target relative PC1–PC2 gaps range .780–.921.
- Maximum target eigenvector-equation residual is below 7e−15. Target condition numbers range approximately 78–1,382.
- All 96,000 simulated cohort PCAs are admissible, with no numerical failures or near-tied PC1 directions. Minimum simulated relative gap is .577.
- Exact-size counts are asserted for every draw. Original observed angles match the previous PCA study. Spectral targets preserve eigenvalues and both constructions preserve trace to numerical precision.
- All 43 repository tests pass, including covariance/axis construction, orthogonal rotation, transformed-cluster geometry, exact row counts without splitting configurations, and Monte Carlo p-value handling.

Source/code hashes, target covariance matrices, every simulated PC1 vector, angles/congruence, spectral gaps, explained variance, cohort sizes and statuses are saved. There is no sample covariance regularization or PCA optimizer convergence issue.

## Interpretation and limitations

Under these explicit plug-in null-generating assumptions, named-base sampling variation is insufficient to explain the full-period change in the dominant common-unit performance direction. This is stronger evidence than the earlier descriptive bootstrap angle intervals alone.

It is not evidence that a latent intelligence dimension itself changed, that a benchmark's psychometric discrimination changed, or that a particular training mechanism caused the rotation. Changes in the mix of model families, reasoning configurations, score floors, evaluation conditions and cohort-specific benchmark variances can rotate covariance PC1. The null bootstrap does not adjust these compositional differences away; it asks whether sampling from the chosen common-axis cohort distributions could reproduce the observed angle.

The common-axis hypothesis does not uniquely specify a joint data distribution. The projected and spectral nulls are reasonable constructions, not exhaustive least-favorable nulls. Their nuisance targets are estimated from the same data, then held fixed. Transformations alter marginal score bounds/floors and numerical within-family correlations even though complete transformed clusters are preserved. Calibration is approximate and conditional, not an exact randomization test; repeated-experiment type-I error has not been independently validated. Item uncertainty and broader shared ancestry are absent.

This remains a release-cohort comparison in a frozen July 2026 snapshot. It does not establish historical score trajectories, formal CFA measurement invariance or identity/change of latent constructs.

[Full report](README.md) · [First-to-last null distributions](first_last_nulls.png) · [All pairwise comparisons](pairwise_null_percentiles.png)
