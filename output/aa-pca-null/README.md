# Shared dominant-axis null calibration

The null allows each cohort a different covariance spectrum and unrestricted covariance on the orthogonal complement of a shared PC1. It does not impose CFA residual assumptions, common complete covariance matrices or equal latent-factor loadings. All calculations use the earlier frozen pooled benchmark metric, with cohort centering and no restandardization after transformation.

## Null construction

The plug-in common axis is the sample-size-minus-one weighted chordal consensus: the leading eigenvector of sum((n_g−1) v_g v_g^T), where v_g is observed cohort PC1. Axis signs do not affect this estimate.

Primary projected null: for cohort covariance S, common unit axis u and P = I − uu^T, set S0 = (u^T S u) uu^T + P S P. This removes axis/complement covariance but retains unrestricted cohort-specific covariance within the complement. It is the fixed-axis block projection, not a Gaussian maximum-likelihood common-principal-component fit. Every target is checked to be positive definite, to preserve total variance, and to have u as a uniquely leading eigenvector; we do not inflate eigenvalues to force dominance.

Spectrum-preserving sensitivity: minimally rotate each observed covariance so its leading eigenvector equals u. Its entire original spectrum is retained. The remaining eigendirections rotate along with the cohort, and need not agree between cohorts. The choice of null nuisance covariance is therefore explicit and checked against an alternative.

## Cluster simulation and sample sizes

Each of four cases (nine/eight indicators × all/one-per-base) has 2000 draws for each null construction and sampling scheme. The same base identities are drawn across batteries, samples and constructions within a scheme. Four simulations per case assess null-construction and sampling assumptions, rather than multiplying independent evidence.

Primary resampling draws whole named-base clusters within strata defined by their full and selected cohort-count signatures. This preserves the exact cohort row counts and cluster counts without splitting setting variants. Source sizes are 59/176/152 for all configurations and 49/127/103 for the selected sample. These bases do not span cohorts in the current mapping. Two singleton size strata in 2026H1 (one four-setting base and one five-setting base) are fixed under this conditioning, limiting their identity variation. The global-cluster sensitivity resamples whole bases without conditioning and allows cohort sizes to vary; its count ranges are exported.

For the projected null, empirical cohort score vectors are centered, whitened and recolored to their target covariance. For the spectral null, an orthogonal rotation alone suffices and preserves within-cohort row distances. Whole transformed configuration blocks are then resampled. This retains transformed empirical within-base dependence; it does not preserve original benchmark margins, floors, numerical within-family correlations or cross-cohort Euclidean distances. A selected case has its own null transform but retains the original selected identities.

## Primary calibration: exact cohort sizes and projected null

| Sample | Battery | Comparison | Observed angle | Null 95th percentile | Null 99th percentile | Exceedances / admissible | Calibrated p | Max-angle adjusted p |
|---|---|---|---:|---:|---:|---:|---:|---:|
| all | nine | 2025H1 / 2025H2 | 15.15° | 13.60° | 19.33° | 62/2000 | 0.03148 | 0.05847 |
| all | nine | 2025H2 / 2026H1 | 21.24° | 9.93° | 13.01° | 1/2000 | 0.00100 | 0.01049 |
| all | nine | 2025H1 / 2026H1 | 30.82° | 14.94° | 20.63° | 0/2000 | 0.00050 | 0.00050 |
| all | nine | omnibus maximum angle | 30.82° | 15.74° | 21.08° | 0/2000 | 0.00050 | withheld |
| all | eight | 2025H1 / 2025H2 | 14.00° | 12.03° | 16.55° | 51/2000 | 0.02599 | 0.03948 |
| all | eight | 2025H2 / 2026H1 | 13.32° | 7.36° | 9.14° | 1/2000 | 0.00100 | 0.04898 |
| all | eight | 2025H1 / 2026H1 | 21.35° | 12.41° | 17.06° | 0/2000 | 0.00050 | 0.00100 |
| all | eight | omnibus maximum angle | 21.35° | 13.23° | 17.20° | 1/2000 | 0.00100 | withheld |
| selected | nine | 2025H1 / 2025H2 | 14.07° | 13.73° | 18.76° | 89/2000 | 0.04498 | 0.09295 |
| selected | nine | 2025H2 / 2026H1 | 20.46° | 10.87° | 14.34° | 2/2000 | 0.00150 | 0.01399 |
| selected | nine | 2025H1 / 2026H1 | 30.32° | 15.48° | 21.23° | 0/2000 | 0.00050 | 0.00050 |
| selected | nine | omnibus maximum angle | 30.32° | 15.82° | 21.43° | 0/2000 | 0.00050 | withheld |
| selected | eight | 2025H1 / 2025H2 | 12.43° | 12.05° | 15.77° | 77/2000 | 0.03898 | 0.06747 |
| selected | eight | 2025H2 / 2026H1 | 12.93° | 7.51° | 9.25° | 2/2000 | 0.00150 | 0.05547 |
| selected | eight | 2025H1 / 2026H1 | 20.61° | 12.58° | 16.59° | 1/2000 | 0.00100 | 0.00100 |
| selected | eight | omnibus maximum angle | 20.61° | 13.20° | 17.22° | 1/2000 | 0.00100 | withheld |

