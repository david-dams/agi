"""Frozen AA release-cohort factor analysis; aggregate scores, no item bootstrap."""
import argparse
from collections import defaultdict, Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

import numpy as np
from scipy import optimize, stats
from aa_provenance_audit import parse_models
from downloaded_data_audit import CORE, DATA, period, write_csv
from factor_models import fit_higher_order

OUT = Path(__file__).resolve().parent / 'output/aa-cohort'
HALVES = ('2025H1', '2025H2', '2026H1')
BATTERIES = {'nine': list(CORE), 'eight': [t for t in CORE if t != 'critpt']}


def identity(model):
    def keep(match):
        text = match.group(1).lower()
        setting = bool(re.search(r'reasoning|effort', text) or text in ('xhigh','high','medium','low','minimal'))
        return '' if setting else match.group(0)
    base = re.sub(r'\s*\(([^)]*)\)', keep, model['name']).strip()
    return model['modelCreatorName'] + '/' + base


def effort(model):
    text = model['name'].lower()
    for rank, pattern in [(6,r'xhigh|max effort'), (5,r'\bhigh\b'), (4,r'\bmedium\b'),
                          (2,r'\blow\b'), (1,r'\bminimal\b')]:
        if re.search(pattern,text): return rank
    return 3 if model['isReasoning'] else 0


def fit(X):
    R = np.corrcoef(X, rowvar=False)
    return fit_higher_order(R, len(X), [list(range(X.shape[1]))])


def metric_invariance(matrices):
    """Equal unstandardized loadings with free group factor/residual variances.

    Covariances use a single pooled unit transformation; no cohort z-scoring.
    GPQA is the marker (loading fixed to one). Means are not constrained.
    """
    pooled_sd = np.vstack(matrices).std(0, ddof=1)
    covs = [np.cov(X / pooled_sd, rowvar=False) for X in matrices]
    ns = np.array([len(X)-1 for X in matrices]); G = len(covs); p = len(pooled_sd)
    freefits = [fit(X) for X in matrices]
    starts = []
    for S, f in zip(covs, freefits):
        lam = f.lam_g * np.sqrt(np.diag(S))
        starts.append(np.r_[lam[1:] / lam[0],
            np.log([ff.lam_g[0]**2 * ss[0,0] for ss,ff in zip(covs,freefits)]),
            np.log(np.concatenate([ff.theta*np.diag(ss) for ss,ff in zip(covs,freefits)]))])
    def objective(x):
        lam = np.r_[1., x[:p-1]]; phi = np.exp(x[p-1:p-1+G]); theta = np.exp(x[p-1+G:]).reshape(G,p)
        value=0.; dl=np.zeros(p); dp=[]; dt=[]
        for S,n,v,t in zip(covs,ns,phi,theta):
            sig=v*np.outer(lam,lam)+np.diag(t); inv=np.linalg.inv(sig)
            value += n*(np.linalg.slogdet(sig)[1]+np.trace(S@inv)-np.linalg.slogdet(S)[1]-p)
            D=n*(inv-inv@S@inv)
            dl += 2*v*D@lam; dp.append(v*lam@D@lam); dt.extend(np.diag(D)*t)
        return value, np.r_[dl[1:],dp,dt]
    bounds=[(-15,15)]*(p-1)+[(-12,8)]*G+[(-12,5)]*(G*p)
    results=[optimize.minimize(objective,x,jac=True,method='L-BFGS-B',bounds=bounds,
        options=dict(maxiter=6000,ftol=1e-11,gtol=1e-6)) for x in starts]
    good=[r for r in results if r.success and np.isfinite(r.fun)]
    if not good:raise RuntimeError('Metric invariance optimization failed')
    r=min(good,key=lambda r:r.fun); free_chi=sum(f.chi2 for f in freefits)
    if r.fun < free_chi-1e-4:raise RuntimeError('Constrained fit beats free fit; check optimizer')
    delta=max(0.,r.fun-free_chi); delta_df=(G-1)*(p-1)
    null_chi=sum(-n*np.linalg.slogdet(S/np.sqrt(np.outer(np.diag(S),np.diag(S))))[1] for n,S in zip(ns,covs))
    null_df=G*p*(p-1)//2; free_df=sum(f.df for f in freefits)
    cfi=lambda chi,df:1-max(chi-df,0)/max(null_chi-null_df,1e-12)
    return dict(free_chi2=free_chi,free_df=free_df,equal_loading_chi2=float(r.fun),equal_loading_df=free_df+delta_df,
        delta_chi2=delta,delta_df=delta_df,approximate_p=float(stats.chi2.sf(delta,delta_df)),
        free_cfi=cfi(free_chi,free_df),equal_loading_cfi=cfi(r.fun,free_df+delta_df),
        delta_cfi=cfi(r.fun,free_df+delta_df)-cfi(free_chi,free_df),
        boundary=any(min(abs(v-lo),abs(v-hi))<1e-4 for v,(lo,hi) in zip(r.x,bounds)),
        caveat='Gaussian reference p-value; family dependence and bounded scores not corrected; covariance-only metric test, no scalar test')


