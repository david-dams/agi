# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2", "scipy>=1.14"]
# ///
"""Analyze downloaded aggregate LiveBench tables; no downloads or item inference."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from factor_models import corr, standardize, discover_groups, fit_higher_order

ROOT = Path(__file__).resolve().parent
METRICS = ('g_variance_share', 'ecv', 'cfi', 'rmsea', 'aic', 'bic', 'residual_rms', 'omega_h')


def load_table(path):
    with path.open(newline='') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if not fields or fields[0] != 'model' or len(set(fields)) != len(fields):
            raise ValueError(f'{path}: expected unique task headers after model')
        records = list(reader)
    models = [row['model'] for row in records]
    if len(models) < 3 or any(not m for m in models) or len(set(models)) != len(models):
        raise ValueError(f'{path}: missing or duplicate model IDs, or too few rows')
    tasks = fields[1:]
    X = np.array([[float(row[t]) for t in tasks] for row in records])
    if not np.isfinite(X).all() or np.any((X < 0) | (X > 100)):
        raise ValueError(f'{path}: expected finite scores in [0,100]')
    standardize(X)  # Reject constant tasks before attempting fits.
    return dict(models=models, tasks=tasks, X=X)


def subset(table, models, tasks):
    return dict(models=models, tasks=tasks, X=table['X'][np.ix_(
        [table['models'].index(m) for m in models], [table['tasks'].index(t) for t in tasks])])


def attempt(X, groups):
    try:
        R = corr(standardize(X))
        if np.linalg.eigvalsh(R).min() <= 1e-9:
            return None, 'singular'
        fit = fit_higher_order(R, len(X), groups)
        return fit, 'boundary' if fit.boundary else 'ok'
    except (ValueError, RuntimeError, np.linalg.LinAlgError) as error:
        return None, f'{type(error).__name__}: {error}'


def analyze(label, table, reps, seed, fixed_groups=None):
    X, tasks = table['X'], table['tasks']
    R = corr(standardize(X))
    groups = fixed_groups if fixed_groups is not None else discover_groups(R, 3)
    specs = {'1': [list(range(len(tasks)))], '3': groups}
    result = dict(panel=label, models=table['models'], tasks=tasks, n=len(X), p=len(tasks),
                  rank=int(np.linalg.matrix_rank(X-X.mean(0))),
                  min_correlation_eigenvalue=float(np.linalg.eigvalsh(R).min()),
                  zero_scores=[dict(model=table['models'][i], task=tasks[j]) for i,j in zip(*np.where(X == 0))],
                  groups=None if groups is None else [[tasks[i] for i in g] for g in groups], fits={})
    fits = {}
    for N, grouping in specs.items():
        fit, status = attempt(X, grouping) if grouping else (None, 'no viable three-group partition')
        fits[N] = fit
        result['fits'][N] = dict(status=status)
        if fit is not None:
            result['fits'][N].update({m: float(getattr(fit, m)) for m in METRICS})
            result['fits'][N]['loadings'] = dict(zip(tasks, fit.standardized_g.tolist()))
    rng = np.random.default_rng(seed)
    draws = {N: [] for N in specs}
    diagnostics = {N: Counter() for N in specs}
    paired_delta = []
    for _ in range(reps):
        sample = X[rng.integers(len(X), size=len(X))]
        replicate = {}
        for N, grouping in specs.items():
            fit, status = attempt(sample, grouping) if grouping else (None, 'no viable three-group partition')
            diagnostics[N][status] += 1
            if status == 'ok':
                draws[N].append([getattr(fit, m) for m in METRICS])
                replicate[N] = fit
        if len(replicate) == 2:
            paired_delta.append(replicate['3'].bic - replicate['1'].bic)
    for N in specs:
        valid = len(draws[N])
        # shortcut: configurations are sampled independently; use curated family clusters before population inference.
        result['fits'][N]['resampling'] = dict(attempted=reps, admissible=valid,
            outcomes=dict(diagnostics[N]), intervals=None)
        if valid >= .9 * reps and result['fits'][N]['status'] == 'ok':
            result['fits'][N]['resampling']['intervals'] = {
                m: np.quantile(np.asarray(draws[N])[:, i], [.025,.975]).tolist()
                for i,m in enumerate(METRICS)}
    result['paired_bootstrap'] = dict(admissible=len(paired_delta),
        hierarchy_bic_wins=int(sum(d < 0 for d in paired_delta)))
    return result


def report(results, overlaps, out, comparison=None):
    lines = ['# Modern LiveBench aggregate-factor study', '',
        'Battery labels identify benchmark versions. They are not frozen publication dates or model release cohorts.', '',
        '| Panel | Configurations | Tasks | One-factor g variance | Hierarchical g variance | Hierarchy minus one-factor BIC |',
        '|---|---:|---:|---:|---:|---:|']
    for r in results:
        a,b = r['fits']['1'],r['fits']['3']
        def value(f, key):
            return f"{f[key]:.3f}" + ('*' if f['status'] != 'ok' else '') if key in f else 'unavailable'
        delta = f"{b['bic']-a['bic']:.2f}" if 'bic' in a and 'bic' in b else 'unavailable'
        lines.append(f"| {r['panel']} | {r['n']} | {r['p']} | {value(a,'g_variance_share')} | {value(b,'g_variance_share')} | {delta} |")
    lines += ['', '* marks a boundary fit. Such estimates are diagnostics, not admissible results.', '',
        '## Interpretation limits', '',
        '- These fits describe covariance across the configurations included in each export. Different cohorts and task batteries can change that covariance.',
        '- The matched 2025 panels hold exact configuration IDs and task names fixed. Question IDs, scoring implementations and identical evaluation settings are not supplied by these CSVs; measurement equivalence remains unverified. No temporal growth or decline is inferred.',
        '- June 2026 has only 28 configurations for 23 tasks. Configuration bootstrap often produces singular covariance matrices; no regularization or replacement sampling scheme conceals this.',
        '- Resampling uses whole configuration rows with fixed point-estimate groups. It measures configuration sensitivity, assumes independent rows, and does not account for shared model families, group selection or item uncertainty. It is not an item bootstrap or a calibrated population interval.',
        '- Percentile sensitivity ranges are withheld below 90% admissible draws or when the point fit is inadmissible. Zero scores are retained and listed for provenance review.',
        '- Three-group partitions are discovered separately for full panels. The matched comparison uses the first matched panel partition for both batteries. If no partition has at least three indicators per group, the hierarchy is unavailable.', '',
        '## Overlap', '']
    for row in overlaps:
        lines.append(f"- {row['left']} / {row['right']}: {len(row['models'])} exact configuration IDs; {len(row['tasks'])} task names.")
    if comparison:
        lines += ['', '## Matched score changes', '',
            f"{comparison['changed_cells']} of {len(comparison['models'])*len(comparison['tasks'])} matched cells differ; maximum absolute change is {comparison['max_absolute_score_change']:.2f} points.", '',
            '| Task | Mean score change, November minus May battery |', '|---|---:|']
        for task, change in comparison['mean_changes_by_task'].items():
            lines.append(f'| {task} | {change:+.3f} |')
        lines += ['', 'Large changes for unchanged model IDs require question/scoring provenance review before interpreting differences in factor structure.']
    lines += ['', '## Fit and resampling diagnostics', '']
    for r in results:
        lines += [f"### {r['panel']}", '', f"Matrix rank {r['rank']}/{r['p']}; minimum correlation eigenvalue {r['min_correlation_eigenvalue']:.6g}.", '']
        for N,fit in r['fits'].items():
            boot = fit['resampling']
            lines.append(f"- N={N}: {fit['status']}; {boot['admissible']}/{boot['attempted']} admissible row resamples. Ranges {'reported' if boot['intervals'] else 'withheld'}.")
        pair = r['paired_bootstrap']
        lines.append(f"- Hierarchy wins BIC in {pair['hierarchy_bic_wins']}/{pair['admissible']} paired admissible draws; failed draws are excluded from this conditional comparison.")
        if r['groups']:
            lines += ['', 'Groups: ' + '; '.join(', '.join(g) for g in r['groups']) + '.']
        lines.append('')
    lines += ['## Reproduce', '', '```sh', 'uv run modern_gai_factor.py --resamples 200 --seed 0', '```', '',
        'Inputs and code are hashed in metadata.json. results.json contains full loadings, zero-score flags and failure counts; fit_statistics.csv contains point estimates. Earlier 2024 outputs are preserved.', '',
        'Source: https://github.com/LiveBench/livebench.github.io/tree/main/public. Download URLs reference mutable main; local SHA256 hashes pin the bytes analyzed. Retrieval timestamps and original upstream commit revisions were not recorded by the manual downloads.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'livebench-tables')
    parser.add_argument('--out', type=Path, default=ROOT/'output/modern-gai')
    parser.add_argument('--resamples', type=int, default=200)
    parser.add_argument('--seed', type=int, default=0)
    args=parser.parse_args()
    if args.resamples < 2:
        parser.error('--resamples must be at least 2')
    paths=sorted(args.data.glob('table_*.csv'))
    if not paths:
        parser.error('no table_*.csv files found')
    tables={p.stem.removeprefix('table_'):load_table(p) for p in paths}
    overlaps=[]
    for i,a in enumerate(tables):
        for b in list(tables)[i+1:]:
            overlaps.append(dict(left=a,right=b,models=sorted(set(tables[a]['models'])&set(tables[b]['models'])),
                                 tasks=sorted(set(tables[a]['tasks'])&set(tables[b]['tasks']))))
    results=[]
    for i,(label,table) in enumerate(tables.items()):
        print(f'Analyzing {label}', flush=True)
        results.append(analyze(label,table,args.resamples,args.seed+i))
    a,b='2025_05_30','2025_11_25'
    if a in tables and b in tables:
        overlap=next(o for o in overlaps if o['left']==a and o['right']==b)
        matched=[subset(tables[k],overlap['models'],overlap['tasks']) for k in (a,b)]
        groups=discover_groups(corr(standardize(matched[0]['X'])),3)
        # If discovery fails, both panels must record the same unavailable hierarchy.
        for label,table in zip((a,b),matched):
            print(f'Analyzing matched {label}',flush=True)
            results.append(analyze(label+' matched',table,args.resamples,args.seed+10,groups if groups is not None else []))
        change=matched[1]['X']-matched[0]['X']
        comparison=dict(models=overlap['models'],tasks=overlap['tasks'],
            changed_cells=int(np.count_nonzero(change)), max_absolute_score_change=float(abs(change).max()),
            mean_changes_by_task=dict(zip(overlap['tasks'],change.mean(0).tolist())),
            interpretation='Same IDs and task names; identical questions and scoring not verified. Not a temporal capability estimate.')
    else:
        comparison=None
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'results.json').write_text(json.dumps(dict(panels=results,overlaps=overlaps,matched_comparison=comparison),indent=2,allow_nan=False)+'\n')
    hashes={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths+[Path(__file__),ROOT/'factor_models.py']}
    (args.out/'metadata.json').write_text(json.dumps(dict(seed=args.seed,resamples=args.resamples,sha256=hashes,
        python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        sources={p.name:'https://raw.githubusercontent.com/LiveBench/livebench.github.io/main/public/'+p.name for p in paths}),indent=2)+'\n')
    with (args.out/'fit_statistics.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['panel','n','p','N','status',*METRICS]);writer.writeheader()
        for r in results:
            for N,fit in r['fits'].items():
                writer.writerow(dict(panel=r['panel'],n=r['n'],p=r['p'],N=N,status=fit['status'],**{m:fit.get(m,'') for m in METRICS}))
    report(results,overlaps,args.out,comparison)
    print(args.out/'README.md',flush=True)


if __name__=='__main__':
    main()
