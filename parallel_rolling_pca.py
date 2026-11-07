"""Fixed-battery rolling PCA, source-specific scales and cluster uncertainty."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import numpy as np
from aa_cohort_pca import pc1, similarity
from rolling_pca_sources import load_sources

ROOT=Path(__file__).resolve().parent
DEFAULT_OUT=ROOT/'output/parallel-rolling-pca'


def write_csv(path, rows):
    if not rows:
        path.write_text(''); return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)


def complete_rows(rows,tasks):
    """Fixed tasks first. Reject ambiguous repeated configuration records."""
    collected=defaultdict(list); missing=0
    for row in rows:
        try:
            values=np.array([float(row['scores'][t]) for t in tasks])
            if not np.isfinite(values).all():raise ValueError('nonfinite')
        except (KeyError,TypeError,ValueError):missing+=1;continue
        collected[row['model']].append(dict(row,scores=dict(zip(tasks,values))))
    kept=[];conflicts=0
    for m,rs in sorted(collected.items()):
        signatures={(r['base'],r['date'],tuple(r['scores'][t] for t in tasks)) for r in rs}
        if len(signatures)!=1:conflicts+=1;continue
        kept.append(rs[0])
    return kept,dict(incomplete_records=missing,conflicting_configurations=conflicts)


def monthly_windows(base_dates,target=50):
    """Nearest eligible bases, including all ties; input already passed battery filter."""
    keys=sorted(base_dates); ordinal=np.array([date.fromisoformat(base_dates[b]).toordinal() for b in keys])
    lo=date.fromordinal(int(ordinal.min()));hi=date.fromordinal(int(ordinal.max()));out=[]
    for month_number in range(lo.year*12+lo.month-1,hi.year*12+hi.month):
        y,mo=divmod(month_number,12);center=date(y,mo+1,15);dist=abs(ordinal-center.toordinal())
        radius=int(np.partition(dist,min(target,len(keys))-1)[min(target,len(keys))-1])
        selected=[b for b,d in zip(keys,dist) if d<=radius]
        ds=[date.fromisoformat(base_dates[b]) for b in selected]
        fraction=sum(d<=center for d in ds)/len(ds)
        out.append(dict(date=center.isoformat(),bases=selected,radius_days=radius,
                        start=min(ds).isoformat(),end=max(ds).isoformat(),span_days=(max(ds)-min(ds)).days,
                        effective_date=date.fromordinal(int(np.median([d.toordinal() for d in ds]))).isoformat(),
                        endpoint_imbalanced=fraction<.2 or fraction>.8))
    return out


def weighted_axes(X, multiplicities):
    """Batched PCA on literal bootstrap copies using frequency-weight covariance."""
    n=multiplicities.sum(axis=1);safe=np.maximum(n,1)
    mean=multiplicities@X/safe[:,None]
    covariance=np.einsum('bn,ni,nj->bij',multiplicities,X,X,optimize=True)-n[:,None,None]*mean[:,:,None]*mean[:,None,:]
    covariance/=np.maximum(n-1,1)[:,None,None]
    values,vectors=np.linalg.eigh(covariance)
    leading=values[:,-1];gap=leading-values[:,-2];trace=values.sum(axis=1)
    valid=(n>=3)&(leading>1e-12)&(trace>1e-12)&(gap>1e-8*leading)&(values[:,0]>=-1e-9*np.maximum(1,leading))
    axes=vectors[:,:,-1];axes[~valid]=np.nan
    return axes,np.divide(leading,trace,out=np.full_like(trace,np.nan),where=valid),np.divide(gap,leading,out=np.full_like(gap,np.nan),where=valid),valid


def angles(a,b):
    return np.degrees(np.arccos(np.clip(np.abs(np.sum(a*b,axis=-1)),0,1)))


def interval(values,total):
    valid=np.asarray(values)[np.isfinite(values)];n=len(valid)
    lo,hi=np.quantile(valid,[.025,.975]) if n>=.9*total else (np.nan,np.nan)
    return float(lo),float(hi),n


def prepare(spec):
    rows,issues=complete_rows(spec['rows'],spec['tasks']);dated=[r for r in rows if r['date']]
    base_dates={b:min(r['date'] for r in dated if r['base']==b) for b in {r['base'] for r in dated}}
    mode='rolling' if len(base_dates)>=50 else 'whole-panel (20–49 dated bases)' if len(base_dates)>=20 else 'static only'
    eligible=dated if len(base_dates)>=20 else rows
    if spec.get('select_one'):
        grouped=defaultdict(list)
        for r in eligible:grouped[r['base']].append(r)
        eligible=[max(rs,key=lambda r:(r['priority'],r['model'])) for b,rs in sorted(grouped.items())]
    return dict(spec,rows=eligible,base_dates=base_dates,mode=mode,issues=issues,
                complete_configurations=len(rows),dated_configurations=len(dated),dated_bases=len(base_dates))


def run(resamples,seed,out):
    out.mkdir(parents=True,exist_ok=True)
    specs,statuses,input_hashes=load_sources();panels=[prepare(s) for s in specs];bykey={p['key']:p for p in panels}
    summaries=[];window_rows=[];loading_rows=[];membership=[];matrix=[];scales=[];failures=[];static=[]
    # Share cluster counts across windows and variants within a source, not across sources.
    universes={}
    for p in panels:
        universes.setdefault(p['source'],set()).update(r['base'] for r in p['rows'])
    draws={};indexes={}
    for source,keys in universes.items():
        keys=sorted(keys);indexes[source]={b:i for i,b in enumerate(keys)}
        source_seed=int.from_bytes(hashlib.sha256(source.encode()).digest()[:4],'little')
        rng=np.random.default_rng(np.random.SeedSequence([seed,source_seed]))
        draws[source]=rng.multinomial(len(keys),np.full(len(keys),1/len(keys)),size=resamples)
    for p in panels:
        key=p['key'];tasks=p['tasks'];rows=p['rows'];pcount=len(tasks)
        print('Analyzing',key,len(rows),'configurations',p['dated_bases'],'dated bases',flush=True)
        summary={k:p[k] for k in ('key','source','label','time_axis','mode','notes','sensitivity','complete_configurations','dated_configurations','dated_bases')}
        summary.update(benchmarks=len(tasks),**p['issues']);summaries.append(summary)
        parent=bykey.get(p.get('scale_from'),p)
        if len(rows)<3 or len(parent['rows'])<3:
            summary.update(status='insufficient models for static PCA');continue
        reference=np.array([[r['scores'][t] for t in tasks] for r in parent['rows']]);mu=reference.mean(0);sd=reference.std(0,ddof=1)
        if np.any(sd<=1e-12) or not np.isfinite(sd).all():
            summary.update(status='constant or invalid benchmark on source panel');continue
        X=np.array([[r['scores'][t] for t in tasks] for r in rows]);Z=(X-mu)/sd
        for j,t in enumerate(tasks):scales.append(dict(series=key,benchmark=t,mean=mu[j],sd=sd[j],reference_n=len(reference)))
        for r in rows:matrix.append(dict(series=key,model=r['model'],base=r['base'],date=r['date'],date_evidence=r['date_evidence'],publisher=r['publisher'],scores=json.dumps(r['scores'],sort_keys=True)))
        try:pooled=pc1(Z)
        except ValueError as e:summary.update(status=str(e));continue
        if p['mode']=='static only':
            summary.update(status='static only; fewer than 20 dated bases')
            static.append(dict(series=key,models=len(rows),benchmarks=pcount,explained_variance=pooled['explained_variance'],relative_gap=pooled['relative_gap']))
            for t,w in zip(tasks,pooled['weights']):loading_rows.append(dict(series=key,date='static',benchmark=t,weight=w))
            continue
        ws=monthly_windows(p['base_dates']);group_index=indexes[p['source']];counts=draws[p['source']]
        W=len(ws);directions=np.full((resamples,W,pcount),np.nan);evr=np.full((resamples,W),np.nan);gaps=evr.copy()
        point_axes=[];fits=[];cache={};point_errors=[]
        for wi,w in enumerate(ws):
            bs=set(w['bases']);ix=np.array([i for i,r in enumerate(rows) if r['base'] in bs]);sub=Z[ix]
            keyix=tuple(ix)
            try:
                fit=pc1(sub,pooled['weights']);point_axes.append(fit['weights']);fits.append(fit)
            except ValueError as e:
                point_axes.append(np.full(pcount,np.nan));fits.append(None);point_errors.append((wi,str(e)));continue
            if keyix not in cache:
                m=counts[:,[group_index[rows[i]['base']] for i in ix]]
                axis,ve,gap,valid=weighted_axes(sub,m)
                unique_counts=(counts[:,[group_index[b] for b in sorted(bs)]]>0).sum(axis=1)
                valid &= unique_counts>=3
                axis[~valid]=np.nan;ve[~valid]=np.nan;gap[~valid]=np.nan
                axis*=np.where(axis@fit['weights']<0,-1,1)[:,None]
                cache[keyix]=(axis,ve,gap,valid)
            axis,ve,gap,valid=cache[keyix]
            directions[:,wi]=axis;evr[:,wi]=ve;gaps[:,wi]=gap
            for i in ix:membership.append(dict(series=p['key'],date=w['date'],model=rows[i]['model'],base=rows[i]['base']))
            if not valid.all():failures.append(dict(series=p['key'],date=w['date'],failed=int((~valid).sum()),attempted=resamples,reason='fewer than 3 distinct sampled bases or nonseparated/degenerate PC1'))
        valid_points=[i for i,f in enumerate(fits) if f is not None]
        if not valid_points:summary.update(status='no admissible point fits');continue
        first=valid_points[0];previous=None;point_axes=np.array(point_axes)
        rotation=angles(directions,directions[:,first:first+1,:]);rotation[:,first]=np.where(np.isfinite(evr[:,first]),0,np.nan)
        deviation=angles(directions,point_axes[None,:,:]);adjacent=np.full((resamples,W),np.nan)
        for wi in valid_points:
            if previous is not None:adjacent[:,wi]=angles(directions[:,wi],directions[:,previous])
            previous=wi
        np.savez_compressed(out/(p['key']+'_bootstrap.npz'),directions=directions,explained_variance=evr,relative_gap=gaps,
                            rotation=rotation,adjacent_rotation=adjacent,angle_to_point=deviation,dates=np.array([w['date'] for w in ws]),tasks=np.array(tasks))
        previous=None
        for wi,w in enumerate(ws):
            fit=fits[wi]
            if fit is None:
                failures.append(dict(series=p['key'],date=w['date'],failed=resamples,attempted=resamples,reason=dict(point_errors)[wi]));continue
            ix=[i for i,r in enumerate(rows) if r['base'] in w['bases']]
            r=dict(series=p['key'],source=p['source'],time_axis=p['time_axis'],date=w['date'],baseline_date=ws[first]['date'],models=len(ix),bases=len(w['bases']),benchmarks=pcount,
                   radius_days=w['radius_days'],window_start=w['start'],window_end=w['end'],span_days=w['span_days'],effective_date=w['effective_date'],endpoint_imbalanced=w['endpoint_imbalanced'],
                   rotation=similarity(point_axes[first],point_axes[wi])['angle_degrees'],explained_variance=fit['explained_variance'],relative_gap=fit['relative_gap'],constant_tasks=fit['constant_tasks'],
                   adjacent_rotation=similarity(point_axes[previous],point_axes[wi])['angle_degrees'] if previous is not None else np.nan)
            for name,values in [('rotation',rotation[:,wi]),('explained_variance',evr[:,wi]),('relative_gap',gaps[:,wi]),('adjacent_rotation',adjacent[:,wi])]:
                low,high,n=interval(values,resamples);r[name+'_low']=low;r[name+'_high']=high;r[name+'_admissible']=n
            good=deviation[:,wi][np.isfinite(deviation[:,wi])];r['angular_deviation_q95']=float(np.quantile(good,.95)) if len(good)>=.9*resamples else np.nan
            window_rows.append(r)
            for j,t in enumerate(tasks):
                low,high,n=interval(directions[:,wi,j],resamples)
                loading_rows.append(dict(series=p['key'],date=w['date'],benchmark=t,weight=point_axes[wi,j],low=low,high=high,admissible=n))
            previous=wi
        summary.update(status='ok',windows=len(valid_points),unique_windows=len(cache),start=ws[first]['date'],end=ws[valid_points[-1]]['date'],
                       first_last_angle=float(similarity(point_axes[first],point_axes[valid_points[-1]])['angle_degrees']))
    for name,rs in [('series',summaries),('windows',window_rows),('loadings',loading_rows),('memberships',membership),('matrix',matrix),('standardization',scales),('bootstrap_failures',failures),('static',static),('source_status',statuses)]:write_csv(out/(name+'.csv'),rs)
    manifest=dict(resamples=resamples,seed=seed,inputs=input_hashes,code={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['parallel_rolling_pca.py','rolling_pca_sources.py','aa_cohort_pca.py','epoch_cohort_overlap.py','epoch_data_audit.py']},
        methods=dict(window='monthly midpoints, nearest 50 eligible bases, include distance ties; complete fixed battery BEFORE windows; 20–49 bases use whole panel; fewer than 20 static',
        base_date='earliest eligible date within base; preserves all configurations together',scaling='fixed complete dated source-panel mean and sample SD; selected-config sensitivities reuse parent scaling',
        bootstrap='2000 global whole-base multinomial draws per source, matched across its windows and variants; fixed eligibility/scaling/window membership; >=3 sampled distinct bases and unique PC1 required',
        intervals='pointwise percentile, withheld below 90% admissible; no formal rotation null test or simultaneous coverage',
        comparison='each series has its own first window, battery and source scale; overlay is descriptive, not equal latent units',
        shared_battery='no verified multi-benchmark protocol-equivalent cross-source battery established; direct cross-source vector angles withheld'))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    lines=['# Parallel rolling PCA','','Separate fixed-battery trajectories, using all locally supportable dates. Complete eligible configurations are selected before time windows.','',
           '![Rolling PCA](rolling-pca.png)','','[Source loadings](loadings.png) · [Configuration and battery sensitivities](sensitivities.png)','','| Series | Time axis | Complete configurations | Dated bases | Result | Range |','|---|---|---:|---:|---|---|']
    for r in summaries:lines.append(f"| {r['label']} | {r['time_axis']} | {r['complete_configurations']} | {r['dated_bases']} | {r['status']} | {r.get('start','')} – {r.get('end','')} |")
    lines+=['','## Interpretation','',
      'Rotation is relative to each series’s own first window, in fixed within-source benchmark units. Curves have different batteries, populations and baselines; their angles and variance shares are descriptive cross-checks, not a shared intelligence scale. A three-task Epoch battery is much narrower than AA. PCA rotation does not identify a change in latent intelligence.',
      f'{resamples:,} whole-base cluster draws per source produce pointwise 95% percentile intervals. Adjacent windows overlap. Positive angle intervals are not a test of a shared-axis null; rotation has a sampling-noise floor. More than 10% inadmissibility withholds an interval. Base IDs do not establish independent ancestry.',
      'Monthly plotting does not create monthly information: early/late windows borrow across releases. Hollow markers indicate less than 20% of window bases on one side of the grid date; window spans, effective dates and unique membership counts are exported. Whole-panel series with 20–49 dated bases contain no within-series temporal resolution.',
      'Release/version-date panels, evaluation-date panels and unclassified recorded-timestamp panels are separate. Dates resolved by exact alias do not establish equal configurations or protocols. No cross-source scores are pooled and no missing scores are filled.',
      'Source loaders and frozen model matrices are included. Old integration-audit candidates are not used as verified model bridges. Bootstrap output arrays and code/input hashes accompany the CSVs. Figures replace the earlier invalid coverage plot, which mixed window-radius days with configuration counts.','', '## Source notes','']
    for r in summaries:lines.append(f"- **{r['label']}**: {r['notes']}")
    lines+=['','## Reproduce','','```sh','OPENBLAS_NUM_THREADS=1 uv run python parallel_rolling_pca.py --resamples 2000','uv run python plot_parallel_rolling_pca.py','```','', 'Raw inputs must be present locally; large downloads remain Git-ignored. Use `--out` for a separate run. `matrix.csv` exports the final source panels for inspection.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')
    print('COMPLETE',out,flush=True)
    return summaries


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--resamples',type=int,default=2000);ap.add_argument('--seed',type=int,default=20261107);ap.add_argument('--out',type=Path,default=DEFAULT_OUT)
    args=ap.parse_args()
    if args.resamples<1:ap.error('--resamples must be positive')
    run(args.resamples,args.seed,args.out)
