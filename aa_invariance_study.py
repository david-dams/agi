"""Cluster-bootstrap loading invariance study for AA domain-residual CFA."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy import stats
from aa_cohort_factor import HALVES, BATTERIES
from aa_residual_cfa import residual_fit, SPECS
from downloaded_data_audit import write_csv

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'output/aa-cohort'
OUT=ROOT/'output/aa-invariance'
SEED=20261027
PARTIALS=(('lcr',),('critpt',),('critpt','lcr'))
STATE=None


def read(path):return list(csv.DictReader(path.open()))


def covariances(matrices):return [np.cov(m,rowvar=False) for m in matrices]


def null_transform(X,target):
    """Covariance-null recoloring; keep row/cluster identities, not original margins."""
    centered=X-X.mean(0)
    return np.linalg.solve(np.linalg.cholesky(np.cov(X,rowvar=False)),centered.T).T@np.linalg.cholesky(target).T


def paired_fit(matrices,blocks,starts):
    covs=covariances(matrices);ns=[len(m) for m in matrices]
    free=residual_fit(covs,ns,blocks,initial_fit=starts['free'])
    equal=residual_fit(covs,ns,blocks,True,initial_fit=starts['equal'])
    if equal['chi2']<free['chi2']-1e-4:
        free=residual_fit(covs,ns,blocks,initial_fit=equal)
    if equal['chi2']<free['chi2']-1e-3:raise RuntimeError('Constrained fit beats free fit')
    return free,equal


def setup():
    members=read(SOURCE/'configurations.csv');rows=read(SOURCE/'matrix.csv')
    if [m['id'] for m in members]!=[r['id'] for r in rows]:raise ValueError('Source memberships differ')
    cases=[];families={}
    for i,m in enumerate(members):families.setdefault(m['base_cluster'],[]).append(i)
    for sample in ('all','selected'):
        for battery,tasks in BATTERIES.items():
            ix=[i for i,m in enumerate(members) if sample=='all' or m['selected']=='True']
            X=np.array([[float(rows[i][t]) for t in tasks] for i in ix]);X/=X.std(0,ddof=1)
            cohorts=np.array([members[i]['cohort'] for i in ix]);matrices=[X[cohorts==h] for h in HALVES]
            cases.append(dict(sample=sample,battery=battery,tasks=tasks,indices=np.array(ix),X=X,cohorts=cohorts,
                blocks=[[tasks.index(t) for t in b] for b in SPECS['coding_academic']],
                matrices=matrices))
    return dict(cases=cases,families=families)


def point_analysis(state):
    fits=[];partials=[];single=[];loading=[];absfits=[];anchors=[]
    for case in state['cases']:
        covs=covariances(case['matrices']);ns=[len(m) for m in case['matrices']];blocks=case['blocks'];tags={k:case[k] for k in ('sample','battery')}
        free=residual_fit(covs,ns,blocks);equal=residual_fit(covs,ns,blocks,True,initial_fit=free)
        case['starts']=dict(free=free,equal=equal)
        fits.append(dict(**tags,free=free,equal=equal,delta_cfi=equal['cfi']-free['cfi'],delta_chi2=equal['chi2']-free['chi2']))
        case['null_X']=case['X'].copy()
        for g,h in enumerate(HALVES):
            target=np.array(equal['groups'][g]['sigma']);mask=case['cohorts']==h
            case['null_X'][mask]=null_transform(case['X'][mask],target)
            if not np.allclose(np.cov(case['null_X'][mask],rowvar=False),target,atol=1e-9):raise RuntimeError('Null covariance transform failed')
            group=free['groups'][g]
            # RMSEA per cohort uses that cohort's chi-square contribution, not total df.
            S=covs[g];sigma=np.array(group['sigma']);chi=(ns[g]-1)*(np.linalg.slogdet(sigma)[1]+np.trace(S@np.linalg.inv(sigma))-np.linalg.slogdet(S)[1]-len(S))
            df=free['df']//3
            absfits.append(dict(**tags,cohort=h,n=ns[g],chi2=chi,df=df,rmsea=float(np.sqrt(max((chi-df)/(df*(ns[g]-1)),0))),residual_rms=group['residual_rms']))
            for j,t in enumerate(case['tasks']):loading.append(dict(**tags,cohort=h,task=t,raw=group['raw_loadings'][j],standardized=group['loadings'][j]))
        for names in PARTIALS:
            if not set(names)<=set(case['tasks']):continue
            f=residual_fit(covs,ns,blocks,True,[case['tasks'].index(t) for t in names],initial_fit=free)
            if f['chi2']<free['chi2']-1e-3 or f['chi2']>equal['chi2']+1e-3:raise RuntimeError('Partial model nesting failure')
            partials.append(dict(**tags,freed='+'.join(names),selection='floor-motivated before new fits',chi2=f['chi2'],df=f['df'],cfi=f['cfi'],rmsea=f['rmsea'],
                delta_cfi_vs_free=f['cfi']-free['cfi'],delta_chi2_vs_equal=equal['chi2']-f['chi2'],boundary=f['boundary'],
                relative_screen=f['cfi']-free['cfi']>=-.01,absolute_screen=f['cfi']>=.95 and f['rmsea']<=.08))
        for j,t in enumerate(case['tasks']):
            marker=case['tasks'].index('ifbench') if t=='gpqa' else 0
            f=residual_fit(covs,ns,blocks,True,[j],marker,initial_fit=free)
            if f['chi2']<free['chi2']-1e-3 or f['chi2']>equal['chi2']+1e-3:raise RuntimeError('Single release nesting failure')
            single.append(dict(**tags,freed=t,marker=case['tasks'][marker],gain_chi2=equal['chi2']-f['chi2'],gain_cfi=f['cfi']-equal['cfi'],
                delta_cfi_vs_free=f['cfi']-free['cfi'],boundary=f['boundary'],interpretation='exhaustive exploratory diagnostic; not used to select partial specification'))
        # Alternate anchor exposes the arbitrary scale underlying marker-relative loading diagnostics.
        alt=residual_fit(covs,ns,blocks,marker=case['tasks'].index('ifbench'),initial_fit=free)
        for g,h in enumerate(HALVES):
            for j,t in enumerate(case['tasks']):anchors.append(dict(**tags,cohort=h,task=t,marker='ifbench',raw=alt['groups'][g]['raw_loadings'][j],standardized=alt['groups'][g]['loadings'][j]))
        print('points',tags,'dCFI',round(equal['cfi']-free['cfi'],4),flush=True)
    write_csv(OUT/'partial_invariance.csv',partials);write_csv(OUT/'single_release_diagnostics.csv',single);write_csv(OUT/'point_loadings.csv',loading);write_csv(OUT/'absolute_fit_by_cohort.csv',absfits);write_csv(OUT/'alternate_anchor_loadings.csv',anchors)
    (OUT/'point_fits.json').write_text(json.dumps(fits,indent=2)+'\n')
    return fits


def init_worker(state):
    global STATE
    STATE=state


def draw(job):
    mode,rep=job;rng=np.random.default_rng(np.random.SeedSequence(SEED,spawn_key=(mode,rep)))
    families=STATE['families'];keys=sorted(families)
    sampled=[i for k in rng.choice(keys,len(keys),replace=True) for i in families[k]]
    results=[]
    for case in STATE['cases']:
        tags={k:case[k] for k in ('sample','battery')};pos={int(ix):j for j,ix in enumerate(case['indices'])}
        ix=[pos[i] for i in sampled if i in pos];cohort=case['cohorts'][ix];X=(case['X'] if mode==0 else case['null_X'])[ix]
        matrices=[X[cohort==h] for h in HALVES]
        result=dict(**tags,status='ok',free_status='failed',detail='',delta_cfi=None,delta_chi2=None,raw=None,standardized=None)
        try:
            free,equal=paired_fit(matrices,case['blocks'],case['starts'])
            result.update(delta_cfi=equal['cfi']-free['cfi'],delta_chi2=equal['chi2']-free['chi2'],
                free_status='boundary' if free['boundary'] else 'ok',
                status='boundary' if free['boundary'] or equal['boundary'] else 'ok',
                raw=[g['raw_loadings'] for g in free['groups']],standardized=[g['loadings'] for g in free['groups']],
                free_gradient=free['gradient_norm'],equal_gradient=equal['gradient_norm'])
        except (ValueError,RuntimeError,np.linalg.LinAlgError) as e:
            result.update(status='failed',detail=str(e))
        results.append(result)
    return mode,rep,results


def summarize(values,statuses,point):
    finite=np.isfinite(values);ok=finite&(statuses=='ok');n=len(values)
    row=dict(point=float(point),draws=n,finite=int(finite.sum()),admissible=int(ok.sum()),low=None,high=None,median=None,
             finite_low=None,finite_high=None,finite_median=None)
    if finite.any():row.update(zip(('finite_low','finite_median','finite_high'),map(float,np.quantile(values[finite],[.025,.5,.975]))))
    if ok.sum()>=.9*n:row.update(zip(('low','median','high'),map(float,np.quantile(values[ok],[.025,.5,.975]))))
    return row


def exports(state,pointfits,results,bootstrap,null_reps):
    cases=state['cases'];C=len(cases);maxp=9
    delta=np.full((bootstrap,C),np.nan);lr=delta.copy();status=np.full((bootstrap,C),'missing',dtype='U12');free_status=status.copy()
    raw=np.full((bootstrap,C,3,maxp),np.nan);standardized=raw.copy()
    ndelta=np.full((null_reps,C),np.nan);nlr=ndelta.copy();nstatus=np.full((null_reps,C),'missing',dtype='U12')
    problems=[];gradients=[]
    for mode,rep,rs in results:
        for c,r in enumerate(rs):
            if r['status']!='ok':problems.append(dict(mode='bootstrap' if mode==0 else 'null',replicate=rep,case=c,sample=r['sample'],battery=r['battery'],status=r['status'],free_status=r['free_status'],detail=r['detail']))
            if mode==0:
                status[rep,c]=r['status'];free_status[rep,c]=r['free_status']
                if r['delta_cfi'] is not None:
                    delta[rep,c]=r['delta_cfi'];lr[rep,c]=r['delta_chi2'];p=len(cases[c]['tasks']);raw[rep,c,:,:p]=r['raw'];standardized[rep,c,:,:p]=r['standardized']
            else:
                nstatus[rep,c]=r['status']
                if r['delta_cfi'] is not None:ndelta[rep,c]=r['delta_cfi'];nlr[rep,c]=r['delta_chi2']
            if r['delta_cfi'] is not None:gradients.append(dict(mode=mode,replicate=rep,case=c,free_gradient=r['free_gradient'],equal_gradient=r['equal_gradient']))
    np.savez_compressed(OUT/'distributions.npz',delta_cfi=delta,delta_chi2=lr,status=status,free_status=free_status,raw_loadings=raw,standardized_loadings=standardized,
        null_delta_cfi=ndelta,null_delta_chi2=nlr,null_status=nstatus,cases=np.array([[c['sample'],c['battery']] for c in cases]))
    write_csv(OUT/'fit_problems.csv',problems or [dict(mode='',replicate='',case='',sample='',battery='',status='none',free_status='',detail='')]);write_csv(OUT/'gradient_diagnostics.csv',gradients)
    summaries=[];nulltests=[];loading_intervals=[];differences=[];matched=[]
    for c,case in enumerate(cases):
        tags={k:case[k] for k in ('sample','battery')};pt=pointfits[c]
        for name,v,point in [('delta_cfi',delta[:,c],pt['delta_cfi']),('delta_chi2',lr[:,c],pt['delta_chi2'])]:
            summaries.append(dict(**tags,statistic=name,**summarize(v,status[:,c],point)))
        for name,v,observed in [('deterioration_cfi',-ndelta[:,c],-pt['delta_cfi']),('delta_chi2',nlr[:,c],pt['delta_chi2'])]:
            finite=np.isfinite(v);ok=finite&(nstatus[:,c]=='ok');k=int(sum(v[ok]>=observed));valid=int(ok.sum());invalid=null_reps-valid
            nfinite=int(finite.sum());kf=int(sum(v[finite]>=observed))
            nulltests.append(dict(**tags,statistic=name,observed=observed,draws=null_reps,admissible=valid,
                p_admissible=(1+k)/(1+valid) if valid>=.9*null_reps else None,
                exceedances_admissible=k,p_failure_lower=(1+k)/(1+null_reps),p_failure_upper=(1+k+invalid)/(1+null_reps),
                finite=nfinite,p_including_boundaries=(1+kf)/(1+nfinite) if nfinite else None,
                null_finite_q95=float(np.quantile(v[finite],.95)) if nfinite else None,
                mc_upper_exceedance_rate=float(stats.beta.ppf(.975,k+1,valid-k)) if valid>k else 1.))
        p=len(case['tasks']);mask=free_status[:,c];rawpoint=np.array([g['raw_loadings'] for g in pt['free']['groups']]);stdpoint=np.array([g['loadings'] for g in pt['free']['groups']])
        for scale,array,point in [('raw',raw[:,:,:, :p][:,c],rawpoint),('standardized',standardized[:,:,:,:p][:,c],stdpoint)]:
            for g,h in enumerate(HALVES):
                for j,t in enumerate(case['tasks']):loading_intervals.append(dict(**tags,scale=scale,cohort=h,task=t,**summarize(array[:,g,j],mask,point[g,j])))
            contrasts=[(0,1),(1,2),(0,2)];D=np.stack([array[:,b,:]-array[:,a,:] for a,b in contrasts],axis=1);Dpoint=np.stack([point[b]-point[a] for a,b in contrasts]);ok=(mask=='ok')&np.isfinite(D).all(axis=(1,2))
            # Simultaneous bands across all benchmark/contrast diagnostics within a case and scale.
            s=D[ok].std(0,ddof=1) if ok.sum()>1 else np.zeros_like(Dpoint);usable=s>1e-8
            critical=None
            if ok.sum()>=.9*bootstrap and usable.any():critical=float(np.quantile(np.max(np.abs(((D[ok]-Dpoint)/np.where(usable,s,1))[:,usable]),axis=1),.95))
            for k,(a,b) in enumerate(contrasts):
                for j,t in enumerate(case['tasks']):
                    r=dict(**tags,scale=scale,contrast=HALVES[b]+' minus '+HALVES[a],task=t,**summarize(D[:,k,j],mask,Dpoint[k,j]),
                        simultaneous_low=None,simultaneous_high=None)
                    if critical is not None and usable[k,j]:r.update(simultaneous_low=float(Dpoint[k,j]-critical*s[k,j]),simultaneous_high=float(Dpoint[k,j]+critical*s[k,j]))
                    differences.append(r)
    for sample in ('all','selected'):
        a=next(i for i,c in enumerate(cases) if c['sample']==sample and c['battery']=='nine');b=a+1
        joint=np.where((status[:,a]=='ok')&(status[:,b]=='ok'),'ok','inadmissible')
        matched.append(dict(sample=sample,contrast='nine minus eight delta_cfi',**summarize(delta[:,a]-delta[:,b],joint,pointfits[a]['delta_cfi']-pointfits[b]['delta_cfi'])))
    write_csv(OUT/'delta_summaries.csv',summaries);write_csv(OUT/'null_tests.csv',nulltests);write_csv(OUT/'loading_intervals.csv',loading_intervals);write_csv(OUT/'loading_differences.csv',differences);write_csv(OUT/'matched_battery_differences.csv',matched)
    return summaries,nulltests


def run(args):
    OUT.mkdir(parents=True,exist_ok=True)
    specification=dict(bootstrap_draws=args.bootstrap,null_draws=args.null,seed=SEED,
        residual_blocks=SPECS['coding_academic'],partial_candidates=PARTIALS,
        candidate_rationale='previously documented CritPt and AA-LCR floor effects, fixed before these fits; not selected from new loading results',
        diagnostic_sweep='all single benchmark releases; no ranking-based selection; GPQA release uses IFBench marker',
        resampling='one global matched named-base cluster draw across four cases',
        null='covariance-null recoloring to fitted equal-loading covariance, then whole-cluster empirical resampling',
        reporting='admissible intervals only if >=90%; finite-boundary sensitivity separately; null failure bounds',
        relative_screen='deltaCFI >= -0.01, descriptive only',absolute_screen='CFI >= .95 and multi-group RMSEA <= .08, descriptive only',
        phase='locked before point_analysis')
    (OUT/'specification.json').write_text(json.dumps(specification,indent=2)+'\n')
    state=setup();points=point_analysis(state)
    (OUT/'point_state.json').write_text(json.dumps([dict(sample=c['sample'],battery=c['battery'],starts=c['starts']) for c in state['cases']],indent=2)+'\n')
    jobs=[(0,r) for r in range(args.bootstrap)]+[(1,r) for r in range(args.null)]
    results=[];start=time.monotonic()
    # Persist each completed draw so interruption never loses the expensive fits.
    with (OUT/'draws.jsonl').open('w') as log,ProcessPoolExecutor(max_workers=args.workers,initializer=init_worker,initargs=(state,)) as pool:
        for result in pool.map(draw,jobs,chunksize=2):
            results.append(result);log.write(json.dumps(result)+'\n')
            if len(results)%25==0:
                log.flush();print('draws',len(results),'/',len(jobs),'elapsed',round(time.monotonic()-start),'s',flush=True)
    summaries,nulltests=exports(state,points,results,args.bootstrap,args.null)
    meta=dict(specification=specification,elapsed_seconds=time.monotonic()-start,workers=args.workers,python=sys.version,numpy=np.__version__,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE/'matrix.csv',SOURCE/'configurations.csv')},
        code_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('aa_invariance_study.py','aa_residual_cfa.py','factor_models.py')})
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('complete',OUT,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bootstrap',type=int,default=2000);parser.add_argument('--null',type=int,default=500);parser.add_argument('--workers',type=int,default=4);args=parser.parse_args()
    if min(args.bootstrap,args.null,args.workers)<1:parser.error('counts must be positive')
    run(args)
