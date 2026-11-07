# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2", "pyarrow>=17"]
# ///
"""Offline audit of acquired datasets for longitudinal gAI; no factor fits."""
from collections import Counter,defaultdict
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'public-data'
OUT=ROOT/'output/downloaded-data-audit'
CORE=('gpqa','hle','omniscience','tau2','ifbench','lcr','scicode','critpt','terminalbenchHard')
FULL=CORE+('gdpval_elo','terminalbenchV21','tauBanking')


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def period(value,kind):
    if not value:return 'unknown'
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if kind=='year':return str(d.year)
    if kind=='half':return f'{d.year}H{1+(d.month-1)//6}'
    return f'{d.year}Q{1+(d.month-1)//3}'


def aa_audit():
    path=DATA/'archives/aa-bundle.zip'
    with zipfile.ZipFile(path) as z:
        name=next(n for n in z.namelist() if n.endswith('/data/processed/aa_analysis_models.csv'))
        raw=z.read(name)
        rows=list(csv.DictReader(io.StringIO(raw.decode())))
        taxonomy_name=next(n for n in z.namelist() if n.endswith('/benchmark_taxonomy.csv'))
        taxonomy=list(csv.DictReader(io.StringIO(z.read(taxonomy_name).decode())))
    cohorts=[];panels={};memberships=[]
    for label,tasks in [('nine',CORE),('twelve',FULL)]:
        complete=[r for r in rows if all(r[t] for t in tasks)]
        X=np.array([[float(r[t]) for t in tasks] for r in complete])
        if not np.isfinite(X).all():raise ValueError('AA nonfinite score')
        for kind in ('year','half','quarter'):
            for value in sorted({period(r['releaseDate'],kind) for r in complete}):
                group=[r for r in complete if period(r['releaseDate'],kind)==value]
                x=np.array([[float(r[t]) for t in tasks] for r in group])
                sd=x.std(0,ddof=1) if len(x)>1 else np.zeros(len(tasks))
                R=np.corrcoef(x,rowvar=False) if len(x)>len(tasks) and np.all(sd>0) else None
                cohorts.append(dict(battery=label,period_kind=kind,period=value,configurations=len(group),
                    distinct_shortnames=len({r['shortName'] for r in group}),
                    publishers=dict(Counter(r['modelCreatorName'] for r in group)),
                    rank=int(np.linalg.matrix_rank(x-x.mean(0))) if len(x)>1 else 0,
                    min_eigenvalue=float(np.linalg.eigvalsh(R).min()) if R is not None else None,
                    reasoning=sum(r['isReasoning']=='True' for r in group),
                    open_weights=sum(r['isOpenWeights']=='True' for r in group)))
        for r in complete:
            memberships.append({k:r[k] for k in ('slug','name','shortName','releaseDate','modelCreatorName','isReasoning','isOpenWeights')}|dict(battery=label,half=period(r['releaseDate'],'half'),quarter=period(r['releaseDate'],'quarter')))
        panels[label]=dict(tasks=tasks,complete=len(complete),missing=len(rows)-len(complete))
    if len({r['slug'] for r in rows})!=len(rows):raise ValueError('duplicate AA slug')
    short_dates=defaultdict(set)
    for r in rows:
        if r['releaseDate']:short_dates[r['shortName']].add(r['releaseDate'])
    original=DATA/'aa-snapshot/aa_analysis_models.csv'
    result=dict(rows=len(rows),csv_sha256=hashlib.sha256(raw).hexdigest(),
        browser_copy_matches_bytes=original.read_bytes()==raw,
        browser_copy_matches_records=list(csv.DictReader(original.open()))==rows,
        panels=panels,cohorts=cohorts,taxonomy=taxonomy,
        shortnames_with_multiple_dates={k:sorted(v) for k,v in short_dates.items() if len(v)>1})
    write_csv(OUT/'aa_memberships.csv',memberships)
    return result


