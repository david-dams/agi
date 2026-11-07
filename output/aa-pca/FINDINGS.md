# PCA direction stability: findings

A strong, broadly positive dominant performance direction exists in every release cohort, without imposing CFA residual assumptions. Adjacent cohorts have fairly similar directions. The first-to-last direction is less stable: it rotates by about 31 degrees with CritPt and 21 degrees without CritPt. Selecting one configuration per named base leaves that pattern essentially unchanged. Thus the data support persistence of a broad dominant performance axis, but not an unchanged weighting of benchmarks in the chosen common metric.

## Fixed metric and matching

All benchmark columns use one pooled mean and sample standard deviation calculated from the 387 complete configurations spanning 2025H1, 2025H2 and 2026H1. Those scales are frozen for both samples, both CritPt batteries and all bootstrap draws. Each cohort is centered before covariance PCA; there is no cohort-specific rescaling and cohort means do not drive the PCs. The one-configuration sample retains 49, 127 and 103 models using the existing outcome-independent effort rule.

The directions are unit eigenvectors in those common units. Conventional covariance loadings multiply each eigenvector by sqrt(lambda1), which leaves its direction unchanged. Score-variable correlations are exported separately and are not treated as equivalent common-unit direction vectors.

## Cohort comparisons: all configurations

Parentheses show nominal 95% matched cluster-bootstrap percentile ranges.

| Battery | Cohort pair | Tucker congruence = cosine | Axis angle |
|---|---|---:|---:|
| Nine | 2025H1 / 2025H2 | .965 (.922–.985) | 15.2° (10.0–22.8°) |
| Nine | 2025H2 / 2026H1 | .932 (.860–.976) | 21.2° (12.5–30.6°) |
| Nine | 2025H1 / 2026H1 | .859 (.776–.920) | 30.8° (23.0–39.1°) |
| Eight | 2025H1 / 2025H2 | .970 (.929–.988) | 14.0° (9.0–21.7°) |
| Eight | 2025H2 / 2026H1 | .973 (.944–.988) | 13.3° (8.9–19.3°) |
| Eight | 2025H1 / 2026H1 | .931 (.886–.956) | 21.3° (17.0–27.6°) |

Tucker congruence and cosine are identical here: both are the uncentered normalized dot product. Angle is the corresponding arccosine. These are equivalent descriptions, not three independent confirmations. PC signs are arbitrary; axes are compared after sign alignment.

For the one-configuration sample, first-to-last congruence is .863 (.779–.922), angle 30.3° (22.7–38.8°), with CritPt; without CritPt it is .936 (.888–.961), angle 20.6° (16.1–27.4°). All pairwise results are in README.md and similarities.csv.

## What rotates

All point-estimate PC1 coefficients are positive. The primary nine-indicator unit coefficient for CritPt rises from .038 to .135 to .403 across the three cohorts; HLE rises from .134 to .272 to .402. GPQA falls from .466 to .383 to .305. Without CritPt, HLE still rises from .133 to .271 to .420, and Terminal-Bench Hard rises from .228 to .332 to .391. These coefficient shifts describe variance-weighted geometry, not causal benchmark contributions or changes in latent intelligence.

CritPt therefore accounts for an important part of the first-to-last rotation, but excluding it does not make the direction identical. A benchmark gaining within-cohort variance as a floor recedes can gain covariance-PCA weight even without an equivalent change in its standardized correlation with an underlying factor. The pooled metric, battery and sampled model population are part of the estimand.

## Direction and variance explained are different

| Sample | Battery | 2025H1 | 2025H2 | 2026H1 |
|---|---|---:|---:|---:|
| All | Nine | 76.9% | 74.3% | 72.4% |
| All | Eight | 77.0% | 75.7% | 76.8% |
| One per base | Nine | 76.3% | 76.7% | 75.4% |
| One per base | Eight | 76.4% | 78.0% | 80.8% |

Every first-to-last variance-share difference has a nominal bootstrap range containing zero. For all configurations, the nine-indicator difference is −4.5 percentage points (−10.9 to +2.8); the eight-indicator difference is −0.3 points (−7.2 to +7.1). Similar variance share can coexist with a rotated direction. These PCA covariance variance shares are not the earlier CFA mean squared standardized g loadings and should not be compared as the same statistic.

## Admissibility and spectral diagnostics

All 2,000 matched named-base cluster draws are admissible for every cohort, battery, sample and pair: 24,000/24,000 cohort PCAs and 24,000/24,000 pair comparisons. There are no optimizer parameters or residual-variance boundaries in PCA. Full-rank covariance is not required, although all observed point covariance matrices are full rank.

Point PC1–PC2 relative gaps are .840–.921, so a clear leading eigenvector exists. No bootstrap draw has a near tie under the diagnostic relative-gap threshold of .1. The 95th percentile bootstrap angular perturbation around each cohort's own estimated direction is roughly 5–9 degrees, depending on the case. These diagnostics distinguish sampling variation in a separated axis from arbitrary switching between nearly tied components; they are not formal tests for between-cohort equality.

## Limits and validation

Bootstrap ranges are nominal conditional uncertainty summaries. Angles are positive under sampling noise even for identical population axes, so an angle range excluding zero is not a calibrated rejection of equality. Congruence can be biased downward and angles upward; bootstrap means and bias are exported. No directional equality test, pre-specified equivalence margin, construct-identity test or null calibration was performed.

Directional persistence does not imply unchanged full covariance, formal CFA loading invariance, scalar invariance or an identical latent construct. The primary nine-indicator first-to-last rotation is substantial enough that we should not describe the coefficient vector as fixed. All results remain conditional on pooled scaling, benchmark selection, release-cohort composition, the limited named-base clustering and the archived evaluation scores. The global scaling reference is fixed rather than re-estimated in each draw; item-level and protocol uncertainty are not represented.

All 39 repository tests pass. Source and code hashes, 2,000-draw dimensions, sign/scalar invariance, common-unit covariance PCA, top-eigenvalue ties and bootstrap status counts were checked. No sample covariance regularization or CFA fitter was used. Plots render from saved outputs without refitting.

[Full numerical report](README.md) · [Direction and variance comparisons](pca_comparisons.png) · [PC1 weights](pca_weights.png)
