# Public datasets for longitudinal gAI: source search

Search date: 2026-10-25. Purpose: identify public **evaluation results**, rather than just question datasets, that could support broad latent-factor analysis and comparisons over time.

## What this search changes

Our earlier conclusion was too broad. The coverage limitations demonstrated for the downloaded Epoch ZIP do not establish that suitable data are unavailable elsewhere. There are materially stronger candidates, particularly a released Artificial Analysis snapshot, WILD, HELM archives, and the Open LLM Leaderboard archives.

This is a systematic search across evaluation suites, repositories, Hugging Face datasets, published psychometric work, training-checkpoint corpora, regional evaluations and historical preference data. It cannot certify that every dataset on the internet has been found. Public source pages and selected files were inspected; new source matrices have not been downloaded and audited locally.

Evidence labels:

- **File inspected:** a machine-readable result file was opened and its schema inspected.
- **Primary documentation:** the maintainer's repository, dataset card or documentation describes the data. Counts are publisher-reported, not independently reproduced.
- **Lead:** relevant resource found, but result files or access could not be verified.

## Priority candidates

### 1. Artificial Analysis research snapshot: strongest immediate contemporary matrix

**File inspected.** The public repository accompanying *One Capability or Many?* distributes a July 6, 2026 snapshot. Its analysis CSV has 421 configuration rows and constituent benchmark columns, including GPQA, HLE, Omniscience, tau2, IFBench, long-context reasoning, SciCode, CritPt, Terminal-Bench Hard, GDPval, Terminal-Bench 2.1 and tau Banking. It also contains release dates, names, reasoning flags, and metadata. Missing scores are explicit blanks; the Intelligence Index column is a composite and must be excluded from factor inputs.

The paper reports 96 complete configurations on twelve benchmarks, reduced to 89 base models in its deduplicated analysis. These counts need independent reproduction from the actual file. This is a substantial improvement over the four-indicator Epoch candidate, but it is one historical snapshot and does not prove adequate coverage within every release cohort. Effort settings, evaluation versions and repeated base models still need auditing. The repository distinguishes its source-site terms from its own code/data licenses; a public mirror does not settle upstream publication rights.

