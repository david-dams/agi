# Acquired-data audit for a gAI time series

The original goal remains a series of general-factor measurements on comparable capabilities. The strongest acquired candidate is now the nine-benchmark AA panel. This audit establishes observed coverage and numerical rank, not measurement invariance or a validated gAI trend. See AA-SUITABILITY.md for the subsequent raw-page provenance and comparability audit: the panel is exploratory, with substantial floor effects and unverified per-cell protocol equivalence.

## Artificial Analysis: primary candidate

Original repository ZIP: 421 configuration rows. The recovered browser CSV matches original records: True; matches original bytes: True.

Nine fixed indicators: GPQA, HLE, AA-Omniscience, tau2, IFBench, AA-LCR, SciCode, CritPt and Terminal-Bench Hard. Each selected configuration has an observed value on every indicator. Composite Intelligence Index and MMMU-Pro are excluded.

| Battery | Release cohort | Configurations | Distinct publisher short names | Reasoning configurations | Rank |
|---|---|---:|---:|---:|---:|
| nine | 2024H1 | 4 | 4 | 0 | 3 |
| nine | 2024H2 | 18 | 18 | 1 | 9 |
| nine | 2025H1 | 59 | 49 | 27 | 9 |
| nine | 2025H2 | 176 | 140 | 97 | 9 |
| nine | 2026H1 | 152 | 126 | 97 | 9 |
| twelve | 2024H2 | 4 | 4 | 0 | 3 |
| twelve | 2025H1 | 16 | 16 | 7 | 12 |
| twelve | 2025H2 | 27 | 27 | 18 | 12 |
| twelve | 2026H1 | 49 | 48 | 43 | 12 |

Quarterly resolution on the same nine indicators:

| Release quarter | Complete configurations | Distinct short names |
|---|---:|---:|
| 2025Q1 | 17 | 16 |
| 2025Q2 | 42 | 33 |
| 2025Q3 | 88 | 67 |
| 2025Q4 | 88 | 73 |
| 2026Q1 | 72 | 58 |
| 2026Q2 | 80 | 68 |

Distinct short names are a descriptive count, not a verified base-model or ancestry count: the source sometimes retains effort labels inside short names. Exact memberships are in aa_memberships.csv.

**What we can do:** estimate a fixed nine-indicator flat factor model, then compare its structure across 2025H1, 2025H2 and 2026H1 using predeclared release cohorts. Quarterly counts are exported in audit.json and may support finer exploratory resolution. Fit one pooled calibration for a relative capability trajectory and use separate cohort fits/invariance tests for whether factor structure changes. These are different outcomes.

**What is not established:** equal evaluation settings, common grader/question versions across every row, independent families, selection representativeness, and invariance. Release dates are source-reported and this July 2026 snapshot cannot represent later releases. A three-group model needs at least three defensible indicators per group; nine columns alone do not supply that theory or sufficient group separation.

For capability levels, retain one common reference scale; do not independently z-score each cohort and call those scores progress. For changing g strength, report a specified variance-share/reliability measure with uncertainty within fixed windows, recognizing changing variance and population composition. Reasoning/nonreasoning and publisher/family composition require sensitivity analyses.

## WILD: item-level replication candidate

7,237,945 observations, 65 models, 27 benchmarks. Observed model/task cells: 1755. Repeated model/item keys: 116220.
26 benchmark item unions are fully covered by every model. A coverage-only screen retains 26 benchmarks covered by >=50 models, with 65 models complete across that whole screened battery.

Every benchmark has common item keys across all 65 models; the intersection sizes are in audit.json. Repeated item keys have conflicting binary scores in 25733 model/item cells. This requires inspecting whether repeated prompts represent distinct original items, stochastic repetitions or record duplication before aggregating them.

The item union is derived from observations, not guaranteed identical to the official question bank. Coverage details and unmodified score means are in wild_coverage.csv; duplicate keys must be resolved before those means are used in fits. This source can independently test benchmark structure and common-item uncertainty. It needs verified release dates for calendar cohorts; its limited model population does not replace the AA frontier timeline.

