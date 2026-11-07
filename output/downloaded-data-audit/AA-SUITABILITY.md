# Does AA actually support the proposed longitudinal gAI study?

Verdict: **yes for an exploratory retrospective release-cohort analysis; not yet a verified longitudinal measurement panel or a historical snapshot series.** The earlier coverage audit establishes availability, but overstates readiness if read as approval for comparable CFA trends.

## Verified against the original archived page

Input: `public-data/archives/aa-bundle.zip`, the [Zhu reproducibility bundle](https://github.com/louisyzhu/frontier-ai-economic-validity), rather than a direct AA API download. The embedded manifest dates capture to 2026-07-06 15:17:51 UTC. The archived HTML matches its SHA-256. Our independent parser finds the full 548-model score array (alongside a separate navigation array).

All 4,210 checked cells in the 421-row processed table—nine proposed scores plus release date—match the embedded source, allowing 1e-12 floating-point serialization tolerance. The original source itself contains 409 configurations with all nine numeric fields. The complete-case density therefore does not result from this paper filling missing cells. The extraction notebook copies these fields and filters rows; it does not impute them during extraction. This does not independently certify how AA produced each score upstream.

| Release cohort | Nine scores present | Composite index estimated | Composite index not estimated | CritPt exactly zero |
|---|---:|---:|---:|---:|
| 2025H1 | 59 | 43 | 16 | 45 (76%) |
| 2025H2 | 176 | 148 | 28 | 123 (70%) |
| 2026H1 | 152 | 103 | 49 | 48 (32%) |

`intelligenceIndexIsEstimated` is explicitly an index-level flag. We exclude the composite from the factor model, so it is incorrect to infer that all nine component values are estimated, or to call 16/28/49 the only independently evaluated cohort sizes. The source contains per-evaluation token metadata for GPQA, HLE, Omniscience, IFBench, SciCode and CritPt in every one of these rows, including index-flagged rows. Token records corroborate evaluation activity; they do not prove score provenance or protocol equality. Other task token records are incomplete. The page offers no separate per-component estimated flags in this payload.

## Comparability audit

The current [AA methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking) documents model-dependent temperature/output allowances, benchmark replacements, grader changes, and a SciCode regrading. Consequently, matching column names across captures is insufficient. These current disclosures are not a captured July methodology and cannot certify each July cell's protocol.

The archived model objects have no per-cell run dates, dataset/grader versions, endpoint revisions, question responses or item scores. Release date is a model attribute, not an evaluation timestamp. Configuration effort often appears in names/slugs; there is no uniform effort field in the archived objects. Shared model IDs are retained in the raw payload and should be restored for subsequent joins. The current [API reference](https://artificialanalysis.ai/api-reference) documents a keyed model endpoint, but no historical LLM-score query in its public specification. Commercial capabilities were not inspected.

The current nine-score panel therefore allows **a single-snapshot comparison of release vintages**, conditional on AA's evaluation process. It does not establish which scores were available at release or in each past calendar month. Later captures require explicit version bridges, not automatic appending.

## Consequences for the analysis

- A pooled flat factor model can be attempted now using the nine source scores. Negative Omniscience values are legitimate source values, not missing-value codes; generic 0–1 range checks would be wrong.
- Three cohort CFAs are numerically identifiable, but full rank is not evidence of suitable distributions, adequate effective sample size or invariance. CritPt's floor changes substantially between cohorts; AA-LCR also has 20/59 zeros in 2025H1. Ordinary Gaussian CFA deserves robust uncertainty and floor sensitivity. Any indicator removal must be applied to all cohorts and reported as a sensitivity, not chosen to manufacture a trend.
- Estimate common-scale capability levels separately from within-cohort general-factor strength. Mean/variance comparisons require appropriate measurement-invariance assumptions/tests. Different model-family, publisher and reasoning-effort composition can change correlations without any change in the underlying architecture of capability.
- Cohort sizes are configuration counts. Do not count effort variants as independent models. Curate a model-family/effort mapping and use clustered uncertainty; choose a configuration rule without maximizing its observed benchmark performance. The upstream notebook's deduplication chooses the highest index and uses pandas groupby.first, which can mix columns from different rows when values are missing; do not reuse that procedure for this study.
- A hierarchical CFA is not supplied by nine available columns. The source taxonomy has one long-context and one instruction-following indicator, so it does not identify a ready-made multi-domain hierarchy under our fitter's requirements.

## Study decision

Proceed with AA as an **exploratory, retrospective configuration-level cohort dataset**, after configuration mapping and with transparent floor/protocol sensitivities. Retain the frozen July snapshot for that comparison. Do not yet describe its results as a confirmed change in gAI structure, an independently replicated CFA, a representative sample of all LLMs, or a historically observed capability series. Protocol equivalence and measurement invariance remain unverified, not disproven.

Reproduce local checks: `python3 aa_provenance_audit.py`. Machine-readable evidence: `aa_provenance.json`. Two parser tests pass; no new factor models were fitted in this suitability audit.
