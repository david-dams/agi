# Dataset acquisition status

Historical acquisition notes, 2026-10-25. Later downloads and audits supersede the missing-file table below; consult `output/downloaded-data-audit/README.md` for verified status.

## Retrieved locally

| Source | File | Data rows | Columns |
|---|---|---:|---:|
| AA July 2026 snapshot | `aa-snapshot/aa_analysis_models.csv` | 421 | 34 |
| Observational Scaling Laws, pretrained models | `obsscaling/base_llm_benchmark_eval.csv` | 148 | 13 |
| Observational Scaling Laws, instruction models | `obsscaling/instruct_llm_benchmark_eval.csv` | 27 | 14 |
| Estonian LLM leaderboard | `estonian/summary.csv` | 98 | 15 |

AA's `aa_snapshot_manifest.json` was also recovered. That manifest's SHA256 describes the authors' original HTML snapshot, not our CSV.

These five files were reconstructed from complete line-numbered plain-text browser responses, with LF line endings. Every expected source line was collected and each CSV has a consistent field count. Their local hashes and source URLs are in `acquisition-manifest.json`. They are usable text copies, **not yet byte-verified original downloads**. The recovery did not infer or fill missing cells. AA's table has 96 complete configurations on the twelve primary benchmarks, matching the paper's count: four released in 2024, 43 in 2025 and 49 in 2026.

The pre-existing Epoch ZIP, cached historical LiveBench data and three downloaded modern LiveBench CSVs remain available elsewhere in the repository.

## Missing

| Source | Still needed | Reason / supplied acquisition route |
|---|---|---|
| AA | Original raw HTML, raw parsed table, analysis bundle and byte-original CSV | Direct network DNS fails; fetch complete research repository ZIP with batch script. |
| WILD | Score Parquet, item Parquet and remaining repository metadata | Binary downloads unavailable through browser; batch script downloads dataset. Full raw conversations are optional below. |
| HELM | Versioned summary JSON; selected run specs and item results afterward | GCS DNS fails. Batch helper lists public release objects and downloads core-scenario summaries, pinned by object generation. It does not download full response corpora. |
| Open LLM Leaderboard v1/v2 | Contents and detailed aggregate results | HF DNS fails. Batch script downloads both archives where available. Per-model `*-details` repositories are not included. |
| EEE | Full AA/HELM/LiveBench/OpenCompass records, snapshot index and provenance | HF DNS fails. Batch script fetches selected `data/` collections and flat index metadata, not capped viewer samples or duplicate flat objects. |
| Arena | Full historical leaderboard data | HF DNS fails; included in batch script. |
| DataDecide | Aggregate checkpoint evaluation data | HF DNS fails; included in batch script. Instance-level corpora are optional below. |
| ObsScaling / Estonian | Byte-original repository bundles and auxiliary files | Full bundles included in batch script. |
| MetaBench / tinyBenchmarks / Pythia | Repository evaluation material | Included as repository ZIPs. Git submodules/LFS objects and Pythia model weights are not fetched by ZIP download. |
| AIMS Measurement Data Bank | Gated metadata and selected compatible response tables | Requires accepting the HF dataset terms and authenticating on the host. Separate metadata-only command below. |
| OpenCompass / EuroEval / Japanese boards | Verified export URLs and appropriate versioned raw result files | Discovery leads, not verified batch targets. No fabricated download endpoint supplied. |
| LiveBench 2.0 | Verified current task export and version metadata | Proposed endpoint could not be retrieved. Batch downloads the known v1 export repository; this does not acquire 2.0. |
| Large-scale factor-analysis paper corpus | Released model-by-benchmark matrix, if publicly distributed | No downloadable corpus located in the source search. |

Direct probes to raw.githubusercontent.com, huggingface.co and storage.googleapis.com all failed with `Temporary failure in name resolution`. Attempts to retrieve AA raw CSV, density/overlap files and EEE manifest through the browser also failed. Failure to acquire them here does not prove that they are absent upstream.

## Run the remaining downloads on the host

The script uses an existing `hf` CLI, otherwise `uvx --from huggingface_hub hf`. It continues after individual failures and prints a status table. Exit 2 means at least one operation failed. Budget several GB plus potentially many small files; Open LLM detailed results can take a while. Full WILD conversations, DataDecide instances and AIMS corpora are excluded from this default batch.

```bash
cd /path/to/public-gai
bash download_public_datasets.sh 2>&1 | tee public-data-download.log
```

Completed data go under `public-data/`. Hugging Face revisions are pinned and recorded per dataset. Repository ZIPs use current `main`; their source URLs and downloaded hashes are recorded. Logs and status go to `public-data/logs/` and `public-data/download-status.tsv`. `host-download-manifest.json` hashes completed files. Re-running reuses the HF local download metadata but resolves the then-current source revision.

The batch script passed Bash syntax checking. HELM helper tests cover object-generation pinning and incomplete-size rejection. The real host downloads cannot be verified until this command runs with working network access. Some source repositories or object layouts may have moved; those are reported as failures.

### Optional large item/response corpora

```bash
cd /path/to/public-gai
uvx --from huggingface_hub hf download kensho/WILD-raw --repo-type dataset --local-dir public-data/wild-raw
uvx --from huggingface_hub hf download allenai/DataDecide-eval-instances --repo-type dataset --local-dir public-data/datadecide-instances
```

These can be much larger than the summary data. Their total download sizes were not verified. They are not required for the initial coverage audit; WILD's ordinary score dataset already provides item-level correctness.

### Optional AIMS metadata, after accepting access conditions

Accept conditions at https://huggingface.co/datasets/aims-foundations/measurement-db, then authenticate locally. Do not send a token in chat.

```bash
uvx --from huggingface_hub hf auth login
uvx --from huggingface_hub hf download aims-foundations/measurement-db \
  --repo-type dataset --local-dir public-data/aims-metadata \
  --include 'README.md' 'data_manifest.json' '**/metadata.yaml' '**/characterization.yaml' '**/formatted_tables/benchmarks.parquet'
```

This requests metadata/catalog files only. Select relevant response tables after inspecting coverage and upstream terms; the complete repository is very large.