def run(reps,seed):
    OUT.mkdir(parents=True,exist_ok=True)
    archive=DATA/'archives/aa-bundle.zip'
    with zipfile.ZipFile(archive) as z:
        name=next(n for n in z.namelist() if n.endswith('/aa_leaderboards_models_snapshot.html'))
        models=parse_models(z.read(name).decode())
    models=[m for m in models if all(type(m.get(t)) in (int,float) for t in CORE) and m.get('releaseDate') and period(m['releaseDate'],'half') in HALVES]
    groups=defaultdict(list)
    for i,m in enumerate(models):groups[identity(m)].append(i)
    selected={max(indices,key=lambda i:(effort(models[i]),models[i]['slug'])) for indices in groups.values()}
    mapping=[dict(id=m['id'],slug=m['slug'],name=m['name'],release_date=m['releaseDate'],cohort=period(m['releaseDate'],'half'),
        publisher=m['modelCreatorName'],base_cluster=identity(m),selected=i in selected,effort_rank=effort(m),
        identity_status='explicit name setting variants; broader ancestry unresolved',source='archived AA name and modelCreatorName') for i,m in enumerate(models)]
    write_csv(OUT/'configurations.csv',mapping)
    write_csv(OUT/'matrix.csv',[dict(id=m['id'],slug=m['slug'],**{t:m[t] for t in CORE}) for m in models])
    allX=np.array([[m[t] for t in CORE] for m in models]); cohort=np.array([period(m['releaseDate'],'half') for m in models])
    points=[];loadings=[];residuals=[];diagnostics=[];invariance=[]; cases={};fits={}
    for sample in ('all','selected'):
        for battery,tasks in BATTERIES.items():
            cols=[CORE.index(t) for t in tasks]
            for half in HALVES:
                ix=np.array([i for i in range(len(models)) if cohort[i]==half and (sample=='all' or i in selected)])
                X=allX[np.ix_(ix,cols)]; f=fit(X);key=(sample,battery,half);cases[key]=(ix,cols);fits[key]=f
                row=dict(sample=sample,battery=battery,cohort=half,n=len(X),clusters=len({identity(models[i]) for i in ix}),boundary=f.boundary,
                    **{k:float(getattr(f,k)) for k in ('g_variance_share','cfi','rmsea','chi2','df','residual_rms','omega_h','aic','bic')})
                points.append(row)
                print('point',sample,battery,half,'n',len(X),'g',round(f.g_variance_share,4),'CFI',round(f.cfi,4),flush=True)
                for j,t in enumerate(tasks):loadings.append(dict(sample=sample,battery=battery,cohort=half,task=t,loading=float(f.standardized_g[j]),zeros=int(sum(X[:,j]==0))))
                R=np.corrcoef(X,rowvar=False); scale=np.sqrt(np.diag(f.sigma)); E=R-f.sigma/np.outer(scale,scale)
                for j in range(len(tasks)):
                    for k in range(j):residuals.append(dict(sample=sample,battery=battery,cohort=half,task1=tasks[k],task2=tasks[j],residual=float(E[j,k])))
            inv=metric_invariance([allX[np.ix_(*cases[(sample,battery,h)])] for h in HALVES])
            invariance.append(dict(sample=sample,battery=battery,**inv))
    write_csv(OUT/'fits.csv',points);write_csv(OUT/'loadings.csv',loadings);write_csv(OUT/'residuals.csv',residuals)
    (OUT/'invariance.json').write_text(json.dumps(invariance,indent=2)+'\n')
    # Quarterly fits are secondary and have no inferential intervals in this run.
    quarters=[]
    for q in sorted({period(m['releaseDate'],'quarter') for m in models}):
        for battery,tasks in BATTERIES.items():
            X=np.array([[m[t] for t in tasks] for m in models if period(m['releaseDate'],'quarter')==q])
            try:
                f=fit(X);quarters.append(dict(quarter=q,battery=battery,n=len(X),g_variance_share=f.g_variance_share,cfi=f.cfi,rmsea=f.rmsea,status='boundary' if f.boundary else 'ok'))
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:quarters.append(dict(quarter=q,battery=battery,n=len(X),g_variance_share=None,cfi=None,rmsea=None,status=str(e)))
    write_csv(OUT/'quarters.csv',quarters)
    keys=list(cases);draws=np.full((reps,len(keys)),np.nan);loading_draws={k:np.full((reps,len(cases[k][1])),np.nan) for k in keys}
    rng=np.random.default_rng(seed);family_keys=sorted(groups)
    for rep in range(reps):
        # One global cluster draw preserves repeat-base dependence between cohorts and A/B.
        sampled=[i for f in rng.choice(family_keys,size=len(family_keys),replace=True) for i in groups[f]]
        for c,key in enumerate(keys):
            eligible,cols=cases[key]; eligible=set(eligible);ix=[i for i in sampled if i in eligible]
            status='ok';detail=''
            try:
                f=fit(allX[np.ix_(ix,cols)])
                if f.boundary:status='boundary'
                else:draws[rep,c]=f.g_variance_share;loading_draws[key][rep]=f.standardized_g
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:status='failed';detail=str(e)
            if status!='ok':diagnostics.append(dict(replicate=rep,sample=key[0],battery=key[1],cohort=key[2],status=status,detail=detail))
        if (rep+1)%50==0:print('bootstrap',rep+1,'/',reps,flush=True)
    np.savez_compressed(OUT/'bootstrap.npz',g=draws,keys=np.array(keys),**{':'.join(k):v for k,v in loading_draws.items()})
    write_csv(OUT/'bootstrap_problems.csv',diagnostics or [dict(replicate='',sample='',battery='',cohort='',status='none',detail='')])
    def interval(v):
        ok=np.isfinite(v);out=dict(admissible=int(ok.sum()),replicates=reps,low=None,high=None,bootstrap_mean=None)
        if ok.sum()>=.9*reps:
            lo,hi=np.quantile(v[ok],[.025,.975]);out.update(low=float(lo),high=float(hi),bootstrap_mean=float(v[ok].mean()))
        return out
    intervals=[dict(sample=k[0],battery=k[1],cohort=k[2],point=fits[k].g_variance_share,**interval(draws[:,c])) for c,k in enumerate(keys)]
    differences=[]
    for sample in ('all','selected'):
        for a,b in [(HALVES[0],HALVES[1]),(HALVES[1],HALVES[2]),(HALVES[0],HALVES[2])]:
            ds={};ps={}
            for battery in BATTERIES:
                ka=(sample,battery,a);kb=(sample,battery,b)
                ds[battery]=draws[:,keys.index(kb)]-draws[:,keys.index(ka)];ps[battery]=fits[kb].g_variance_share-fits[ka].g_variance_share
                differences.append(dict(sample=sample,battery=battery,contrast=b+' minus '+a,point=ps[battery],**interval(ds[battery])))
            differences.append(dict(sample=sample,battery='nine-minus-eight',contrast=b+' minus '+a,point=ps['nine']-ps['eight'],**interval(ds['nine']-ds['eight'])))
    write_csv(OUT/'intervals.csv',intervals);write_csv(OUT/'differences.csv',differences)
    li=[]
    for key,v in loading_draws.items():
        for j,t in enumerate(BATTERIES[key[1]]):li.append(dict(sample=key[0],battery=key[1],cohort=key[2],task=t,**interval(v[:,j])))
    write_csv(OUT/'loading_intervals.csv',li)
    meta=dict(replicates=reps,seed=seed,source_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        code_sha256={p:hashlib.sha256((Path(__file__).resolve().parent / p).read_bytes()).hexdigest() for p in ('aa_cohort_factor.py','factor_models.py','aa_provenance_audit.py')},
        python=sys.version,numpy=np.__version__,cluster_count=len(groups),configurations=len(models),selected=len(selected),
        selection='highest explicit effort rank, then reasoning for unspecified effort, then lexicographically last slug; no benchmark selection',
        cluster_limit='base setting variants only; broader shared ancestry unresolved; intervals conditional on clustering and selected AA population')
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    render(points,intervals,differences,invariance,meta,loadings,residuals)


