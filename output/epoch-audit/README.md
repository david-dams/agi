# Epoch public-data feasibility audit

Verdict: useful for a retrospective model-release cohort study, subject to coverage and evaluation-setting controls. This ZIP is one current snapshot and does not reconstruct what was known at past dates. A representative longitudinal hierarchical-factor dataset has not yet been established.

The ZIP contains 90 CSV files and 91 benchmark metadata records. Raw configuration release dates span 2019-11-05 to 2026-10-17. ECI constituent data are scores, not the ECI composite or its bootstraps.

## Coverage

| Input | Models/configurations | Benchmarks | Observed cells | Density | Complete across all |
|---|---:|---:|---:|---:|---:|
| exact_configuration | 998 | 84 | 5589 | 6.7% | 0 |
| epoch_runs | 416 | 18 | 1632 | 21.8% | 0 |
| active_epoch_runs | 403 | 14 | 1445 | 25.6% | 0 |
| eci_grouped | 270 | 59 | 2888 | 18.1% | 0 |

Raw matrices preserve exact configuration IDs. Conflicting scores for the same configuration/benchmark are excluded; equal-score repeats collapse. Epoch-run matrices use mean_score, avoiding an additional best-across-scorers selection. External matrices use the declared score column or an explicit header-audited supplemental mapping and retain source units. LiveBench Global average is inventoried but excluded as a composite. No scales are pooled into a composite or imputed. Active Epoch runs exclude superseded benchmarks and the two SpireClimb components when retaining the aggregate.

## Release cohorts

| Input | Release year | Models/configurations | Benchmarks with >=20 | Benchmarks with >=50 | Greedy complete on 9 benchmarks |
|---|---|---:|---:|---:|---:|
| exact_configuration | 2019 | 1 | 0 | 0 | 0 |
| exact_configuration | 2020 | 1 | 0 | 0 | 0 |
| exact_configuration | 2021 | 3 | 0 | 0 | 0 |
| exact_configuration | 2022 | 13 | 0 | 0 | 0 |
| exact_configuration | 2023 | 81 | 9 | 0 | 1 |
| exact_configuration | 2024 | 165 | 11 | 3 | 3 |
| exact_configuration | 2025 | 320 | 30 | 9 | 10 |
| exact_configuration | 2026 | 388 | 34 | 22 | 27 |
| exact_configuration | unknown | 26 | 0 | 0 | 0 |
| epoch_runs | 2023 | 13 | 0 | 0 | 0 |
| epoch_runs | 2024 | 59 | 3 | 2 | 0 |
| epoch_runs | 2025 | 154 | 9 | 3 | 6 |
| epoch_runs | 2026 | 188 | 11 | 7 | 12 |
| epoch_runs | unknown | 2 | 0 | 0 | 0 |
| active_epoch_runs | 2023 | 13 | 0 | 0 | 0 |
| active_epoch_runs | 2024 | 59 | 3 | 2 | 0 |
| active_epoch_runs | 2025 | 144 | 7 | 2 | 1 |
| active_epoch_runs | 2026 | 185 | 9 | 7 | 12 |
| active_epoch_runs | unknown | 2 | 0 | 0 | 0 |
| eci_grouped | 2023 | 48 | 9 | 0 | 10 |
| eci_grouped | 2024 | 63 | 9 | 1 | 3 |
| eci_grouped | 2025 | 63 | 14 | 1 | 15 |
| eci_grouped | 2026 | 85 | 21 | 10 | 43 |
| eci_grouped | unknown | 11 | 0 | 0 | 2 |

Benchmark threshold counts describe coverage separately for each benchmark. Nine-benchmark searches run separately within each year and may select different batteries, so those counts do not establish a fixed longitudinal panel. Unknown/conflicting dates are kept outside dated cohorts.

## Complete-panel search

Coverage-only greedy search seeded at every benchmark, without looking at scores. These are candidate panels, not proven global maxima or representative selections. Strong coverage can concentrate on one domain or organization.

| Input | Benchmarks | Complete configurations/groups | Benchmarks selected |
|---|---:|---:|---|
| exact_configuration | 3 | 133 | Chess Puzzles, GPQA diamond, OTIS Mock AIME 2024-2025 |
| exact_configuration | 6 | 61 | ARC-AGI, ARC-AGI-2, CritPt, DTBench, LMCA, SciCode |
| exact_configuration | 8 | 35 | Chess Puzzles, CritPt, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, OTIS Mock AIME 2024-2025, SciCode, SimpleQA Verified |
| exact_configuration | 9 | 29 | Chess Puzzles, CritPt, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SciCode, SimpleQA Verified |
| exact_configuration | 12 | 20 | ARC-AGI, Chess Puzzles, CritPt, DTBench, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, LMCA, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SciCode, SimpleQA Verified |
| epoch_runs | 3 | 133 | Chess Puzzles, GPQA diamond, OTIS Mock AIME 2024-2025 |
| epoch_runs | 6 | 47 | Chess Puzzles, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| epoch_runs | 8 | 23 | Chess Puzzles, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, Furniture Assembly, GPQA diamond, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| epoch_runs | 9 | 12 | Chess Puzzles, EBR-bench, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, Furniture Assembly, GPQA diamond, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| epoch_runs | 12 | 5 | Chess Puzzles, EBR-bench, FrontierMath-Erdos, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, Furniture Assembly, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified, SpireClimb, SpireClimb (Slay the Spire 1, Ascension 20 Heart), SpireClimb (Slay the Spire 2, Ascension 10) |
| active_epoch_runs | 3 | 133 | Chess Puzzles, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_epoch_runs | 6 | 47 | Chess Puzzles, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_epoch_runs | 8 | 23 | Chess Puzzles, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, Furniture Assembly, GPQA diamond, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_epoch_runs | 9 | 12 | Chess Puzzles, EBR-bench, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, Furniture Assembly, GPQA diamond, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_epoch_runs | 12 | 1 | Chess Puzzles, EBR-bench, FrontierMath-Erdos, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, Furniture Assembly, GPQA diamond, MirrorCode, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified, SpireClimb |
| eci_grouped | 3 | 134 | DTBench, GPQA diamond, OTIS Mock AIME 2024-2025 |
| eci_grouped | 6 | 66 | Chess Puzzles, DTBench, GPQA diamond, LMCA, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| eci_grouped | 8 | 54 | Chess Puzzles, DTBench, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, LMCA, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| eci_grouped | 9 | 50 | Chess Puzzles, DTBench, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, LMCA, OTIS Mock AIME 2024-2025, ProofBench, SimpleQA Verified |
| eci_grouped | 12 | 38 | ARC-AGI, ARC-AGI-2, Chess Puzzles, DTBench, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, LMCA, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, ProofBench, SimpleQA Verified |

