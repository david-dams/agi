"""Shared-PC1 covariance nulls with cluster-aware empirical simulation."""
import argparse
from collections import defaultdict,Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy import stats
from aa_cohort_pca import pc1,similarity,HALVES,BATTERIES,PAIRS
from downloaded_data_audit import write_csv

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'output/aa-cohort'
PCA=ROOT/'output/aa-pca'
OUT=ROOT/'output/aa-pca-null'
SEED=20261028
METHODS=('projected','rotated_spectrum')
SCHEMES=('fixed_sizes','global_clusters')


def consensus_axis(directions,weights):
    directions=np.asarray(directions,dtype=float);weights=np.asarray(weights,dtype=float)
    if directions.ndim!=2 or len(weights)!=len(directions) or np.any(weights<=0):raise ValueError('Invalid consensus inputs')
    A=sum(w*np.outer(v,v)/(v@v) for w,v in zip(weights,directions))
    values,vectors=np.linalg.eigh(A)
    if values[-1]-values[-2]<1e-10*values[-1]:raise ValueError('Consensus axis is not unique')
    u=vectors[:,-1]
    return -u if u.sum()<0 else u


def minimum_rotation(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);a=a/np.linalg.norm(a);b=b/np.linalg.norm(b)
    if a@b<0:a=-a
    c=float(np.clip(a@b,-1,1));v=b-c*a;s=float(np.linalg.norm(v))
    if s<1e-12:return np.eye(len(a))
    t=v/s
    return np.eye(len(a))+(c-1)*(np.outer(a,a)+np.outer(t,t))+s*(np.outer(t,a)-np.outer(a,t))


def construct_null(S,u,method):
    S=np.asarray(S,dtype=float);u=np.asarray(u,dtype=float);u=u/np.linalg.norm(u);p=len(u)
    if S.shape!=(p,p) or not np.isfinite(S).all() or not np.allclose(S,S.T) or np.linalg.eigvalsh(S)[0]<=0:raise ValueError('Null construction needs SPD covariance')
    if method=='projected':
        P=np.eye(p)-np.outer(u,u);target=float(u@S@u)*np.outer(u,u)+P@S@P
    elif method=='rotated_spectrum':
        old=np.linalg.eigh(S)[1][:,-1];R=minimum_rotation(old,u);target=R@S@R.T
    else:raise ValueError('Unknown covariance null')
    target=(target+target.T)/2
    values,vectors=np.linalg.eigh(target);alignment=abs(float(vectors[:,-1]@u))
    if values[0]<=0 or alignment<1-1e-8 or (values[-1]-values[-2])/values[-1]<=1e-8:
        raise ValueError('Constructed common axis is not a unique leading eigenvector')
    if not np.isclose(np.trace(target),np.trace(S),rtol=1e-10):raise RuntimeError('Null changed covariance trace')
    return target


def transform_rows(X,target,method,u):
    centered=X-X.mean(0);S=np.cov(X,rowvar=False)
    if method=='rotated_spectrum':
        old=np.linalg.eigh(S)[1][:,-1];Y=centered@minimum_rotation(old,u).T
    else:
        Y=np.linalg.solve(np.linalg.cholesky(S),centered.T).T@np.linalg.cholesky(target).T
    if not np.allclose(np.cov(Y,rowvar=False),target,atol=1e-9,rtol=1e-9):raise RuntimeError('Empirical null covariance does not match target')
    return Y


def cluster_strata(members):
    families=defaultdict(list)
    for i,m in enumerate(members):families[m['base_cluster']].append(i)
    strata=defaultdict(list)
    for key,ix in sorted(families.items()):
        # Preserve all and selected sample row counts even if bases span cohorts.
        signature=tuple(sum(members[i]['cohort']==h for i in ix) for h in HALVES)+tuple(sum(members[i]['cohort']==h and members[i]['selected']=='True' for i in ix) for h in HALVES)
        strata[signature].append(key)
    return dict(families),dict(strata)


def resample_indices(families,strata,rng,scheme):
    if scheme=='fixed_sizes':
        names=[k for signature in sorted(strata) for k in rng.choice(strata[signature],len(strata[signature]),replace=True)]
    elif scheme=='global_clusters':names=rng.choice(sorted(families),len(families),replace=True)
    else:raise ValueError('Unknown resampling scheme')
    return [i for k in names for i in families[k]]


