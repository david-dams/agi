# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2"]
# ///
"""Audit an Epoch benchmark ZIP without extracting it or fitting latent factors."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import hashlib
import io
import itertools
import json
from pathlib import Path
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parent
# File/column mappings verified against headers where the ZIP metadata leaves them blank.
SUPPLEMENTAL = {
    'ALE-Bench': ('ale_bench_external.csv', 'Performance'),
    'AlgoTune': ('algotune_external.csv', 'Score'),
    'Blueprint-Bench 2': ('blueprint_bench_2_external.csv', 'Score'),
    'BoolQ': ('bool_q_external.csv', 'Score'),
    'BTF-3': ('btf3_external.csv', 'Pooled score'),
    'CSQA2': ('common_sense_qa_2_external.csv', 'Score'),
    'CritPt': ('critpt_external.csv', 'Accuracy'),
    'CursorBench': ('cursorbench_external.csv', 'Score'),
    'DeepSWE': ('deepswe_external.csv', 'Pass@1'),
    'EnigmaEval': ('enigma_eval_external.csv', 'Accuracy'),
    'ForecastBench': ('forecastbench_external.csv', 'Overall score'),
    'FrontierMath-Erdos': ('frontiermath_erdos.csv', 'mean_score'),
    'GBAEval': ('gbaeval_external.csv', 'Overall score'),
    'GDP.pdf': ('gdp_pdf_external.csv', 'GDP.pdf score'),
    'HLE': ('hle_external.csv', 'Accuracy'),
    'LiveBench': ('live_bench_external.csv', 'Global average'),
    'MindCube': ('mindcube_external.csv', 'Overall score'),
    'SciCode': ('scicode_external.csv', 'Score'),
    'ScienceQA': ('science_qa_external.csv', 'Score'),
    'SpatialViz-Bench': ('spatialviz_bench_external.csv', 'Overall score'),
    'SpireClimb (Slay the Spire 1, Ascension 20 Heart)': ('spireclimb_sts1_a20_heart.csv', 'mean_score'),
    'SpireClimb (Slay the Spire 2, Ascension 10)': ('spireclimb_sts2_a10.csv', 'mean_score'),
    'Vending-Bench 2': ('vending_bench_2_external.csv', 'Score'),
    'VideoMME': ('video_mme_external.csv', 'Overall (no subtitles)'),
    'WebDev Arena': ('webdev_arena_external.csv', 'Arena Score'),
}


def read_csv(z, name):
    with z.open(name) as stream:
        reader = csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig'))
        if len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f'duplicate headers: {name}')
        return list(reader)


def unique_cells(records):
    """Keep a cell only when all finite reported scores agree; never pick the best."""
    grouped = defaultdict(list)
    invalid = 0
    for model, task, score in records:
        try:
            number = float(score)
            if not model or not np.isfinite(number):
                raise ValueError('missing identity or nonfinite score')
        except (TypeError, ValueError):
            invalid += 1
            continue
        grouped[model,task].append(number)
    conflict = {key: values for key,values in grouped.items() if len(set(values)) > 1}
    cells = {key: values[0] for key,values in grouped.items() if key not in conflict}
    return cells, dict(invalid_records=invalid, repeated_cells=sum(len(v)>1 for v in grouped.values()),
                      conflicting_cells=len(conflict), conflicts=[dict(model=k[0],benchmark=k[1],values=v) for k,v in sorted(conflict.items())])


def coverage(cells, dates, organizations):
    models = sorted({m for m,t in cells})
    tasks = sorted({t for m,t in cells})
    observed = {t: {m for m in models if (m,t) in cells} for t in tasks}
    panels = {}
    # Coverage-only greedy search, seeded at every benchmark. It is not exhaustive.
    for anchor in tasks:
        chosen = [anchor]
        shared = observed[anchor].copy()
        for _ in range(min(12,len(tasks))-1):
            candidates = [t for t in tasks if t not in chosen]
            task = min(candidates,key=lambda t: (-len(shared & observed[t]),t))
            chosen.append(task)
            shared &= observed[task]
            p = len(chosen)
            if p not in panels or (len(shared),tuple(sorted(chosen))) > (panels[p]['n'],tuple(panels[p]['tasks'])):
                panels[p] = dict(n=len(shared),tasks=sorted(chosen),models=sorted(shared))
    for panel in panels.values():
        panel['cohorts'] = dict(Counter((dates[m][:4] if m in dates else 'unknown') for m in panel['models']))
        panel['organizations'] = dict(Counter(organizations.get(m,'unknown') for m in panel['models']))
        if panel['n'] > len(panel['tasks']):
            X=np.array([[cells[m,t] for t in panel['tasks']] for m in panel['models']])
            panel['rank']=int(np.linalg.matrix_rank(X-X.mean(0)))
    cohorts=[]
    def release_year(m):
        return dates[m][:4] if m in dates else 'unknown'
    periods=sorted({release_year(m) for m in models})
    for year in periods:
        cohort={m for m in models if (dates[m][:4] if m in dates else 'unknown')==year}
        counts=sorted(((len(cohort&observed[t]),t) for t in tasks),reverse=True)
        best9=0; best9tasks=[]
        if len(tasks)>=9:
            for anchor in tasks:
                chosen=[anchor]; shared=cohort&observed[anchor]
                for _ in range(8):
                    task=min((t for t in tasks if t not in chosen),key=lambda t:(-len(shared&observed[t]),t))
                    chosen.append(task); shared &= observed[task]
                if len(shared)>best9: best9=len(shared); best9tasks=sorted(chosen)
        cohorts.append(dict(year=year,models=len(cohort),benchmarks_with_20_models=sum(n>=20 for n,t in counts),
                            benchmarks_with_50_models=sum(n>=50 for n,t in counts),top_benchmarks=counts[:12],
                            greedy_nine_benchmark_complete=best9,greedy_nine_benchmarks=best9tasks))
    pairwise=[dict(left=a,right=b,shared_models=len(observed[a]&observed[b])) for a,b in itertools.combinations(tasks,2)]
    return dict(models=len(models),benchmarks=len(tasks),observations=len(cells),density=len(cells)/(len(models)*len(tasks)),
        complete_all=len(set.intersection(*observed.values())),
        benchmark_counts={t:len(observed[t]) for t in tasks},cohorts=cohorts,
        greedy_panels={str(p):v for p,v in sorted(panels.items())},pairwise_overlap=pairwise)


def run(path,out):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP checksum failure')
        files={f.filename:dict(bytes=f.file_size,sha256=hashlib.sha256(z.read(f)).hexdigest()) for f in z.infolist() if not f.is_dir()}
        metadata=read_csv(z,'benchmark_metadata.csv')
        model_metadata=read_csv(z,'model_metadata.csv')
        processed=read_csv(z,'epoch_capabilities_index/processed_data_for_eci.csv')
        inventory=[]; records=[]; configdates=defaultdict(set); configorgs=defaultdict(set)
        lags=[]; raw_dates=[]; own_rows=0; best_diff=0; own_scored=0
        duplicate_meta={k:v for k,v in Counter(r['model_version'] for r in model_metadata if r['model_version']).items() if v>1}
        for original_meta in metadata:
            meta=original_meta.copy()
            supplemental=not bool(meta['source_file']) and meta['benchmark'] in SUPPLEMENTAL
            if supplemental:
                meta['source_file'],meta['score_column']=SUPPLEMENTAL[meta['benchmark']]
            name=meta['source_file']; column=meta['score_column']
            if not name or name not in z.namelist() or not column:
                inventory.append(dict(benchmark=meta['benchmark'],status='no declared source file/score column'))
                continue
            rows=read_csv(z,name)
            if rows and column not in rows[0]:
                raise ValueError(f'missing score column: {name}: {column}')
            own=not name.endswith('_external.csv')
            local=[]
            for row in rows:
                model=row['Model version'].strip(); score=row.get('mean_score') if own else row[column]
                local.append((model,meta['benchmark'],score))
                if meta['benchmark']!='LiveBench': records.append(local[-1])
                if row.get('Release date'): configdates[model].add(row['Release date'])
                if row.get('Organization'): configorgs[model].add(row['Organization'])
                if own:
                    own_rows+=1
                    if row.get('mean_score') and row.get('Best score (across scorers)'):
                        own_scored+=1
                        best_diff+=float(row['mean_score'])!=float(row['Best score (across scorers)'])
                if row.get('Started at'):
                    raw_dates.append(row['Started at'])
                    if row.get('Release date'):
                        lags.append((date.fromisoformat(row['Started at'][:10])-date.fromisoformat(row['Release date'])).days)
            cells,issues=unique_cells(local)
            dates=sorted({r['Release date'] for r in rows if r.get('Release date')})
            inventory.append(dict(benchmark=meta['benchmark'],status='audited',source_file=name,
                score_column='mean_score' if own else column,scale=meta['scale'],random_baseline=meta['random_baseline'],
                mapping='header-audited supplemental mapping' if supplemental else 'ZIP metadata',
                included_in_candidate_matrix=meta['benchmark']!='LiveBench',
                source_labels=dict(Counter(r.get('Source','') for r in rows)),
                score_ceiling=meta['score_ceiling'],superseded_by=meta['superseded_by'],epoch_run=own,rows=len(rows),
                unique_configurations=len({m for m,t in cells}),release_date_range=[dates[0],dates[-1]] if dates else [],
                has_evaluation_timestamp=bool(rows and 'Started at' in rows[0]),
                rows_with_log_link=sum(bool(r.get('Logs')) for r in rows),
                setting_columns=[c for c in (rows[0] if rows else {}) if any(w in c.lower() for w in ('harness','effort','prompt','format','provider'))],
                **issues))
        cells,raw_issues=unique_cells(records)
        dates={m:next(iter(v)) for m,v in configdates.items() if len(v)==1}
        orgs={m:next(iter(v)) for m,v in configorgs.items() if len(v)==1}
        groups=defaultdict(set); groupdates=defaultdict(set); grouporgs=defaultdict(set)
        version_groups=defaultdict(set)
        metamap=defaultdict(set)
        for r in model_metadata:
            if r['model_version'] and r['organization']:metamap[r['model_version']].add(r['organization'])
        for row in processed:
            groups[row['model_id']].add(row['model_version'])
            groupdates[row['model_id']].add(row['date'])
            version_groups[row['model_version']].add(row['model_id'])
            grouporgs[row['model_id']].update(metamap[row['model_version']])
        eci,eci_issues=unique_cells([(r['model_id'],r['benchmark'],r['performance']) for r in processed])
        eci_dates={m:next(iter(d)) for m,d in groupdates.items() if len(d)==1}
        eci_orgs={m:next(iter(o)) for m,o in grouporgs.items() if len(o)==1}
        own_names={r['benchmark'] for r in inventory if r.get('epoch_run')}
        active_own={r['benchmark'] for r in inventory if r.get('epoch_run') and not r['superseded_by'] and not r['source_file'].startswith('spireclimb_sts')}
        results=dict(zip_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),files=files,
            license_readme=z.read('README.md').decode(), csv_files=sum(n.endswith('.csv') for n in files),
            benchmark_metadata_rows=len(metadata),inventory=inventory,
            unconfigured_csvs=sorted(n for n in files if n.endswith('.csv') and n not in {m.get('source_file') for m in inventory} and '/' not in n and n not in {'benchmark_metadata.csv','model_metadata.csv'}),
            raw_cell_issues=raw_issues,eci_cell_issues=eci_issues,
            model_metadata_duplicate_keys=duplicate_meta,
            conflicting_release_dates={m:sorted(v) for m,v in configdates.items() if len(v)>1},
            conflicting_organizations={m:sorted(v) for m,v in configorgs.items() if len(v)>1},
            raw_date_range=[min(dates.values()),max(dates.values())],
            evaluation_timestamp_range=[min(raw_dates),max(raw_dates)],
            evaluation_lag_days=dict(count=len(lags),quantiles=np.quantile(lags,[0,.25,.5,.75,1]).tolist(),
                over_365_days=sum(d>365 for d in lags),negative=sum(d<0 for d in lags)),
            epoch_rows=own_rows,epoch_rows_with_both_scores=own_scored,mean_vs_best_different=best_diff,
            eci_models_using_multiple_versions=sum(len(v)>1 for v in groups.values()),
            eci_conflicting_release_dates={m:sorted(v) for m,v in groupdates.items() if len(v)>1},
            eci_versions_in_multiple_groups={v:sorted(g) for v,g in version_groups.items() if len(g)>1},
            eci_rows_benchmark_newer_than_model=sum(r['benchmark_release_date']>r['date'] for r in processed),
            eci_rows_with_blank_source=sum(not r['source'] for r in processed),
            coverage=dict(exact_configuration=coverage(cells,dates,orgs),
                epoch_runs=coverage({k:v for k,v in cells.items() if k[1] in own_names},dates,orgs),
                active_epoch_runs=coverage({k:v for k,v in cells.items() if k[1] in active_own},dates,orgs),
                eci_grouped=coverage(eci,eci_dates,eci_orgs)),
            eci_group_versions={m:sorted(v) for m,v in groups.items()},
            eci_model_names={r['model_id']:r['model'] for r in processed})
    out.mkdir(parents=True,exist_ok=True)
    results['audit_code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (out/'audit.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    render(results,out)
    return results


def render(r,out):
    lines=['# Epoch public-data feasibility audit','',
        'Verdict: useful for a retrospective model-release cohort study, subject to coverage and evaluation-setting controls. This ZIP is one current snapshot and does not reconstruct what was known at past dates. A representative longitudinal hierarchical-factor dataset has not yet been established.','',
        f"The ZIP contains {r['csv_files']} CSV files and {r['benchmark_metadata_rows']} benchmark metadata records. Raw configuration release dates span {r['raw_date_range'][0]} to {r['raw_date_range'][1]}. ECI constituent data are scores, not the ECI composite or its bootstraps.",'',
        '## Coverage','',
        '| Input | Models/configurations | Benchmarks | Observed cells | Density | Complete across all |',
        '|---|---:|---:|---:|---:|---:|']
    for label,c in r['coverage'].items():
        lines.append(f"| {label} | {c['models']} | {c['benchmarks']} | {c['observations']} | {c['density']:.1%} | {c['complete_all']} |")
    lines += ['', 'Raw matrices preserve exact configuration IDs. Conflicting scores for the same configuration/benchmark are excluded; equal-score repeats collapse. Epoch-run matrices use mean_score, avoiding an additional best-across-scorers selection. External matrices use the declared score column or an explicit header-audited supplemental mapping and retain source units. LiveBench Global average is inventoried but excluded as a composite. No scales are pooled into a composite or imputed. Active Epoch runs exclude superseded benchmarks and the two SpireClimb components when retaining the aggregate.','',
        '## Release cohorts','', '| Input | Release year | Models/configurations | Benchmarks with >=20 | Benchmarks with >=50 | Greedy complete on 9 benchmarks |','|---|---|---:|---:|---:|---:|']
    for label,c in r['coverage'].items():
        for co in c['cohorts']:
            lines.append(f"| {label} | {co['year']} | {co['models']} | {co['benchmarks_with_20_models']} | {co['benchmarks_with_50_models']} | {co['greedy_nine_benchmark_complete']} |")
    lines += ['', 'Benchmark threshold counts describe coverage separately for each benchmark. Nine-benchmark searches run separately within each year and may select different batteries, so those counts do not establish a fixed longitudinal panel. Unknown/conflicting dates are kept outside dated cohorts.','',
        '## Complete-panel search','',
        'Coverage-only greedy search seeded at every benchmark, without looking at scores. These are candidate panels, not proven global maxima or representative selections. Strong coverage can concentrate on one domain or organization.','',
        '| Input | Benchmarks | Complete configurations/groups | Benchmarks selected |','|---|---:|---:|---|']
    for label,c in r['coverage'].items():
        for p in ('3','6','8','9','12'):
            panel=c['greedy_panels'].get(p)
            if panel: lines.append(f"| {label} | {p} | {panel['n']} | {', '.join(panel['tasks'])} |")
    lines += ['', 'Exact panel memberships, release-year counts, organization counts, ranks and all pairwise overlaps are recorded in audit.json. Three-group hierarchy needs at least nine indicators, and domain breadth must be checked separately from numerical coverage.','',
        '## Provenance and comparability','',
        f"- {r['eci_models_using_multiple_versions']} of {r['coverage']['eci_grouped']['models']} ECI model groups use different configuration/version IDs across their benchmark observations. They cannot be treated as fixed effort/harness configurations.",
        f"- {len(r['eci_conflicting_release_dates'])} ECI groups have inconsistent dates across observations and are excluded from dated cohort assignment. Their dates remain in audit.json.",
        f"- {r['eci_rows_benchmark_newer_than_model']} ECI observations use a benchmark released after the model. This is retrospective evaluation coverage, not a historical as-published panel.",
        f"- Raw evaluation timestamps span {r['evaluation_timestamp_range'][0]} to {r['evaluation_timestamp_range'][1]}. Of {r['evaluation_lag_days']['count']} dated evaluations, {r['evaluation_lag_days']['over_365_days']} occurred more than a year after model release; {r['evaluation_lag_days']['negative']} have negative release-to-evaluation lags and need review.",
        f"- {r['raw_cell_issues']['conflicting_cells']} raw configuration/benchmark cells have differing reported values and were excluded. Full conflicting values are retained in audit.json. Duplicate model-metadata keys: {json.dumps(r['model_metadata_duplicate_keys'])}.",
        f"- mean_score differs from best-across-scorers in {r['mean_vs_best_different']}/{r['epoch_rows_with_both_scores']} Epoch-run records. ECI processing uses its own selection/transformation pipeline; do not infer an unprocessed fixed-configuration matrix from its labels.",
        '- ECI performance values are processed. For example, GPQA uses baseline/ceiling normalization. Positive affine normalization alone preserves Pearson correlations, but configuration selection, clipping, and nonlinear transformations require separate inspection.',
        f"- {r['eci_rows_with_blank_source']} ECI rows have blank source labels. This is not proof of missing provenance: some match Epoch-run files with log links. Availability of each linked log and its item-level content was not checked.",
        '- Exact model IDs alone do not establish identical agent harnesses, tool budgets, prompts, model providers, graders or question sets. External CSVs expose these fields inconsistently. Source metadata and per-run logs must be checked before combining them.',
        '- Superseded FrontierMath versions and component/aggregate benchmark overlap must not be treated as independent indicators. The metadata supplies some supersession links, not a complete overlap map.',
        '- Metadata leaves file mappings blank for some supplied CSVs, including HLE and SciCode. Supplemental mappings are explicit and recorded in inventory. Score direction and grading are not harmonized by this coverage audit.',
        '- The SciCode CSV already includes 226 records attributed to Artificial Analysis. This supplies one AA benchmark through Epoch, not the full historical AA score matrix.',
        '- Organization and accessibility are not sampling probabilities. The data emphasize publicly evaluated models; complete-case selection adds its own bias. Effort variants and related models require a declared sampling and family policy.','',
        '## Recommendation','',
        '1. Use a retrospective release-cohort design first. Pin exact model configuration, benchmark version and evaluation setup. Keep publication-history questions separate.',
        '2. Start with the active Epoch-run exact-configuration matrix as the most controlled candidate. Check a fixed, diverse anchor battery across release cohorts before committing to a hierarchical time trend. Coverage-only panels above are screening results.',
        '3. Use ECI grouped data as a separate sensitivity source after auditing configuration selection and score processing. Do not use ECI composite scores or ECI bootstrap draws to estimate independent general-factor structure.',
        '4. Compare domain-balanced batteries and broad versus frontier-only cohorts. Report when sample size or domain coverage cannot support three groups. Never silently fill sparse cells or regularize covariance to obtain a fit.',
        '   A model that explicitly handles sparse observations could retain more data than complete-case analysis, but requires a separate validated implementation and checks for nonrandom missingness. ECI coverage alone does not validate a sparse multidimensional hierarchy.',
        '5. Archive this ZIP now and future snapshots with hashes. Historical publication snapshots require additional archives; this download alone cannot supply them.','',
        '## Sources and reproduction','',
        'Source: Epoch AI, Capabilities & benchmarking, https://epoch.ai/benchmarks. ZIP README grants CC BY 4.0 with attribution. Source files retain external citations and context; third-party benchmark items and linked logs were not downloaded.','',
        f"ZIP SHA256: `{r['zip_sha256']}`. Every member and the audit script are hashed in audit.json. The download time and upstream snapshot revision were not supplied.",'',
        '```sh','uv run epoch_data_audit.py --zip benchmark_data.zip','```','',
        'This audit fits no latent factors. It checks feasibility before another model is estimated.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path,default=ROOT/'benchmark_data.zip')
    parser.add_argument('--out',type=Path,default=ROOT/'output/epoch-audit')
    args=parser.parse_args()
    run(args.zip,args.out)
    print(args.out/'README.md')
