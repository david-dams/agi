"""Trace the proposed AA cohort panel to its archived public-page payload."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from downloaded_data_audit import CORE, DATA, OUT, period


def parse_models(html):
    parts = re.findall(r'self\.__next_f\.push\(\[\d+,"((?:[^"\\]|\\.)*)"\]\)', html)
    stream = ''.join(json.loads('"' + p + '"') for p in parts)
    arrays = [json.JSONDecoder().raw_decode(stream[m.start(1):])[0]
              for m in re.finditer(r'"models":(\[\{"id")', stream)]
    if not arrays:
        raise ValueError('No embedded model arrays')
    # The page includes a short navigation array and a full score array.
    models = max(arrays, key=lambda a: len(a[0]))
    if len({m['slug'] for m in models}) != len(models):
        raise ValueError('Duplicate source slugs')
    return models


def main():
    with zipfile.ZipFile(DATA / 'archives/aa-bundle.zip') as z:
        prefix = next(n for n in z.namelist() if n.endswith('/data/raw/aa_snapshot_manifest.json')).removesuffix('data/raw/aa_snapshot_manifest.json')
        manifest = json.loads(z.read(prefix + 'data/raw/aa_snapshot_manifest.json'))
        html = z.read(prefix + 'data/raw/aa_leaderboards_models_snapshot.html')
        if hashlib.sha256(html).hexdigest() != manifest['sha256']:
            raise ValueError('Source HTML hash mismatch')
        models = parse_models(html.decode())
        rows = list(csv.DictReader(io.StringIO(z.read(prefix + 'data/processed/aa_analysis_models.csv').decode())))
    index = {m['slug']: m for m in models}
    checked = 0
    for row in rows:
        for key in (*CORE, 'releaseDate'):
            source, value = index[row['slug']].get(key), row[key]
            if source in (None, '$undefined'):
                equal = value == ''
            elif key == 'releaseDate':
                equal = source == value
            else:
                equal = abs(float(source) - float(value)) < 1e-12
            if not equal:
                raise ValueError(f'Source mismatch: {row["slug"]}/{key}')
            checked += 1
    complete = [m for m in models if all(type(m.get(t)) in (int, float) for t in CORE)]
    cohorts = []
    for half in ('2025H1', '2025H2', '2026H1'):
        group = [m for m in complete if m.get('releaseDate') and period(m['releaseDate'], 'half') == half]
        cohorts.append(dict(half=half, configurations=len(group),
            composite_estimated=sum(m['intelligenceIndexIsEstimated'] is True for m in group),
            composite_not_estimated=sum(m['intelligenceIndexIsEstimated'] is False for m in group),
            zeros={t: sum(m[t] == 0 for m in group) for t in CORE},
            token_metadata={t: sum(isinstance(m.get('evalTokenCounts'), dict) and
                                  isinstance(m['evalTokenCounts'].get(t), dict) for m in group) for t in CORE}))
    result = dict(source=manifest, source_models=len(models), complete_nine=len(complete),
                  verified_processed_cells=checked, mismatches=0, cohorts=cohorts,
                  source_fields=list(models[0]),
                  interpretation='Composite estimate flags do not establish component imputation; token metadata does not establish shared versions.')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'aa_provenance.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('source_models', 'complete_nine', 'verified_processed_cells', 'mismatches', 'cohorts')}, indent=2))


if __name__ == '__main__':
    main()