def wild_audit():
    path=DATA/'wild/data.parquet'
    table=pq.read_table(path,columns=['model','task','subtask','item_id','score'])
    key=pc.binary_join_element_wise(table['task'],table['subtask'],table['item_id'],'\x1f')
    table=table.append_column('key',key)
    if table['score'].null_count or pc.sum(pc.invert(pc.is_in(table['score'],value_set=pa.array([0,1],type=pa.int64())))).as_py():
        raise ValueError('WILD score outside binary range')
    grouped=table.group_by(['model','task']).aggregate([('score','count'),('score','mean'),('key','count_distinct')]).to_pylist()
    task_items={r['task']:r['key_count_distinct'] for r in table.group_by('task').aggregate([('key','count_distinct')]).to_pylist()}
    models=sorted(set(table['model'].to_pylist())); tasks=sorted(task_items)
    index={(r['model'],r['task']):r for r in grouped}
    complete={t:[m for m in models if (m,t) in index and index[m,t]['key_count_distinct']==task_items[t]] for t in tasks}
    repeated=sum(r['score_count']-r['key_count_distinct'] for r in grouped)
    item_coverage=table.group_by(['task','key']).aggregate([('model','count_distinct'),('score','count')])
    common_counts=Counter(r['task'] for r in item_coverage.to_pylist() if r['model_count_distinct']==len(models))
    duplicate_keys=item_coverage.filter(pc.greater(item_coverage['score_count'],item_coverage['model_count_distinct']))['key']
    duplicate_rows=table.filter(pc.is_in(table['key'],value_set=duplicate_keys.combine_chunks()))
    repeated_scores=duplicate_rows.group_by(['model','key']).aggregate([('score','min'),('score','max'),('score','count')])
    conflicting_repeated_scores=sum(r['score_min']!=r['score_max'] for r in repeated_scores.to_pylist())
    battery=[t for t in tasks if len(complete[t])==len(models)]
    candidate=[t for t in tasks if len(complete[t])>=50]
    counts={m:sum(m in complete[t] for t in candidate) for m in models}
    all_complete=[m for m in models if all(m in complete[t] for t in candidate)] if candidate else []
    write_csv(OUT/'wild_coverage.csv',[dict(model=m,task=t,observations=index[m,t]['score_count'] if (m,t) in index else 0,
        unique_items=index[m,t]['key_count_distinct'] if (m,t) in index else 0,
        union_items=task_items[t],complete_item_union=m in complete[t],
        mean_score=index[m,t]['score_mean'] if (m,t) in index else '') for m in models for t in tasks])
    return dict(observations=table.num_rows,models=models,tasks=tasks,
        task_items=task_items,model_task_cells=len(grouped),repeated_model_item_keys=repeated,
        common_item_keys_per_task=dict(common_counts),conflicting_repeated_model_item_cells=conflicting_repeated_scores,
        tasks_complete_for_all_models=battery,tasks_complete_for_50_models=candidate,
        models_complete_on_50_model_tasks=all_complete,
        complete_models_per_task={t:len(v) for t,v in complete.items()},
        common_item_caveat='Completeness is against the union of recorded item keys, not the official benchmark item bank. Duplicate keys require further review before score use.' )


def hf_audit(version):
    directory=DATA/f'open-llm-{version}-contents'
    path=next((directory/'data').glob('*.parquet'))
    rows=pq.read_table(path).to_pylist()
    columns=['ARC','HellaSwag','MMLU','TruthfulQA','Winogrande','GSM8K'] if version=='v1' else ['IFEval Raw','BBH Raw','MATH Lvl 5 Raw','GPQA Raw','MUSR Raw','MMLU-PRO Raw']
    complete=[r for r in rows if all(r[t] is not None and np.isfinite(r[t]) for t in columns)]
    return dict(rows=len(rows),complete_six=len(complete),columns=columns,
        flags=dict(Counter(str(r['Flagged']) for r in rows)),
        types=dict(Counter(r['Type'] for r in rows)),
        distinct_fullnames=len({r['fullname'] for r in rows}),
        merged=sum(r.get('Merged') is True for r in rows),
        dates={c:dict(Counter(r.get(c,'')[:4] or 'unknown' for r in rows))
            for c in ('date','Upload To Hub Date','Submission Date') if c in rows[0]})


