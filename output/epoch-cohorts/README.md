# Shared Epoch benchmarks across release cohorts

Finding: shared named benchmark batteries exist. Complete coverage and model diversity do not establish a well-supported three-group hierarchy across cohorts. Configuration IDs can be held fixed within a row, but equal evaluation budgets, prompts and harnesses have not been verified.

Release cohorts are calendar years 2024, 2025 and 2026 (2026 includes only releases in this snapshot). All comparisons below use one identical battery in every cohort and require every included configuration to have a score on every selected benchmark. Exact configuration IDs are retained.

Superseded benchmark versions, the two SpireClimb components and the LiveBench global composite are excluded. Differing repeated scores are excluded. No ECI model-group score aggregation, missing-cell imputation or factor fitting is used.

## Shared battery coverage

Exhaustive subset search through nine benchmarks, requiring at least five complete configurations in every cohort. For each battery size, maximize the smallest cohort count, then the total count. Search does not inspect score magnitudes. A dash means no battery meets the five-per-cohort threshold.

| Source and cohorts | Battery size | 2024 | 2025 | 2026 | Shared benchmarks |
|---|---:|---:|---:|---:|---|
| active_all_sources 2024,2025,2026 | 3 | 27 | 32 | 59 | DTBench, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_all_sources 2024,2025,2026 | 6 | — | — | — | No eligible battery |
| active_all_sources 2024,2025,2026 | 9 | — | — | — | No eligible battery |
| active_all_sources 2025,2026 | 3 | — | 50 | 50 | ARC-AGI-2, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_all_sources 2025,2026 | 6 | — | 19 | 28 | ARC-AGI, ARC-AGI-2, Chess Puzzles, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_all_sources 2025,2026 | 9 | — | 8 | 17 | ARC-AGI, ARC-AGI-2, Chess Puzzles, DTBench, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, LMCA, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_all_sources 2025,2026 high-label | 3 | — | 10 | 11 | DTBench, LMCA, WeirdML |
| active_all_sources 2025,2026 high-label | 6 | — | 7 | 10 | ARC-AGI, ARC-AGI-2, Chess Puzzles, GPQA diamond, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_all_sources 2025,2026 high-label | 9 | — | 5 | 6 | ALE-Bench, ARC-AGI, ARC-AGI-2, Chess Puzzles, DTBench, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, LMCA, OTIS Mock AIME 2024-2025 |
| active_epoch_runs 2024,2025,2026 | 3 | 7 | 24 | 72 | FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_epoch_runs 2024,2025,2026 | 6 | — | — | — | No eligible battery |
| active_epoch_runs 2024,2025,2026 | 9 | — | — | — | No eligible battery |
| active_epoch_runs 2025,2026 | 3 | — | 35 | 92 | Chess Puzzles, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_epoch_runs 2025,2026 | 6 | — | 7 | 40 | Chess Puzzles, FrontierMath-Tier-4-v2-Private, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_epoch_runs 2025,2026 | 9 | — | — | — | No eligible battery |
| active_epoch_runs 2025,2026 high-label | 3 | — | 9 | 18 | Chess Puzzles, GPQA diamond, OTIS Mock AIME 2024-2025 |
| active_epoch_runs 2025,2026 high-label | 6 | — | 6 | 7 | Chess Puzzles, FrontierMath-Tiers-1-3-v2-Private, GPQA diamond, Mystery Game Puzzles, OTIS Mock AIME 2024-2025, SimpleQA Verified |
| active_epoch_runs 2025,2026 high-label | 9 | — | — | — | No eligible battery |

Each row can use a different battery. Compare counts across years within a row. Memberships, organization concentration and known model-group counts are exported in overlap.json. Configurations from one model group are correlated observations, so counts above overstate independent model diversity.

## Diversity of selected candidate panels

