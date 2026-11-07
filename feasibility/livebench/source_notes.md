# Public-source inspection, 2026-10-24

## Download follow-up

The user's background acquisition completed at 13:37 UTC. Its manifest now
contains 303 source records and about 1.61 GB of distinct cached input bytes.
All seven HF repositories and the upstream LiveBench code were acquired.
`LiveBench/new-livebench` returned HTTP 404 through the real GitHub API; the
previous web-reader directory listing did not establish that this repository
was currently downloadable. The acquisition verdict is **partial**.

There are 12 archived judgment files but only 10 distinct file hashes. The
latest score pool has 60,372 rows and 195 model IDs, covering only coding,
language and instruction following. Earlier pools contain all six categories.
The acquired HF data cards specify no dataset license; raw-cache redistribution
has not been cleared.

The updated audit was run offline against these original files. Its measured
results supersede the pre-download observations below. Published-export
validation remains pending because the newer export repository was unavailable.

## Initial inspection before the download

These are documentation observations from the web reader, not downloaded score
data. They do not establish current endpoint availability, measured overlap or
permission to redistribute raw data. The reader can return cached pages.

| Source | Observation | Acquisition status |
| --- | --- | --- |
| [HF judgments card](https://huggingface.co/datasets/livebench/model_judgment/blob/9704e5da7bfbefe75ac1482a13de827127295993/README.md) | Describes 60,372 judgment rows with question ID, model, task, category, score, turn and timestamp. This is not a model-coverage measurement. | Card inspected; Parquet bytes not acquired. |
| [HF reasoning dataset](https://huggingface.co/datasets/livebench/reasoning) | Preview exposes question release and removal dates. Historical reconstruction needs archived questions that may no longer occur in the current revision. | Preview inspected; full data and revisions not acquired. |
| [Official public export directory](https://github.com/LiveBench/new-livebench/tree/main/public) | Listing shows 11 dated subtask tables and category mappings from 2024-06-24 through 2026-06-25. These are candidate batteries, not verified independent historical snapshots. | Listing inspected; attempted raw June 2024 and June 2026 tables returned HTTP 404 through the web reader. |
| [Membership code](https://github.com/LiveBench/LiveBench/blob/main/livebench/common.py) | Selects questions introduced in the allowed release set; removal is exclusive, so an item is absent on its removal date. | Source inspected; immutable revision not acquired. |
| [Aggregation code](https://github.com/LiveBench/LiveBench/blob/main/livebench/show_livebench_result.py) | Excludes score -1, requires complete question coverage by default, averages items within tasks and tasks within categories. Lowercases model names and averages repeated judgment rows; the audit retains exact identities and excludes unresolved repeated evaluations. | Source inspected; immutable revision not acquired. |
| [Changelog](https://github.com/LiveBench/LiveBench/blob/main/changelog.md) | Records question replacements and difficulty changes. The October 2025 entry describes a coding-agent/step-budget change followed by rerunning models and updating an older leaderboard. | Documentation inspected; immutable revision not acquired. |

The shell could not resolve `huggingface.co` or `api.github.com`. Nine attempted
source acquisitions are recorded in `manifest.json`. No cached public Parquet
files were found locally, and the browser inventory was empty. The web reader
also could not retrieve dataset API responses.

Next step: run `uv run livebench_feasibility.py --refresh` from this repository on
a host with public network access. Preserve the resulting `cache/` directory
with `manifest.json`; replay using `--offline`. Do not interpret the generated
empty tables as evidence that LiveBench lacks public coverage.

Even with complete downloads, this audit measures retrospective **benchmark
batteries**, not chronological model cohorts. Model release dates, configuration
equivalence and verified family ancestry are required before claiming that gAI
changed across generations.