Pairwise p-values use the angle upper tail; a congruence lower-tail comparison is equivalent because angle is monotone in congruence. Congruence null percentiles are exported. The omnibus statistic is the maximum of the three pairwise angles. Pairwise max-angle adjustments calibrate against that joint maximum under the complete shared-axis null, not strong FWER control for arbitrary partial nulls. The four overlapping battery/sample cases and the null-construction/sampling sensitivities are not separately multiplicity-corrected.

## First-to-last robustness

| Sampling | Null covariance | Sample | Battery | Null angle q95 | Observed angle | Exceedances / admissible | Calibrated p |
|---|---|---|---|---:|---:|---:|---:|
| fixed_sizes | projected | all | nine | 14.94° | 30.82° | 0/2000 | 0.00050 |
| fixed_sizes | rotated_spectrum | all | nine | 10.27° | 30.82° | 0/2000 | 0.00050 |
| fixed_sizes | projected | all | eight | 12.41° | 21.35° | 0/2000 | 0.00050 |
| fixed_sizes | rotated_spectrum | all | eight | 9.90° | 21.35° | 0/2000 | 0.00050 |
| fixed_sizes | projected | selected | nine | 15.48° | 30.32° | 0/2000 | 0.00050 |
| fixed_sizes | rotated_spectrum | selected | nine | 11.05° | 30.32° | 0/2000 | 0.00050 |
| fixed_sizes | projected | selected | eight | 12.58° | 20.61° | 1/2000 | 0.00100 |
| fixed_sizes | rotated_spectrum | selected | eight | 10.18° | 20.61° | 0/2000 | 0.00050 |
| global_clusters | projected | all | nine | 16.10° | 30.82° | 2/2000 | 0.00150 |
| global_clusters | rotated_spectrum | all | nine | 11.52° | 30.82° | 0/2000 | 0.00050 |
| global_clusters | projected | all | eight | 12.83° | 21.35° | 2/2000 | 0.00150 |
| global_clusters | rotated_spectrum | all | eight | 10.41° | 21.35° | 0/2000 | 0.00050 |
| global_clusters | projected | selected | nine | 15.93° | 30.32° | 1/2000 | 0.00100 |
| global_clusters | rotated_spectrum | selected | nine | 11.48° | 30.32° | 0/2000 | 0.00050 |
| global_clusters | projected | selected | eight | 12.72° | 20.61° | 3/2000 | 0.00200 |
| global_clusters | rotated_spectrum | selected | eight | 10.36° | 20.61° | 0/2000 | 0.00050 |

## Numerical validation and calibration limits

Null target covariances were all constructed successfully. Cohort PCAs: 96000/96000 admissible; simulation failures: 0. null_covariance_diagnostics.csv reports leading-axis alignment, eigenvector residual, positive-definiteness, condition numbers, trace/spectrum changes and source/target gaps. null_spectral_gaps.csv reports simulated gap distributions and near-tie counts. sample_size_diagnostics.csv verifies fixed-size preservation and variable-size ranges.

Calibrated p-values have a plus-one correction, (exceedances+1)/(admissible+1), and are withheld below 90% admissibility. They are never reported as zero. At 2,000 draws, the finest resolution is about .00050. Exact binomial intervals for Monte Carlo exceedance probabilities and conservative invalid-draw bounds are exported; these address Monte Carlo/fit uncertainty, not all null assumptions.

The null targets are estimated from the same finite data and held fixed during generation; calibration is an approximate plug-in empirical bootstrap, not an exact randomization test or proof of its finite-sample size. No independent simulation study of repeated-experiment type-I error has been run. Projection can change eigenvalues; the rotation sensitivity preserves them but imposes a particular rotation of the remaining covariance. Neither construction is uniquely implied by the shared-axis hypothesis. The exact-size design conditions on the observed cluster-size distribution, while global resampling relaxes that condition.

## Interpretation

Exceeding these null distributions is evidence that the observed common-unit covariance PC1 geometry differs more across release cohorts than this named-base sampling model predicts under a shared leading axis. It does not establish changes in latent intelligence, benchmark discrimination, causal model architecture or training effects. Different mixtures of model families, reasoning configurations, score floors and evaluation conditions can produce the same geometric result. Named-base clusters capture explicit setting variants, not all shared ancestry; item uncertainty is absent.

This remains a retrospective release-cohort study in a frozen July 2026 snapshot. It does not establish historical score trajectories, CFA measurement invariance or equality/inequality of latent constructs. Explained variance can change independently of direction.

## Reproduction and files

`OPENBLAS_NUM_THREADS=1 uv run aa_pca_null.py --resamples 2000`

`uv run aa_pca_null_plot.py`

calibrated_tests.csv contains all pairwise/omnibus tests, null percentiles, Monte Carlo uncertainty and invalid-draw bounds. null_distributions.npz stores vectors, angles/congruence, gaps, variance fractions, cohort sizes and statuses. null_covariances.json and common_axes.csv pin target geometry. specification.json fixes methods and reporting. Input/code hashes are in metadata.json.
