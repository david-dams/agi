#!/usr/bin/env bash
# Run on the host with internet access, from any working directory.
set -uo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mkdir -p public-data/archives public-data/logs
status=public-data/download-status.tsv
printf 'dataset\tstatus\n' > "$status"
if command -v hf >/dev/null 2>&1; then
    hf_cmd=(hf)
elif command -v uvx >/dev/null 2>&1; then
    hf_cmd=(uvx --from huggingface_hub hf)
else
    printf 'Install huggingface_hub or uv first.\n' >&2
    exit 1
fi
run() {
    local label="$1"
    shift
    printf '\nDownloading %s\n' "$label"
    if "$@" > >(tee "public-data/logs/${label}.log") 2>&1; then
        printf '%s\tok\n' "$label" >> "$status"
    else
        printf '%s\tfailed; see logs\n' "$label" >> "$status"
    fi
}
hf_data() {
    local label="$1" repo="$2" revision
    shift 2
    # Pin the upstream revision before fetching, including when rerunning partial downloads.
    if ! revision=$(curl -fLsS --retry 2 --connect-timeout 20 --max-time 90 "https://huggingface.co/api/datasets/${repo}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["sha"])'); then
        printf '%s\tfailed resolving revision\n' "$label" >> "$status"
        return
    fi
    mkdir -p "public-data/${label}"
    printf '%s\t%s\n' "$repo" "$revision" > "public-data/${label}/upstream-revision.tsv"
    run "$label" "${hf_cmd[@]}" download "$repo" --repo-type dataset --revision "$revision" --local-dir "public-data/${label}" "$@"
}
archive() {
    local label="$1" url="$2"
    local target="public-data/archives/${label}.zip"
    printf '%s\n' "$url" > "${target}.source.txt"
    if curl -fL --retry 3 --connect-timeout 20 --max-time 1800 -o "${target}.part" "$url" && python3 -m zipfile -t "${target}.part"; then
        mv -- "${target}.part" "$target"
    else
        return 1
    fi
}

# Summary scores + item IDs. Full WILD conversations are an optional separate download.
hf_data wild kensho/WILD
hf_data open-llm-v2-contents open-llm-leaderboard/contents
hf_data open-llm-v1-contents open-llm-leaderboard-old/contents
# Detailed aggregate results: many JSON files, but no per-model *-details repositories.
hf_data open-llm-v2-results open-llm-leaderboard/results
hf_data open-llm-v1-results open-llm-leaderboard-old/results
hf_data arena lmarena-ai/leaderboard-dataset
hf_data datadecide allenai/DataDecide-eval-results
# Full selected EEE records, not its capped viewer samples or duplicate flat objects.
hf_data eee evaleval/EEE_datastore --include \
    'README.md' --include 'USAGE_EEE_datastore.md' --include 'flat/latest_manifest.json' \
    --include 'flat/manifests/*/entries.jsonl' --include 'flat/indexes/by_collection/*.jsonl' \
    --include 'data/artificial-analysis-llms/*' --include 'data/helm*/*' \
    --include 'data/livebench/*' --include 'data/opencompass*/*'

run aa-bundle archive aa-bundle https://codeload.github.com/louisyzhu/frontier-ai-economic-validity/zip/refs/heads/main
run obsscaling-bundle archive obsscaling-bundle https://codeload.github.com/ryoungj/ObsScaling/zip/refs/heads/main
run estonian-bundle archive estonian-bundle https://codeload.github.com/keeleinstituut/leaderboard-data-ui/zip/refs/heads/main
run livebench-exports archive livebench-exports https://codeload.github.com/LiveBench/livebench.github.io/zip/refs/heads/main
run metabench-bundle archive metabench-bundle https://codeload.github.com/adkipnis/metabench/zip/refs/heads/main
run tinybenchmarks-bundle archive tinybenchmarks-bundle https://codeload.github.com/felipemaiapolo/tinyBenchmarks/zip/refs/heads/main
run pythia-evals archive pythia-evals https://codeload.github.com/EleutherAI/pythia/zip/refs/heads/main
run helm-summaries python3 download_helm_summaries.py

python3 - <<'PY'
from pathlib import Path
import hashlib,json,datetime
root=Path('public-data')
files=[]
for p in sorted(root.rglob('*')):
    if not p.is_file() or '.cache' in p.parts or 'logs' in p.parts or p.suffix=='.part' or p.name=='host-download-manifest.json':
        continue
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest()))
(root/'host-download-manifest.json').write_text(json.dumps(dict(completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=files),indent=2)+'\n')
print('Completed files hashed in public-data/host-download-manifest.json')
PY
cat "$status"
if grep -q 'failed' "$status"; then exit 2; fi
