"""Offline, provenance-preserving fixed-battery inputs for rolling PCA."""
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from aa_cohort_factor import identity, effort
from aa_provenance_audit import parse_models
from downloaded_data_audit import CORE
from epoch_cohort_overlap import load_inputs
from epoch_data_audit import read_csv

ROOT = Path(__file__).resolve().parent


def iso(value):
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        return ''


def normalized(value):
    # Preserve effort, revision, publisher and version tokens; only ignore punctuation/case.
    return re.sub(r'[^a-z0-9]', '', value.lower())


def finite(value):
    try:
        return np.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def record(model, base, when, scores, provenance, publisher='', priority=0):
    return dict(model=model, base=base or model, date=iso(when), scores=scores,
                date_evidence=provenance, publisher=publisher, priority=priority)


def panel(key, source, label, time_axis, tasks, rows, notes='', sensitivity=False):
    return dict(key=key, source=source, label=label, time_axis=time_axis,
                tasks=list(tasks), rows=rows, notes=notes, sensitivity=sensitivity)


def load_sources():
    panels=[]; statuses=[]; inputs={}; lookup=defaultdict(set); evidence=defaultdict(set)
    def track(name):
        path=ROOT/name
        inputs[name]=hashlib.sha256(path.read_bytes()).hexdigest()
        return path
    def remember(names, when, origin):
        if iso(when):
            for name in names:
                if name:
                    lookup[normalized(name)].add(iso(when)); evidence[normalized(name)].add(origin)
    def dated(name):
        ds=lookup[normalized(name)]
        return (next(iter(ds)), '; '.join(sorted(evidence[normalized(name)]))) if len(ds)==1 else ('','no unambiguous exact alias date')

    with zipfile.ZipFile(track('public-data/archives/aa-bundle.zip')) as z:
        member=next(n for n in z.namelist() if n.endswith('/aa_leaderboards_models_snapshot.html'))
        models=parse_models(z.read(member).decode())
    aa=[]
    for m in models:
        remember([m.get(k,'') for k in ('slug','name','shortName')],m.get('releaseDate'), 'AA archived releaseDate')
        if all(finite(m.get(t)) for t in CORE) and iso(m.get('releaseDate')):
            aa.append(record(m['slug'],identity(m),m['releaseDate'],{t:float(m[t]) for t in CORE},'AA archived releaseDate',m['modelCreatorName'],effort(m)))
    for battery in ('nine','eight'):
        tasks=[t for t in CORE if battery=='nine' or t!='critpt']
        panels.append(panel('aa_'+battery,'AA','AA '+('with CritPt' if battery=='nine' else 'without CritPt'),'release',tasks,aa,'All complete archived configurations; no half-year date cutoff.'))
        p=panel('aa_'+battery+'_selected','AA','AA '+battery+' · one configuration/base','release',tasks,aa,'Highest explicit effort, then model slug; no score-based choice.',True)
        p['select_one']=True;p['scale_from']='aa_'+battery;panels.append(p)

    zip_path=track('benchmark_data.zip');audit_path=track('output/epoch-audit/audit.json')
    audit,cells,dates,orgs,groups,issues=load_inputs(zip_path,audit_path)
    with zipfile.ZipFile(zip_path) as z:
        for m in read_csv(z,'model_metadata.csv'):
            remember([m.get(k,'') for k in ('model_version','model_group','display_name')],m.get('date'),'Epoch model_metadata.date')
    for m,d in dates.items():remember([m],d,'Epoch unambiguous score-row Release date')
    for key,tasks in [('broad',['DTBench','GPQA diamond','OTIS Mock AIME 2024-2025']),('chess',['Chess Puzzles','GPQA diamond','OTIS Mock AIME 2024-2025'])]:
        rows=[]
        for m,d in sorted(dates.items()):
            if all((m,t) in cells for t in tasks):
                base=next(iter(groups[m])) if len(groups[m])==1 else m
                pub=next(iter(orgs[m])) if len(orgs[m])==1 else 'unknown'
                rows.append(record(m,base,d,{t:cells[m,t] for t in tasks},'Epoch unambiguous Release date',pub,1 if m.endswith('_high') else 0))
        note='Fixed audited battery; conflicting cells/dates excluded; exact configurations, known model groups; mixed evaluation sources/settings remain. Group date is earliest eligible configuration release.'
        panels.append(panel('epoch_'+key,'Epoch','Epoch '+('DTBench / GPQA / OTIS' if key=='broad' else 'Chess / GPQA / OTIS'),'release',tasks,rows,note,key=='chess'))
        p=panel('epoch_'+key+'_selected','Epoch','Epoch '+key+' · one configuration/group','release',tasks,rows,note+' Prefer high label then lexical configuration ID.',True)
        p['select_one']=True;p['scale_from']='epoch_'+key;panels.append(p)
    statuses.append(dict(source='Epoch',status='loaded',detail=f"{issues['conflicting_cells']} conflicting source cells excluded by existing audit"))

    path=track('public-data/estonian/summary.csv');raw=list(csv.DictReader(path.open()))
    tasks=['bib_bench','keelenou','trivia_et_2','idiom_bench','term_bench','propaganda_resistance','trivia_et_3']
    rows=[]
    for r in raw:
        remember([r['model_id'],r['name']],r['release_date'],'Estonian release_date')
        rows.append(record(r['model_id'],r['model_id'],r['release_date'],{t:r[t] for t in tasks},'Estonian release_date',r['provider']))
    panels.append(panel('estonian','Estonian','Estonian · seven language tasks','release',tasks,rows,'Source release dates; model IDs treated as bases; broader ancestry unresolved. Fixed seven-task battery.'))

    inventory=list(csv.DictReader(track('output/downloaded-data-audit/hf_v2_runs.csv').open()))
    by_protocol=defaultdict(list)
    for r in inventory:by_protocol[r['protocol']].append(r)
    # Largest protocol first; add a protocol only when it extends observed calendar months.
    protocols=[];covered=set()
    for sig,rs in sorted(by_protocol.items(),key=lambda kv:(-len(kv[1]),kv[0])):
        months={r['date'][:7] for r in rs}
        if len({r['model'] for r in rs})>=50 and months-covered:
            protocols.append(sig);covered.update(months)
    metrics=[('IFEval','leaderboard_ifeval','prompt_level_strict_acc,none'),('BBH','leaderboard_bbh','acc_norm,none'),('MATH L5','leaderboard_math_hard','exact_match,none'),('GPQA','leaderboard_gpqa','acc_norm,none'),('MUSR','leaderboard_musr','acc_norm,none'),('MMLU-Pro','leaderboard_mmlu_pro','acc,none')]
    for protocol_number,signature in enumerate(protocols):
        chosen={}
        for r in sorted(by_protocol[signature],key=lambda r:(r['date'],r['path'])):
            model=r['model']+'@'+r['revision']+'|'+r['precision']
            if model in chosen:continue
            obj=json.loads(track(r['path']).read_text());result=obj['results']
            scores={label:result.get(task,{}).get(metric) for label,task,metric in metrics}
            if all(finite(v) for v in scores.values()):
                chosen[model]=record(model,r['model'],r['date'],scores,r['path'],r['model'].split('/')[0])
        key='openllm_v2' if protocol_number==0 else 'openllm_v2_'+signature[:8]
        panels.append(panel(key,'OpenLLMv2','Open LLM v2 · protocol '+signature[:6],'evaluation',[m[0] for m in metrics],list(chosen.values()),'Stored protocol signature '+signature+'. Largest group first; additional >=50-model groups chosen by run count only when they extend calendar-month coverage. Each protocol has its own scale/baseline and is not spliced. Earliest complete run per model/revision/precision; base cluster is repository name. Fixed six aggregate metrics; IFEval prompt-level strict accuracy. Protocol signature is a consistency screen, not proof of identical chat templates.'))

    # Keep v1 timestamps on their own axis: the local source card does not define their semantics.
    p=next((ROOT/'public-data/open-llm-v1-contents/data').glob('*.parquet'));track(str(p.relative_to(ROOT)))
    raw=pq.read_table(p).to_pylist();tasks=['ARC','HellaSwag','MMLU','TruthfulQA','Winogrande','GSM8K'];chosen={}
    for r in sorted(raw,key=lambda r:(str(r.get('date','')),r['eval_name'])):
        model=r['fullname']+'@'+str(r.get('Model sha',''))+'|'+str(r['Precision'])
        if model not in chosen:chosen[model]=record(model,r['fullname'],r.get('date'),{t:r.get(t) for t in tasks},'Open LLM v1 contents date (semantics unverified)',r['fullname'].split('/')[0])
    panels.append(panel('openllm_v1','OpenLLMv1','Open LLM v1 · recorded-date sensitivity','recorded',tasks,list(chosen.values()),'Contents date semantics are unverified; not treated as release/evaluation time. All rows flagged=True with unresolved semantics; protocol variation and selection bias remain. Exploratory separate-axis sensitivity.'))

    # Parse only quoted fields from the inert JS metadata; do not execute downloaded code.
    with zipfile.ZipFile(track('public-data/archives/livebench-exports.zip')) as z:
        text=z.read(next(n for n in z.namelist() if n.endswith('modelLinks.js'))).decode()
        links={m.group(1):dict(re.findall(r'(\w+)\s*:\s*"([^"]*)"',m.group(2))) for m in re.finditer(r'"([^"\n]+)"\s*:\s*\{([^{}]*)\}',text)}
        candidates=[]
        for name in sorted(n for n in z.namelist() if '/table_' in n and n.endswith('.csv')):
            raw=list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))));tasks=[t for t in raw[0] if t!='model'];rows=[]
            for r in raw:
                model=r['model'];meta=links.get(model,{})
                when=iso(meta.get('version'));how='LiveBench modelLinks explicit version date'
                # An explicit version date is stronger than a display-name lookup. Otherwise
                # require an exact identifier alias; do not erase effort or version tokens.
                if not when:when,how=dated(model)
                base=(meta.get('organization','unknown')+'/'+meta['displayName']+'@'+when) if meta.get('displayName') and when else model
                rows.append(record(model,base,when,{t:r[t] for t in tasks},how,meta.get('organization','unknown')))
            complete=sum(bool(r['date']) and all(finite(r['scores'][t]) for t in tasks) for r in rows)
            candidates.append((complete,name,tasks,rows))
        complete,name,tasks,rows=max(candidates,key=lambda x:(x[0],x[1]))
        panels.append(panel('livebench','LiveBench','LiveBench · '+Path(name).stem.removeprefix('table_'),'release',tasks,rows,'Fixed edition chosen by largest complete dated count only. Explicit model version dates and unambiguous exact aliases; release/version dates may differ. Base groups use explicit organization/displayName/version date when available; broader ancestry unresolved. No edition-date cohort assignment; no stripped effort-name aliases.'))
        statuses.extend(dict(source='LiveBench battery',status=Path(n).stem,detail=f'{c} complete dated configurations'+(' (chosen)' if n==name else '')) for c,n,t,rs in candidates)

    for mode in ('base','instruct'):
        raw=list(csv.DictReader(track(f'public-data/obsscaling/{mode}_llm_benchmark_eval.csv').open()))
        tasks=['MMLU','ARC-C','HellaSwag','Winograd' if mode=='base' else 'Winogrande','TruthfulQA','GSM8K','HumanEval'];rows=[]
        for r in raw:
            when,how=dated(r['Model'])
            rows.append(record(r['Model'],r['Model'],when,{t:r[t] for t in tasks},how,r['Model Family']))
        panels.append(panel('obsscaling_'+mode,'ObsScaling '+mode,'ObsScaling '+mode,'release',tasks,rows,'No source release-date column. Dates only from unambiguous exact aliases; do not infer release dates from FLOPs/training size.'))

    # WILD's prior audit already exports task means. Retain as explicitly provisional
    # static replication when dates are sparse; do not claim item-level independence.
    raw=list(csv.DictReader(track('output/downloaded-data-audit/wild_coverage.csv').open()))
    values=defaultdict(dict)
    for r in raw:values[r['model']][r['task']]=r['mean_score']
    tasks=sorted(set.intersection(*(set(v) for v in values.values())))
    rows=[]
    for m,sc in values.items():
        when,how=dated(m);rows.append(record(m,m,when,sc,how,m.split('/')[0]))
    panels.append(panel('wild','WILD','WILD · provisional aggregate replication','release',tasks,rows,'Task means include unresolved repeated/conflicting item keys. Aggregate replication is provisional; no item-bootstrap or definitive directional claim.'))
    statuses.extend([dict(source='DataDecide / Pythia',status='outside calendar study',detail='Training-step/checkpoint trajectories require a separate time axis.'),dict(source='Arena',status='external validation',detail='Preference ratings and changing opponents are not this fixed benchmark PCA.'),dict(source='HELM / EEE',status='not added',detail='Existing acquisition failures; no verified local fixed battery beyond the sources above.')])
    return panels,statuses,inputs