def tail_result(values,observed,total):
    v=np.asarray(values);v=v[np.isfinite(v)];valid=len(v);exceed=int(sum(v>=observed));invalid=total-valid
    # Exact binomial interval describes Monte Carlo exceedance-rate uncertainty.
    lo=0. if exceed==0 else float(stats.beta.ppf(.025,exceed,valid-exceed+1))
    hi=1. if exceed==valid else float(stats.beta.ppf(.975,exceed+1,valid-exceed))
    return dict(observed=float(observed),attempted=total,admissible=valid,exceedances=exceed,
        p_calibrated=(exceed+1)/(valid+1) if valid>=.9*total else None,
        p_invalid_lower=(exceed+1)/(total+1),p_invalid_upper=(exceed+invalid+1)/(total+1),
        mc_exceedance_low=lo,mc_exceedance_high=hi,
        null_q50=float(np.quantile(v,.5)) if valid else None,null_q95=float(np.quantile(v,.95)) if valid else None,
        null_q99=float(np.quantile(v,.99)) if valid else None)


def run(reps):
    OUT.mkdir(parents=True,exist_ok=True)
    read=lambda name:list(csv.DictReader((SOURCE/name).open()))
    rows=read('matrix.csv');members=read('configurations.csv')
    if [r['id'] for r in rows]!=[m['id'] for m in members]:raise ValueError('Input IDs differ')
    scales=list(csv.DictReader((PCA/'standardization.csv').open()));tasks9=BATTERIES['nine'];scales={r['task']:r for r in scales}
    X=np.array([[float(r[t]) for t in tasks9] for r in rows]);mu=np.array([float(scales[t]['mean']) for t in tasks9]);sd=np.array([float(scales[t]['sd']) for t in tasks9]);Z=(X-mu)/sd
    if not np.isfinite(Z).all() or np.any(sd<=0):raise ValueError('Invalid fixed-metric inputs')
    families,strata=cluster_strata(members);cohorts=np.array([m['cohort'] for m in members]);cases=[];diagnostics=[];weights=[];spectra=[];observed=[]
    spec=dict(draws_per_design=reps,seed=SEED,methods=METHODS,sampling_schemes=SCHEMES,
        common_axis='sample-size-minus-one weighted chordal consensus of observed cohort PC1 axes; top eigenvector of sum((n_g-1)*v_g*v_g.T)',
        primary_null='projected covariance: a_g*u*u.T + P*S_g*P, a_g=u.T*S_g*u, P=I-u*u.T; no common constraints within orthogonal complements',
        sensitivity_null='minimum orthogonal rotation maps observed PC1 to consensus while preserving entire cohort covariance spectrum',
        primary_sampling='sample whole bases within full/selected cohort-count signature strata to preserve exact cohort sizes and number of bases',
        sensitivity_sampling='global named-base cluster resampling; cohort row counts vary',
        scaling='previous PCA pooled metric frozen across cohorts, constructions and simulation draws; no null restandardization',
        statistic='three acute pairwise PC1 angles, their congruences, and maximum angle as omnibus statistic; plus-one Monte Carlo p-values',
        multiplicity='max-angle adjusted pairwise p-values under the complete shared-axis null; not asserted strong FWER for arbitrary partial nulls',
        interpretation='conditional covariance-geometry null, not a latent-intelligence, discrimination or causal model')
    (OUT/'specification.json').write_text(json.dumps(spec,indent=2)+'\n')
    write_csv(OUT/'cluster_strata.csv',[dict(signature=str(k),bases=len(v),rows_per_base=sum(k[:3]),selected_rows_per_base=sum(k[3:]),singleton_stratum=len(v)==1,base_names=' | '.join(v)) for k,v in sorted(strata.items())])
    for sample in ('all','selected'):
        for battery,tasks in BATTERIES.items():
            ix=np.array([i for i,m in enumerate(members) if sample=='all' or m['selected']=='True']);cols=[tasks9.index(t) for t in tasks];W=Z[np.ix_(ix,cols)];cohort=cohorts[ix]
            matrices=[W[cohort==h] for h in HALVES];fits=[pc1(M) for M in matrices];ns=[len(M) for M in matrices];u=consensus_axis([f['weights'] for f in fits],np.array(ns)-1)
            case=dict(sample=sample,battery=battery,tasks=tasks,indices=ix,cohorts=cohort,ns=ns,common=u,nulls={})
            for j,t in enumerate(tasks):weights.append(dict(sample=sample,battery=battery,task=t,common_axis=float(u[j])))
            for a,b in PAIRS:observed.append(dict(sample=sample,battery=battery,cohort_a=HALVES[a],cohort_b=HALVES[b],**similarity(fits[a]['weights'],fits[b]['weights'])))
            for method in METHODS:
                Y=np.empty_like(W)
                for g,(h,M,f) in enumerate(zip(HALVES,matrices,fits)):
                    S=np.cov(M,rowvar=False);target=construct_null(S,u,method);Y[cohort==h]=transform_rows(M,target,method,u)
                    val,vec=np.linalg.eigh(target);Sval=np.linalg.eigvalsh(S)
                    gap=float((val[-1]-val[-2])/val[-1]);alignment=abs(float(vec[:,-1]@u));residual=float(np.linalg.norm(target@u-float(u@target@u)*u))
                    diagnostics.append(dict(sample=sample,battery=battery,method=method,cohort=h,n=len(M),source_relative_gap=f['relative_gap'],null_relative_gap=gap,
                        source_evr=f['explained_variance'],null_evr=float(val[-1]/val.sum()),alignment=alignment,eigenvector_residual=residual,
                        min_eigenvalue=float(val[0]),condition_number=float(val[-1]/val[0]),trace_change=float(np.trace(target)-np.trace(S)),
                        max_spectrum_change=float(np.max(np.abs(val-Sval))),covariance_change_frobenius=float(np.linalg.norm(target-S))))
                    for j,v in enumerate(val[::-1]):spectra.append(dict(sample=sample,battery=battery,method=method,cohort=h,component=j+1,source_eigenvalue=float(Sval[::-1][j]),null_eigenvalue=float(v)))
                    case.setdefault('targets',{}).setdefault(method,[]).append(target.tolist())
                case['nulls'][method]=Y
            cases.append(case)
    write_csv(OUT/'null_covariance_diagnostics.csv',diagnostics);write_csv(OUT/'common_axes.csv',weights);write_csv(OUT/'spectra.csv',spectra);write_csv(OUT/'observed_comparisons.csv',observed)
    (OUT/'null_covariances.json').write_text(json.dumps([dict(sample=c['sample'],battery=c['battery'],axis=c['common'].tolist(),covariances=c['targets']) for c in cases],indent=2)+'\n')
    S=len(SCHEMES);M=len(METHODS);C=len(cases)
    angles=np.full((S,M,reps,C,3),np.nan);congruence=angles.copy();gaps=angles.copy();evr=angles.copy();statuses=np.full((S,M,reps,C,3),'missing',dtype='U12');counts=np.zeros((S,reps,C,3),dtype=int)
    directions=np.full((S,M,reps,C,3,9),np.nan);problems=[]
    for s,scheme in enumerate(SCHEMES):
        for rep in range(reps):
            rng=np.random.default_rng(np.random.SeedSequence(SEED,spawn_key=(s,rep)));draw=resample_indices(families,strata,rng,scheme)
            for c,case in enumerate(cases):
                pos={int(i):j for j,i in enumerate(case['indices'])};local=[pos[i] for i in draw if i in pos];hdraw=case['cohorts'][local]
                counts[s,rep,c]=[sum(hdraw==h) for h in HALVES]
                if scheme=='fixed_sizes' and not np.array_equal(counts[s,rep,c],case['ns']):raise RuntimeError('Conditional cluster bootstrap changed cohort sizes')
                for m,method in enumerate(METHODS):
                    Y=case['nulls'][method][local];fits=[]
                    for g,h in enumerate(HALVES):
                        try:
                            f=pc1(Y[hdraw==h],case['common']);fits.append(f)
                            directions[s,m,rep,c,g,:len(case['tasks'])]=f['weights'];gaps[s,m,rep,c,g]=f['relative_gap'];evr[s,m,rep,c,g]=f['explained_variance'];statuses[s,m,rep,c,g]='ok'
                        except (ValueError,np.linalg.LinAlgError) as e:
                            fits.append(None);statuses[s,m,rep,c,g]='failed';problems.append(dict(scheme=scheme,method=method,replicate=rep,sample=case['sample'],battery=case['battery'],cohort=h,detail=str(e)))
                    for k,(a,b) in enumerate(PAIRS):
                        if fits[a] is not None and fits[b] is not None:
                            comparison=similarity(fits[a]['weights'],fits[b]['weights']);angles[s,m,rep,c,k]=comparison['angle_degrees'];congruence[s,m,rep,c,k]=comparison['cosine_similarity']
            if (rep+1)%500==0:print(scheme,rep+1,'/',reps,flush=True)
    np.savez_compressed(OUT/'null_distributions.npz',angles=angles,congruence=congruence,relative_gap=gaps,explained_variance=evr,status=statuses,directions=directions,
        sample_sizes=counts,schemes=np.array(SCHEMES),methods=np.array(METHODS),cases=np.array([[c['sample'],c['battery']] for c in cases]),pairs=np.array(PAIRS))
    write_csv(OUT/'simulation_problems.csv',problems or [dict(scheme='',method='',replicate='',sample='',battery='',cohort='',detail='none')])
    tests=[];gap_summary=[];size_summary=[]
    for s,scheme in enumerate(SCHEMES):
        for c,case in enumerate(cases):
            tags={k:case[k] for k in ('sample','battery')};obs=[r for r in observed if r['sample']==case['sample'] and r['battery']==case['battery']]
            for g,h in enumerate(HALVES):size_summary.append(dict(scheme=scheme,**tags,cohort=h,target=case['ns'][g],minimum=int(counts[s,:,c,g].min()),q025=float(np.quantile(counts[s,:,c,g],.025)),median=float(np.median(counts[s,:,c,g])),q975=float(np.quantile(counts[s,:,c,g],.975)),maximum=int(counts[s,:,c,g].max())))
            for m,method in enumerate(METHODS):
                A=angles[s,m,:,c];valid=np.isfinite(A).all(1);maximum=np.where(valid,np.max(np.where(np.isfinite(A),A,-np.inf),axis=1),np.nan)
                for k,(a,b) in enumerate(PAIRS):
                    r=dict(scheme=scheme,method=method,**tags,comparison=HALVES[a]+' / '+HALVES[b],**tail_result(A[:,k],obs[k]['angle_degrees'],reps))
                    r['p_max_adjusted']=tail_result(maximum,obs[k]['angle_degrees'],reps)['p_calibrated']
                    finite=congruence[s,m,:,c,k];finite=finite[np.isfinite(finite)]
                    r.update(observed_congruence=obs[k]['cosine_similarity'],null_congruence_q01=float(np.quantile(finite,.01)) if len(finite) else None,null_congruence_q05=float(np.quantile(finite,.05)) if len(finite) else None)
                    tests.append(r)
                tests.append(dict(scheme=scheme,method=method,**tags,comparison='omnibus maximum angle',**tail_result(maximum,max(r['angle_degrees'] for r in obs),reps),
                    p_max_adjusted=None,observed_congruence=None,null_congruence_q01=None,null_congruence_q05=None))
                for g,h in enumerate(HALVES):
                    v=gaps[s,m,:,c,g];v=v[np.isfinite(v)]
                    gap_summary.append(dict(scheme=scheme,method=method,**tags,cohort=h,admissible=len(v),attempted=reps,
                        minimum=float(v.min()) if len(v) else None,q025=float(np.quantile(v,.025)) if len(v) else None,median=float(np.median(v)) if len(v) else None,q975=float(np.quantile(v,.975)) if len(v) else None,near_ties=int(sum(v<.1))))
    write_csv(OUT/'calibrated_tests.csv',tests);write_csv(OUT/'null_spectral_gaps.csv',gap_summary);write_csv(OUT/'sample_size_diagnostics.csv',size_summary)
    meta=dict(specification=spec,configurations=len(rows),bases=len(families),strata=len(strata),singleton_strata=sum(len(v)==1 for v in strata.values()),
        numerical_construction_failures=0,simulation_failures=len(problems),attempted_cohort_pcas=int(statuses.size),admissible_cohort_pcas=int((statuses=='ok').sum()),
        python=sys.version,numpy=np.__version__,scipy=__import__('scipy').__version__,
        input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE/'matrix.csv',SOURCE/'configurations.csv',PCA/'standardization.csv',PCA/'point_similarities.csv']},
        code_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['aa_pca_null.py','aa_cohort_pca.py','aa_cohort_factor.py','downloaded_data_audit.py']})
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');report(tests,diagnostics,meta)
    print(OUT,flush=True)