def hf_v2_protocol_audit():
    records=[];errors=[];protocols=Counter();versions=Counter();leafcounts=Counter();hashes=defaultdict(Counter)
    paths=sorted((DATA/'open-llm-v2-results').rglob('results_*.json'))
    for p in paths:
        try:
            r=json.loads(p.read_text())
            config=r.get('config',{}); results=r['results'];dt=r.get('date')
            if isinstance(dt,(int,float)):datevalue=datetime.fromtimestamp(dt,timezone.utc).date().isoformat()
            else:datevalue=p.stem.removeprefix('results_')[:10]
            leaves=[t for t in results if t in r.get('configs',{})]
            signature=json.dumps(dict(git_hash=r.get('git_hash'),versions=r.get('versions'),shots=r.get('n-shot'),
                system_instruction=r.get('system_instruction'),limit=config.get('limit'),gen_kwargs=config.get('gen_kwargs')),sort_keys=True)
            sig=hashlib.sha256(signature.encode()).hexdigest()
            protocols[sig]+=1;versions[str(r.get('git_hash'))]+=1
            for t in leaves:leafcounts[t]+=1
            for t,h in r.get('task_hashes',{}).items():hashes[t][h]+=1
            records.append(dict(path=str(p.relative_to(ROOT)),model=r.get('model_name',config.get('model_args','')),
                revision=config.get('model_revision',config.get('model_sha','')),date=datevalue,
                precision=config.get('model_dtype',''),protocol=sig,leaf_tasks=len(leaves)))
        except (ValueError,KeyError,TypeError,OverflowError) as e:errors.append(dict(path=str(p),error=str(e)))
    write_csv(OUT/'hf_v2_runs.csv',records)
    largest=protocols.most_common(1)[0][0] if protocols else None
    selected=[r for r in records if r['protocol']==largest]
    return dict(result_files=len(paths),parsed=len(records),errors=errors,git_hashes=dict(versions),
        distinct_protocol_signatures=len(protocols),largest_protocol_runs=len(selected),
        largest_protocol_distinct_model_revisions=len({(r['model'],r['revision'],r['precision']) for r in selected}),
        largest_protocol_dates=dict(Counter(r['date'][:7] for r in selected)),
        task_occurrences=dict(leafcounts),task_hash_variants={t:len(v) for t,v in hashes.items()},
        run_date_range=[min(r['date'] for r in records),max(r['date'] for r in records)])


def arena_audit():
    sources=[]
    for directory in sorted(p for p in (DATA/'arena').iterdir() if p.is_dir() and not p.name.startswith('.')):
        files=list(directory.glob('full-*.parquet'))
        if not files:continue
        rows=pq.read_table(files,columns=['model_name','category','leaderboard_publish_date']).to_pylist()
        dates=sorted({r['leaderboard_publish_date'] for r in rows})
        sources.append(dict(subset=directory.name,rows=len(rows),dates=len(dates),range=[dates[0],dates[-1]],
            models=len({r['model_name'] for r in rows}),categories=sorted({r['category'] for r in rows})))
    return sources


def datadecide_audit():
    files=sorted((DATA/'datadecide/data').glob('train-*.parquet'))
    table=pq.read_table(files,columns=['params','data','task','step','seed','tokens','compute'])
    counts=table.group_by(['params','data','step','seed']).aggregate([('task','count_distinct')])
    rows=counts.to_pylist();freq=Counter(r['task_count_distinct'] for r in rows)
    return dict(rows=table.num_rows,checkpoints=len(rows),task_counts=dict(freq),
        tasks=sorted(set(table['task'].to_pylist())),sizes=sorted(set(table['params'].to_pylist())),
        recipes=len(set(table['data'].to_pylist())),seeds=sorted(set(table['seed'].to_pylist())),
        token_range=pc.min_max(table['tokens']).as_py())


def livebench_audit():
    result=[]
    with zipfile.ZipFile(DATA/'archives/livebench-exports.zip') as z:
        for name in sorted(n for n in z.namelist() if re.search(r'/table_\d{4}_\d{2}_\d{2}\.csv$',n)):
            rows=list(csv.DictReader(io.StringIO(z.read(name).decode())))
            tasks=[k for k in rows[0] if k!='model']
            complete=[]
            for r in rows:
                try:
                    values=[float(r[t]) for t in tasks]
                    if all(np.isfinite(v) and 0<=v<=100 for v in values):complete.append(r['model'])
                except (TypeError,ValueError):pass
            result.append(dict(battery=Path(name).stem,rows=len(rows),tasks=tasks,complete_models=complete))
    return result


