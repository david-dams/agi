# Reproducing the public analyses

Run commands from this repository root after `uv sync`. These are the existing analysis procedures; no analyses were rerun during the move. Raw inputs are local and excluded from Git. Saved compact AA matrices permit PCA and CFA extensions without downloads. See README.md for the dependency order and data acquisition limits.

## Public longitudinal data audit

`livebench_feasibility.py` audits public LiveBench results independently of the
internal benchmark inputs. It pins downloaded files, reconstructs retrospective
question batteries, measures complete model/task coverage and release overlap,
and checks public subtask scores when matching exports are available.

```sh
uv run livebench_feasibility.py --refresh     # discover and cache public inputs
uv run livebench_feasibility.py --offline     # replay the pinned snapshot
uv run livebench_feasibility.py --self-check  # synthetic tests; no network
```

Results and current limitations are in [feasibility/livebench/README.md](feasibility/livebench/README.md).
The raw cache is local and ignored by git; retain it with `manifest.json` to
replay a snapshot. Exit code 2 means acquisition was blocked or partial. This
audit does not fit factors or treat old release labels as historical publication
snapshots. Python 3.12+ with NumPy and PyArrow also works without `uv`.

## Public latent-factor analysis

```sh
uv run public_gai_factor.py --seed 0 --resamples 1000
python -m unittest discover -s tests -v
```

The frozen primary panel is August 18, 2024 (July 26 battery): 65 complete models
and 18 tasks. The analysis fits one-factor and identified three-group models,
uses paired-item and family/item bootstrap intervals, checks group rediscovery,
and compares historical archives with matched cohorts. Model-family curation and
provenance are in `public_model_families.csv`; unresolved identities remain
singleton clusters. The script does not download data or read internal runs.

Results are written to `output/public-gai/`, including `report.pdf`, numeric CSVs,
bootstrap diagnostics and provenance metadata. Intervals are withheld below 90%
admissible replicates. Scores are relative to the selected panel; archive dates
do not establish model-release cohorts or a multi-year gAI trend.

## Modern aggregate exports

```sh
uv run modern_gai_factor.py --resamples 200 --seed 0
```

Reads downloaded `livebench-tables/table_*.csv` and writes a separate
`output/modern-gai/README.md`, fit statistics, loadings, resampling diagnostics
and input/code hashes. Includes full panels and the matched 2025 cohort.
Aggregate inputs support configuration sensitivity, not item bootstrap.
Battery dates do not establish publication snapshots; task names alone do not
establish unchanged questions or scoring.

## Epoch ZIP feasibility audit

```sh
uv run epoch_data_audit.py --zip benchmark_data.zip
```

Audits raw benchmark exports and ECI constituent scores separately, without
extracting the ZIP or fitting factors. Results in `output/epoch-audit/README.md`
and `audit.json` cover exact configuration joins, conflicting scores, release
cohorts, complete-panel screening, evaluation dates and provenance limitations.
Input members and audit code are hashed. The download is a current snapshot,
not an archive of historical leaderboard states.

To search for identical complete benchmark batteries across release years:

```sh
uv run epoch_cohort_overlap.py
```

`output/epoch-cohorts/README.md` reports exhaustive shared-battery coverage
through nine benchmarks with at least five configurations in every cohort.
Exact memberships and diversity diagnostics are in `overlap.json`. A common
benchmark label does not verify equal prompts, harnesses or compute budgets.

## Audit the acquired public datasets

```sh
uv run downloaded_data_audit.py
```

Run the AA release-cohort analysis, with matched CritPt inclusion/exclusion and 1,000 base-model cluster resamples:

```bash
uv run aa_cohort_factor.py --resamples 1000 --seed 20261026
```

Results and interpretation: [AA cohort findings](output/aa-cohort/FINDINGS.md). This compares release vintages in a frozen snapshot; it does not reconstruct scores observed at historical dates.

For the exploratory CFA extension with coding and academic/knowledge residual covariance blocks, reuse the saved cohort inputs and matched bootstrap draws:

```bash
uv run aa_residual_cfa.py --resamples 1000
uv run aa_residual_cfa_plot.py
```

Results: [AA residual CFA](output/aa-residual-cfa/README.md). Residual blocks are fixed before these fits; their pairwise correlations are freely estimated, including negative values.

For cluster-bootstrap loading invariance, fixed partial-invariance candidates, and a covariance-null cluster calibration of the expanded residual model:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run aa_invariance_study.py --bootstrap 2000 --null 500 --workers 4
uv run aa_invariance_report.py
```

The [invariance report](output/aa-invariance/README.md) separates relative from absolute fit and reports boundary/failed fits, conditional bootstrap ranges, loading diagnostics, and conservative null-test failure bounds. The null transform retains whole-family resampling but changes score margins; it is conditional on the specified residual structure.

For dominant-direction comparisons without CFA residual assumptions, use covariance PCA in one frozen pooled benchmark metric:

```bash
OPENBLAS_NUM_THREADS=1 uv run aa_cohort_pca.py --resamples 2000
uv run aa_pca_plot.py
```

[PCA findings](output/aa-pca/FINDINGS.md) compare cohort PC1 directions, explained variance and spectral separation with matched named-base cluster uncertainty. Congruence/cosine similarity does not establish an identical latent construct or CFA invariance.

To calibrate PCA rotation against shared-leading-axis covariance nulls:

```bash
OPENBLAS_NUM_THREADS=1 uv run aa_pca_null.py --resamples 2000
uv run aa_pca_null_plot.py
```

[Shared-axis null findings](output/aa-pca-null/FINDINGS.md) cover projected and spectrum-preserving null covariances, exact-size and global cluster sampling, pairwise/omnibus calibration, spectral checks and null-generating assumptions. These tests concern covariance geometry, not causal changes in latent intelligence.

Reads the completed host downloads and repository ZIPs offline. The report in
`output/downloaded-data-audit/README.md` evaluates AA release cohorts, WILD item
coverage, Open LLM run protocols, Arena history, DataDecide checkpoints and the
full LiveBench export archive. Membership tables and input hashes accompany it.
The audit does not fit a factor model or establish measurement invariance.

