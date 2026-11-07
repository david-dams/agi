"""Exploratory AA CFA with fixed domain residual blocks; reuse the frozen cohort run."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy import optimize, stats, linalg
from aa_cohort_factor import HALVES, BATTERIES
from downloaded_data_audit import write_csv
from factor_models import fit_higher_order

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'output/aa-cohort'
OUT=ROOT/'output/aa-residual-cfa'
SPECS={'coding': [('scicode','terminalbenchHard')],
       'coding_academic': [('scicode','terminalbenchHard'),('gpqa','hle','omniscience')]}


def residual_fit(covs, ns, blocks, equal_loadings=False, free_loadings=(), marker=0, initial_fit=None):
    """ML covariance CFA, GPQA marker, free factor variance, PD block residuals.

    Blocks must be disjoint cliques. Their Cholesky factors parameterize residual
    covariance; other residuals remain independent. No sample regularization.
    """
    covs=np.asarray(covs,dtype=float); ns=np.asarray(ns,dtype=float)
    if covs.ndim!=3 or len(covs)!=len(ns):raise ValueError('Expected group covariance matrices and sample sizes')
    G,p,_=covs.shape
    if marker not in range(p) or any(i not in range(p) or i==marker for i in free_loadings):
        raise ValueError('Invalid marker or partial loading indices')
    if covs.shape[1:]!=(p,p) or not np.isfinite(covs).all() or np.any(ns<3):raise ValueError('Invalid covariance inputs')
    for S in covs:
        if not np.allclose(S,S.T) or np.linalg.eigvalsh(S).min()<=1e-9:raise ValueError('Sample covariance must be positive definite; no regularization')
    members=[i for b in blocks for i in b]
    if len(set(members))!=len(members) or any(i<0 or i>=p for i in members):raise ValueError('Residual blocks must be disjoint and in range')
    edges=[(i,j) for b in blocks for i in sorted(b) for j in sorted(b) if i>j]
    e=len(edges);width=p+e
    indicators=[i for i in range(p) if i!=marker]
    if not equal_loadings:
        loading_map=np.arange(G*(p-1)).reshape(G,p-1)
    else:
        loading_map=np.empty((G,p-1),dtype=int);counter=0
        for j,i in enumerate(indicators):
            if i in free_loadings:
                loading_map[:,j]=np.arange(counter,counter+G);counter+=G
            else:loading_map[:,j]=counter;counter+=1
    nl=int(loading_map.max())+1
    nparams=nl+G+G*width;df=G*p*(p+1)//2-nparams
    if df<=0:raise ValueError('Model must be overidentified')
    baseline=[]
    for g,(S,n) in enumerate(zip(covs,ns)):
        if initial_fit is None:
            sd=np.sqrt(np.diag(S));f=fit_higher_order(S/np.outer(sd,sd),int(n),[list(range(p))])
            lam=f.lam_g*sd;phi=1.;residual=np.diag(f.theta*sd**2)
        else:
            previous=initial_fit['groups'][g]
            lam=np.array(previous['raw_loadings']);phi=previous['factor_variance'];residual=np.array(previous['residual_covariance'])
        if abs(lam[marker])<1e-6:raise ValueError('Marker loading too small')
        C=np.linalg.cholesky(residual)
        baseline.append((lam/lam[marker],phi*lam[marker]**2,C))
    loads=np.zeros(nl);counts=np.zeros(nl)
    for g,v in enumerate(baseline):
        np.add.at(loads,loading_map[g],v[0][indicators]);np.add.at(counts,loading_map[g],1)
    loads/=counts
    initial=np.r_[loads,np.log([v[1] for v in baseline]),np.concatenate([np.r_[np.log(np.diag(v[2])),[v[2][i,j] for i,j in edges]] for v in baseline])]
    def unpack(x):
        ls=np.ones((G,p));ls[:,indicators]=x[:nl][loading_map]
        phis=np.exp(x[nl:nl+G]); pars=x[nl+G:].reshape(G,width)
        Cs=[]
        for v in pars:
            C=np.diag(np.exp(v[:p]))
            for k,(i,j) in enumerate(edges):C[i,j]=v[p+k]
            Cs.append(C)
        return ls,phis,Cs
    constants=[np.linalg.slogdet(S)[1]+p for S in covs]
    def objective(x):
        ls,phis,Cs=unpack(x);value=0.;dl=[];dp=[];dr=[]
        for S,n,lam,phi,C,constant in zip(covs,ns,ls,phis,Cs,constants):
            sigma=phi*np.outer(lam,lam)+C@C.T
            # A mathematically PD parameterization can lose definiteness numerically.
            if np.linalg.eigvalsh(sigma)[0] <= 1e-10 * max(1.,np.max(np.diag(sigma))):
                return 1e8,np.zeros_like(x)
            try:
                factor=linalg.cho_factor(sigma,lower=True,check_finite=False)
                inv=linalg.cho_solve(factor,np.eye(p),check_finite=False)
            except linalg.LinAlgError:
                return 1e8,np.zeros_like(x)
            logdet=2*np.log(np.diag(factor[0])).sum()
            value+=(n-1)*(logdet+np.trace(S@inv)-constant)
            D=(n-1)*(inv-inv@S@inv);dl.append((2*phi*D@lam)[indicators]);dp.append(phi*lam@D@lam)
            dC=2*D@C;dr.extend(np.r_[np.diag(dC)*np.diag(C),[dC[i,j] for i,j in edges]])
        loading_gradient=np.zeros(nl)
        np.add.at(loading_gradient,loading_map.ravel(),np.array(dl).ravel())
        return float(value),np.r_[loading_gradient,dp,dr]
    bounds=[(-15,15)]*nl+[(-12,8)]*G+([(-6,3)]*p+[(-5,5)]*e)*G
    starts=[initial]
    if e:
        second=initial.copy()
        for g,S in enumerate(covs):
            for k,(i,j) in enumerate(edges):second[nl+G+g*width+p+k]=.1*S[i,j]/np.sqrt(S[j,j])
        starts.append(second)
    results=[optimize.minimize(objective,x,jac=True,method='L-BFGS-B',bounds=bounds,
             options=dict(maxiter=4000,maxls=60,ftol=1e-12,gtol=1e-6)) for x in starts]
    results=[r for r in results if r.success and np.isfinite(r.fun) and r.fun<1e8]
    def projected_gradient(r):
        gradient=r.jac.copy()
        for j,(v,(lo,hi)) in enumerate(zip(r.x,bounds)):
            if (v<=lo+1e-5 and gradient[j]>0) or (v>=hi-1e-5 and gradient[j]<0):gradient[j]=0
        return float(np.max(np.abs(gradient)))
    # A line-search stop at the starting point is not a fitted solution.
    results=[r for r in results if projected_gradient(r)<.1]
    if not results:raise RuntimeError('No residual CFA start converged')
    best=min(results,key=lambda r:r.fun);ls,phis,Cs=unpack(best.x)
    chi=max(0.,float(best.fun));null=sum(-(n-1)*np.linalg.slogdet(S/np.sqrt(np.outer(np.diag(S),np.diag(S))))[1] for n,S in zip(ns,covs));null_df=G*p*(p-1)//2
    cfi=1-max(chi-df,0)/max(null-null_df,1e-12)
    group_results=[]
    for S,lam,phi,C in zip(covs,ls,phis,Cs):
        residual=C@C.T;sigma=phi*np.outer(lam,lam)+residual;sd=np.sqrt(np.diag(sigma));loading=lam*np.sqrt(phi)/sd
        R=S/np.sqrt(np.outer(np.diag(S),np.diag(S)));error=R-sigma/np.outer(sd,sd)
        group_results.append(dict(g_variance_share=float(np.mean(loading**2)),loadings=loading.tolist(),
            raw_loadings=lam.tolist(),factor_variance=float(phi),sigma=sigma.tolist(),
            residual_covariance=residual.tolist(),residual_correlation=(residual/np.sqrt(np.outer(np.diag(residual),np.diag(residual)))).tolist(),
            residuals=error.tolist(),residual_rms=float(np.sqrt(np.mean(error[np.triu_indices(p,1)]**2)))))
    return dict(chi2=chi,df=df,cfi=cfi,rmsea=float(np.sqrt(max((chi-df)/(df*sum(ns-1)/G),0))),
        aic=chi+2*nparams,bic=chi+sum(np.log(ns))*nparams/G,nparams=nparams,
        boundary=any(min(abs(v-lo),abs(v-hi))<1e-4 for v,(lo,hi) in zip(best.x,bounds)),
        gradient_norm=float(np.max(np.abs(best.jac))),projected_gradient_norm=projected_gradient(best),groups=group_results)


def read_csv(path):return list(csv.DictReader(path.open()))


def run(reps):
    OUT.mkdir(parents=True,exist_ok=True)
    meta=json.loads((SOURCE/'metadata.json').read_text());members=read_csv(SOURCE/'configurations.csv');rows=read_csv(SOURCE/'matrix.csv')
    if [r['id'] for r in rows]!=[m['id'] for m in members]:raise ValueError('Membership/matrix IDs differ')
    primary=read_csv(SOURCE/'fits.csv');X=np.array([[float(r[t]) for t in BATTERIES['nine']] for r in rows]);tasks9=BATTERIES['nine']
    cases={};pointfits={};points=[];loadings=[];correlations=[];errors=[];invariance=[]
    for sample in ('all','selected'):
        for battery,tasks in BATTERIES.items():
            cols=[tasks9.index(t) for t in tasks]
            matrices=[]
            for h in HALVES:
                ix=[i for i,m in enumerate(members) if m['cohort']==h and (sample=='all' or m['selected']=='True')]
                matrices.append(X[np.ix_(ix,cols)]);cases[(sample,battery,h)]=(ix,cols)
            for spec,namedblocks in SPECS.items():
                blocks=[[tasks.index(t) for t in b] for b in namedblocks]
                fs=[]
                for h,M in zip(HALVES,matrices):
                    f=residual_fit([np.corrcoef(M,rowvar=False)],[len(M)],blocks);key=(sample,battery,spec,h);pointfits[key]=f;fs.append(f)
                    baseline=next(r for r in primary if r['sample']==sample and r['battery']==battery and r['cohort']==h)
                    if f['chi2']>float(baseline['chi2'])+1e-3:raise RuntimeError('Expanded model fit worse than nested baseline')
                    g=f['groups'][0];points.append(dict(sample=sample,battery=battery,spec=spec,cohort=h,n=len(M),
                        **{k:f[k] for k in ('chi2','df','cfi','rmsea','aic','bic','boundary')},g_variance_share=g['g_variance_share'],residual_rms=g['residual_rms'],
                        delta_chi2=float(baseline['chi2'])-f['chi2'],delta_bic=f['bic']-float(baseline['bic'])))
                    for j,t in enumerate(tasks):loadings.append(dict(sample=sample,battery=battery,spec=spec,cohort=h,task=t,loading=g['loadings'][j]))
                    for b in blocks:
                        for j in b:
                            for k in b:
                                if k<j:correlations.append(dict(sample=sample,battery=battery,spec=spec,cohort=h,task1=tasks[k],task2=tasks[j],correlation=g['residual_correlation'][j][k]))
                    for j in range(len(tasks)):
                        for k in range(j):errors.append(dict(sample=sample,battery=battery,spec=spec,cohort=h,task1=tasks[k],task2=tasks[j],residual=g['residuals'][j][k]))
                    print('point',key,'g',round(g['g_variance_share'],3),'CFI',round(f['cfi'],3),'dBIC',round(points[-1]['delta_bic'],1),flush=True)
                pooled_sd=np.vstack(matrices).std(0,ddof=1);covs=[np.cov(M/pooled_sd,rowvar=False) for M in matrices];ns=[len(M) for M in matrices]
                free=residual_fit(covs,ns,blocks);equal=residual_fit(covs,ns,blocks,True)
                if equal['chi2']<free['chi2']-1e-3:raise RuntimeError('Metric constrained fit beats free fit')
                dc=max(0,equal['chi2']-free['chi2']);dd=equal['df']-free['df']
                invariance.append(dict(sample=sample,battery=battery,spec=spec,free_cfi=free['cfi'],equal_cfi=equal['cfi'],delta_cfi=equal['cfi']-free['cfi'],delta_chi2=dc,delta_df=dd,approximate_p=float(stats.chi2.sf(dc,dd)),boundary=free['boundary'] or equal['boundary']))
    write_csv(OUT/'fits.csv',points);write_csv(OUT/'loadings.csv',loadings);write_csv(OUT/'domain_correlations.csv',correlations);write_csv(OUT/'remaining_residuals.csv',errors)
    (OUT/'invariance.json').write_text(json.dumps(invariance,indent=2)+'\n')
    keys=list(pointfits);draws=np.full((reps,len(keys)),np.nan);problems=[];rng=np.random.default_rng(meta['seed']);families={}
    for i,m in enumerate(members):families.setdefault(m['base_cluster'],[]).append(i)
    famkeys=sorted(families)
    for rep in range(reps):
        sampled=[i for fam in rng.choice(famkeys,len(famkeys),replace=True) for i in families[fam]]
        for j,key in enumerate(keys):
            sample,battery,spec,h=key;eligible,cols=cases[(sample,battery,h)];eligible=set(eligible);ix=[i for i in sampled if i in eligible]
            M=X[np.ix_(ix,cols)];tasks=BATTERIES[battery];blocks=[[tasks.index(t) for t in b] for b in SPECS[spec]]
            status='ok';detail=''
            try:
                f=residual_fit([np.corrcoef(M,rowvar=False)],[len(M)],blocks)
                if f['boundary']:status='boundary'
                else:draws[rep,j]=f['groups'][0]['g_variance_share']
            except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:status='failed';detail=str(e)
            if status!='ok':problems.append(dict(replicate=rep,key=':'.join(key),status=status,detail=detail))
        if (rep+1)%25==0:print('bootstrap',rep+1,'/',reps,flush=True)
    np.savez_compressed(OUT/'bootstrap.npz',g=draws,keys=np.array(keys))
    write_csv(OUT/'bootstrap_problems.csv',problems or [dict(replicate='',key='',status='none',detail='')])
    def interval(v):
        v=v[np.isfinite(v)];out=dict(admissible=len(v),replicates=reps,low=None,high=None)
        if len(v)>=.9*reps:out.update(zip(('low','high'),map(float,np.quantile(v,[.025,.975]))))
        return out
    intervals=[dict(zip(('sample','battery','spec','cohort'),k),point=pointfits[k]['groups'][0]['g_variance_share'],**interval(draws[:,j])) for j,k in enumerate(keys)]
    baseline_draws=np.load(SOURCE/'bootstrap.npz');basekeys=[tuple(k) for k in baseline_draws['keys']]
    if reps>len(baseline_draws['g']):raise ValueError('Cannot match baseline draws beyond saved replicate count')
    diffs=[]
    for sample in ('all','selected'):
        for spec in SPECS:
            for a,b in [(HALVES[0],HALVES[1]),(HALVES[1],HALVES[2]),(HALVES[0],HALVES[2])]:
                contrasts={};pointcontrasts={}
                for battery in BATTERIES:
                    ka=(sample,battery,spec,a);kb=(sample,battery,spec,b)
                    v=draws[:,keys.index(kb)]-draws[:,keys.index(ka)];pt=pointfits[kb]['groups'][0]['g_variance_share']-pointfits[ka]['groups'][0]['g_variance_share'];contrasts[battery]=v;pointcontrasts[battery]=pt
                    diffs.append(dict(sample=sample,battery=battery,spec=spec,contrast=b+' minus '+a,point=pt,**interval(v)))
                    bv=baseline_draws['g'][:reps,basekeys.index((sample,battery,b))]-baseline_draws['g'][:reps,basekeys.index((sample,battery,a))]
                    bp=float(next(r['g_variance_share'] for r in primary if r['sample']==sample and r['battery']==battery and r['cohort']==b))-float(next(r['g_variance_share'] for r in primary if r['sample']==sample and r['battery']==battery and r['cohort']==a))
                    diffs.append(dict(sample=sample,battery=battery,spec=spec+'-minus-independent',contrast=b+' minus '+a,point=pt-bp,**interval(v-bv)))
                diffs.append(dict(sample=sample,battery='nine-minus-eight',spec=spec,contrast=b+' minus '+a,point=pointcontrasts['nine']-pointcontrasts['eight'],**interval(contrasts['nine']-contrasts['eight'])))
    write_csv(OUT/'intervals.csv',intervals);write_csv(OUT/'differences.csv',diffs)
    metadata=dict(replicates=reps,seed=meta['seed'],specifications=SPECS,
        input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'matrix.csv',SOURCE/'configurations.csv',SOURCE/'metadata.json',SOURCE/'bootstrap.npz',SOURCE/'fits.csv']},
        code_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('aa_residual_cfa.py','factor_models.py')},
        exploratory=True,numpy=np.__version__,python=sys.version)
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    report(points,intervals,diffs,invariance,metadata)


def report(points,intervals,diffs,invariance,metadata):
    ci=lambda r:'withheld' if r['low'] is None else f"[{r['low']:.3f}, {r['high']:.3f}]"
    lines=['# AA CFA with domain residual correlations','',
        'Exploratory extension of the frozen release-cohort analysis. Coding residual block: SciCode and Terminal-Bench Hard. Expanded specification adds an academic/knowledge residual block: GPQA, HLE and AA-Omniscience. All pairwise residual covariances within each block are free; correlations need not be equal. CritPt remains a standalone indicator and is excluded in the eight-indicator battery. No edges were chosen from modification indices.','',
        '| Sample | Battery | Residual specification | Cohort | g variance | 95% cluster range | CFI | RMSEA | ΔBIC vs independent residuals |',
        '|---|---|---|---|---:|---|---:|---:|---:|']
    for r in points:
        v=next(v for v in intervals if all(v[k]==r[k] for k in ('sample','battery','spec','cohort')))
        lines.append(f"| {r['sample']} | {r['battery']} | {r['spec']} | {r['cohort']} | {r['g_variance_share']:.3f} | {ci(v)} ({v['admissible']}/{metadata['replicates']}) | {r['cfi']:.3f} | {r['rmsea']:.3f} | {r['delta_bic']:+.1f} |")
    lines+=['','## Direct cohort differences','','| Sample | Battery | Specification | Contrast | Difference | 95% cluster range |','|---|---|---|---|---:|---|']
    for r in diffs:lines.append(f"| {r['sample']} | {r['battery']} | {r['spec']} | {r['contrast']} | {r['point']:+.3f} | {ci(r)} |")
    lines+=['','## Equal general-factor loadings across cohorts','','Domain residual covariances and variances remain free by cohort in both models. Factor variances remain free; GPQA loading fixes scale in common pooled units. Covariance-only comparisons do not test scalar invariance. Approximate Gaussian p-values are not corrected for cluster dependence, bounded scores or exploratory model selection.','']
    for r in invariance:lines.append(f"- {r['sample']}/{r['battery']}/{r['spec']}: Δχ²={r['delta_chi2']:.2f}, Δdf={r['delta_df']}, approximate p={r['approximate_p']:.4g}, ΔCFI={r['delta_cfi']:+.3f}; boundary={r['boundary']}.")
    lines+=['','## Limits and reproduction','',
        'General-factor variance is the mean squared standardized g loading, excluding the fitted domain residual covariance. This is a different covariance allocation from independent-residual CFA, not an arithmetic correction to the old g share. Shared domain residuals are not identified as causal factors. Academic/knowledge is a provisional broad grouping, not a claim that these tasks are interchangeable.','',
        f"{metadata['replicates']} global base-cluster draws use the original seed and memberships, matched to the earlier independent-residual fits and the CritPt A/B cases. Configuration selection is unchanged. Intervals are nominal conditional sensitivity ranges and withheld below 90% admissibility; no item-level uncertainty or broader family ancestry is modeled. No new capability-level trajectory is estimated.",'',
        'Reproduce: `uv run aa_residual_cfa.py --resamples 1000`. Requires the saved original 1,000-draw run. Source and code hashes are pinned in metadata.json. Domain residual correlations and remaining observed-minus-implied correlations are exported separately.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resamples',type=int,default=1000);args=parser.parse_args()
    if not 1<=args.resamples<=1000:parser.error('resamples must be between 1 and 1000 to match saved baseline')
    run(args.resamples)
