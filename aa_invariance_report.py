"""Render loading-invariance results from saved outputs; never refit models."""
import csv
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output/aa-invariance'


def read(name):
    rows=list(csv.DictReader((OUT/name).open()))
    for row in rows:
        for k,v in row.items():
            try:row[k]=json.loads(v) if v else None
            except (ValueError,TypeError):pass
    return rows


def main():
    point=json.loads((OUT/'point_fits.json').read_text());meta=json.loads((OUT/'metadata.json').read_text())
    summaries=read('delta_summaries.csv');null=read('null_tests.csv');partials=read('partial_invariance.csv');single=read('single_release_diagnostics.csv');loads=read('loading_differences.csv');loading_intervals=read('loading_intervals.csv')
    def fmt(x):return 'withheld' if x is None else f'{x:.4f}'
    def span(r):return 'withheld' if r['low'] is None else f"[{r['low']:.4f}, {r['high']:.4f}]"
    lines=['# AA general-factor loading invariance study','',
        'This is a covariance-only, exploratory multi-group CFA using the fixed coding-plus-academic residual specification. Delta CFI is equal-loading CFI minus free-loading CFI: negative values indicate relative deterioration. Absolute fit is evaluated separately. The same named-base cluster draws are matched across both batteries and both configuration samples.','',
        f"{meta['specification']['bootstrap_draws']} cluster-bootstrap draws and {meta['specification']['null_draws']} covariance-null cluster draws were attempted for every case. Residual covariance blocks and variances, and factor variances, remain free by cohort. GPQA is the primary loading-scale marker. No means or scalar invariance constraints are fitted.",'',
        '## Fit deterioration and cluster uncertainty','',
        '| Sample | Battery | Free CFI | Equal CFI | Delta CFI | Admissible / attempted | 95% admissible range | All finite-fit 95% sensitivity range |',
        '|---|---|---:|---:|---:|---:|---|---|']
    for p in point:
        r=next(r for r in summaries if r['sample']==p['sample'] and r['battery']==p['battery'] and r['statistic']=='delta_cfi')
        lines.append(f"| {p['sample']} | {p['battery']} | {p['free']['cfi']:.4f} | {p['equal']['cfi']:.4f} | {p['delta_cfi']:.4f} | {r['admissible']}/{r['draws']} | {span(r)} | [{r['finite_low']:.4f}, {r['finite_high']:.4f}] |")
    lines+=['','Admissible ranges are withheld below 90% admissibility. Finite-fit sensitivity ranges include boundary fits and are deliberately labeled separately; they are not calibrated confidence intervals. Boundary filtering can select the distribution even when the threshold is met. A bootstrap distribution around observed data measures estimator variation, not a null hypothesis test.','',
        '## Null-calibrated comparison','',
        '| Sample | Battery | Null statistic | Admissible / attempted | Calibrated p (admissible) | p including finite boundaries | Worst-case p range for inadmissible draws | Null finite 95th percentile |',
        '|---|---|---|---:|---:|---:|---|---:|']
    for r in null:
        lines.append(f"| {r['sample']} | {r['battery']} | {r['statistic']} | {r['admissible']}/{r['draws']} | {fmt(r['p_admissible'])} | {fmt(r['p_including_boundaries'])} | [{r['p_failure_lower']:.4f}, {r['p_failure_upper']:.4f}] | {r['null_finite_q95']:.4f} |")
    lines+=['',
        'For each case/cohort, center and whiten its empirical score vectors and recolor them to the fitted equal-loading covariance. The transformed original sample exactly matches that null covariance. Then resample complete named-base clusters using the same global draws across cases. This retains transformed empirical within-family dependence, rather than inventing independent Gaussian observations. It does not preserve original marginal bounds, floor rates or numerical within-family correlations. Most named-base clusters are singletons, and broader model ancestry remains unresolved.','',
        'The null is the entire fitted equal-loading covariance model, including the selected residual structure. Recoloring removes the original covariance misspecification. Rejection can therefore be affected by residual-model misspecification and cannot isolate a change in the latent general factor. Reported null p-values use a plus-one correction; with 500 simulations their finest resolution is about .002. Monte Carlo upper exceedance-rate bounds are in null_tests.csv. Worst-case ranges count every inadmissible null fit as either exceeding or not exceeding the observed statistic.','',
        '## Loading diagnostics','',
        'Raw loadings are GPQA-relative coefficients in common pooled score units. Standardized loadings also depend on cohort factor and residual variances and can differ under metric invariance. GPQA is fixed at one in the raw diagnostics, so its noninvariance cannot be assessed from that coefficient. The exhaustive single-release diagnostic uses IFBench as anchor when freeing GPQA. Alternate IFBench-anchored point loadings are exported; no benchmark is assumed intrinsically invariant.','',
        'Primary all-configuration, nine-indicator standardized loadings (point estimate and nominal 95% admissible-fit range):','',
        '| Benchmark | 2025H1 | 2025H2 | 2026H1 |','|---|---|---|---|']
    task_names=[r['task'] for r in loading_intervals if r['sample']=='all' and r['battery']=='nine' and r['scale']=='standardized' and r['cohort']=='2025H1']
    for task in task_names:
        rows=[next(r for r in loading_intervals if r['sample']=='all' and r['battery']=='nine' and r['scale']=='standardized' and r['cohort']==h and r['task']==task) for h in ('2025H1','2025H2','2026H1')]
        lines.append('| '+task+' | '+' | '.join(f"{r['point']:.3f} {span(r)}" for r in rows)+' |')
    lines+=['','| Sample | Battery | Largest single-release contributors (chi-square gain) |',
        '|---|---|---|']
    for p in point:
        rows=sorted([r for r in single if r['sample']==p['sample'] and r['battery']==p['battery']],key=lambda r:r['gain_chi2'],reverse=True)[:3]
        lines.append(f"| {p['sample']} | {p['battery']} | "+'; '.join(f"{r['freed']} ({r['gain_chi2']:.1f})" for r in rows)+' |')
    lines+=['','These gains are exhaustive exploratory attribution diagnostics, not independent tests or unique causal contributions; they are not additive. Their ranking was not used to select partial-invariance specifications.','',
        'Loading intervals and all three pairwise cohort differences are in loading_intervals.csv and loading_differences.csv. Within each case/scale, simultaneous bands use the bootstrap maximum standardized deviation across all benchmark × contrast diagnostics, scaled by fixed bootstrap standard errors and excluding the fixed marker coefficient. They are nominal bootstrap bands, not calibrated across the four overlapping cases. As with marginal intervals, simultaneous bands are withheld below 90% free-model admissibility.','',
        '| Sample | Battery | First-to-last raw-loading differences with nominal simultaneous bands excluding zero |',
        '|---|---|---|']
    for p in point:
        rs=[r for r in loads if r['sample']==p['sample'] and r['battery']==p['battery'] and r['scale']=='raw' and r['contrast']=='2026H1 minus 2025H1']
        selected=[r for r in rs if r['simultaneous_low'] is not None and (r['simultaneous_low']>0 or r['simultaneous_high']<0)]
        text='; '.join(f"{r['task']}: {r['point']:+.3f} [{r['simultaneous_low']:+.3f}, {r['simultaneous_high']:+.3f}]" for r in selected)
        if not text:text='none' if any(r['simultaneous_low'] is not None for r in rs) else 'bands withheld'
        lines.append(f"| {p['sample']} | {p['battery']} | {text} |")
    lines+=['','## Partial invariance: fixed candidate set','',
        'Candidates release AA-LCR, CritPt, or both, where present. They were fixed before these fits because prior audits documented substantial floors. This uses prior observations from the same dataset and is not independent confirmatory preregistration. No candidate was chosen from the new contribution ranking. Partial fits are point-fit diagnostics; they have not received their own cluster-bootstrap/null calibration or out-of-sample validation.','',
        '| Sample | Battery | Freed loadings | CFI | Multi-group RMSEA | Delta CFI vs free | Relative screen | Absolute screen | Boundary |',
        '|---|---|---|---:|---:|---:|---|---|---|']
    for r in partials:lines.append(f"| {r['sample']} | {r['battery']} | {r['freed']} | {r['cfi']:.4f} | {r['rmsea']:.4f} | {r['delta_cfi_vs_free']:.4f} | {r['relative_screen']} | {r['absolute_screen']} | {r['boundary']} |")
    lines+=['',
        'The descriptive relative screen is Delta CFI >= −.01. The separate absolute screen requires CFI >= .95 and multi-group RMSEA <= .08. These conventional screens are not universal calibrated cutoffs for bounded, clustered benchmark scores. Multi-group RMSEA uses the average group N−1 convention. Cohort-specific free-model RMSEA and residual RMS are in absolute_fit_by_cohort.csv. Better relative fit does not make an inadequate absolute model adequate.','',
        '## Interpretation and limitations','',
        'The estimand is stability of benchmark-to-factor loading relationships across release cohorts in a frozen July 2026 snapshot. Evidence against equal loadings concerns this measurement model. It does not establish that the underlying general capability changed, grew, weakened or acquired new dimensions. Residual misspecification, differing floors, model/configuration composition and evaluation conditions are alternative explanations. Scalar invariance, latent capability means and item-level measurement error remain untested.','',
        'fit_problems.csv records every boundary or failed fit, including whether the free model itself was admissible. distributions.npz stores delta-CFI/chi-square draws, loading draws and statuses without pickle. draws.jsonl retains each completed matched draw. gradient_diagnostics.csv exposes convergence gradients; optimizer convergence alone is not proof of a well-determined model. The finite-boundary analyses and conservative failure bounds are necessary sensitivity checks, not substitutes for valid interior fits.','',
        'Numerical validation found that an earlier inverse/log-determinant calculation could mis-evaluate near-singular model covariances. The final run uses Cholesky likelihood calculations, rejects numerically singular proposed model covariances (without regularizing sample covariances), and requires projected optimizer gradients below .1. All 2,000 bootstrap and 500 null draws were repeated with the corrected fitter. This numerical guard does not make boundary estimates statistically admissible.','',
        'The tested partial candidate set is deliberately limited; its failure does not prove that no other small set of releases could improve relative fit. Selecting such a set from these same diagnostic rankings would require separate validation.','',
        '## Reproduction','',
        '`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run aa_invariance_study.py --bootstrap 2000 --null 500 --workers 4`','',
        '`uv run aa_invariance_report.py`','',
        'Inputs, analysis code and fixed specification are hashed in metadata.json. Figures render from saved outputs; no refits are needed.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    figures(point,partials)


def figures(point,partials):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d=np.load(OUT/'distributions.npz');case_names=d['cases'];fig,axes=plt.subplots(4,2,figsize=(11,12),layout='constrained')
    for c,(sample,battery) in enumerate(case_names):
        observed=point[c]['delta_cfi'];v=d['delta_cfi'][:,c];ok=d['status'][:,c]=='ok';finite=np.isfinite(v)
        for col,(vals,status) in enumerate([(v,ok),(d['null_delta_cfi'][:,c],d['null_status'][:,c]=='ok')]):
            ax=axes[c,col];f=np.isfinite(vals);ax.hist(vals[f],bins=35,density=True,histtype='step',color='gray',label='all finite (incl. boundaries)')
            if status.any():ax.hist(vals[status],bins=35,density=True,color='#225ea8',alpha=.5,label='admissible')
            ax.axvline(observed,color='#d95f0e',lw=2,label='observed');ax.axvline(0,color='black',ls=':',lw=1)
            ax.set(title=f'{sample}/{battery}: '+('cluster bootstrap' if col==0 else 'equal-loading null'),xlabel='Delta CFI (equal − free)',ylabel='Density')
            if c==0:ax.legend(fontsize=7)
    fig.suptitle('Loading equality: observed-data uncertainty versus null variation\nBoundary fits shown separately; null calibration is conditional on the residual model')
    fig.savefig(OUT/'delta_cfi_distributions.png',dpi=170);plt.close(fig)
    rs=read('loading_differences.csv');fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for c,(sample,battery) in enumerate(case_names):
        rows=[r for r in rs if r['sample']==sample and r['battery']==battery and r['scale']=='raw' and r['contrast']=='2026H1 minus 2025H1' and r['task']!='gpqa'];ax=axes.flat[c]
        for j,r in enumerate(rows):
            if r['finite_low'] is not None:ax.hlines(j,r['finite_low'],r['finite_high'],color='gray',ls=':',lw=2)
            if r['simultaneous_low'] is not None:ax.hlines(j,r['simultaneous_low'],r['simultaneous_high'],color='#9ecae1',lw=4)
            if r['low'] is not None:ax.hlines(j,r['low'],r['high'],color='#225ea8',lw=2)
            ax.plot(r['point'],j,'o',color='#d95f0e')
        ax.axvline(0,color='black',lw=1);ax.set(title=f'{sample}/{battery}',yticks=range(len(rows)),yticklabels=[r['task'] for r in rows],xlabel='GPQA-relative loading: 2026H1 − 2025H1')
    fig.suptitle('Loading differences in common pooled units\nBlue: nominal 95% bands (light: simultaneous); gray dotted: finite-boundary sensitivity\nAdmissible bands withheld below 90%; GPQA fixes scale')
    fig.savefig(OUT/'loading_differences.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    for c,(sample,battery) in enumerate(case_names):
        p=point[c];rows=[r for r in partials if r['sample']==sample and r['battery']==battery];ax=axes.flat[c]
        names=['equal']+[r['freed'] for r in rows]+['free'];cfis=[p['equal']['cfi']]+[r['cfi'] for r in rows]+[p['free']['cfi']]
        ax.bar(names,cfis,color=['#888888']+['#225ea8']*len(rows)+['#d95f0e']);ax.axhline(.95,color='black',ls='--',label='CFI .95 absolute screen');ax.set(title=f'{sample}/{battery}',ylabel='CFI',ylim=(.7,1));ax.tick_params(axis='x',labelrotation=20)
    fig.suptitle('Fixed partial-invariance candidates: improved relative fit is not adequate absolute fit')
    fig.savefig(OUT/'partial_invariance.png',dpi=170);plt.close(fig)


if __name__=='__main__':main()
