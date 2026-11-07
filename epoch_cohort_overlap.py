# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2"]
# ///
"""Find identical benchmark batteries across Epoch release cohorts, without fitting factors."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import zipfile
from epoch_data_audit import read_csv, unique_cells

ROOT=Path(__file__).resolve().parent
YEARS=('2024','2025','2026')


def shared_batteries(observed,cohorts,min_support=5,max_tasks=9):
    """Exhaustively enumerate frequent benchmark subsets using exact bitset intersections."""
    labels=list(cohorts)
    members={year:sorted(cohorts[year]) for year in labels}
    indexes={year:{m:i for i,m in enumerate(members[year])} for year in labels}
    masks={t:tuple(sum(1<<indexes[y][m] for m in models if m in indexes[y]) for y in labels)
           for t,models in observed.items()}
    masks={t:v for t,v in masks.items() if min(vv.bit_count() for vv in v)>=min_support}
    tasks=sorted(masks)
    best={}; nodes=0
    def visit(chosen,support,candidates):
        nonlocal nodes
        for index,t in enumerate(candidates):
            overlap=tuple(a&b for a,b in zip(support,masks[t]))
            counts=tuple(v.bit_count() for v in overlap)
            if min(counts)<min_support: continue
            nodes+=1
            selected=chosen+[t]; p=len(selected)
            key=(min(counts),sum(counts))
            if p not in best or key>best[p]['objective']:
                best[p]=dict(objective=key,tasks=selected,counts=dict(zip(labels,counts)),
                    models={y:[m for i,m in enumerate(members[y]) if overlap[j]&(1<<i)] for j,y in enumerate(labels)})
            if p<max_tasks:
                # Any candidate below support now remains below support in descendants.
                remaining=[u for u in candidates[index+1:]
                    if min((a&b).bit_count() for a,b in zip(overlap,masks[u]))>=min_support]
                visit(selected,overlap,remaining)
    visit([],tuple((1<<len(members[y]))-1 for y in labels),tasks)
    return dict(min_support=min_support,max_tasks=max_tasks,searched_subsets=nodes,
                eligible_benchmarks=tasks,best={str(p):v for p,v in sorted(best.items())})


def load_inputs(path,audit_path):
    audit=json.loads(audit_path.read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=audit['zip_sha256']:
        raise ValueError('ZIP differs from the audited snapshot; rerun epoch_data_audit.py')
    records=[]; dates=defaultdict(set); orgs=defaultdict(set); groups=defaultdict(set)
    with zipfile.ZipFile(path) as z:
        for row in read_csv(z,'model_metadata.csv'):
            if row['model_version'] and row['model_group']:groups[row['model_version']].add(row['model_group'])
        for task in audit['inventory']:
            if not task.get('included_in_candidate_matrix'): continue
            for row in read_csv(z,task['source_file']):
                model=row['Model version'].strip()
                records.append((model,task['benchmark'],row[task['score_column']]))
                if row.get('Release date'):dates[model].add(row['Release date'])
                if row.get('Organization'):orgs[model].add(row['Organization'])
    cells,issues=unique_cells(records)
    return audit,cells,{m:next(iter(d)) for m,d in dates.items() if len(d)==1},orgs,groups,issues


def enrich(search,groups,orgs):
    for panel in search['best'].values():
        panel['model_groups']={};panel['organizations']={}
        for year,models in panel['models'].items():
            known={next(iter(groups[m])) for m in models if len(groups[m])==1}
            unresolved=[m for m in models if len(groups[m])!=1]
            panel['model_groups'][year]=dict(known_groups=len(known),unresolved_configurations=len(unresolved))
            panel['organizations'][year]=dict(Counter(next(iter(orgs[m])) if len(orgs[m])==1 else 'unknown' for m in models))


def run(path,audit_path,out):
    audit,cells,dates,orgs,groups,issues=load_inputs(path,audit_path)
    inventory={r['benchmark']:r for r in audit['inventory'] if r.get('included_in_candidate_matrix')}
    # Remove explicit supersessions and component/aggregate overlap identified in the ZIP.
    active={t for t,r in inventory.items() if not r['superseded_by'] and not r['source_file'].startswith('spireclimb_sts')}
    sources={'active_all_sources':active,'active_epoch_runs':{t for t in active if inventory[t]['epoch_run']}}
    results={};counts=[]
    for name,tasks in sources.items():
        observed={t:{m for m,b in cells if b==t and m in dates and dates[m][:4] in YEARS} for t in tasks}
        allmodels=set().union(*observed.values())
        cohorts={y:{m for m in allmodels if dates[m][:4]==y} for y in YEARS}
        for task in sorted(observed):
            counts.append(dict(source=name,benchmark=task,counts={y:len(observed[task]&cohorts[y]) for y in YEARS}))
        for window in (YEARS,YEARS[1:]):
            selected={y:cohorts[y] for y in window}
            print(f'Search {name} {window}',flush=True)
            search=shared_batteries(observed,selected)
            enrich(search,groups,orgs)
            search['cohort_totals']={y:len(m) for y,m in selected.items()}
            results[name+' '+','.join(window)]=search
        # A shared effort label is a sensitivity restriction, not a shared token budget.
        high={y:{m for m in cohorts[y] if m.endswith('_high')} for y in YEARS[1:]}
        search=shared_batteries(observed,high)
        enrich(search,groups,orgs)
        search['cohort_totals']={y:len(m) for y,m in high.items()}
        results[name+' 2025,2026 high-label']=search
    result=dict(zip_sha256=audit['zip_sha256'],audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),years=YEARS,
        exclusions=dict(conflicting_score_cells=issues['conflicting_cells'],
            tasks=sorted(set(inventory)-active)),searches=results,individual_benchmark_counts=counts,
        setting_evidence={t:dict(source_file=inventory[t]['source_file'],setting_columns=inventory[t]['setting_columns'],
            evaluation_timestamp_available=inventory[t]['has_evaluation_timestamp']) for t in sorted(active)},
        interpretation='Common benchmark names/versions and exact configuration IDs; complete settings consistency is not established by CSVs.')
    out.mkdir(parents=True,exist_ok=True)
    (out/'overlap.json').write_text(json.dumps(result,indent=2)+'\n')
    render(result,out)
    return result


def render(result,out):
    lines=['# Shared Epoch benchmarks across release cohorts','',
        'Finding: shared named benchmark batteries exist. Complete coverage and model diversity do not establish a well-supported three-group hierarchy across cohorts. Configuration IDs can be held fixed within a row, but equal evaluation budgets, prompts and harnesses have not been verified.','',
        'Release cohorts are calendar years 2024, 2025 and 2026 (2026 includes only releases in this snapshot). All comparisons below use one identical battery in every cohort and require every included configuration to have a score on every selected benchmark. Exact configuration IDs are retained.','',
        'Superseded benchmark versions, the two SpireClimb components and the LiveBench global composite are excluded. Differing repeated scores are excluded. No ECI model-group score aggregation, missing-cell imputation or factor fitting is used.','',
        '## Shared battery coverage','',
        'Exhaustive subset search through nine benchmarks, requiring at least five complete configurations in every cohort. For each battery size, maximize the smallest cohort count, then the total count. Search does not inspect score magnitudes. A dash means no battery meets the five-per-cohort threshold.','',
        '| Source and cohorts | Battery size | 2024 | 2025 | 2026 | Shared benchmarks |',
        '|---|---:|---:|---:|---:|---|']
    for label,search in result['searches'].items():
        for p in ('3','6','9'):
            panel=search['best'].get(p)
            counts=panel['counts'] if panel else {}
            lines.append(f"| {label} | {p} | {counts.get('2024','—')} | {counts.get('2025','—')} | {counts.get('2026','—')} | {', '.join(panel['tasks']) if panel else 'No eligible battery'} |")
    lines+=['','Each row can use a different battery. Compare counts across years within a row. Memberships, organization concentration and known model-group counts are exported in overlap.json. Configurations from one model group are correlated observations, so counts above overstate independent model diversity.','',
        '## Diversity of selected candidate panels','',
        '| Source and cohorts | Battery size | Year | Configurations | Known model groups | Organization counts |',
        '|---|---:|---|---:|---:|---|']
    for label,p in [('active_all_sources 2024,2025,2026','3'),('active_epoch_runs 2025,2026','3'),('active_all_sources 2025,2026','9')]:
        panel=result['searches'][label]['best'].get(p)
        if not panel: continue
        for y,n in panel['counts'].items():
            org=', '.join(f'{o}: {count}' for o,count in sorted(panel['organizations'][y].items()))
            lines.append(f"| {label} | {p} | {y} | {n} | {panel['model_groups'][y]['known_groups']} | {org} |")
    lines+=['','Model groups use the ZIP metadata and are not independent ancestry/family clusters. Counts may still include related checkpoints or aliases. The nine-benchmark 2025 all-source cohort has only eight rows, all OpenAI, so its nine-variable covariance is necessarily singular.','',
        '## Individually shared benchmarks','',
        'Benchmarks with at least ten configurations in every year, before requiring those configurations to be complete across a battery.','',
        '| Source | Benchmark | 2024 | 2025 | 2026 |','|---|---|---:|---:|---:|']
    for r in result['individual_benchmark_counts']:
        c=r['counts']
        if min(c.values())>=10:
            lines.append(f"| {r['source']} | {r['benchmark']} | {c['2024']} | {c['2025']} | {c['2026']} |")
    lines+=['','## What is consistent, and what remains unverified','',
        '- Cohort membership follows one unambiguous release date for each exact configuration ID. Calendar periods do not overlap. These are retrospective measurements, not historical as-published snapshots.',
        '- Benchmark labels and supersession metadata identify the same named battery version across cohorts. Equal labels alone do not prove identical questions, graders or evaluation implementations.',
        '- The Epoch-run subset avoids mixing evaluation organizations. Its CSVs expose release dates, scores, run timestamps and some log links, but do not provide explicit columns for prompts, agent harnesses, tools or token budgets. Consistency of those settings is unverified.',
        '- The high-label restriction keeps only IDs ending in _high. It removes unlabeled/default and other effort settings from that sensitivity check. Different providers can implement high differently, so this does not establish equal compute budgets.',
        '- Counts for exact configurations can include multiple effort settings of the same base model. Known model-group counts are reported separately. Missing group mappings remain unresolved rather than being asserted independent.',
        '- External-source coverage can mix prompts, graders, harnesses, tools and providers. Score conflicts have been removed, but equal repeated scores do not prove that their settings match.',
        '- Coverage optimization can favor related math and reasoning tests and omit instruction following, writing or agent tasks. A numerically shared battery is not automatically representative or suitable for a three-group hierarchy.',
        '- A nine-task covariance matrix requires more than nine independent observations for full rank, and substantially more for stable hierarchical inference. The search threshold of five is for feasibility screening, not an estimation standard.','',
        '## Reproduce','', '```sh','uv run epoch_cohort_overlap.py','```','',
        f"Epoch AI, Capabilities & benchmarking, https://epoch.ai/benchmarks. ZIP SHA256: `{result['zip_sha256']}`. Code and prior audit hashes are in overlap.json. The ZIP README specifies CC BY 4.0 with attribution."]
    (out/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path,default=ROOT/'benchmark_data.zip')
    parser.add_argument('--audit',type=Path,default=ROOT/'output/epoch-audit/audit.json')
    parser.add_argument('--out',type=Path,default=ROOT/'output/epoch-cohorts')
    args=parser.parse_args()
    run(args.zip,args.audit,args.out)
    print(args.out/'README.md')
