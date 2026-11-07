"""PC1 direction stability in fixed pooled benchmark units; no CFA assumptions."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from aa_cohort_factor import HALVES, BATTERIES
from downloaded_data_audit import write_csv

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'output/aa-cohort'
OUT=ROOT/'output/aa-pca'
SEED=20261027
PAIRS=((0,1),(1,2),(0,2))


def pc1(X,reference=None):
    X=np.asarray(X,dtype=float)
    if X.ndim!=2 or len(X)<3 or not np.isfinite(X).all():raise ValueError('PCA needs at least three finite rows')
    # Cohort centering removes mean level differences; benchmark scales stay fixed.
    S=np.cov(X,rowvar=False)
    values,vectors=np.linalg.eigh(S);order=np.argsort(values)[::-1];values=values[order];w=vectors[:,order[0]]
    trace=float(np.trace(S));gap=float(values[0]-values[1])
    if trace<=1e-12 or values[0]<=1e-12:raise ValueError('No cohort variation')
    if values[-1]<-1e-9*max(1.,values[0]):raise ValueError('Numerically non-PSD covariance')
    if gap<=1e-8*values[0]:raise ValueError('PC1 direction not uniquely separated from PC2')
    if reference is not None:
        if w@reference<0:w=-w
    elif w.sum()<0 or (abs(w.sum())<1e-12 and w[np.argmax(abs(w))]<0):w=-w
    sd=np.sqrt(np.diag(S));correlations=np.divide(w*np.sqrt(values[0]),sd,out=np.full_like(w,np.nan),where=sd>1e-12)
    return dict(weights=w,eigenvalues=values,explained_variance=float(values[0]/trace),
        relative_gap=gap/float(values[0]),rank=int(np.linalg.matrix_rank(S)),
        constant_tasks=int(sum(sd<1e-12)),covariance_loadings=w*np.sqrt(values[0]),score_correlations=correlations)


def similarity(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('Directions must be finite and matching')
    norm=np.linalg.norm(a)*np.linalg.norm(b)
    if norm<=1e-12:raise ValueError('Zero direction')
    signed=float(np.clip(a@b/norm,-1,1));cos=abs(signed)
    # Tucker congruence equals uncentered cosine; the PC axis sign is arbitrary.
    return dict(tucker_congruence=cos,cosine_similarity=cos,angle_degrees=float(np.degrees(np.arccos(cos))),signed_cosine=signed)


def interval(v,total,point):
    v=np.asarray(v,dtype=float);v=v[np.isfinite(v)]
    r=dict(point=float(point),admissible=len(v),attempted=total,low=None,high=None,bootstrap_mean=None,bias=None)
    if len(v):r.update(bootstrap_mean=float(v.mean()),bias=float(v.mean()-point))
    if len(v)>=.9*total:r.update(zip(('low','high'),map(float,np.quantile(v,[.025,.975]))))
    return r


def run(reps):
    OUT.mkdir(parents=True,exist_ok=True)
    read=lambda name:list(csv.DictReader((SOURCE/name).open()))
    rows=read('matrix.csv');members=read('configurations.csv');tasks9=BATTERIES['nine']
    if [r['id'] for r in rows]!=[m['id'] for m in members]:raise ValueError('Matrix/membership IDs differ')
    X=np.array([[float(r[t]) for t in tasks9] for r in rows]);mu=X.mean(0);sd=X.std(0,ddof=1)
    if not np.isfinite(X).all() or np.any(sd<=1e-12):raise ValueError('Invalid pooled scores')
    Z=(X-mu)/sd
    # One all-configuration metric is frozen for both samples and both batteries.
    write_csv(OUT/'standardization.csv',[dict(task=t,reference_n=len(X),mean=float(mu[j]),sd=float(sd[j])) for j,t in enumerate(tasks9)])
    specification=dict(draws=reps,seed=SEED,cohorts=HALVES,batteries=BATTERIES,
        scaling='one pooled mean and sample SD across all 387 complete configurations, frozen for all cases and bootstrap draws',
        centering='within each cohort, including within bootstrap draws; covariance PCA, not uncentered second moments',
        direction='unit PC1 eigenvector in common pooled units; covariance loadings differ only by scalar sqrt(eigenvalue)',
        sign='align bootstrap direction to its cohort estimate; compare sign-invariant axes',
        bootstrap='matched global named-base cluster draws; SeedSequence(seed, spawn_key=(0, replicate)) matches invariance study',
        admissibility='>=3 rows, finite nonzero total variance, PC1-PC2 gap > 1e-8 times PC1; no full-rank requirement; intervals withheld below 90%',
        interpretation='descriptive directional similarity, not a latent-construct identity, equivalence or CFA invariance test')
    (OUT/'specification.json').write_text(json.dumps(specification,indent=2)+'\n')
    families={}
    for i,m in enumerate(members):families.setdefault(m['base_cluster'],[]).append(i)
    cohorts=np.array([m['cohort'] for m in members]);cases=[];points=[];weights=[];spectra=[];comparisons=[]
    for sample in ('all','selected'):
        for battery,tasks in BATTERIES.items():
            cols=[tasks9.index(t) for t in tasks];eligible={i for i,m in enumerate(members) if sample=='all' or m['selected']=='True'};fits=[]
            for h in HALVES:
                ix=[i for i in sorted(eligible) if cohorts[i]==h];f=pc1(Z[np.ix_(ix,cols)]);fits.append(f)
                points.append(dict(sample=sample,battery=battery,cohort=h,n=len(ix),base_clusters=len({members[i]['base_cluster'] for i in ix}),
                    explained_variance=f['explained_variance'],relative_gap=f['relative_gap'],rank=f['rank'],constant_tasks=f['constant_tasks']))
                for j,t in enumerate(tasks):weights.append(dict(sample=sample,battery=battery,cohort=h,task=t,weight=float(f['weights'][j]),covariance_loading=float(f['covariance_loadings'][j]),score_correlation=float(f['score_correlations'][j])))
                for j,v in enumerate(f['eigenvalues']):spectra.append(dict(sample=sample,battery=battery,cohort=h,component=j+1,eigenvalue=float(v)))
            for a,b in PAIRS:comparisons.append(dict(sample=sample,battery=battery,cohort_a=HALVES[a],cohort_b=HALVES[b],**similarity(fits[a]['weights'],fits[b]['weights'])))
            cases.append(dict(sample=sample,battery=battery,tasks=tasks,cols=cols,eligible=eligible,fits=fits))
    write_csv(OUT/'cohorts.csv',points);write_csv(OUT/'weights.csv',weights);write_csv(OUT/'spectra.csv',spectra);write_csv(OUT/'point_similarities.csv',comparisons)
    C=len(cases);directions=np.full((reps,C,3,9),np.nan);evr=np.full((reps,C,3),np.nan);gaps=evr.copy();cones=evr.copy()
    sim=np.full((reps,C,3),np.nan);angles=sim.copy();status=np.full((reps,C,3),'missing',dtype='U16');problems=[]
    keys=sorted(families)
    for rep in range(reps):
        rng=np.random.default_rng(np.random.SeedSequence(SEED,spawn_key=(0,rep)))
        ix=[i for k in rng.choice(keys,len(keys),replace=True) for i in families[k]]
        for c,case in enumerate(cases):
            for g,h in enumerate(HALVES):
                subset=[i for i in ix if i in case['eligible'] and cohorts[i]==h]
                try:
                    f=pc1(Z[np.ix_(subset,case['cols'])],case['fits'][g]['weights'])
                    directions[rep,c,g,:len(case['tasks'])]=f['weights'];evr[rep,c,g]=f['explained_variance'];gaps[rep,c,g]=f['relative_gap']
                    cones[rep,c,g]=similarity(f['weights'],case['fits'][g]['weights'])['angle_degrees'];status[rep,c,g]='ok'
                except (ValueError,np.linalg.LinAlgError) as e:
                    status[rep,c,g]='failed';problems.append(dict(replicate=rep,sample=case['sample'],battery=case['battery'],cohort=h,n=len(subset),detail=str(e)))
            for k,(a,b) in enumerate(PAIRS):
                if status[rep,c,a]=='ok' and status[rep,c,b]=='ok':
                    s=similarity(directions[rep,c,a,:len(case['tasks'])],directions[rep,c,b,:len(case['tasks'])]);sim[rep,c,k]=s['cosine_similarity'];angles[rep,c,k]=s['angle_degrees']
        if (rep+1)%500==0:print('bootstrap',rep+1,'/',reps,flush=True)
    np.savez_compressed(OUT/'bootstrap.npz',directions=directions,explained_variance=evr,relative_gap=gaps,angle_to_cohort_estimate=cones,
        congruence=sim,cosine=sim,angles=angles,status=status,cases=np.array([[c['sample'],c['battery']] for c in cases]),pairs=np.array(PAIRS))
    write_csv(OUT/'bootstrap_problems.csv',problems or [dict(replicate='',sample='',battery='',cohort='',n='',detail='none')])
    summaries=[];variance=[];loading_intervals=[];variance_diffs=[]
    for c,case in enumerate(cases):
        tags={k:case[k] for k in ('sample','battery')}
        for k,(a,b) in enumerate(PAIRS):
            s=similarity(case['fits'][a]['weights'],case['fits'][b]['weights'])
            for name,v in [('tucker_congruence',sim[:,c,k]),('cosine_similarity',sim[:,c,k]),('angle_degrees',angles[:,c,k])]:
                summaries.append(dict(**tags,cohort_a=HALVES[a],cohort_b=HALVES[b],metric=name,**interval(v,reps,s[name])))
            variance_diffs.append(dict(**tags,contrast=HALVES[b]+' minus '+HALVES[a],**interval(evr[:,c,b]-evr[:,c,a],reps,case['fits'][b]['explained_variance']-case['fits'][a]['explained_variance'])))
        for g,h in enumerate(HALVES):
            ok=np.isfinite(cones[:,c,g]);f=case['fits'][g]
            variance.append(dict(**tags,cohort=h,**interval(evr[:,c,g],reps,f['explained_variance']),
                point_relative_gap=f['relative_gap'],gap_low=float(np.quantile(gaps[ok,c,g],.025)) if ok.any() else None,
                gap_high=float(np.quantile(gaps[ok,c,g],.975)) if ok.any() else None,
                near_tie_draws=int(sum(gaps[ok,c,g]<.1)),angle_to_estimate_q95=float(np.quantile(cones[ok,c,g],.95)) if ok.sum()>=.9*reps else None))
            for j,t in enumerate(case['tasks']):loading_intervals.append(dict(**tags,cohort=h,task=t,**interval(directions[:,c,g,j],reps,f['weights'][j])))
    write_csv(OUT/'similarities.csv',summaries);write_csv(OUT/'explained_variance.csv',variance);write_csv(OUT/'variance_differences.csv',variance_diffs);write_csv(OUT/'weight_intervals.csv',loading_intervals)
    metadata=dict(specification=specification,python=sys.version,numpy=np.__version__,configurations=len(rows),named_bases=len(families),
        input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'matrix.csv',SOURCE/'configurations.csv']},
        code_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['aa_cohort_pca.py','aa_cohort_factor.py','downloaded_data_audit.py']},
        cohort_fits_attempted=reps*C*3,cohort_fits_admissible=int(sum((status=='ok').ravel())),problems=len(problems))
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    report(summaries,variance,variance_diffs,metadata)
    print(OUT,flush=True)


def report(similarities,variance,differences,metadata):
    span=lambda r:'withheld' if r['low'] is None else f"[{r['low']:.4f}, {r['high']:.4f}]"
    lines=['# Dominant performance direction across release cohorts','',
        'Separate covariance PCA uses a single benchmark metric: pooled means and sample standard deviations of all 387 complete configurations, frozen across all cohorts, both batteries, the selected-base sensitivity and all bootstrap draws. Each cohort is centered before PCA. Thus mean performance changes do not drive these axes; variation and covariance can. This analysis imposes no CFA residual structure.','',
        '## Directional comparisons','',
        '| Sample | Battery | Cohort pair | Tucker = cosine | Nominal 95% bootstrap range | Angle (degrees) | Nominal 95% range | Admissible / attempted |',
        '|---|---|---|---:|---|---:|---|---:|']
    for r in similarities:
        if r['metric']!='cosine_similarity':continue
        a=next(a for a in similarities if a['sample']==r['sample'] and a['battery']==r['battery'] and a['cohort_a']==r['cohort_a'] and a['cohort_b']==r['cohort_b'] and a['metric']=='angle_degrees')
        lines.append(f"| {r['sample']} | {r['battery']} | {r['cohort_a']} / {r['cohort_b']} | {r['point']:.4f} | {span(r)} | {a['point']:.2f} | {span(a)} | {r['admissible']}/{r['attempted']} |")
    lines+=['','Tucker congruence is the uncentered cosine of the coefficient/loading vectors. It is therefore numerically identical to cosine here, and angle is its arccosine; these are not three independent pieces of evidence. PCA axes have arbitrary signs, so comparisons align signs and use the acute axis angle. Covariance loadings (coefficient times sqrt(eigenvalue)) give the same direction. Cohort score-variable correlations are exported separately and are not substituted for common-metric directions.','',
        '## Explained variance and spectral separation','',
        '| Sample | Battery | Cohort | PC1 variance fraction | Nominal 95% bootstrap range | Relative PC1–PC2 gap | 95th percentile bootstrap angle to own estimate |',
        '|---|---|---|---:|---|---:|---:|']
    for r in variance:lines.append(f"| {r['sample']} | {r['battery']} | {r['cohort']} | {r['point']:.4f} | {span(r)} | {r['point_relative_gap']:.4f} | {r['angle_to_estimate_q95']:.2f}° |")
    lines+=['','Relative gap is (lambda1 − lambda2)/lambda1. The eigenvalues and covariance ranks are exported. Singular covariance is allowed when PC1 is uniquely separated; PCA does not need CFA-style positive-definite covariance or uniqueness estimates. Numerically tied top eigenvalues are inadmissible. Low but nonzero gaps are tracked as instability diagnostics, not silently discarded.','',
        '## Changes in explained variance','',
        '| Sample | Battery | Contrast | Difference | Nominal 95% bootstrap range |','|---|---|---|---:|---|']
    for r in differences:lines.append(f"| {r['sample']} | {r['battery']} | {r['contrast']} | {r['point']:+.4f} | {span(r)} |")
    lines+=['','## Uncertainty and interpretation','',
        f"{metadata['specification']['draws']} matched global named-base cluster draws preserve whole observed configuration blocks and cross-case matching. The original one-configuration selection rule is unchanged. There were {metadata['cohort_fits_admissible']}/{metadata['cohort_fits_attempted']} admissible cohort PCAs; each pair requires both cohort estimates. Full draw arrays, statuses, per-cohort eigenvalue gaps and angular perturbations are in bootstrap.npz. No covariance regularization is used.",'',
        'The scale is conditional on this frozen pooled dataset; scale-estimation uncertainty is intentionally not resampled because the target is direction in a fixed coordinate system. Nominal percentile ranges describe resampling variability and are not calibrated equality/equivalence tests. Even identical population axes yield positive estimated angles under sampling noise; ranges excluding zero do not establish directional change. Similarity can be biased downward and angles upward; bootstrap means and point-relative bias are exported.','',
        'A close direction means approximately the same weighted performance combination dominates observed covariance in these benchmark units. It does not imply unchanged remaining covariance, equal explained variance, equal benchmark variances, an identical latent construct, or CFA measurement invariance. PCA maximizes variance and is sensitive to the benchmark battery, pooled scaling, floors and sampled model composition. The named-base mapping handles explicit setting variants, not all shared ancestry. Item-level uncertainty and protocol consistency remain unmeasured.','',
        'The comparison is retrospective across release cohorts in a July 2026 snapshot, not historical evaluation snapshots. Standardized PC1 scores or means are not used to claim capability growth.','',
        '## Reproduction','',
        '`OPENBLAS_NUM_THREADS=1 uv run aa_cohort_pca.py --resamples 2000`','',
        '`uv run aa_pca_plot.py`','',
        'Inputs and code are hash-pinned in metadata.json. standardization.csv defines the common metric; weights.csv contains unit eigenvectors, covariance loadings and score correlations. similarities.csv reports both congruence and cosine, angles, uncertainty and bias; explained_variance.csv, spectra.csv, variance_differences.csv and weight_intervals.csv give supporting diagnostics.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resamples',type=int,default=2000);args=parser.parse_args()
    if args.resamples<1:parser.error('resamples must be positive')
    run(args.resamples)
