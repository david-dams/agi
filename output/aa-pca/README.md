# Dominant performance direction across release cohorts

Separate covariance PCA uses a single benchmark metric: pooled means and sample standard deviations of all 387 complete configurations, frozen across all cohorts, both batteries, the selected-base sensitivity and all bootstrap draws. Each cohort is centered before PCA. Thus mean performance changes do not drive these axes; variation and covariance can. This analysis imposes no CFA residual structure.

## Directional comparisons

| Sample | Battery | Cohort pair | Tucker = cosine | Nominal 95% bootstrap range | Angle (degrees) | Nominal 95% range | Admissible / attempted |
|---|---|---|---:|---|---:|---|---:|
| all | nine | 2025H1 / 2025H2 | 0.9652 | [0.9217, 0.9848] | 15.15 | [10.0029, 22.8296] | 2000/2000 |
| all | nine | 2025H2 / 2026H1 | 0.9320 | [0.8603, 0.9764] | 21.24 | [12.4594, 30.6449] | 2000/2000 |
| all | nine | 2025H1 / 2026H1 | 0.8588 | [0.7763, 0.9202] | 30.82 | [23.0397, 39.0746] | 2000/2000 |
| all | eight | 2025H1 / 2025H2 | 0.9703 | [0.9291, 0.9877] | 14.00 | [8.9893, 21.6993] | 2000/2000 |
| all | eight | 2025H2 / 2026H1 | 0.9731 | [0.9436, 0.9880] | 13.32 | [8.8850, 19.3345] | 2000/2000 |
| all | eight | 2025H1 / 2026H1 | 0.9314 | [0.8859, 0.9562] | 21.35 | [17.0243, 27.6377] | 2000/2000 |
| selected | nine | 2025H1 / 2025H2 | 0.9700 | [0.9252, 0.9869] | 14.07 | [9.2676, 22.3034] | 2000/2000 |
| selected | nine | 2025H2 / 2026H1 | 0.9369 | [0.8675, 0.9799] | 20.46 | [11.4973, 29.8342] | 2000/2000 |
| selected | nine | 2025H1 / 2026H1 | 0.8633 | [0.7790, 0.9222] | 30.32 | [22.7435, 38.8296] | 2000/2000 |
| selected | eight | 2025H1 / 2025H2 | 0.9766 | [0.9364, 0.9912] | 12.43 | [7.6102, 20.5438] | 2000/2000 |
| selected | eight | 2025H2 / 2026H1 | 0.9746 | [0.9467, 0.9893] | 12.93 | [8.3719, 18.7967] | 2000/2000 |
| selected | eight | 2025H1 / 2026H1 | 0.9360 | [0.8876, 0.9606] | 20.61 | [16.1297, 27.4316] | 2000/2000 |

Tucker congruence is the uncentered cosine of the coefficient/loading vectors. It is therefore numerically identical to cosine here, and angle is its arccosine; these are not three independent pieces of evidence. PCA axes have arbitrary signs, so comparisons align signs and use the acute axis angle. Covariance loadings (coefficient times sqrt(eigenvalue)) give the same direction. Cohort score-variable correlations are exported separately and are not substituted for common-metric directions.

## Explained variance and spectral separation

| Sample | Battery | Cohort | PC1 variance fraction | Nominal 95% bootstrap range | Relative PC1–PC2 gap | 95th percentile bootstrap angle to own estimate |
|---|---|---|---:|---|---:|---:|
| all | nine | 2025H1 | 0.7690 | [0.7055, 0.8274] | 0.8832 | 9.11° |
| all | nine | 2025H2 | 0.7435 | [0.7036, 0.7797] | 0.9051 | 5.80° |
| all | nine | 2026H1 | 0.7242 | [0.6955, 0.7573] | 0.8465 | 8.91° |
| all | eight | 2025H1 | 0.7704 | [0.7062, 0.8290] | 0.8831 | 9.06° |
| all | eight | 2025H2 | 0.7566 | [0.7140, 0.7943] | 0.9080 | 5.15° |
| all | eight | 2026H1 | 0.7677 | [0.7294, 0.8023] | 0.9153 | 5.48° |
| selected | nine | 2025H1 | 0.7632 | [0.6965, 0.8251] | 0.8769 | 9.22° |
| selected | nine | 2025H2 | 0.7670 | [0.7262, 0.8027] | 0.9109 | 5.81° |
| selected | nine | 2026H1 | 0.7535 | [0.7253, 0.7867] | 0.8403 | 8.55° |
| selected | eight | 2025H1 | 0.7644 | [0.6975, 0.8265] | 0.8768 | 9.18° |
| selected | eight | 2025H2 | 0.7800 | [0.7373, 0.8165] | 0.9192 | 5.11° |
| selected | eight | 2026H1 | 0.8078 | [0.7740, 0.8396] | 0.9208 | 5.16° |

