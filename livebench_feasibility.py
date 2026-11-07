# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2.0", "pyarrow>=17"]
# ///
"""Audit public LiveBench coverage. No inference, credentials, or internal data.

uv run livebench_feasibility.py                 # acquire once, then audit
uv run livebench_feasibility.py --offline       # replay checksum-verified inputs
uv run livebench_feasibility.py --refresh       # discover a new public snapshot
uv run livebench_feasibility.py --self-check    # synthetic checks, no network
"""

import argparse
import ast
import csv
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import hashlib
import html
import io
import itertools
import json
import math
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent / "feasibility" / "livebench"
CATEGORIES = ("coding", "data_analysis", "instruction_following", "math", "reasoning", "language")
HF = "https://huggingface.co"
GH = "https://api.github.com/repos/LiveBench"


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Sources:
    """A manifest pins discovery responses as well as original file bytes."""

    def __init__(self, root, offline=False, refresh=False):
        self.root, self.offline, self.refresh = root, offline, refresh
        self.path = root / "manifest.json"
        self.manifest = json.loads(self.path.read_text()) if self.path.exists() else {"sources": [], "errors": []}

    def get(self, url, **meta):
        old = next((s for s in reversed(self.manifest["sources"]) if s["url"] == url), None)
        if old and (not self.refresh or meta.get("revision")):
            data = (self.root / old["cache"]).read_bytes()
            if sha(data) != old["sha256"]:
                raise ValueError(f"Checksum mismatch: {old['cache']}")
            return data
        if self.offline:
            raise FileNotFoundError(f"Not cached: {url}")
        request = urllib.request.Request(url, headers={"User-Agent": "livebench-feasibility/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()
            final_url = response.url
            # Discovery must be complete, including paginated commit listings.
            if 'rel="next"' in response.headers.get("Link", ""):
                raise ValueError(f"Paginated response requires follow-up; refusing partial inventory: {url}")
        digest = sha(data)
        cache = f"cache/{digest}"
        target = self.root / cache
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entry = dict(url=url, resolved_url=final_url, cache=cache, sha256=digest,
                     retrieved_at=datetime.now(timezone.utc).isoformat(), **meta)
        self.manifest["sources"].append(entry)
        dump(self.path, self.manifest)
        return data

    def json(self, url, **meta):
        return json.loads(self.get(url, **meta))

    def attempt(self, name, action):
        try:
            action()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.manifest["errors"].append({"source": name, "error": str(exc)})
            dump(self.path, self.manifest)
            print(f"Unavailable: {name}: {exc}", flush=True)


def acquire(sources):
    """Fetch original files; never import or execute downloaded code."""
    sources.manifest["errors"] = []
    for dataset in ("model_judgment", *CATEGORIES):
        def fetch_dataset(dataset=dataset):
            base = f"{HF}/api/datasets/livebench/{dataset}"
            info = sources.json(base, kind="hf-info", dataset=dataset)
            history = sources.json(base + "/commits/main", kind="hf-history", dataset=dataset)
            revisions = {info["sha"]: None}
            revisions.update({c["id"]: c.get("date") for c in history})
            for revision, committed_at in revisions.items():
                version = sources.json(base + f"/revision/{revision}", kind="hf-version",
                                       dataset=dataset, revision=revision, committed_at=committed_at)
                license_info = (version.get("cardData") or {}).get("license", "unspecified")
                for item in version.get("siblings", []):
                    filename = item["rfilename"]
                    if filename == "README.md" or filename.endswith(".parquet"):
                        url = f"{HF}/datasets/livebench/{dataset}/resolve/{revision}/{urllib.parse.quote(filename)}"
                        sources.get(url, kind="hf-data" if filename.endswith(".parquet") else "hf-card",
                                    dataset=dataset, revision=revision, filename=filename,
                                    committed_at=committed_at, license=license_info, current=revision == info["sha"])
        sources.attempt(f"HF/{dataset}", fetch_dataset)
    for repository in ("LiveBench", "livebench.github.io"):
        def fetch_repository(repository=repository):
            base = f"{GH}/{repository}"
            commit = sources.json(base + "/commits/main", kind="github-head", repository=repository)
            revision = commit["sha"]
            tree = sources.json(base + f"/git/trees/{revision}?recursive=1", kind="github-tree",
                                repository=repository, revision=revision)
            if tree.get("truncated"):
                raise ValueError("Truncated GitHub tree")
            for item in tree["tree"]:
                path = item["path"]
                wanted = path in {"README.md", "LICENSE", "changelog.md", "livebench/common.py",
                                  "livebench/show_livebench_result.py", "src/Table/modelLinks.js"}
                wanted |= bool(re.fullmatch(r"public/(table_.*\.csv|categories_.*\.json)", path))
                wanted |= path.startswith("livebench/model/model_configs/") and path.endswith((".yaml", ".yml"))
                if wanted and item["type"] == "blob":
                    url = f"https://raw.githubusercontent.com/LiveBench/{repository}/{revision}/{path}"
                    sources.get(url, kind="github-file", repository=repository, revision=revision,
                                filename=path, license="see repository LICENSE; data terms require separate review")
        sources.attempt(f"GitHub/{repository}", fetch_repository)
    dump(sources.path, sources.manifest)


def read_source(root, entry):
    data = (root / entry["cache"]).read_bytes()
    if sha(data) != entry["sha256"]:
        raise ValueError(f"Checksum mismatch: {entry['cache']}")
    return data


def rows(root, entry):
    import pyarrow.parquet as pq
    parquet = pq.ParquetFile(io.BytesIO(read_source(root, entry)))
    # Coding test-case payloads can be hundreds of MB; coverage needs metadata only.
    needed = {"question_id", "task", "category", "turns", "ground_truth", "livebench_release_date",
              "livebench_removal_date", "model", "score", "turn", "tstamp"}
    columns = [name for name in parquet.schema_arrow.names if name in needed]
    return parquet.read(columns=columns).to_pylist()


def iso(value, optional=False):
    if optional and value in (None, ""):
        return ""
    text = str(value)[:10]
    date.fromisoformat(text)
    return text


def question_catalog(question_rows):
    catalog, conflicts = {}, set()
    for row in question_rows:
        if not row.get("livebench_release_date"):
            # Early archives predate release metadata; do not invent membership dates.
            continue
        q = {"question_id": str(row["question_id"]), "task": row["task"], "category": row["category"],
             "release": iso(row["livebench_release_date"]), "removal": iso(row.get("livebench_removal_date"), True)}
        if not q["question_id"] or any(not isinstance(q[k], str) or not q[k] for k in ("task", "category")):
            raise ValueError("Question requires nonempty ID, task and category")
        if q["removal"] and q["removal"] < q["release"]:
            raise ValueError(f"Question removed before release: {q['question_id']}")
        # Same ID with changed prompt/answer is not an unchanged anchor item.
        q["content_hash"] = sha(json.dumps({k: row.get(k) for k in ("turns", "ground_truth", "task", "category")},
                                          sort_keys=True, default=str).encode())
        previous = catalog.get(q["question_id"])
        if previous:
            if any(previous[k] != q[k] for k in ("release", "content_hash", "category", "task")):
                conflicts.add(q["question_id"])
            if previous["removal"] and q["removal"] and previous["removal"] != q["removal"]:
                conflicts.add(q["question_id"])
            # A later announcement of retirement completes the item's lifecycle.
            q["removal"] = q["removal"] or previous["removal"]
        catalog[q["question_id"]] = q
    return catalog, conflicts


def judgments(judgment_rows, catalog):
    selected, conflicts, seen = {}, set(), set()
    issues = Counter()
    for row in judgment_rows:
        signature = json.dumps(row, sort_keys=True, default=str)
        if signature in seen:
            issues["exact_duplicates"] += 1
            continue
        seen.add(signature)
        qid = str(row["question_id"])
        model = row["model"]
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Empty or non-string model identity")
        key = (model, qid)
        score = float(row["score"])
        if score == -1:
            issues["unscored_sentinel"] += 1
            continue
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"Invalid score for {key}: {score}")
        if qid not in catalog:
            issues["unmatched_questions"] += 1
            continue
        q = catalog[qid]
        if (row["task"], row["category"]) != (q["task"], q["category"]):
            issues["task_category_mismatch"] += 1
            conflicts.add(key)
        if key in selected:
            # Upstream averages rows without identifying runs; do not pick a latest run.
            conflicts.add(key)
            issues["repeated_evaluations"] += 1
        else:
            selected[key] = score
    for key in conflicts:
        selected.pop(key, None)
    issues["conflicted_model_items"] = len(conflicts)
    return selected, dict(issues), conflicts


def active_questions(catalog, release, releases):
    return {qid: q for qid, q in catalog.items() if q["release"] in releases and q["release"] <= release
            and (not q["removal"] or q["removal"] > release)}


def family(model):
    # shortcut: name prefixes are only a concentration diagnostic; verify ancestry before inference.
    match = re.match(r"(?:[^/]+/)?([a-z]+(?:-[a-z]+)?)", model.lower())
    return match[1] if match else "unknown"


def make_panel(catalog, scores, releases, release):
    questions = active_questions(catalog, release, releases)
    tasks = sorted({f"{q['category']}/{q['task']}" for q in questions.values()})
    expected = {t: {qid for qid, q in questions.items() if f"{q['category']}/{q['task']}" == t} for t in tasks}
    models = sorted({m for m, qid in scores if qid in questions})
    values, counts = {}, {}
    for model in models:
        for task in tasks:
            available = [scores[model, q] for q in expected[task] if (model, q) in scores]
            counts[model, task] = len(available)
            # No renormalization over partially answered tasks in the primary matrix.
            values[model, task] = sum(available) / len(available) if len(available) == len(expected[task]) else None
    return dict(release=release, questions=questions, tasks=tasks, models=models, expected=expected,
                values=values, counts=counts)


def diagnostic(panel, tasks):
    import numpy as np
    models = [m for m in panel["models"] if all(panel["values"][m, t] is not None for t in tasks)]
    x = np.array([[panel["values"][m, t] for t in tasks] for m in models], dtype=float).reshape(len(models), len(tasks))
    varying = np.std(x, axis=0) > 1e-12 if models else np.zeros(len(tasks), dtype=bool)
    rank = None
    correlation_mean, correlation_min, pc1_share = None, None, None
    if len(models) >= 2 and varying.any():
        correlation = np.corrcoef(x[:, varying], rowvar=False).reshape(int(varying.sum()), -1)
        rank = int(np.linalg.matrix_rank(correlation))
        pc1_share = float(np.linalg.eigvalsh(correlation)[-1] / varying.sum())
        if varying.sum() > 1:
            pairs = correlation[np.triu_indices(int(varying.sum()), 1)]
            correlation_mean, correlation_min = float(pairs.mean()), float(pairs.min())
    categories = {t.split("/")[0] for t, keep in zip(tasks, varying) if keep}
    n, p = len(models), int(varying.sum())
    families = Counter(family(m) for m in models)
    return dict(models=n, tasks=len(tasks), varying_tasks=p, categories=len(categories), correlation_rank=rank,
                mean_task_correlation=correlation_mean, minimum_task_correlation=correlation_min,
                pc1_variance_share=pc1_share,
                screen_pass=p >= 8 and len(categories) >= 4 and n >= max(50, 5 * p),
                largest_family_share=max(families.values(), default=0) / n if n else None,
                saturated_tasks=[t for j, t in enumerate(tasks) if n and ((x[:, j] >= .95).mean() >= .9)],
                constant_tasks=[t for t, keep in zip(tasks, varying) if not keep], model_ids=models, task_ids=list(tasks))


def shortlist(panel):
    tasks = panel["tasks"][:]
    candidates = []
    while tasks:
        d = diagnostic(panel, tasks)
        candidates.append(d)
        if len(tasks) <= 8:
            break
        # Greedy coverage-only pruning; correlations and factor fit never select tasks.
        drop = max(tasks, key=lambda t: (sum(all(panel["values"][m, s] is not None for s in tasks if s != t)
                                                for m in panel["models"]),
                                        len({s.split("/")[0] for s in tasks if s != t}), t))
        tasks.remove(drop)
    return sorted(candidates, key=lambda d: (d["screen_pass"], d["models"] * d["varying_tasks"], d["varying_tasks"]), reverse=True)[:3]


def write_csv(path, names, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def heatmap(path, panels):
    tasks = sorted({t for p in panels for t in p["tasks"]})
    width, height = 260 + 36 * len(panels), 80 + 22 * len(tasks)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img" aria-label="Share of models with complete item coverage by release and task">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="10" y="20" font-size="13">Complete item coverage (0–100%); gray = absent task</text>']
    for j, panel in enumerate(panels):
        x = 255 + j * 36
        out.append(f'<text x="{x}" y="70" font-size="9" transform="rotate(-60 {x} 70)">{panel["release"]}</text>')
        for i, task in enumerate(tasks):
            fraction = sum(panel["values"].get((m, task)) is not None for m in panel["models"]) / len(panel["models"]) if panel["models"] else 0
            color = f'rgb({int(240 - fraction * 200)},{int(245 - fraction * 105)},230)' if task in panel["tasks"] else '#ddd'
            y = 80 + i * 22
            out.append(f'<rect x="{x}" y="{y}" width="34" height="20" fill="{color}"><title>{html.escape(task)}: {fraction:.1%}</title></rect>')
    for i, task in enumerate(tasks):
        out.append(f'<text x="5" y="{95 + i * 22}" font-size="11">{html.escape(task)}</text>')
    path.write_text("\n".join(out + ["</svg>"]) + "\n")


def verify_published(root, sources, panels):
    """Compare exact IDs only; never guess that similarly named models are aliases."""
    checks = []
    if not panels:
        return checks
    panel = panels[-1]
    suffix = panel["release"].replace("-", "_")
    tables = [s for s in sources if s.get("filename") == f"public/table_{suffix}.csv"]
    if not tables:
        return checks
    published = list(csv.DictReader(io.StringIO(read_source(root, tables[-1]).decode())))
    for row in sorted(published, key=lambda r: r.get("model", "")):
        model = row.get("model")
        if model not in panel["models"] or not all(panel["values"][model, t] is not None for t in panel["tasks"]):
            continue
        published_tasks = {}
        for task in panel["tasks"]:
            column = task.split("/", 1)[1]
            if row.get(column, "") == "":
                checks.append(dict(release=panel["release"], model=model, field=column,
                                   computed=100 * panel["values"][model, task], published=None, passed=False))
                continue
            value = float(row[column])
            places = len(row[column].split(".")[1]) if "." in row[column] else 0
            delta = abs(100 * panel["values"][model, task] - value)
            checks.append(dict(release=panel["release"], model=model, field=column,
                               computed=100 * panel["values"][model, task], published=value,
                               passed=delta <= .5 * 10 ** -places + 1e-8))
            published_tasks[task] = (value, .5 * 10 ** -places)
        for category in sorted({t.split("/")[0] for t in panel["tasks"]}):
            tasks = [t for t in panel["tasks"] if t.startswith(category + "/")]
            if all(t in published_tasks for t in tasks):
                expected = sum(published_tasks[t][0] for t in tasks) / len(tasks)
                computed = sum(100 * panel["values"][model, t] for t in tasks) / len(tasks)
                tolerance = sum(published_tasks[t][1] for t in tasks) / len(tasks)
                checks.append(dict(release=panel["release"], model=model, field=f"category:{category}",
                                   computed=computed, published=expected, passed=abs(expected - computed) <= tolerance + 1e-8))
        if len({r["model"] for r in checks}) >= 3:
            break
    return checks


def release_ledger(root, sources, releases, panels):
    changes, exports = {}, {}
    for source in sources:
        path = source.get("filename", "")
        if path == "changelog.md":
            text = read_source(root, source).decode()
            for section in re.split(r"(?m)^### ", text)[1:]:
                heading, _, body = section.partition("\n")
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", heading.strip()):
                    changes[heading.strip()] = body.strip()
        match = re.fullmatch(r"public/table_(\d{4}_\d{2}_\d{2})\.csv", path)
        if match:
            table = list(csv.DictReader(io.StringIO(read_source(root, source).decode())))
            exports[match[1].replace("_", "-")] = dict(
                url=source["url"], revision=source["revision"], rows=len(table),
                tasks=sorted(k for k in (table[0] if table else []) if k != "model"))
    ledger = []
    for release in sorted(set(releases) | set(exports) | set(changes)):
        panel = next((p for p in panels if p["release"] == release), None)
        export = exports.get(release)
        available = {t.split("/", 1)[1] for t in panel["tasks"]} if panel else set()
        expected = set(export["tasks"]) if export else set()
        ledger.append(dict(release=release, changelog=changes.get(release, "not documented in acquired changelog"),
                           published_export=export, retrospective_questions=len(panel["questions"]) if panel else 0,
                           tasks_missing_from_questions=sorted(expected - available),
                           tasks_missing_from_export=sorted(available - expected) if export else [],
                           task_name_match=expected == available if export and panel else None,
                           as_published_snapshot="not established; dated exports may be revised"))
    return ledger


def analyze(root, manifest):
    sources = manifest["sources"]
    for source in sources:
        read_source(root, source)
    # Last acquired metadata identifies current files; older revisions stay in the manifest.
    heads = {s["dataset"]: json.loads(read_source(root, s))["sha"] for s in sources if s.get("kind") == "hf-info"}
    files = {s["url"]: s for s in sources}.values()
    for path in (root / "matrices").glob("????-??-??.csv"):
        path.unlink()
    question_rows, judgment_rows, histories = [], [], []
    judgment_archives, archive_dates = defaultdict(list), {}
    for source in files:
        if source.get("kind") != "hf-data":
            continue
        data = rows(root, source)
        if source["dataset"] == "model_judgment":
            judgment_archives[source["revision"]].extend(data)
            archive_dates[source["revision"]] = source.get("committed_at")
            histories.append(dict(revision=source["revision"], committed_at=source.get("committed_at"),
                                  filename=source["filename"], rows=len(data), models=len({r["model"] for r in data})))
            if source["revision"] == heads.get("model_judgment"):
                judgment_rows.extend(data)
        else:
            question_rows.extend(data)
    catalog, changed_questions = question_catalog(question_rows)
    scores, issues, conflicts = judgments(judgment_rows, catalog)
    releases = set()
    for source in files:
        if source.get("filename") == "livebench/common.py":
            for node in ast.walk(ast.parse(read_source(root, source).decode())):
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "LIVE_BENCH_RELEASES" for t in node.targets):
                    releases.update(iso(x) for x in ast.literal_eval(node.value))
    release_origin = "pinned upstream release registry"
    if not releases:
        releases = {q["release"] for q in catalog.values()} | {q["removal"] for q in catalog.values() if q["removal"]}
        release_origin = "question dates only; upstream registry unavailable"
    # Changed item metadata is explicitly excluded, never silently treated as a stable anchor.
    clean_catalog = {qid: q for qid, q in catalog.items() if qid not in changed_questions}
    scores = {key: value for key, value in scores.items() if key[1] in clean_catalog}
    panels = [make_panel(clean_catalog, scores, releases, release) for release in sorted(releases)]
    panels = [p for p in panels if p["questions"]]
    archived_panels = []
    for revision, archive_rows in sorted(judgment_archives.items()):
        committed_at = archive_dates[revision]
        available_releases = [r for r in releases if committed_at and r <= committed_at[:10]]
        if not available_releases:
            continue
        archive_scores, archive_issues, _ = judgments(archive_rows, clean_catalog)
        panel = make_panel(clean_catalog, archive_scores, releases, max(available_releases))
        if panel["models"] and panel["tasks"]:
            archived_panels.append(dict(revision=revision, committed_at=committed_at,
                                        battery=panel["release"], issues=archive_issues,
                                        full_panel=diagnostic(panel, panel["tasks"]),
                                        candidates=shortlist(panel)))
    summaries, candidates, cells, overlaps = [], [], [], []
    for panel in panels:
        d = diagnostic(panel, panel["tasks"])
        summaries.append(dict(release=panel["release"], questions=len(panel["questions"]),
                              observed_models=len(panel["models"]), **{k: v for k, v in d.items() if k not in ("model_ids", "task_ids")}))
        candidates.extend(dict(release=panel["release"], candidate=i + 1, **d) for i, d in enumerate(shortlist(panel)))
        cells.extend(dict(release=panel["release"], model=m, task=t, score=panel["values"][m, t],
                          observed_items=panel["counts"][m, t], expected_items=len(panel["expected"][t]))
                     for m in panel["models"] for t in panel["tasks"])
        write_csv(root / "matrices" / f"{panel['release']}.csv", ["model", *panel["tasks"]],
                  [dict(model=m, **{t: panel["values"][m, t] for t in panel["tasks"]}) for m in panel["models"]])
    for left, right in itertools.combinations(panels, 2):
        common_tasks = sorted(set(left["tasks"]) & set(right["tasks"]))
        bridge_models = set(left["models"]) & set(right["models"])
        complete_bridge = [m for m in sorted(bridge_models) if common_tasks and all(
            p["values"][m, t] is not None for p in (left, right) for t in common_tasks)]
        overlaps.append(dict(left=left["release"], right=right["release"], shared_task_names=len(common_tasks),
                             identical_item_sets=sum(left["expected"][t] == right["expected"][t] for t in common_tasks),
                             shared_items=len(set(left["questions"]) & set(right["questions"])),
                             shared_model_ids=len(bridge_models), complete_bridge_models=len(complete_bridge),
                             verified_task_definitions="not established by task names", verified_configurations="unresolved"))
    checks = verify_published(root, list(files), panels)
    ledger = release_ledger(root, list(files), releases, panels)
    issues["changed_question_metadata"] = len(changed_questions)
    issues["undated_question_rows"] = sum(not row.get("livebench_release_date") for row in question_rows)
    verified_releases = {entry["release"] for entry in ledger if entry["task_name_match"] is True}
    historical_panels = [p for p in panels if p["release"] in verified_releases]
    span = (date.fromisoformat(historical_panels[-1]["release"]) - date.fromisoformat(historical_panels[0]["release"])).days if historical_panels else 0
    historical_screen = len(historical_panels) >= 3 and span >= 365
    for left, right in zip(historical_panels, historical_panels[1:]):
        bridge = next(o for o in overlaps if (o["left"], o["right"]) == (left["release"], right["release"]))
        historical_screen &= bridge["complete_bridge_models"] >= 20 and bridge["shared_task_names"] >= 8
    status = "blocked" if not panels or not judgment_rows else "partial" if manifest["errors"] else "measured"
    result = dict(status=status, release_origin=release_origin, historical_coverage_screen=bool(historical_screen),
                  release_span_days=span, export_matched_releases=sorted(verified_releases),
                  latest_score_pool=dict(rows=len(judgment_rows), models=len({r["model"] for r in judgment_rows}),
                                         categories=dict(Counter(r["category"] for r in judgment_rows))),
                  issues=issues, releases=summaries, candidates=candidates, overlaps=overlaps,
                  published_checks=checks, archived_judgment_files=histories,
                  historical_score_panels=archived_panels,
                  release_ledger=ledger,
                  unresolved_configuration_ids=sorted({m for m, _ in scores}),
                  changed_question_ids=sorted(changed_questions),
                  conflict_keys=[list(k) for k in sorted(conflicts)])
    dump(root / "audit.json", result)
    dump(root / "release_ledger.json", ledger)
    write_csv(root / "coverage.csv", ["release", "model", "task", "score", "observed_items", "expected_items"], cells)
    write_csv(root / "overlap.csv", ["left", "right", "shared_task_names", "identical_item_sets", "shared_items", "shared_model_ids", "complete_bridge_models", "verified_task_definitions", "verified_configurations"], overlaps)
    write_csv(root / "published_checks.csv", ["release", "model", "field", "computed", "published", "passed"], checks)
    write_csv(root / "source_inventory.csv", ["kind", "dataset", "repository", "revision", "filename", "url", "sha256", "retrieved_at", "license"], sources)
    heatmap(root / "coverage.svg", panels)
    report(root, manifest, result)
    return result


def report(root, manifest, result):
    blocked = result["status"] == "blocked"
    passed = [c for c in result["candidates"] if c["screen_pass"]]
    checks = result["published_checks"]
    validated = len({c["model"] for c in checks}) >= 3 and all(c["passed"] for c in checks)
    lines = ["# LiveBench longitudinal gAI feasibility", "",
             "**Status: blocked — original score/question files could not be acquired.**" if blocked else
             f"**Status: {result['status']}; interpretation remains conditional on configuration and version review.**", "",
             "## Verdict", "",
             "- Latest-pool analysis: **undetermined**; no coverage claim is supported yet." if blocked else
             f"- Latest-pool analysis: **{'suitable with limitations' if passed else 'insufficient coverage against initial screening targets'}**; {len(passed)} candidate panels pass the numerical screen.",
             "- Future repeatability: checksum-verified replay is implemented. Continuing availability, complete publication and configuration stability are not established.",
             f"- Published-score validation: **{'passed' if validated else 'pending or failed'}** ({len(set(c['model'] for c in checks))} configurations checked).", "",
             f"Historical coverage screen: {result['historical_coverage_screen']}; {len(result['export_matched_releases'])} export-matched batteries spanning {result['release_span_days']} days. Bridge IDs are not yet verified equivalent configurations.", "",
             f"Latest judgment pool: {result['latest_score_pool']['rows']:,} rows, {result['latest_score_pool']['models']} exact model IDs; category counts: {result['latest_score_pool']['categories']}.", "",
             "## Measured coverage", "",
             "Release | Questions | Observed models | Complete models | Varying tasks | Categories | Screen",
             "--- | ---: | ---: | ---: | ---: | ---: | ---"]
    for r in result["releases"]:
        lines.append(f"{r['release']} | {r['questions']} | {r['observed_models']} | {r['models']} | {r['varying_tasks']} | {r['categories']} | {r['screen_pass']}")
    if blocked:
        lines += ["", "No rows measured. Empty CSVs and the empty heatmap indicate unavailable inputs, not zero public coverage."]
    lines += ["", "See `audit.json` for candidate model/task lists, exclusions, concentration, saturation and matrix rank; `overlap.csv` for release bridges; `coverage.svg` for item-complete coverage. Initial documentation observations and download failures are in [source_notes.md](source_notes.md).", "",
              "## Archived score pools", "",
              "Each archive is checked separately against the newest battery predating its commit. Question metadata is reconstructed today; these are not verified as-published snapshots. Duplicate commits do not constitute independent cohorts.", "",
              "Score commit | Battery | Complete models | Tasks | Categories | Mean task correlation | PC1 variance | Full-panel screen",
              "--- | --- | ---: | ---: | ---: | ---: | ---: | ---"]
    for archive in sorted(result["historical_score_panels"], key=lambda a: a["committed_at"]):
        d = archive["full_panel"]
        correlation = f"{d['mean_task_correlation']:.3f}" if d["mean_task_correlation"] is not None else "n/a"
        variance = f"{d['pc1_variance_share']:.1%}" if d["pc1_variance_share"] is not None else "n/a"
        lines.append(f"{archive['committed_at'][:10]} ({archive['revision'][:8]}) | {archive['battery']} | {d['models']} | {d['varying_tasks']} | {d['categories']} | {correlation} | {variance} | {d['screen_pass']}")
    archived_passes = [a for a in result["historical_score_panels"] if any(c["screen_pass"] for c in a["candidates"])]
    lines += ["", f"{len(archived_passes)} archived score revisions have a shortlisted panel passing the numerical pilot screen. Multiple revisions may contain the same data. PC1 is an exploratory principal component, not an estimated latent g factor or evidence of intelligence growth."]
    lines += ["",
              "## Interpretation", "",
              "- These are retrospective batteries reconstructed from the latest acquired judgment pool and archived question metadata. They are not as-published historical snapshots or model-release cohorts.",
              "- Historical judgment revisions are inventoried separately in `audit.json`; a repository commit date is evidence provenance, not an evaluation date or benchmark release date.",
              "- `release_ledger.json` preserves acquired changelog entries, dated export availability and mismatches between public subtask exports and reconstructed question batteries. Release labels alone do not establish comparability.",
              "- All exact model IDs are retained. Configuration equivalence, release dates and family ancestry require verification before cohort-level inference. Family prefixes are only a diagnostic.",
              "- Exact duplicate rows collapse; unresolved repeated evaluations are excluded by model/item. Sentinel -1 means unscored; zero remains a valid scored failure. Changed question metadata is excluded conservatively.",
              "- Task means require all active items. Task names do not prove stable prompts, scoring, agent setup or difficulty; identical item sets are reported separately.",
              "- Screening targets: 8 varying tasks, 4 categories and max(50, 5 × varying tasks) complete configurations. Historical target: 3 releases across 12 months and 20 complete bridge IDs per compared pair. These are feasibility heuristics, not power calculations.",
              "- Published validation compares task means against the public subtask table and category means against equal-task averages of that table; category values are derived references, not a second independent publication.",
              "- Coverage-only greedy task pruning shortlists candidates; it does not exhaustively search for the globally largest complete matrix.",
              "- Mean correlations and PC1 variance describe each observed sample. Task sets and model populations change between rows; differences are not estimates of temporal change in gAI. No model-release cohorts or uncertainty intervals have been constructed.",
              "- Public visibility is not a blanket redistribution license. Source license fields and original README/LICENSE files remain authoritative; raw cache is ignored by git.", "",
              "## Acquisition failures", ""]
    lines += [f"- {e['source']}: `{e['error']}`" for e in manifest["errors"]] or ["None recorded."]
    lines += ["", "## Next experiment", "",
              "Acquire the missing original inputs on a network-enabled host, rerun offline, and reproduce three published configurations before fitting factors." if blocked else
              "Review the largest passing panels and their shared item/setting definitions. Verify model ancestry and settings, then fit a one-factor pilot on the largest comparable panel; do not infer temporal changes from release labels alone.", "",
              "If LiveBench lacks sufficient bridges, test HELM for versioned scenario overlap or the archived HF leaderboards for a larger common-battery model population. Neither source repairs missing LiveBench history automatically.", "",
              "## Reproduce", "", "```sh", "uv run livebench_feasibility.py --refresh",
              "uv run livebench_feasibility.py --offline", "uv run livebench_feasibility.py --self-check", "```", "",
              "No factor fitting, new model evaluations, publication, or internal benchmark access was performed."]
    (root / "README.md").write_text("\n".join(lines) + "\n")


def self_check():
    qrows = [dict(question_id="a", task="t", category="math", ground_truth="x", turns=["x"],
                  livebench_release_date="2024-06-24", livebench_removal_date="2024-08-31"),
             dict(question_id="b", task="t", category="math", ground_truth="y", turns=["y"],
                  livebench_release_date="2024-08-31", livebench_removal_date="")]
    catalog, changed = question_catalog(qrows)
    assert not changed
    releases = {"2024-06-24", "2024-08-31"}
    assert set(active_questions(catalog, "2024-06-24", releases)) == {"a"}
    assert set(active_questions(catalog, "2024-08-31", releases)) == {"b"}
    row = dict(model="M", question_id="a", score=0, task="t", category="math", turn=1, tstamp=1)
    selected, issues, conflicts = judgments([row, row], catalog)
    assert selected == {("M", "a"): 0} and issues["exact_duplicates"] == 1
    assert judgments([row, dict(row, score=1, tstamp=2)], catalog)[0] == {}
    assert judgments([dict(row, score=-1)], catalog)[0] == {}
    assert judgments([dict(row, question_id="missing")], catalog)[1]["unmatched_questions"] == 1
    assert judgments([dict(row, task="wrong")], catalog)[2] == {("M", "a")}
    for invalid in [float("nan"), float("inf"), -2, 1.1]:
        try:
            judgments([dict(row, score=invalid)], catalog)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Accepted invalid score {invalid}")
    assert question_catalog(qrows + [dict(qrows[0], ground_truth="changed")])[1] == {"a"}
    assert question_catalog([dict(qrows[0], livebench_release_date=None)])[0] == {}
    retired, changed = question_catalog([dict(qrows[0], livebench_removal_date=""), qrows[0]])
    assert not changed and retired["a"]["removal"] == "2024-08-31"
    panel = make_panel(catalog, {("M", "a"): 0}, releases, "2024-06-24")
    assert panel["values"]["M", "math/t"] == 0
    two = dict(catalog, c=dict(catalog["a"], question_id="c"))
    assert make_panel(two, {("M", "a"): 0}, releases, "2024-06-24")["values"]["M", "math/t"] is None
    assert diagnostic(panel, panel["tasks"])["varying_tasks"] == 0
    broad = dict(tasks=[f"c{i // 4}/t{i}" for i in range(16)], models=[f"m{m}" for m in range(60)])
    broad["values"] = {(model, task): ((m + i) % 61) / 60 for m, model in enumerate(broad["models"])
                       for i, task in enumerate(broad["tasks"])}
    assert any(candidate["screen_pass"] and candidate["categories"] == 4 for candidate in shortlist(broad))
    common = dict(tasks=["a/x", "b/y"], models=["m1", "m2", "m3"],
                  values={(m, t): i / 2 for i, m in enumerate(["m1", "m2", "m3"]) for t in ["a/x", "b/y"]})
    stats = diagnostic(common, common["tasks"])
    assert abs(stats["mean_task_correlation"] - 1) < 1e-12 and abs(stats["pc1_variance_share"] - 1) < 1e-12
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        manifest = {"sources": [], "errors": [{"source": "synthetic", "error": "fixture only"}]}
        analyze(root, manifest)
        before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        analyze(root, manifest)
        assert before == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        (root / "cache").mkdir()
        (root / "cache" / "test").write_bytes(b"changed")
        try:
            read_source(root, {"cache": "cache/test", "sha256": sha(b"original")})
        except ValueError:
            pass
        else:
            raise AssertionError("Accepted tampered cache")
    # Exercise real Parquet decoding, the populated analysis path, exports and validation.
    import pyarrow as pa
    import pyarrow.parquet as pq
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        manifest = {"sources": [], "errors": []}

        def cache(data, **meta):
            entry = dict(url=f"https://fixture.invalid/{len(manifest['sources'])}", cache=f"cache/{sha(data)}",
                         sha256=sha(data), retrieved_at="synthetic", **meta)
            path = root / entry["cache"]
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
            manifest["sources"].append(entry)

        questions = [dict(question_id=f"q{i}", task=f"t{i}", category=f"c{i % 4}", turns=[f"prompt{i}"],
                          ground_truth="answer", livebench_release_date="2024-06-24", livebench_removal_date="") for i in range(8)]
        data = [dict(model=f"family{m}/model", question_id=f"q{i}", task=f"t{i}", category=f"c{i % 4}",
                     score=((m * (i + 1)) % 61) / 60, turn=1, tstamp=1) for m in range(60) for i in range(8)]
        for dataset, records in [("math", questions), ("model_judgment", data)]:
            buffer = io.BytesIO()
            pq.write_table(pa.Table.from_pylist(records), buffer)
            cache(buffer.getvalue(), kind="hf-data", dataset=dataset, revision="fixture", filename="data.parquet",
                  committed_at="2026-06-26T00:00:00Z")
            cache(b'{"sha":"fixture"}', kind="hf-info", dataset=dataset)
        cache(b"LIVE_BENCH_RELEASES = {'2024-06-24','2025-06-24','2026-06-25'}", kind="github-file", filename="livebench/common.py")
        table = io.StringIO()
        writer = csv.writer(table)
        writer.writerow(["model", *[f"t{i}" for i in range(8)]])
        for m in range(60):
            writer.writerow([f"family{m}/model", *[round(100 * ((m * (i + 1)) % 61) / 60, 3) for i in range(8)]])
        for release in ["2024_06_24", "2025_06_24", "2026_06_25"]:
            cache(table.getvalue().encode(), kind="github-file", revision="fixture", filename=f"public/table_{release}.csv")
        result = analyze(root, manifest)
        assert result["status"] == "measured" and result["historical_coverage_screen"]
        assert all(r["models"] == 60 and r["screen_pass"] for r in result["releases"])
        assert len(result["overlaps"]) == 3 and all(r["complete_bridge_models"] == 60 for r in result["overlaps"])
        assert len(result["published_checks"]) == 36 and all(r["passed"] for r in result["published_checks"])
        assert result["release_ledger"][-1]["task_name_match"] is True
        assert len(result["historical_score_panels"]) == 1 and result["historical_score_panels"][0]["full_panel"]["screen_pass"]
        before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        analyze(root, manifest)
        assert before == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    print("Self-check passed: membership, joins, duplicates, scores, missingness, checksums, deterministic replay.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    sources = Sources(args.out, args.offline, args.refresh)
    if args.offline and not sources.path.exists():
        parser.error("Offline replay requires an existing manifest.json")
    if not args.offline:
        acquire(sources)
    result = analyze(args.out, sources.manifest)
    print(f"{result['status']}: {args.out / 'README.md'}")
    return 2 if result["status"] != "measured" else 0


if __name__ == "__main__":
    raise SystemExit(main())
