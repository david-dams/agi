# LiveBench longitudinal gAI feasibility

**Status: partial; interpretation remains conditional on configuration and version review.**

## Verdict

- Latest-pool analysis: **insufficient coverage against initial screening targets**; 0 candidate panels pass the numerical screen.
- Future repeatability: checksum-verified replay is implemented. Continuing availability, complete publication and configuration stability are not established.
- Published-score validation: **pending or failed** (0 configurations checked).

Historical coverage screen: False; 0 export-matched batteries spanning 0 days. Bridge IDs are not yet verified equivalent configurations.

Latest judgment pool: 60,372 rows, 195 exact model IDs; category counts: {'language': 31179, 'coding': 21541, 'instruction_following': 7652}.

## Measured coverage

Release | Questions | Observed models | Complete models | Varying tasks | Categories | Screen
--- | ---: | ---: | ---: | ---: | ---: | ---
2024-06-24 | 910 | 180 | 0 | 0 | 0 | False
2024-07-26 | 1000 | 183 | 0 | 0 | 0 | False
2024-08-31 | 1000 | 183 | 0 | 0 | 0 | False
2024-11-25 | 1000 | 191 | 0 | 0 | 0 | False
2025-04-02 | 682 | 109 | 0 | 0 | 0 | False
2025-04-25 | 682 | 109 | 0 | 0 | 0 | False
2025-05-30 | 682 | 109 | 0 | 0 | 0 | False
2025-11-25 | 682 | 109 | 0 | 0 | 0 | False
2025-12-23 | 682 | 109 | 0 | 0 | 0 | False
2026-01-08 | 682 | 109 | 0 | 0 | 0 | False
2026-06-25 | 682 | 109 | 0 | 0 | 0 | False

See `audit.json` for candidate model/task lists, exclusions, concentration, saturation and matrix rank; `overlap.csv` for release bridges; `coverage.svg` for item-complete coverage. Initial documentation observations and download failures are in [source_notes.md](source_notes.md).

## Archived score pools

Each archive is checked separately against the newest battery predating its commit. Question metadata is reconstructed today; these are not verified as-published snapshots. Duplicate commits do not constitute independent cohorts.

Score commit | Battery | Complete models | Tasks | Categories | Mean task correlation | PC1 variance | Full-panel screen
--- | --- | ---: | ---: | ---: | ---: | ---: | ---
2024-06-26 (9ecfb727) | 2024-06-24 | 50 | 17 | 6 | 0.787 | 80.1% | False
2024-07-03 (1090e27b) | 2024-06-24 | 50 | 17 | 6 | 0.787 | 80.1% | False
2024-07-20 (b6494fe9) | 2024-06-24 | 57 | 17 | 6 | 0.780 | 79.4% | False
2024-07-29 (86ad8e20) | 2024-07-26 | 59 | 18 | 6 | 0.786 | 80.0% | False
2024-08-04 (65fce612) | 2024-07-26 | 60 | 18 | 6 | 0.789 | 80.2% | False
2024-08-18 (81f6a1cd) | 2024-07-26 | 65 | 18 | 6 | 0.795 | 80.7% | False
2024-10-22 (d24cc5c5) | 2024-08-31 | 46 | 18 | 6 | 0.598 | 62.9% | False
2024-10-22 (5896e3b1) | 2024-08-31 | 46 | 18 | 6 | 0.598 | 62.9% | False
2025-04-07 (9704e5da) | 2025-04-02 | 0 | 0 | 0 | n/a | n/a | False

8 archived score revisions have a shortlisted panel passing the numerical pilot screen. Multiple revisions may contain the same data. PC1 is an exploratory principal component, not an estimated latent g factor or evidence of intelligence growth.

## Interpretation

- These are retrospective batteries reconstructed from the latest acquired judgment pool and archived question metadata. They are not as-published historical snapshots or model-release cohorts.
- Historical judgment revisions are inventoried separately in `audit.json`; a repository commit date is evidence provenance, not an evaluation date or benchmark release date.
- `release_ledger.json` preserves acquired changelog entries, dated export availability and mismatches between public subtask exports and reconstructed question batteries. Release labels alone do not establish comparability.
- All exact model IDs are retained. Configuration equivalence, release dates and family ancestry require verification before cohort-level inference. Family prefixes are only a diagnostic.
- Exact duplicate rows collapse; unresolved repeated evaluations are excluded by model/item. Sentinel -1 means unscored; zero remains a valid scored failure. Changed question metadata is excluded conservatively.
- Task means require all active items. Task names do not prove stable prompts, scoring, agent setup or difficulty; identical item sets are reported separately.
- Screening targets: 8 varying tasks, 4 categories and max(50, 5 × varying tasks) complete configurations. Historical target: 3 releases across 12 months and 20 complete bridge IDs per compared pair. These are feasibility heuristics, not power calculations.
- Published validation compares task means against the public subtask table and category means against equal-task averages of that table; category values are derived references, not a second independent publication.
- Coverage-only greedy task pruning shortlists candidates; it does not exhaustively search for the globally largest complete matrix.
- Mean correlations and PC1 variance describe each observed sample. Task sets and model populations change between rows; differences are not estimates of temporal change in gAI. No model-release cohorts or uncertainty intervals have been constructed.
- Public visibility is not a blanket redistribution license. Source license fields and original README/LICENSE files remain authoritative; raw cache is ignored by git.

## Acquisition failures

- GitHub/new-livebench: `HTTP Error 404: Not Found`

## Next experiment

Review the largest passing panels and their shared item/setting definitions. Verify model ancestry and settings, then fit a one-factor pilot on the largest comparable panel; do not infer temporal changes from release labels alone.

If LiveBench lacks sufficient bridges, test HELM for versioned scenario overlap or the archived HF leaderboards for a larger common-battery model population. Neither source repairs missing LiveBench history automatically.

## Reproduce

```sh
uv run livebench_feasibility.py --refresh
uv run livebench_feasibility.py --offline
uv run livebench_feasibility.py --self-check
```

No factor fitting, new model evaluations, publication, or internal benchmark access was performed.