Relative gap is (lambda1 − lambda2)/lambda1. The eigenvalues and covariance ranks are exported. Singular covariance is allowed when PC1 is uniquely separated; PCA does not need CFA-style positive-definite covariance or uniqueness estimates. Numerically tied top eigenvalues are inadmissible. Low but nonzero gaps are tracked as instability diagnostics, not silently discarded.

## Changes in explained variance

| Sample | Battery | Contrast | Difference | Nominal 95% bootstrap range |
|---|---|---|---:|---|
| all | nine | 2025H2 minus 2025H1 | -0.0256 | [-0.0958, 0.0510] |
| all | nine | 2026H1 minus 2025H2 | -0.0193 | [-0.0655, 0.0338] |
| all | nine | 2026H1 minus 2025H1 | -0.0449 | [-0.1092, 0.0280] |
| all | eight | 2025H2 minus 2025H1 | -0.0138 | [-0.0862, 0.0629] |
| all | eight | 2026H1 minus 2025H2 | +0.0111 | [-0.0427, 0.0641] |
| all | eight | 2026H1 minus 2025H1 | -0.0026 | [-0.0723, 0.0708] |
| selected | nine | 2025H2 minus 2025H1 | +0.0038 | [-0.0700, 0.0827] |
| selected | nine | 2026H1 minus 2025H2 | -0.0134 | [-0.0577, 0.0404] |
| selected | nine | 2026H1 minus 2025H1 | -0.0097 | [-0.0752, 0.0652] |
| selected | eight | 2025H2 minus 2025H1 | +0.0156 | [-0.0596, 0.0945] |
| selected | eight | 2026H1 minus 2025H2 | +0.0278 | [-0.0207, 0.0799] |
| selected | eight | 2026H1 minus 2025H1 | +0.0435 | [-0.0271, 0.1168] |

## Uncertainty and interpretation

2000 matched global named-base cluster draws preserve whole observed configuration blocks and cross-case matching. The original one-configuration selection rule is unchanged. There were 24000/24000 admissible cohort PCAs; each pair requires both cohort estimates. Full draw arrays, statuses, per-cohort eigenvalue gaps and angular perturbations are in bootstrap.npz. No covariance regularization is used.

The scale is conditional on this frozen pooled dataset; scale-estimation uncertainty is intentionally not resampled because the target is direction in a fixed coordinate system. Nominal percentile ranges describe resampling variability and are not calibrated equality/equivalence tests. Even identical population axes yield positive estimated angles under sampling noise; ranges excluding zero do not establish directional change. Similarity can be biased downward and angles upward; bootstrap means and point-relative bias are exported.

A close direction means approximately the same weighted performance combination dominates observed covariance in these benchmark units. It does not imply unchanged remaining covariance, equal explained variance, equal benchmark variances, an identical latent construct, or CFA measurement invariance. PCA maximizes variance and is sensitive to the benchmark battery, pooled scaling, floors and sampled model composition. The named-base mapping handles explicit setting variants, not all shared ancestry. Item-level uncertainty and protocol consistency remain unmeasured.

The comparison is retrospective across release cohorts in a July 2026 snapshot, not historical evaluation snapshots. Standardized PC1 scores or means are not used to claim capability growth.

## Reproduction

`OPENBLAS_NUM_THREADS=1 uv run aa_cohort_pca.py --resamples 2000`

`uv run aa_pca_plot.py`

Inputs and code are hash-pinned in metadata.json. standardization.csv defines the common metric; weights.csv contains unit eigenvectors, covariance loadings and score correlations. similarities.csv reports both congruence and cosine, angles, uncertainty and bias; explained_variance.csv, spectra.csv, variance_differences.csv and weight_intervals.csv give supporting diagnostics.