def write_csv(path,rows):
    if not rows:return
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def render(r):
    aa=r['aa'];wild=r['wild'];hf=r['hf_v2_protocol']
    lines=['# Acquired-data audit for a gAI time series','',
        'The original goal remains a series of general-factor measurements on comparable capabilities. The strongest acquired candidate is now the nine-benchmark AA panel. This audit establishes observed coverage and numerical rank, not measurement invariance or a validated gAI trend. See AA-SUITABILITY.md for the subsequent raw-page provenance and comparability audit: the panel is exploratory, with substantial floor effects and unverified per-cell protocol equivalence.','',
        '## Artificial Analysis: primary candidate','',
        f"Original repository ZIP: {aa['rows']} configuration rows. The recovered browser CSV matches original records: {aa['browser_copy_matches_records']}; matches original bytes: {aa['browser_copy_matches_bytes']}.",'',
        'Nine fixed indicators: GPQA, HLE, AA-Omniscience, tau2, IFBench, AA-LCR, SciCode, CritPt and Terminal-Bench Hard. Each selected configuration has an observed value on every indicator. Composite Intelligence Index and MMMU-Pro are excluded.','',
        '| Battery | Release cohort | Configurations | Distinct publisher short names | Reasoning configurations | Rank |','|---|---|---:|---:|---:|---:|']
    for c in aa['cohorts']:
        if c['period_kind']=='half':
            lines.append(f"| {c['battery']} | {c['period']} | {c['configurations']} | {c['distinct_shortnames']} | {c['reasoning']} | {c['rank']} |")
    lines+=['','Quarterly resolution on the same nine indicators:', '',
        '| Release quarter | Complete configurations | Distinct short names |','|---|---:|---:|']
    for c in aa['cohorts']:
        if c['battery']=='nine' and c['period_kind']=='quarter' and c['period']>='2025Q1':
            lines.append(f"| {c['period']} | {c['configurations']} | {c['distinct_shortnames']} |")
    lines+=['','Distinct short names are a descriptive count, not a verified base-model or ancestry count: the source sometimes retains effort labels inside short names. Exact memberships are in aa_memberships.csv.','',
        '**What we can do:** estimate a fixed nine-indicator flat factor model, then compare its structure across 2025H1, 2025H2 and 2026H1 using predeclared release cohorts. Quarterly counts are exported in audit.json and may support finer exploratory resolution. Fit one pooled calibration for a relative capability trajectory and use separate cohort fits/invariance tests for whether factor structure changes. These are different outcomes.','',
        '**What is not established:** equal evaluation settings, common grader/question versions across every row, independent families, selection representativeness, and invariance. Release dates are source-reported and this July 2026 snapshot cannot represent later releases. A three-group model needs at least three defensible indicators per group; nine columns alone do not supply that theory or sufficient group separation.','',
        'For capability levels, retain one common reference scale; do not independently z-score each cohort and call those scores progress. For changing g strength, report a specified variance-share/reliability measure with uncertainty within fixed windows, recognizing changing variance and population composition. Reasoning/nonreasoning and publisher/family composition require sensitivity analyses.','',
        '## WILD: item-level replication candidate','',
        f"{wild['observations']:,} observations, {len(wild['models'])} models, {len(wild['tasks'])} benchmarks. Observed model/task cells: {wild['model_task_cells']}. Repeated model/item keys: {wild['repeated_model_item_keys']}.",
        f"{len(wild['tasks_complete_for_all_models'])} benchmark item unions are fully covered by every model. A coverage-only screen retains {len(wild['tasks_complete_for_50_models'])} benchmarks covered by >=50 models, with {len(wild['models_complete_on_50_model_tasks'])} models complete across that whole screened battery.",'',
        f"Every benchmark has common item keys across all 65 models; the intersection sizes are in audit.json. Repeated item keys have conflicting binary scores in {wild['conflicting_repeated_model_item_cells']} model/item cells. This requires inspecting whether repeated prompts represent distinct original items, stochastic repetitions or record duplication before aggregating them.",'',
        'The item union is derived from observations, not guaranteed identical to the official question bank. Coverage details and unmodified score means are in wild_coverage.csv; duplicate keys must be resolved before those means are used in fits. This source can independently test benchmark structure and common-item uncertainty. It needs verified release dates for calendar cohorts; its limited model population does not replace the AA frontier timeline.','',
        '## Open LLM Leaderboard: historical open-model replication','']
    for label,source in r['hf_contents'].items():
        lines.append(f"- {label}: {source['rows']} rows, {source['complete_six']} complete six-score rows, {source['distinct_fullnames']} distinct model names. Flag values: {source['flags']}.")
    lines += [f"- V2 raw result files: {hf['result_files']}, parsed {hf['parsed']}, errors {len(hf['errors'])}. Run-date range {hf['run_date_range'][0]} to {hf['run_date_range'][1]}. Largest exact protocol-signature group: {hf['largest_protocol_runs']} runs, {hf['largest_protocol_distinct_model_revisions']} distinct model/revision/precision identities.",'',
        'V2 retains task-level results, task hashes, shots, model revisions and harness commits, so consistency is much more auditable than aggregate leaderboards. Identical signature grouping includes version/shot metadata and selected global generation settings; it is a screening proxy, not proof of identical task instances. Chat templates are model-specific and need review. Repeated runs must not become additional independent models. Submission, Hub-upload and evaluation dates are not interchangeable with release dates. V1 marks every contents row flagged in this snapshot, so flag semantics need investigation before exclusion or use.','',
        '## LiveBench archive','',
        f"The export ZIP contains {len(r['livebench'])} battery tables. Counts and exact complete model memberships are in audit.json. More editions are acquired than the three analyzed earlier. In particular, table_2026_01_08 has 126 complete configurations on 23 tasks (versus 28 on 23 in table_2026_06_25), including models released after January. Battery labels are not evaluation cutoffs. This is another promising fixed-battery cohort candidate, pending verified release-date mapping and family/configuration controls. The modelLinks.js metadata supplies source links and some version strings, not uniform release dates. Battery labels still identify changing measuring instruments, so stitching table dates together is not a gAI series.",'',
        '## Arena and DataDecide','',
        'Arena has actual published snapshots. It can validate an independently estimated capability trajectory against preference outcomes; changing opponents, voters, categories and rating methods prevent treating the ratings as an invariant objective battery. Dataset ranges are in audit.json.','',
        f"DataDecide: {r['datadecide']['rows']:,} training-result rows, {r['datadecide']['checkpoints']:,} (size, recipe, step, seed) checkpoints, {len(r['datadecide']['tasks'])} task labels. Task-count distribution per checkpoint: {r['datadecide']['task_counts']}.",
        'This supports a controlled training-progress experiment, with dependence across steps/seeds handled explicitly. It is not calendar-time frontier progress. Derived macro-average and scaling-fit Parquets were excluded to avoid duplicating raw observations.','',
        '## Acquisition failures and fixes','',
        'The saved EEE log reports HTTP 504 Gateway Timeout while listing the large repository. It also shows that the CLI treated extra include patterns as filenames; the batch command now repeats --include for each pattern. This recorded failure is not evidence of a rate-limit 429, though earlier rate limits may also have occurred. EEE is not needed to start the AA baseline.',
        'HELM located release objects but received gzip-compressed bytes. The downloader incorrectly attempted to parse those bytes as JSON. It now decompresses gzip after checking stored object size. Classic had no matching core-scenario release files under the searched prefix; that layout remains unresolved. No retry with remote access was performed in this audit.','',
        '## Recommended study sequence','',
        '1. Primary retrospective calendar series: the AA nine-indicator panel, with half-year windows as the initial comparison and quarter windows as a sensitivity check. Fix indicator definitions and separate capability-level trends from changes in factor strength.',
        '2. Freeze a confirmatory specification before fitting cohort contrasts. Audit source model identities, configurations and indicator/version metadata; run measurement-invariance and family/publisher/reasoning composition checks. A failure is a result to report, not a reason to silently change the battery.',
        '3. Replicate structure with WILD common items and v2 Open LLM subtask results. Keep their populations/scales distinct until anchor equivalence is established. Later snapshots or disjoint model families can provide confirmation rather than reusing discovery data.',
        '4. Extend past June 2026 using a new constituent-score snapshot (EEE/AA or equivalent) only after matching definitions. The acquired AA data do not yet extend the primary series to October 2026.',
        '5. Use Arena history for external validity and DataDecide as a separate controlled training-time analysis.','',
        'No new factor models were fitted. Numeric feasibility is improved; longitudinal construct validity remains to be tested. Input hashes and software versions are recorded in audit.json.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    print('AA',flush=True);r={'aa':aa_audit()}
    print('WILD',flush=True);r['wild']=wild_audit()
    print('HF contents',flush=True);r['hf_contents']={v:hf_audit(v) for v in ('v1','v2')}
    print('HF v2 run settings',flush=True);r['hf_v2_protocol']=hf_v2_protocol_audit()
    print('Arena',flush=True);r['arena']=arena_audit()
    print('DataDecide',flush=True);r['datadecide']=datadecide_audit()
    print('LiveBench',flush=True);r['livebench']=livebench_audit()
    critical=[DATA/'archives/aa-bundle.zip',DATA/'archives/livebench-exports.zip',DATA/'wild/data.parquet',*sorted((DATA/'datadecide/data').glob('train-*.parquet')),
        *sorted((DATA/'open-llm-v1-contents/data').glob('*.parquet')),*sorted((DATA/'open-llm-v2-contents/data').glob('*.parquet'))]
    manifest=json.loads((DATA/'host-download-manifest.json').read_text())
    expected={e['path']:e['sha256'] for e in manifest['files']}
    r['input_hashes']={str(p.relative_to(ROOT)):digest(p) for p in critical}
    for name,value in r['input_hashes'].items():
        if expected.get(name)!=value:raise ValueError(f'host manifest mismatch: {name}')
    r['code_sha256']=digest(Path(__file__))
    r['numpy_version']=np.__version__;r['pyarrow_version']=pa.__version__
    (OUT/'audit.json').write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    render(r)
    print(OUT/'README.md')


if __name__=='__main__':main()