def report(tests,diagnostics,meta):
    lines=['# Shared dominant-axis null calibration','',
        'The null allows each cohort a different covariance spectrum and unrestricted covariance on the orthogonal complement of a shared PC1. It does not impose CFA residual assumptions, common complete covariance matrices or equal latent-factor loadings. All calculations use the earlier frozen pooled benchmark metric, with cohort centering and no restandardization after transformation.','',
        '## Null construction','',
        'The plug-in common axis is the sample-size-minus-one weighted chordal consensus: the leading eigenvector of sum((n_g−1) v_g v_g^T), where v_g is observed cohort PC1. Axis signs do not affect this estimate.','',
        'Primary projected null: for cohort covariance S, common unit axis u and P = I − uu^T, set S0 = (u^T S u) uu^T + P S P. This removes axis/complement covariance but retains unrestricted cohort-specific covariance within the complement. It is the fixed-axis block projection, not a Gaussian maximum-likelihood common-principal-component fit. Every target is checked to be positive definite, to preserve total variance, and to have u as a uniquely leading eigenvector; we do not inflate eigenvalues to force dominance.','',
        'Spectrum-preserving sensitivity: minimally rotate each observed covariance so its leading eigenvector equals u. Its entire original spectrum is retained. The remaining eigendirections rotate along with the cohort, and need not agree between cohorts. The choice of null nuisance covariance is therefore explicit and checked against an alternative.','',
        '## Cluster simulation and sample sizes','',
        f"Each of four cases (nine/eight indicators × all/one-per-base) has {meta['specification']['draws_per_design']} draws for each null construction and sampling scheme. The same base identities are drawn across batteries, samples and constructions within a scheme. Four simulations per case assess null-construction and sampling assumptions, rather than multiplying independent evidence.",'',
        'Primary resampling draws whole named-base clusters within strata defined by their full and selected cohort-count signatures. This preserves the exact cohort row counts and cluster counts without splitting setting variants. Source sizes are 59/176/152 for all configurations and 49/127/103 for the selected sample. These bases do not span cohorts in the current mapping. Two singleton size strata in 2026H1 (one four-setting base and one five-setting base) are fixed under this conditioning, limiting their identity variation. The global-cluster sensitivity resamples whole bases without conditioning and allows cohort sizes to vary; its count ranges are exported.','',
        'For the projected null, empirical cohort score vectors are centered, whitened and recolored to their target covariance. For the spectral null, an orthogonal rotation alone suffices and preserves within-cohort row distances. Whole transformed configuration blocks are then resampled. This retains transformed empirical within-base dependence; it does not preserve original benchmark margins, floors, numerical within-family correlations or cross-cohort Euclidean distances. A selected case has its own null transform but retains the original selected identities.','',
        '## Primary calibration: exact cohort sizes and projected null','',
        '| Sample | Battery | Comparison | Observed angle | Null 95th percentile | Null 99th percentile | Exceedances / admissible | Calibrated p | Max-angle adjusted p |','|---|---|---|---:|---:|---:|---:|---:|---:|']
    def pvalue(v):return 'withheld' if v is None else f'{v:.5f}'
    for r in tests:
        if r['scheme']!='fixed_sizes' or r['method']!='projected':continue
        lines.append(f"| {r['sample']} | {r['battery']} | {r['comparison']} | {r['observed']:.2f}° | {r['null_q95']:.2f}° | {r['null_q99']:.2f}° | {r['exceedances']}/{r['admissible']} | {pvalue(r['p_calibrated'])} | {pvalue(r['p_max_adjusted'])} |")
    lines+=['','Pairwise p-values use the angle upper tail; a congruence lower-tail comparison is equivalent because angle is monotone in congruence. Congruence null percentiles are exported. The omnibus statistic is the maximum of the three pairwise angles. Pairwise max-angle adjustments calibrate against that joint maximum under the complete shared-axis null, not strong FWER control for arbitrary partial nulls. The four overlapping battery/sample cases and the null-construction/sampling sensitivities are not separately multiplicity-corrected.','',
        '## First-to-last robustness','',
        '| Sampling | Null covariance | Sample | Battery | Null angle q95 | Observed angle | Exceedances / admissible | Calibrated p |','|---|---|---|---|---:|---:|---:|---:|']
    for r in tests:
        if r['comparison']!='2025H1 / 2026H1':continue
        lines.append(f"| {r['scheme']} | {r['method']} | {r['sample']} | {r['battery']} | {r['null_q95']:.2f}° | {r['observed']:.2f}° | {r['exceedances']}/{r['admissible']} | {pvalue(r['p_calibrated'])} |")
    lines+=['','## Numerical validation and calibration limits','',
        f"Null target covariances were all constructed successfully. Cohort PCAs: {meta['admissible_cohort_pcas']}/{meta['attempted_cohort_pcas']} admissible; simulation failures: {meta['simulation_failures']}. null_covariance_diagnostics.csv reports leading-axis alignment, eigenvector residual, positive-definiteness, condition numbers, trace/spectrum changes and source/target gaps. null_spectral_gaps.csv reports simulated gap distributions and near-tie counts. sample_size_diagnostics.csv verifies fixed-size preservation and variable-size ranges.",'',
        'Calibrated p-values have a plus-one correction, (exceedances+1)/(admissible+1), and are withheld below 90% admissibility. They are never reported as zero. At 2,000 draws, the finest resolution is about .00050. Exact binomial intervals for Monte Carlo exceedance probabilities and conservative invalid-draw bounds are exported; these address Monte Carlo/fit uncertainty, not all null assumptions.','',
        'The null targets are estimated from the same finite data and held fixed during generation; calibration is an approximate plug-in empirical bootstrap, not an exact randomization test or proof of its finite-sample size. No independent simulation study of repeated-experiment type-I error has been run. Projection can change eigenvalues; the rotation sensitivity preserves them but imposes a particular rotation of the remaining covariance. Neither construction is uniquely implied by the shared-axis hypothesis. The exact-size design conditions on the observed cluster-size distribution, while global resampling relaxes that condition.','',
        '## Interpretation','',
        'Exceeding these null distributions is evidence that the observed common-unit covariance PC1 geometry differs more across release cohorts than this named-base sampling model predicts under a shared leading axis. It does not establish changes in latent intelligence, benchmark discrimination, causal model architecture or training effects. Different mixtures of model families, reasoning configurations, score floors and evaluation conditions can produce the same geometric result. Named-base clusters capture explicit setting variants, not all shared ancestry; item uncertainty is absent.','',
        'This remains a retrospective release-cohort study in a frozen July 2026 snapshot. It does not establish historical score trajectories, CFA measurement invariance or equality/inequality of latent constructs. Explained variance can change independently of direction.','',
        '## Reproduction and files','',
        '`OPENBLAS_NUM_THREADS=1 uv run aa_pca_null.py --resamples 2000`','',
        '`uv run aa_pca_null_plot.py`','',
        'calibrated_tests.csv contains all pairwise/omnibus tests, null percentiles, Monte Carlo uncertainty and invalid-draw bounds. null_distributions.npz stores vectors, angles/congruence, gaps, variance fractions, cohort sizes and statuses. null_covariances.json and common_axes.csv pin target geometry. specification.json fixes methods and reporting. Input/code hashes are in metadata.json.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resamples',type=int,default=2000);args=parser.parse_args()
    if args.resamples<1:parser.error('resamples must be positive')
    run(args.resamples)