Sources: [repository and file inventory](https://github.com/louisyzhu/frontier-ai-economic-validity), [analysis CSV](https://raw.githubusercontent.com/louisyzhu/frontier-ai-economic-validity/main/data/processed/aa_analysis_models.csv), [paper's coverage and design](https://arxiv.org/html/2608.29420v1).

### 2. WILD: strongest new item-level structural candidate

**Primary documentation.** Kensho's Wide-scale Item Level Dataset reports 65 models, 27 benchmarks, 163 subtasks, 109,566 unique items and about 7.24 million model/item observations. Binary scores, model identifiers, item IDs and token counts are supplied; WILD-raw contains response content. The model list includes GPT-4.1 variants, GPT-4o, Claude 3/3.5, Qwen 1.5/2/2.5, Llama 3 variants, Phi-4, OLMo and other open models.

This is much broader than the small Epoch panel and allows investigation of common items and item-resampling uncertainty. It is not a current frontier census or a sequence of archived evaluations. It may support retrospective release cohorts after model dates and coverage are checked. Do not treat its 163 related subtasks as 163 independent capabilities, or assume every model answered every item. The card labels the dataset Apache 2.0; inspect upstream benchmark terms separately.

Sources: [WILD card](https://huggingface.co/datasets/kensho/WILD), [model and task inventory](https://huggingface.co/datasets/kensho/WILD/blob/main/README.md), [raw responses](https://huggingface.co/datasets/kensho/WILD-raw).

### 3. HELM Classic, Lite and Capabilities: strongest documented evaluation archives

**Primary documentation.** HELM publishes aggregate results and full prompts/responses in an unauthenticated public Google Cloud Storage bucket. Its documentation provides release and suite download paths. Treat Classic, Lite and Capabilities as distinct batteries, with versioned adapters and scenario definitions, rather than concatenating their scores.

Capabilities launched in March 2025 with 22 models and five scenarios: MMLU-Pro, GPQA, IFEval, WildBench and Omni-MATH. Its prompt and grading documentation is substantially more explicit than a heterogeneous score aggregator. Older Classic/Lite results provide earlier coverage and potentially more scenario/subscenario indicators. Release-specific common-model and common-question intersections still need extraction.

Important limitation: HELM entered maintenance mode on June 1, 2026; the official policy says no new evaluations will be added to its leaderboards. It is useful historical material, not a guaranteed feed of new frontier measurements.

Sources: [raw download documentation](https://crfm-helm.readthedocs.io/en/v0.5.8/downloading_raw_results/), [Capabilities methodology](https://crfm.stanford.edu/2025/03/20/helm-capabilities.html), [maintenance policy](https://crfm-helm.readthedocs.io/en/latest/maintenance_mode/).

Selective entry points, not instructions to download the entire bucket:

```
gs://crfm-helm-public/benchmark_output
gs://crfm-helm-public/lite/benchmark_output
gs://crfm-helm-public/capabilities/benchmark_output
```

### 4. Open LLM Leaderboard v1 and v2: strongest large open-model archives

**Primary documentation and table schema inspected.** The v2 contents table displays about 4.58k rows and six benchmark scores: IFEval, BBH, MATH level 5, GPQA, MuSR and MMLU-Pro. It includes raw and normalized scores, model SHA, precision, flags, base-model metadata, submission date and Hub upload date. Detailed results and per-model detail datasets permit subtask/item analysis where retained. The v1 archive uses ARC, HellaSwag, MMLU, TruthfulQA, Winogrande and GSM8K.

These are separate instruments; do not join v1/v2 averages as one scale. Raw task scores are preferable to normalized/clipped leaderboard scores for our audit. Repository history can provide archived states, but submission/upload dates are not verified model release dates. Thousands of merges and fine-tunes are not thousands of independent model families. Current closed frontier models are largely outside scope.

The collection labels v2 as 2024–2025 and v1 as 2023–2024. The v2 result viewer currently reports a schema-generation error; that is not proof that the underlying JSON files are unavailable.

Sources: [official archived collection](https://huggingface.co/collections/OpenEvals/archived-open-llm-leaderboard-2024-2025), [v2 contents](https://huggingface.co/datasets/open-llm-leaderboard/contents), [v2 result files](https://huggingface.co/datasets/open-llm-leaderboard/results), [v1 methodology/archive](https://github.com/huggingface/leaderboards/blob/main/docs/source/en/open_llm_leaderboard/archive.md).

### 5. Every Eval Ever: strongest discovery and dated-record collection

**Primary documentation and repository tree inspected.** EEE consolidates evaluation runs from leaderboards, papers and local evaluations, with source metadata, retrieval timestamps and optional item-level companion files. Its public repository tree shows an October 24, 2026 Artificial Analysis ingestion and a same-date flat rebuild. That is useful evidence of a contemporary collection, not evidence that all records contain detailed benchmark scores or an uninterrupted historical series.

Use the content-addressed `flat/latest_manifest.json` and its linked entry index, or full `data/` records. The dataset card explicitly warns that viewer Parquets contain samples capped at 100 rows per collection. Do not use those samples to estimate corpus coverage. The manifest endpoint could not be fetched through our browsing tool, so current complete counts and AA field coverage remain unverified. Its schema cannot recover settings absent from upstream sources. MIT labeling on the collection does not override upstream terms.

Sources: [dataset and loading contract](https://huggingface.co/datasets/evaleval/EEE_datastore), [dated repository tree](https://huggingface.co/datasets/evaleval/EEE_datastore/tree/main), [flat snapshot layout](https://huggingface.co/datasets/evaleval/EEE_datastore/tree/main/flat).

### 6. AIMS Measurement Data Bank: useful curated item-level source bank

**Primary documentation; access gated.** Stanford's collection preserves raw source captures, standardized item/response tables, metadata and content hashes. Its current card requires agreeing to share Hugging Face account information before file access. It preserves repository history and documents withheld datasets when upstream reproducibility fails.

The public site advertises hundreds of benchmarks, but those counts include different AI systems and task types. They must not be read as the dimensions of one dense LLM matrix. The HF card distinguishes validated migrations, release holds and archived observations. This is valuable for finding well-documented compatible subsets, not an already verified gAI panel. Curation is CC BY-SA 4.0; upstream materials retain their own terms.

Sources: [dataset/access/curation policy](https://huggingface.co/datasets/aims-foundations/measurement-db), [catalog](https://aims.stanford.edu/measurement-db).

## Additional sources and why they matter

| Source | Evidence and available material | Time interpretation | Suitability / remaining problem |
|---|---|---|---|
| [DataDecide](https://huggingface.co/datasets/allenai/DataDecide-eval-results) | Primary card: 1.41M task-result rows; recipe, model size, seed, training step, tokens and compute; 66 task labels including MMLU subtests. [Project](https://github.com/allenai/DataDecide) describes 25 corpora, 14 sizes and three seeds. [Item responses](https://huggingface.co/datasets/allenai/DataDecide-eval-instances) also released. | Genuine training progression. | Strong controlled longitudinal alternative. Models are small, up to 1B; this answers development during training, not frontier progress by calendar date. Repeated checkpoints require dependent-data methods. |
| [Pythia](https://github.com/EleutherAI/pythia) | Primary repository: shared training data/order, 154 saved checkpoints, evaluation material. | Training steps. | Useful controlled baseline. Saved weights alone do not establish a complete common evaluation matrix at every checkpoint. |
| [IRSL response matrices](https://github.com/aims-foundations/irsl) | Primary repository documents training-checkpoint and test-time response datasets, including `stair-lab/irsl_downstream_resmat`. | Training steps or test-time sampling budget. | Direct measurement/linking resource; not a broad multi-provider calendar history. |
| [Observational Scaling Laws](https://github.com/ryoungj/ObsScaling) | Primary repo releases metadata/evaluations for nearly 150 pretrained and instruction-tuned models; `eval_results/` CSVs. | Retrospective model generations, mostly an older research snapshot. | Useful reproducible historical baseline, not contemporary frontier coverage. |
| [MetaBench](https://github.com/adkipnis/metabench) | Primary repo and [paper](https://arxiv.org/abs/2407.12844) derive sparse tests from >5,000 Open LLM Leaderboard models. | Mostly archived leaderboard populations. | Useful measurement calibration and data-processing precedent; not independent evidence added to its parent leaderboard. Do not use reconstructed scores as observed indicators. |
| [tinyBenchmarks](https://github.com/felipemaiapolo/tinyBenchmarks/blob/main/README.md) | Primary repo releases small anchor sets and estimation tools derived from leaderboard/HELM data. | Original research splits and prospective evaluations. | Can reduce the cost of future evaluation, but predicted full-benchmark scores cannot independently validate the factor structure used to construct them. |
| [OpenCompass / CompassRank](https://github.com/open-compass/opencompass) | Primary platform supports open and API models across 100+ datasets and publishes leaderboard links. | Potential version/month snapshots. | High-priority discovery lead for a broader recent matrix. Actual historical result exports, current counts and harness consistency not verified. Client-rendered board and a versioned CDN URL could not be read here; supported task count is not observed matrix size. |
| [EuroEval, formerly ScandEval](https://github.com/EuroEval/EuroEval) | Primary [site](https://euroeval.com/leaderboards/) covers 30+ European languages. A maintainer [documents downloading raw leaderboard results](https://github.com/EuroEval/EuroEval/discussions/1323). | Evolving evaluation versions and model generations. | Promising regional replication and language breadth. Need raw archive, common-version coverage and language-specific battery audit. |
| [Open Japanese LLM Leaderboard / llm-jp](https://llm-jp.github.io/awesome-japanese-llm/en/) | Primary project index documents multi-task Japanese evaluation resources and dashboards. | Model generations within versioned Japanese suites. | Useful regional extension; no complete export or historical common panel verified in this pass. |
| [Estonian leaderboard data](https://github.com/keeleinstituut/leaderboard-data-ui) | Maintainer repo documents `summary.csv`, `models.json`, nested scores and timestamped per-run `results.jsonl`. | Model release dates plus evaluation timestamps. | Concrete additional source; language-specific construct and coverage still need checking. |
| [Arena historical leaderboard dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset) | Official `full` and `latest` splits, category scores and publication dates. | Genuine published leaderboard history. | Strong timeline source for preference validity. Not a fixed objective battery: methods, opponents, prompts and voting populations change. Rating offsets and style control changes must be respected. |
| [Arena-Hard-Auto](https://github.com/lmarena/arena-hard-auto) | Primary evaluation repo with answer/judgment workflows and results. | Fixed benchmark versions, plus model additions. | Complementary judged response quality. One benchmark and its categories do not automatically establish independent capability domains; judge/version effects. |
| [BIG-bench](https://github.com/google/BIG-bench/blob/main/README.md?plain=1) | Maintainer reports >200 tasks and 24-task Lite subset; [score JSON convention](https://github.com/google/BIG-bench/blob/main/docs/model_eval_contribution.md) records model family/size and shots. | Mostly historical scale/model comparisons; Git revisions record contributions. | Broad task content, but current frontier and across-year model coverage need checking. |
| [Papers with Code evaluation dumps](https://github.com/paperswithcode/paperswithcode-data) | Maintainer links downloadable evaluation-table archives, CC BY-SA. | Dated papers and archived dumps. | Broad historical discovery source. Mixed self-reports, model identity ambiguity and missing setup metadata prevent assuming a consistent battery. Repository's daily-refresh prose alone does not establish current freshness. |
| [BenchLM downloads](https://benchlm.ai/data) | Publisher offers JSON with model scores/provenance and current export metadata. | Mainly current exports; selected historical views. | Secondary aggregator, often reuses sources above. CC BY-NC export terms and source-specific protocols; no independent dense matrix verified. |
| [aicharts snapshots](https://aicharts.io/data) | Publisher documents current and frozen older AA index snapshots. | Actual retained snapshot cohorts. | Checked availability, but displayed Intelligence Index composites are insufficient for factor inputs. Constituent score history unverified. |
| [Datazimuts monthly scores](https://datazimuts.com/en/datasets/llm_benchmark_signals/llm_benchmark_scores_monthly) | Publisher describes an Arena/Epoch monthly merge, but says full snapshot is not published; sample downloads only. | Intended monthly snapshots. | Not usable as a full dataset now. It would also largely duplicate sources already found. |
| [2026 large-scale factor-analysis paper](https://arxiv.org/html/2609.36515v1) | Authors report 13,251 scores, 1,618 models, 456 text benchmarks and a release-date analysis. | Cross-section with retrospective dates. | Broad discovery map, not a verified released matrix: no downloadable corpus located. Paper acknowledges heterogeneous setups, averaged disagreements, imputation and weaker date evidence. Do not inherit its estimates or inferred metadata. |
| [2023 capability-structure paper](https://arxiv.org/abs/2306.10062) | Authors analyze 29 models across 27 HELM cognitive tasks. | Historical research snapshot. | A structural replication reference, not a current or independent dataset beyond HELM. |
| [2026 construct-validity study](https://arxiv.org/html/2602.15532v1) | Primary paper analyzes Open LLM Leaderboard task structure and model scale. | Archived leaderboard cohort. | Relevant CFA/scale-control design reference; not a new independent frontier corpus. |

## Recheck of sources already used

- **Epoch:** local audit still stands for the downloaded ZIP. Its sparse matrix is one source, not an upper bound on public-data feasibility.
- **LiveBench v1:** eleven battery-version files were located previously. Git history and full-file acquisition remain necessary for a historical-state study; the three locally downloaded tables are not the entire collection.
- **LiveBench 2.0:** a fresh search found an official-site search result describing an October 2026 long-horizon release. Direct page reads returned a JavaScript shell; reported CSV endpoints could not be retrieved. Record this as a **lead requiring acquisition**, not as a verified local dataset. Do not splice 1.0 and 2.0 score scales. [Official site](https://livebench.ai/), [previous public export repository](https://github.com/LiveBench/livebench.github.io/tree/main/public).
- **Artificial Analysis API:** its current [reference](https://artificialanalysis.ai/data-api/docs/reference) distinguishes free headline indices from paid constituent scores. The public research snapshot is an additional acquisition route; publication terms and original data provenance still matter.

## What to do with these findings

1. **Audit the actual AA analysis CSV first:** reproduce observed/complete counts; exclude composites and estimated aggregate fields; enumerate release cohorts, effort variants and model families. Inspect its reported 96-by-12 complete subset and whether early/late cohorts retain enough rows. Use it to specify a hypothesis, not to claim confirmation on the same discovery rows.
2. **Audit WILD next:** aggregate observed item scores into predeclared benchmark/subtask indicators, verify common item IDs and exact model identities, attach verified release dates, and inspect family/domain balance. Preserve a disjoint model/family or later-release confirmation sample if feasible.
3. **Inventory HELM releases without bulk raw download:** fetch release/suite metadata and summary tables, then request only necessary run specs and item scores. Measure cross-release common models, prompts, instances and graders.
4. **Query full EEE records selectively:** search AA, HELM, OpenCompass and relevant benchmark collections. Preserve source/version/retrieval metadata and deduplicate against the other inputs. Do not use its capped viewer samples for the coverage audit.
5. **Use Open LLM Leaderboard v2 for an explicitly open-model historical study**, with raw scores, task versions and family-balanced cohort sampling. Treat present-day frontier generalization as a separate question.
6. **If a controlled time axis is the priority, use DataDecide or checkpoint response matrices.** Name the study “capability structure during training”; do not present training steps as historical frontier progress.

A suitable source may permit flat CFA or a multi-group invariance study, but public availability and high row counts do not establish identifiability, domain coverage, model independence, or measurement invariance. None of the newly located sources has yet passed those checks here.

## Acquisition limits in this search

Shell network access still fails DNS resolution. Browsing retrieved public documentation, repository listings and the AA CSV, but some direct object downloads/CDN assets were inaccessible. No bulk datasets, gated files, API credentials or paid access were obtained. Endpoint failures are recorded as acquisition failures, not as evidence that the underlying data do not exist.

No new fits or software dependencies were introduced. This is a source-discovery report; the earlier numeric studies remain unchanged.
