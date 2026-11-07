# AA cohort study: first run

The three release cohorts have strong shared benchmark covariance, but this run does not establish a change in general-factor strength over time. Removing CritPt improves one-factor fit without materially changing the primary first-to-last contrast. Equal-loading constraints worsen fit for both batteries, and unrestricted one-factor fit already leaves substantial residual structure.

| Release cohort | Configurations | Nine-indicator g variance | Eight-indicator g variance |
|---|---:|---:|---:|
| 2025H1 | 59 | 65.4% | 68.5% |
| 2025H2 | 176 | 68.3% | 71.6% |
| 2026H1 | 152 | 69.2% | 72.2% |

These are fitted shares of standardized task variance within each cohort, not average capability scores. The cohorts contain different model populations.

## CritPt A/B and uncertainty

Using all configurations and 1,000 matched base-cluster draws, the 2026H1 minus 2025H1 differences are:

- Nine indicators: +3.8 percentage points, nominal 95% cluster range [−3.6, +12.5].
- Eight indicators: +3.7 points, range [−3.9, +12.6].
- Difference between those two changes: +0.1 points, range [−1.9, +1.7].

All adjacent-cohort contrast ranges also include zero. CritPt changes the estimated level of general-factor variance more than it changes the temporal contrast.

The sensitivity selecting one configuration per named base model retains 49, 127 and 103 configurations. Its first-to-last changes are larger: +6.8 points with CritPt [−1.0, +16.1] and +7.6 without CritPt [−0.3, +17.2]. Neither range excludes zero. Selection used effort labels, not observed performance; it is not an equal-compute comparison.

All 12,000 fitted bootstrap cells (1,000 draws × two samples × two batteries × three cohorts) were admissible. No covariance regularization was applied. Broader ancestry beyond named setting variants remains unresolved, so these are conditional sensitivity ranges rather than population confidence guarantees.

## One-factor fit and measurement stability

Nine-indicator CFI rises from .794 to .853, with RMSEA .262 to .233. Removing CritPt gives CFI .851 to .920, but RMSEA remains .242 to .186. Thus shared variance is strong while a strict one-factor covariance model is insufficient; CritPt alone does not explain the residual structure.

The covariance-only multi-group comparison uses common pooled units, GPQA as marker, free cohort factor variances, free residual variances and unconstrained means. Equal unstandardized loadings worsen CFI by .061 with CritPt and .044 without CritPt. The one-configuration sensitivity gives similar deterioration (.060 and .043). Approximate Gaussian likelihood-ratio diagnostics also strongly disfavor equality, but family dependence, bounded scores and existing one-factor misspecification limit formal p-value interpretation. This is evidence against the constrained measurement model, not identification of a grader effect or proof that capability itself changed dimensions.

## Study implication

A defensible public finding is: **a substantial common performance factor appears across these release cohorts; its estimated strength shows a small upward tendency, but the data do not distinguish that tendency from base-model sampling variation, and a stable one-factor measurement model is not supported.** We cannot conclude either that g strengthened or that it stayed constant.

The quarterly estimates are exploratory and nonmonotonic; the smallest quarter has only 17 configurations. No quarterly bootstrap intervals, hierarchical CFA, scalar invariance or capability-level trajectory were run.

[Main figure](cohort_g.png), [loadings](loadings.png), [residual correlations](residuals.png), [floors](floors.png), [full numerical report](README.md).

## Validation and reproduction

Run with the project's dependencies: `uv run aa_cohort_factor.py --resamples 1000 --seed 20261026`.

The initial system-Python run completed the numeric analysis but lacked Matplotlib for plotting. Figures were subsequently rendered from the saved outputs using an already cached Matplotlib build; no factor fits were repeated. Input and analysis-code hashes are pinned in metadata.json. Distribution summaries are computed directly from matrix.csv and configurations.csv. Synthetic covariance tests verify that the equal-loading comparison permits cohort factor variances to differ and detects changed loadings; identity tests retain dated/version parentheticals while merging explicit setting variants.
