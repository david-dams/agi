# AA release-cohort g analysis

Frozen July 6, 2026 snapshot; 387 complete configurations in 2025H1–2026H1; 279 base-setting clusters; 279 selected configurations. 1000 matched global cluster bootstrap draws.

| Sample | Battery | Cohort | N | g variance | 95% cluster range | CFI | RMSEA |
|---|---|---|---:|---:|---|---:|---:|
| all | nine | 2025H1 | 59 | 0.654 | [0.572, 0.718] (1000/1000) | 0.794 | 0.262 |
| all | nine | 2025H2 | 176 | 0.683 | [0.638, 0.724] (1000/1000) | 0.810 | 0.260 |
| all | nine | 2026H1 | 152 | 0.692 | [0.656, 0.730] (1000/1000) | 0.853 | 0.233 |
| all | eight | 2025H1 | 59 | 0.685 | [0.606, 0.747] (1000/1000) | 0.851 | 0.242 |
| all | eight | 2025H2 | 176 | 0.716 | [0.669, 0.759] (1000/1000) | 0.876 | 0.227 |
| all | eight | 2026H1 | 152 | 0.722 | [0.682, 0.764] (1000/1000) | 0.920 | 0.186 |
| selected | nine | 2025H1 | 49 | 0.668 | [0.580, 0.737] (1000/1000) | 0.766 | 0.285 |
| selected | nine | 2025H2 | 127 | 0.718 | [0.671, 0.758] (1000/1000) | 0.791 | 0.289 |
| selected | nine | 2026H1 | 103 | 0.735 | [0.701, 0.774] (1000/1000) | 0.855 | 0.251 |
| selected | eight | 2025H1 | 49 | 0.693 | [0.603, 0.760] (1000/1000) | 0.846 | 0.247 |
| selected | eight | 2025H2 | 127 | 0.747 | [0.700, 0.786] (1000/1000) | 0.860 | 0.254 |
| selected | eight | 2026H1 | 103 | 0.769 | [0.729, 0.811] (1000/1000) | 0.920 | 0.202 |

## Direct cohort differences

| Sample | Battery | Contrast | Difference | 95% cluster range |
|---|---|---|---:|---|
| all | nine | 2025H2 minus 2025H1 | +0.029 | [-0.049, 0.114] |
| all | eight | 2025H2 minus 2025H1 | +0.031 | [-0.045, 0.115] |
| all | nine-minus-eight | 2025H2 minus 2025H1 | -0.003 | [-0.025, 0.015] |
| all | nine | 2026H1 minus 2025H2 | +0.009 | [-0.047, 0.075] |
| all | eight | 2026H1 minus 2025H2 | +0.005 | [-0.055, 0.075] |
| all | nine-minus-eight | 2026H1 minus 2025H2 | +0.004 | [-0.010, 0.017] |
| all | nine | 2026H1 minus 2025H1 | +0.038 | [-0.036, 0.125] |
| all | eight | 2026H1 minus 2025H1 | +0.037 | [-0.039, 0.126] |
| all | nine-minus-eight | 2026H1 minus 2025H1 | +0.001 | [-0.019, 0.017] |
| selected | nine | 2025H2 minus 2025H1 | +0.051 | [-0.027, 0.145] |
| selected | eight | 2025H2 minus 2025H1 | +0.053 | [-0.024, 0.144] |
| selected | nine-minus-eight | 2025H2 minus 2025H1 | -0.003 | [-0.027, 0.017] |
| selected | nine | 2026H1 minus 2025H2 | +0.017 | [-0.038, 0.081] |
| selected | eight | 2026H1 minus 2025H2 | +0.023 | [-0.034, 0.086] |
| selected | nine-minus-eight | 2026H1 minus 2025H2 | -0.006 | [-0.020, 0.010] |
| selected | nine | 2026H1 minus 2025H1 | +0.068 | [-0.010, 0.161] |
| selected | eight | 2026H1 minus 2025H1 | +0.076 | [-0.003, 0.172] |
| selected | nine-minus-eight | 2026H1 minus 2025H1 | -0.008 | [-0.032, 0.012] |

## Equal-loading comparison

Covariance-only multi-group CFA uses pooled units, GPQA marker loading = 1, free cohort factor variances and residual variances; means unconstrained. These approximate Gaussian p-values do not correct family dependence or bounded scores. They are diagnostics, not calibrated hypothesis decisions.

- all/nine: Δχ²=242.02, Δdf=16, approximate p=2.234e-42, ΔCFI=-0.061, boundary=False.
- all/eight: Δχ²=156.54, Δdf=14, approximate p=3.522e-26, ΔCFI=-0.044, boundary=False.
- selected/nine: Δχ²=194.89, Δdf=16, approximate p=8.544e-33, ΔCFI=-0.060, boundary=False.
- selected/eight: Δχ²=124.03, Δdf=14, approximate p=1.021e-19, ΔCFI=-0.043, boundary=False.

## Interpretation limits

g variance is the mean squared standardized one-factor loading; it describes covariance within each cohort, not capability level. A strong g can coexist with poor one-factor fit. CritPt A/B uses exactly matched rows. Cohorts are source release dates, not historical evaluation snapshots. No cross-battery AIC/BIC comparison is made.

Cluster intervals are nominal percentile sensitivity ranges, conditional on base-setting clusters; broader ancestry is unresolved and item uncertainty cannot be estimated from these aggregates. Fewer than 90% admissible draws causes interval withholding. Failed and boundary fits are recorded, not regularized. Loading intervals do not adjust for multiple comparisons. No scalar invariance or capability-mean comparison is claimed.

Configuration selection uses explicit effort labels without benchmark performance. Unspecified reasoning settings rank between medium and low; ranks are an operational rule, not equal compute budgets. Remaining name/version differences and shared training ancestry are not inferred away.

Files: configurations.csv, matrix.csv, fits.csv, loadings.csv, loading_intervals.csv, residuals.csv, intervals.csv, differences.csv, invariance.json, quarters.csv, bootstrap.npz, bootstrap_problems.csv, metadata.json.
