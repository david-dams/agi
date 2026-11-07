# Modern LiveBench aggregate-factor study

Battery labels identify benchmark versions. They are not frozen publication dates or model release cohorts.

| Panel | Configurations | Tasks | One-factor g variance | Hierarchical g variance | Hierarchy minus one-factor BIC |
|---|---:|---:|---:|---:|---:|
| 2025_05_30 | 70 | 20 | 0.457 | 0.365 | -468.62 |
| 2025_11_25 | 65 | 20 | 0.426 | 0.382 | -332.83 |
| 2026_06_25 | 28 | 23 | 0.355 | 0.302 | -26.77 |
| 2025_05_30 matched | 46 | 19 | 0.410 | 0.333 | -283.71 |
| 2025_11_25 matched | 46 | 19 | 0.337 | 0.316 | -348.46 |

* marks a boundary fit. Such estimates are diagnostics, not admissible results.

## Interpretation limits

- These fits describe covariance across the configurations included in each export. Different cohorts and task batteries can change that covariance.
- The matched 2025 panels hold exact configuration IDs and task names fixed. Question IDs, scoring implementations and identical evaluation settings are not supplied by these CSVs; measurement equivalence remains unverified. No temporal growth or decline is inferred.
- June 2026 has only 28 configurations for 23 tasks. Configuration bootstrap often produces singular covariance matrices; no regularization or replacement sampling scheme conceals this.
- Resampling uses whole configuration rows with fixed point-estimate groups. It measures configuration sensitivity, assumes independent rows, and does not account for shared model families, group selection or item uncertainty. It is not an item bootstrap or a calibrated population interval.
- Percentile sensitivity ranges are withheld below 90% admissible draws or when the point fit is inadmissible. Zero scores are retained and listed for provenance review.
- Three-group partitions are discovered separately for full panels. The matched comparison uses the first matched panel partition for both batteries. If no partition has at least three indicators per group, the hierarchy is unavailable.

## Overlap

- 2025_05_30 / 2025_11_25: 46 exact configuration IDs; 19 task names.
- 2025_05_30 / 2026_06_25: 0 exact configuration IDs; 19 task names.
- 2025_11_25 / 2026_06_25: 2 exact configuration IDs; 20 task names.

## Matched score changes

449 of 874 matched cells differ; maximum absolute change is 74.50 points.

| Task | Mean score change, November minus May battery |
|---|---:|
| AMPS_Hard | +0.239 |
| code_completion | -0.236 |
| code_generation | +0.122 |
| connections | +3.511 |
| javascript | +4.239 |
| math_comp | -1.558 |
| olympiad | +7.524 |
| paraphrase | -47.916 |
| plot_unscrambling | +0.152 |
| python | +2.283 |
| simplify | -46.366 |
| spatial | -0.130 |
| story_generation | -39.956 |
| summarize | -39.189 |
| tablejoin | +0.045 |
| tablereformat | -0.000 |
| typescript | +3.261 |
| typos | +0.043 |
| zebra_puzzle | -45.402 |

Large changes for unchanged model IDs require question/scoring provenance review before interpreting differences in factor structure.

## Fit and resampling diagnostics

### 2025_05_30

Matrix rank 20/20; minimum correlation eigenvalue 0.0418266.

- N=1: ok; 200/200 admissible row resamples. Ranges reported.
- N=3: ok; 179/200 admissible row resamples. Ranges withheld.
- Hierarchy wins BIC in 179/179 paired admissible draws; failed draws are excluded from this conditional comparison.

Groups: AMPS_Hard, connections, math_comp, spatial, tablejoin, tablereformat, web_of_lies_v3, zebra_puzzle; code_completion, code_generation, javascript, olympiad, plot_unscrambling, python, typescript, typos; paraphrase, simplify, story_generation, summarize.

### 2025_11_25

Matrix rank 20/20; minimum correlation eigenvalue 0.0172471.

- N=1: ok; 200/200 admissible row resamples. Ranges reported.
- N=3: ok; 97/200 admissible row resamples. Ranges withheld.
- Hierarchy wins BIC in 97/97 paired admissible draws; failed draws are excluded from this conditional comparison.

Groups: AMPS_Hard, connections, math_comp, paraphrase, simplify, story_generation, summarize, theory_of_mind, zebra_puzzle; code_completion, code_generation, javascript, olympiad, plot_unscrambling, python, typescript, typos; spatial, tablejoin, tablereformat.

### 2026_06_25

Matrix rank 23/23; minimum correlation eigenvalue 0.0109494.

- N=1: ok; 0/200 admissible row resamples. Ranges withheld.
- N=3: ok; 0/200 admissible row resamples. Ranges withheld.
- Hierarchy wins BIC in 0/0 paired admissible draws; failed draws are excluded from this conditional comparison.

Groups: AMPS_Hard, connections, math_comp, paraphrase, plot_unscrambling, simplify, story_generation, summarize, tablejoin, tablereformat; logic_with_navigation, spatial, typos; code_completion, code_generation, consecutive_events, integrals_with_game, javascript, olympiad, python, theory_of_mind, typescript, zebra_puzzle.

### 2025_05_30 matched

Matrix rank 19/19; minimum correlation eigenvalue 0.030902.

- N=1: ok; 180/200 admissible row resamples. Ranges reported.
- N=3: ok; 157/200 admissible row resamples. Ranges withheld.
- Hierarchy wins BIC in 142/142 paired admissible draws; failed draws are excluded from this conditional comparison.

Groups: paraphrase, simplify, story_generation, summarize, tablereformat; code_completion, code_generation, javascript, olympiad, plot_unscrambling, python, typescript, typos; AMPS_Hard, connections, math_comp, spatial, tablejoin, zebra_puzzle.

### 2025_11_25 matched

Matrix rank 19/19; minimum correlation eigenvalue 0.0174946.

- N=1: ok; 200/200 admissible row resamples. Ranges reported.
- N=3: ok; 109/200 admissible row resamples. Ranges withheld.
- Hierarchy wins BIC in 109/109 paired admissible draws; failed draws are excluded from this conditional comparison.

Groups: paraphrase, simplify, story_generation, summarize, tablereformat; code_completion, code_generation, javascript, olympiad, plot_unscrambling, python, typescript, typos; AMPS_Hard, connections, math_comp, spatial, tablejoin, zebra_puzzle.

## Reproduce

```sh
uv run modern_gai_factor.py --resamples 200 --seed 0
```

Inputs and code are hashed in metadata.json. results.json contains full loadings, zero-score flags and failure counts; fit_statistics.csv contains point estimates. Earlier 2024 outputs are preserved.

Source: https://github.com/LiveBench/livebench.github.io/tree/main/public. Download URLs reference mutable main; local SHA256 hashes pin the bytes analyzed. Retrieval timestamps and original upstream commit revisions were not recorded by the manual downloads.
