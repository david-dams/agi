# First public-data study: LiveBench

**A historical pilot is feasible. A comparable multi-year gAI series is not yet
supported by the acquired LiveBench data.**

The background download acquired approximately 1.61 GB of inputs from all seven
HF repositories and the upstream evaluation code. The newer leaderboard-export
repository returned HTTP 404. Original bytes, immutable source revisions and
checksums are recorded in `manifest.json`; the cache remains local.

## What the historical data shows

The audit reconstructed active question batteries from public release/removal
metadata, required every item within a task, and retained exact model IDs.
Unresolved repeated evaluations were excluded rather than selecting whichever
score looked best. Early question records without release dates were not given
invented dates.

| Score archive | Battery | Complete models | Tasks | Domains | Mean task correlation | PC1 variance share |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2024-06-26 | 2024-06-24 | 50 | 17 | 6 | 0.787 | 80.1% |
| 2024-08-18 | 2024-07-26 | 65 | 18 | 6 | 0.795 | 80.7% |
| 2024-10-22 | 2024-08-31 | 46 | 18 | 6 | 0.598 | 62.9% |

These full-battery point estimates show a strong positive manifold. PC1 is the
first principal component of the standardized task-score correlation matrix;
its variance share is **not** an estimated latent g-factor variance share.
The full tables, candidate panels and exclusions are in `audit.json` and the
generated `README.md`.

Eight archived revisions have a smaller, coverage-selected panel passing the
initial pilot screen; they represent six distinct judgment files. Model and
task selection still matters. Full-battery panels above are descriptive and do
not all pass the provisional models-per-task screen.

The October difference cannot establish declining generality: the models,
battery and complete-case population changed. Related models are not
independent observations, inference settings are not fully verified, and no
uncertainty intervals or model-release cohorts have been constructed.

## Why this does not yet support the longitudinal blog

The latest judgment archive was committed in April 2025. Its 60,372 rows cover
195 exact model IDs but only three domains: coding, language and instruction
following. It has no complete models across the reconstructed broad batteries.
More model IDs therefore do not mean better data for estimating generality.

The useful archived broad-score pools span June–October 2024, rather than the
target year or more. Later dates in the upstream release registry do not supply
missing scores or questions. The newer export repository was unavailable, so
independent reproduction of three published leaderboard configurations remains
pending. Data-card licenses were unspecified; raw-data redistribution has not
been cleared.

## Recommended next study

Use a frozen 2024 archive to replicate the internal study's factor analysis on
public data. Treat that as a baseline replication, with model-family and
inference-setting review, before writing claims about gAI evolution.

For the longitudinal component, obtain a maintained broad score matrix with
versioned evaluation settings and shared anchor tasks/models. Archive each
retrieval from now on. Keep model-release cohorts separate from dates on which
scores or leaderboard revisions became available. If modern LiveBench exports
remain unavailable, investigate HELM and Epoch as the next candidate sources.

No inference calls, latent factor fits, bootstrap intervals or publication were
performed in this first check. The public-data availability question is now
measured rather than blocked by the original network failure.