## Open LLM Leaderboard: historical open-model replication

- v1: 7260 rows, 7170 complete six-score rows, 6896 distinct model names. Flag values: {'True': 7260}.
- v2: 4576 rows, 4576 complete six-score rows, 4497 distinct model names. Flag values: {'False': 4575, 'True': 1}.
- V2 raw result files: 10509, parsed 10509, errors 0. Run-date range 2024-06-13 to 2025-03-13. Largest exact protocol-signature group: 2610 runs, 2464 distinct model/revision/precision identities.

V2 retains task-level results, task hashes, shots, model revisions and harness commits, so consistency is much more auditable than aggregate leaderboards. Identical signature grouping includes version/shot metadata and selected global generation settings; it is a screening proxy, not proof of identical task instances. Chat templates are model-specific and need review. Repeated runs must not become additional independent models. Submission, Hub-upload and evaluation dates are not interchangeable with release dates. V1 marks every contents row flagged in this snapshot, so flag semantics need investigation before exclusion or use.

## LiveBench archive

The export ZIP contains 11 battery tables. Counts and exact complete model memberships are in audit.json. More editions are acquired than the three analyzed earlier. In particular, table_2026_01_08 has 126 complete configurations on 23 tasks (versus 28 on 23 in table_2026_06_25), including models released after January. Battery labels are not evaluation cutoffs. This is another promising fixed-battery cohort candidate, pending verified release-date mapping and family/configuration controls. The modelLinks.js metadata supplies source links and some version strings, not uniform release dates. Battery labels still identify changing measuring instruments, so stitching table dates together is not a gAI series.

## Arena and DataDecide

Arena has actual published snapshots. It can validate an independently estimated capability trajectory against preference outcomes; changing opponents, voters, categories and rating methods prevent treating the ratings as an invariant objective battery. Dataset ranges are in audit.json.

DataDecide: 1,410,750 training-result rows, 21,375 (size, recipe, step, seed) checkpoints, 66 task labels. Task-count distribution per checkpoint: {66: 21375}.
This supports a controlled training-progress experiment, with dependence across steps/seeds handled explicitly. It is not calendar-time frontier progress. Derived macro-average and scaling-fit Parquets were excluded to avoid duplicating raw observations.

## Acquisition failures and fixes

The saved EEE log reports HTTP 504 Gateway Timeout while listing the large repository. It also shows that the CLI treated extra include patterns as filenames; the batch command now repeats --include for each pattern. This recorded failure is not evidence of a rate-limit 429, though earlier rate limits may also have occurred. EEE is not needed to start the AA baseline.
HELM located release objects but received gzip-compressed bytes. The downloader incorrectly attempted to parse those bytes as JSON. It now decompresses gzip after checking stored object size. Classic had no matching core-scenario release files under the searched prefix; that layout remains unresolved. No retry with remote access was performed in this audit.

## Recommended study sequence

1. Primary retrospective calendar series: the AA nine-indicator panel, with half-year windows as the initial comparison and quarter windows as a sensitivity check. Fix indicator definitions and separate capability-level trends from changes in factor strength.
2. Freeze a confirmatory specification before fitting cohort contrasts. Audit source model identities, configurations and indicator/version metadata; run measurement-invariance and family/publisher/reasoning composition checks. A failure is a result to report, not a reason to silently change the battery.
3. Replicate structure with WILD common items and v2 Open LLM subtask results. Keep their populations/scales distinct until anchor equivalence is established. Later snapshots or disjoint model families can provide confirmation rather than reusing discovery data.
4. Extend past June 2026 using a new constituent-score snapshot (EEE/AA or equivalent) only after matching definitions. The acquired AA data do not yet extend the primary series to October 2026.
5. Use Arena history for external validity and DataDecide as a separate controlled training-time analysis.

No new factor models were fitted. Numeric feasibility is improved; longitudinal construct validity remains to be tested. Input hashes and software versions are recorded in audit.json.
