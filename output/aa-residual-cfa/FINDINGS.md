# Domain residual CFA: findings

Allowing coding and academic/knowledge residual covariance improves fit, but does not establish a time trend or restore equal general-factor loadings across the cohorts.

Two exploratory residual specifications were fitted to the same frozen cohorts and CritPt A/B rows:

1. Coding: SciCode ↔ Terminal-Bench Hard (one free residual covariance).
2. Coding plus academic/knowledge: additionally all three pairwise residual covariances among GPQA, HLE and AA-Omniscience (four free covariances total).

These are freely signed pairwise correlations, not a single positive domain factor or a constraint that every correlation is equal. CritPt measures physics reasoning and is not assigned to coding. The provisional academic block follows the source taxonomy. It is an exploratory modeling choice, not independent confirmation of a discovered domain structure. No extra edges were chosen from residual rankings or modification indices.

## Fit improves; remaining misfit is substantial

CFI without CritPt:

| Cohort | Independent residuals | Coding residual | Coding + academic residuals |
|---|---:|---:|---:|
| 2025H1 | .851 | .888 | .897 |
| 2025H2 | .876 | .883 | .904 |
| 2026H1 | .920 | .922 | .948 |

The expanded model lowers BIC versus independent-residual CFA by 8.8, 23.5 and 20.8 respectively without CritPt, and by 11.8, 19.9 and 16.4 with CritPt. Coding-only covariance lowers BIC in 2025 but slightly raises it in 2026H1. These are within-battery comparisons on matched configurations, not cross-battery comparisons.

For the expanded eight-indicator model, RMSEA remains .225, .224 and .167; observed-minus-implied residual RMS is .059, .053 and .033. Thus residual flexibility improves the covariance approximation but does not deliver uniformly satisfactory fit.

## g strength changes little

| Cohort | Expanded model with CritPt | Expanded model without CritPt |
|---|---:|---:|
| 2025H1 | 66.3% | 69.4% |
| 2025H2 | 68.3% | 71.8% |
| 2026H1 | 69.4% | 72.4% |

The expanded nine-indicator first-to-last increase is +3.1 percentage points, with nominal 95% base-cluster range [−4.5, +11.9]; 920/1,000 joint draws are admissible. Without CritPt, the point increase is +2.9 points, but its interval is withheld because only 895/1,000 joint draws are admissible. The eight-indicator early cohort itself has only 898/1,000 admissible draws.

Coding-only models have first-to-last increases of +3.3 points with CritPt [−4.0, +11.7] and +3.0 points without CritPt [−4.5, +11.8]. Neither establishes an increase. Selecting one configuration per base model leaves substantial bootstrap instability, especially in 2025H1; withheld ranges must not be interpreted as zero uncertainty or evidence for a trend.

## Residuals are not a stable positive domain component

The coding-only fitted SciCode / Terminal-Bench Hard residual correlation is −.73, −.35 and +.21 with CritPt (−.72, −.37 and +.22 without CritPt). Expanded-model estimates are similar. These are conditional point estimates after accounting for g, not raw benchmark correlations; their uncertainty has not been estimated. They do not support assuming a consistently positive shared coding component.

Academic residual correlations are also mixed in sign and differ by cohort; see domain_correlations.csv. They should not be interpreted as a causal decomposition of intelligence.

## Equal-loading constraints still worsen fit

With free cohort-specific domain residual covariance, equal g loadings across cohorts worsen CFI by .049 for nine indicators and .032 for eight. One-configuration results are similar (.051 and .033). Approximate Gaussian likelihood-ratio diagnostics favor free loadings, but are not calibrated for clustering, bounded scores, exploratory specification choice or existing model misspecification. One coding-only selected-sample multi-group comparison reaches a boundary and deserves extra caution.

## Stability and validation

There were 24,000 bootstrap fit cells: 22,630 admissible and 1,370 at parameter boundaries; no optimization/sample-matrix failures were recorded. Admissibility varies across cases. A representative boundary refit reaches the lower Cholesky diagonal bound and has a residual covariance eigenvalue near zero, consistent with an almost singular residual block. Such fits were excluded and their frequency retained, not hidden by covariance regularization. Intervals use only admissible fits and therefore remain conditional, even when the 90% reporting threshold is met.

All 32 repository tests pass, including exact-covariance recovery for a three-task residual block, a negative coding residual, and free/equal-loading comparisons with varying factor variance. Source and code hashes were verified. Figures were rendered from saved tables using cached Matplotlib without repeating fits. Residual-correlation uncertainty and an equal-positive domain-factor model were not fitted.

[Full numerical report](README.md) · [Fit and g figure](domain_cfa.png) · [Residual-correlation figure](domain_correlations.png)
