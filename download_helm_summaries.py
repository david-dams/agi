"""Download HELM release core-scenario summaries; never bulk-download run responses."""
import gzip
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parent/'public-data'/'helm-summaries'
ROOT.mkdir(parents=True,exist_ok=True)
entries=[]
failures=[]
for project,prefix in [('classic','benchmark_output/releases/'),('lite','lite/benchmark_output/releases/'),('capabilities','capabilities/benchmark_output/releases/')]:
    token=None
    try:
        while True:
            query=dict(prefix=prefix,maxResults=1000)
            if token: query['pageToken']=token
            url='https://storage.googleapis.com/storage/v1/b/crfm-helm-public/o?'+urllib.parse.urlencode(query)
            with urllib.request.urlopen(url,timeout=90) as response: page=json.load(response)
            for item in page.get('items',[]):
                name=item['name']
                if not name.endswith('/groups/core_scenarios.json'): continue
                relative=name.removeprefix(prefix)
                if '..' in Path(relative).parts or Path(relative).is_absolute(): raise ValueError('unsafe object name')
                target=ROOT/project/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                entry=dict(project=project,name=name,generation=item['generation'],bytes=int(item['size']))
                try:
                    download='https://storage.googleapis.com/download/storage/v1/b/crfm-helm-public/o/'+urllib.parse.quote(name,safe='')+'?alt=media&generation='+item['generation']
                    with urllib.request.urlopen(download,timeout=120) as response: content=response.read()
                    if len(content)!=int(item['size']): raise ValueError('size mismatch')
                    if content.startswith(b'\x1f\x8b'):
                        content=gzip.decompress(content)
                        entry['decompressed_from_gzip']=True
                    json.loads(content)
                    part=target.with_suffix('.json.part')
                    part.write_bytes(content)
                    part.replace(target)
                    entry['path']=str(target.relative_to(ROOT))
                except Exception as error:
                    entry['error']=str(error)
                    failures.append(entry)
                entries.append(entry)
            token=page.get('nextPageToken')
            if not token: break
    except Exception as error:
        failures.append(dict(project=project,error=str(error)))
    if not any(e['project']==project for e in entries):
        failures.append(dict(project=project,error='no matching release summaries discovered; inspect suite layout'))
(ROOT/'manifest.json').write_text(json.dumps(dict(objects=entries,failures=failures),indent=2)+'\n')
print(f'HELM: {sum("path" in e for e in entries)} summaries, {len(failures)} failures')
if failures: raise SystemExit(2)