| Source and cohorts | Battery size | Year | Configurations | Known model groups | Organization counts |
|---|---:|---|---:|---:|---|
| active_all_sources 2024,2025,2026 | 3 | 2024 | 27 | 27 | Alibaba: 2, Anthropic: 6, Google DeepMind: 5, Meta AI: 6, Mistral AI: 3, OpenAI: 4, xAI: 1 |
| active_all_sources 2024,2025,2026 | 3 | 2025 | 32 | 32 | Alibaba: 8, DeepSeek: 2, Google DeepMind: 5, Google DeepMind,Google: 1, Meta AI: 1, Mistral AI: 3, OpenAI: 12 |
| active_all_sources 2024,2025,2026 | 3 | 2026 | 59 | 49 | Alibaba: 13, Anthropic: 13, DeepSeek: 2, Google: 1, Google DeepMind: 6, MiniMax: 1, Moonshot: 2, Nvidia: 1, OpenAI: 14, Thinking Machines: 1, Z.ai (Zhipu AI): 1, xAI: 4 |
| active_epoch_runs 2025,2026 | 3 | 2025 | 35 | 16 | Anthropic: 6, Google DeepMind: 1, OpenAI: 27, Z.ai (Zhipu AI): 1 |
| active_epoch_runs 2025,2026 | 3 | 2026 | 92 | 54 | Alibaba: 7, Anthropic: 18, DeepSeek: 7, Google DeepMind: 13, MiniMax: 2, Mistral AI: 1, Moonshot: 5, OpenAI: 26, Thinking Machines: 1, Z.ai (Zhipu AI): 6, xAI: 6 |
| active_all_sources 2025,2026 | 9 | 2025 | 8 | 8 | OpenAI: 8 |
| active_all_sources 2025,2026 | 9 | 2026 | 17 | 17 | Anthropic: 1, DeepSeek: 1, Google DeepMind: 4, Moonshot: 1, OpenAI: 7, xAI: 3 |

Model groups use the ZIP metadata and are not independent ancestry/family clusters. Counts may still include related checkpoints or aliases. The nine-benchmark 2025 all-source cohort has only eight rows, all OpenAI, so its nine-variable covariance is necessarily singular.

## Individually shared benchmarks

Benchmarks with at least ten configurations in every year, before requiring those configurations to be complete across a battery.

| Source | Benchmark | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|
| active_all_sources | DTBench | 35 | 57 | 130 |
| active_all_sources | ForecastBench | 20 | 33 | 35 |
| active_all_sources | GPQA diamond | 59 | 123 | 128 |
| active_all_sources | LMCA | 14 | 49 | 130 |
| active_all_sources | OTIS Mock AIME 2024-2025 | 46 | 118 | 132 |
| active_all_sources | SimpleBench | 19 | 47 | 36 |
| active_all_sources | WeirdML | 23 | 68 | 76 |
| active_epoch_runs | GPQA diamond | 59 | 123 | 128 |
| active_epoch_runs | OTIS Mock AIME 2024-2025 | 46 | 118 | 132 |

## What is consistent, and what remains unverified

- Cohort membership follows one unambiguous release date for each exact configuration ID. Calendar periods do not overlap. These are retrospective measurements, not historical as-published snapshots.
- Benchmark labels and supersession metadata identify the same named battery version across cohorts. Equal labels alone do not prove identical questions, graders or evaluation implementations.
- The Epoch-run subset avoids mixing evaluation organizations. Its CSVs expose release dates, scores, run timestamps and some log links, but do not provide explicit columns for prompts, agent harnesses, tools or token budgets. Consistency of those settings is unverified.
- The high-label restriction keeps only IDs ending in _high. It removes unlabeled/default and other effort settings from that sensitivity check. Different providers can implement high differently, so this does not establish equal compute budgets.
- Counts for exact configurations can include multiple effort settings of the same base model. Known model-group counts are reported separately. Missing group mappings remain unresolved rather than being asserted independent.
- External-source coverage can mix prompts, graders, harnesses, tools and providers. Score conflicts have been removed, but equal repeated scores do not prove that their settings match.
- Coverage optimization can favor related math and reasoning tests and omit instruction following, writing or agent tasks. A numerically shared battery is not automatically representative or suitable for a three-group hierarchy.
- A nine-task covariance matrix requires more than nine independent observations for full rank, and substantially more for stable hierarchical inference. The search threshold of five is for feasibility screening, not an estimation standard.

## Reproduce

```sh
uv run epoch_cohort_overlap.py
```

Epoch AI, Capabilities & benchmarking, https://epoch.ai/benchmarks. ZIP SHA256: `bbb531f67fb176b936f477e666cf854582dfd1ae51686ed852e35aec14140e0c`. Code and prior audit hashes are in overlap.json. The ZIP README specifies CC BY 4.0 with attribution.
