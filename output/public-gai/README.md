# Latent gAI analysis on public LiveBench

Primary: 65 models, 18 tasks, six domains; archive `81f6a1cd42f793285e215aabed4fd1c71a94889a`, battery `2024-07-26`.

- One factor: g-attributed standardized task variance 79.6%; CFI 0.817, RMSEA 0.204.
- Three-group hierarchy: g variance 75.8%; CFI 0.898, RMSEA 0.155; BIC difference -150.1.
- Hierarchical ECV 0.901, omega_h 0.949. These are not interchangeable variance/reliability metrics.

## Uncertainty

1000 paired-item and 1000 family/item bootstrap draws; 200 group rediscoveries.
Family grouping: 46 clusters; 39 unresolved identities retained as singletons.

- item, N=1: 1000/1000 admissible; 95% percentile intervals reported.
- item, N=3: 996/1000 admissible; 95% percentile intervals reported.
- family_item, N=1: 1000/1000 admissible; 95% percentile intervals reported.
- family_item, N=3: 782/1000 admissible; nominal intervals withheld.

## Interpretation

Strong shared performance coexists with residual domain structure. The hierarchy is exploratory, discovered on the same small model sample, and remains conditional on its group assignment. Better BIC is not independent confirmation of the group structure.

Matched score-archive comparisons hold observed model IDs, tasks and item IDs fixed; see matched_cohorts.json. Differences between unmatched archive fits cannot establish temporal growth or decline in generality.

Scores are relative to this panel and have no human-IQ interpretation. Family clusters are a dependence sensitivity; unresolved or cross-family ancestry and historical provider/settings differences remain limitations. Independent validation against published leaderboard totals is still pending.

Item-only refits attenuate g-attributed variance: some percentile ranges do not contain the original estimate. The intervals are nominal resampling sensitivity summaries; frequentist coverage has not been calibrated. Means, bias/SD and percentile diagnostics are in bias_diagnostics.csv. No significance claim is based on those shifted ranges.

## Files and reproduction

`report.pdf` contains the rendered analysis. `matrix.csv`, `fit_statistics.csv`, `loadings.csv`, `hierarchy.csv`, `scores.csv`, `group_stability.csv` and `sensitivity.csv` contain numeric results. `bootstrap.npz` stores numeric draws without pickle; `bootstrap_diagnostics.csv` records failures. `metadata.json` pins provenance, versions and code hashes.

```sh
uv run public_gai_factor.py --seed 0 --resamples 1000
```

PDF layout can be regenerated from exported results using `public_gai_factor.render_report(output_directory)` without rerunning the bootstrap.

No new model evaluations, new benchmark collection, model-release cohorts or blog publication were performed.