def render(points,intervals,diffs,invariance,meta,loadings,residuals):
    lines=['# AA release-cohort g analysis','',f"Frozen July 6, 2026 snapshot; {meta['configurations']} complete configurations in 2025H1–2026H1; {meta['cluster_count']} base-setting clusters; {meta['selected']} selected configurations. {meta['replicates']} matched global cluster bootstrap draws.",'',
        '| Sample | Battery | Cohort | N | g variance | 95% cluster range | CFI | RMSEA |','|---|---|---|---:|---:|---|---:|---:|']
    def ci(x):return 'withheld' if x['low'] is None else f"[{x['low']:.3f}, {x['high']:.3f}]"
    for r in points:
        v=next(x for x in intervals if all(x[k]==r[k] for k in ('sample','battery','cohort')))
        lines.append(f"| {r['sample']} | {r['battery']} | {r['cohort']} | {r['n']} | {r['g_variance_share']:.3f} | {ci(v)} ({v['admissible']}/{meta['replicates']}) | {r['cfi']:.3f} | {r['rmsea']:.3f} |")
    lines+=['','## Direct cohort differences','','| Sample | Battery | Contrast | Difference | 95% cluster range |','|---|---|---|---:|---|']
    for r in diffs:lines.append(f"| {r['sample']} | {r['battery']} | {r['contrast']} | {r['point']:+.3f} | {ci(r)} |")
    lines+=['','## Equal-loading comparison','','Covariance-only multi-group CFA uses pooled units, GPQA marker loading = 1, free cohort factor variances and residual variances; means unconstrained. These approximate Gaussian p-values do not correct family dependence or bounded scores. They are diagnostics, not calibrated hypothesis decisions.','']
    for r in invariance:lines.append(f"- {r['sample']}/{r['battery']}: Δχ²={r['delta_chi2']:.2f}, Δdf={r['delta_df']}, approximate p={r['approximate_p']:.4g}, ΔCFI={r['delta_cfi']:+.3f}, boundary={r['boundary']}.")
    lines+=['','## Interpretation limits','','g variance is the mean squared standardized one-factor loading; it describes covariance within each cohort, not capability level. A strong g can coexist with poor one-factor fit. CritPt A/B uses exactly matched rows. Cohorts are source release dates, not historical evaluation snapshots. No cross-battery AIC/BIC comparison is made.','',
        'Cluster intervals are nominal percentile sensitivity ranges, conditional on base-setting clusters; broader ancestry is unresolved and item uncertainty cannot be estimated from these aggregates. Fewer than 90% admissible draws causes interval withholding. Failed and boundary fits are recorded, not regularized. Loading intervals do not adjust for multiple comparisons. No scalar invariance or capability-mean comparison is claimed.','',
        'Configuration selection uses explicit effort labels without benchmark performance. Unspecified reasoning settings rank between medium and low; ranks are an operational rule, not equal compute budgets. Remaining name/version differences and shared training ancestry are not inferred away.','',
        'Files: configurations.csv, matrix.csv, fits.csv, loadings.csv, loading_intervals.csv, residuals.csv, intervals.csv, differences.csv, invariance.json, quarters.csv, bootstrap.npz, bootstrap_problems.csv, metadata.json.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    plot(points,intervals,diffs,loadings,residuals)


def plot(points,intervals,diffs,loadings,residuals):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for battery,color,offset in [('nine','#225ea8',-.05),('eight','#d95f0e',.05)]:
        rows=[r for r in intervals if r['sample']=='all' and r['battery']==battery]
        x=np.arange(3)+offset;y=np.array([r['point'] for r in rows]);axes[0].plot(x,y,'o-',color=color,label=battery+' indicators')
        for xx,r in zip(x,rows):
            if r['low'] is not None:axes[0].vlines(xx,r['low'],r['high'],color=color)
        rows=[r for r in diffs if r['sample']=='all' and r['battery']==battery]
        for j,r in enumerate(rows):
            axes[1].plot(j+offset,r['point'],'o',color=color)
            if r['low'] is not None:axes[1].vlines(j+offset,r['low'],r['high'],color=color)
    axes[0].set(xticks=range(3),xticklabels=HALVES,ylabel='g-attributed standardized task variance',title='Release cohorts (all configurations)');axes[0].legend()
    axes[1].set(xticks=range(3),xticklabels=['H2 2025 − H1 2025','H1 2026 − H2 2025','H1 2026 − H1 2025'],ylabel='Difference in g variance',title='Matched cluster-bootstrap contrasts');axes[1].tick_params(axis='x',labelrotation=15);axes[1].axhline(0,color='gray',lw=1)
    fig.savefig(OUT/'cohort_g.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for battery,ax in zip(BATTERIES,axes):
        for half in HALVES:
            rs=[r for r in loadings if r['sample']=='all' and r['battery']==battery and r['cohort']==half]
            ax.plot(range(len(rs)),[r['loading'] for r in rs],'o-',label=half)
        ax.set(xticks=range(len(BATTERIES[battery])),xticklabels=BATTERIES[battery],ylabel='Standardized loading',title=battery+' indicators');ax.tick_params(axis='x',labelrotation=65);ax.legend()
    fig.savefig(OUT/'loadings.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(11,7),layout='constrained')
    for row,battery in enumerate(BATTERIES):
        tasks=BATTERIES[battery]
        for col,half in enumerate(HALVES):
            E=np.zeros((len(tasks),len(tasks)))
            for r in residuals:
                if r['sample']=='all' and r['battery']==battery and r['cohort']==half:
                    j,k=tasks.index(r['task1']),tasks.index(r['task2']);E[j,k]=E[k,j]=r['residual']
            ax=axes[row,col];im=ax.imshow(E,vmin=-.3,vmax=.3,cmap='RdBu_r');ax.set(title=half+' '+battery,xticks=range(len(tasks)),xticklabels=tasks,yticks=range(len(tasks)),yticklabels=tasks);ax.tick_params(axis='x',labelrotation=90,labelsize=7);ax.tick_params(axis='y',labelsize=7)
    fig.colorbar(im,ax=axes,label='Observed minus implied correlation',shrink=.7);fig.savefig(OUT/'residuals.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for j,task in enumerate(('critpt','lcr')):
        rs=[r for r in loadings if r['sample']=='all' and r['battery']=='nine' and r['task']==task]
        ns=[r['n'] for r in points if r['sample']=='all' and r['battery']=='nine']
        axes[j].bar(HALVES,[r['zeros']/n for r,n in zip(rs,ns)]);axes[j].set(title=task,ylabel='Fraction scoring exactly zero',ylim=(0,1))
    fig.savefig(OUT/'floors.png',dpi=180);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resamples',type=int,default=1000);parser.add_argument('--seed',type=int,default=20261026)
    args=parser.parse_args()
    if args.resamples<1:parser.error('resamples must be positive')
    run(args.resamples,args.seed)