Exact panel memberships, release-year counts, organization counts, ranks and all pairwise overlaps are recorded in audit.json. Three-group hierarchy needs at least nine indicators, and domain breadth must be checked separately from numerical coverage.

## Provenance and comparability

- 148 of 270 ECI model groups use different configuration/version IDs across their benchmark observations. They cannot be treated as fixed effort/harness configurations.
- 11 ECI groups have inconsistent dates across observations and are excluded from dated cohort assignment. Their dates remain in audit.json.
- 807 ECI observations use a benchmark released after the model. This is retrospective evaluation coverage, not a historical as-published panel.
- Raw evaluation timestamps span 2025-01-27T00:00:00.000Z to 2026-10-19T22:39:00.000Z. Of 1628 dated evaluations, 214 occurred more than a year after model release; 14 have negative release-to-evaluation lags and need review.
- 290 raw configuration/benchmark cells have differing reported values and were excluded. Full conflicting values are retained in audit.json. Duplicate model-metadata keys: {"deepseek-r1-0528-qwen3-8b": 2}.
- mean_score differs from best-across-scorers in 6/1636 Epoch-run records. ECI processing uses its own selection/transformation pipeline; do not infer an unprocessed fixed-configuration matrix from its labels.
- ECI performance values are processed. For example, GPQA uses baseline/ceiling normalization. Positive affine normalization alone preserves Pearson correlations, but configuration selection, clipping, and nonlinear transformations require separate inspection.
- 1234 ECI rows have blank source labels. This is not proof of missing provenance: some match Epoch-run files with log links. Availability of each linked log and its item-level content was not checked.
- Exact model IDs alone do not establish identical agent harnesses, tool budgets, prompts, model providers, graders or question sets. External CSVs expose these fields inconsistently. Source metadata and per-run logs must be checked before combining them.
- Superseded FrontierMath versions and component/aggregate benchmark overlap must not be treated as independent indicators. The metadata supplies some supersession links, not a complete overlap map.
- Metadata leaves file mappings blank for some supplied CSVs, including HLE and SciCode. Supplemental mappings are explicit and recorded in inventory. Score direction and grading are not harmonized by this coverage audit.
- The SciCode CSV already includes 226 records attributed to Artificial Analysis. This supplies one AA benchmark through Epoch, not the full historical AA score matrix.
- Organization and accessibility are not sampling probabilities. The data emphasize publicly evaluated models; complete-case selection adds its own bias. Effort variants and related models require a declared sampling and family policy.

## Recommendation

1. Use a retrospective release-cohort design first. Pin exact model configuration, benchmark version and evaluation setup. Keep publication-history questions separate.
2. Start with the active Epoch-run exact-configuration matrix as the most controlled candidate. Check a fixed, diverse anchor battery across release cohorts before committing to a hierarchical time trend. Coverage-only panels above are screening results.
3. Use ECI grouped data as a separate sensitivity source after auditing configuration selection and score processing. Do not use ECI composite scores or ECI bootstrap draws to estimate independent general-factor structure.
4. Compare domain-balanced batteries and broad versus frontier-only cohorts. Report when sample size or domain coverage cannot support three groups. Never silently fill sparse cells or regularize covariance to obtain a fit.
   A model that explicitly handles sparse observations could retain more data than complete-case analysis, but requires a separate validated implementation and checks for nonrandom missingness. ECI coverage alone does not validate a sparse multidimensional hierarchy.
5. Archive this ZIP now and future snapshots with hashes. Historical publication snapshots require additional archives; this download alone cannot supply them.

## Sources and reproduction

Source: Epoch AI, Capabilities & benchmarking, https://epoch.ai/benchmarks. ZIP README grants CC BY 4.0 with attribution. Source files retain external citations and context; third-party benchmark items and linked logs were not downloaded.

ZIP SHA256: `bbb531f67fb176b936f477e666cf854582dfd1ae51686ed852e35aec14140e0c`. Every member and the audit script are hashed in audit.json. The download time and upstream snapshot revision were not supplied.

```sh
uv run epoch_data_audit.py --zip benchmark_data.zip
```

This audit fits no latent factors. It checks feasibility before another model is estimated.
