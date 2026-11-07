# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy>=2", "scipy>=1.14", "matplotlib>=3.9", "pyarrow>=17"]
# ///
"""Public LiveBench latent analysis. Reads pinned local inputs; never downloads."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
import platform
from pathlib import Path
import subprocess
import textwrap

import numpy as np
import scipy
from scipy.optimize import linear_sum_assignment
from scipy.stats import rankdata

import livebench_feasibility as audit
from factor_models import standardize, corr, fit_higher_order, discover_groups, point_g_scores, paf, varimax


ROOT = Path(__file__).resolve().parent
PRIMARY = "81f6a1cd42f793285e215aabed4fd1c71a94889a"
BATTERY = "2024-07-26"
GROUP_REPS = 200
FIT_FIELDS = ("cfi", "rmsea", "aic", "bic", "g_variance_share", "ecv", "omega_total", "omega_h", "residual_rms")


def load_inputs(root):
    manifest = json.loads((root / "manifest.json").read_text())
    entries = {s["url"]: s for s in manifest["sources"]}.values()
    questions, archives, used = [], {}, []
    parquet_cache = {}
    for entry in entries:
        if entry.get("kind") != "hf-data":
            continue
        digest = entry["sha256"]
        if digest not in parquet_cache:
            parquet_cache[digest] = audit.rows(root, entry)
        records = parquet_cache[digest]
        used.append(entry)
        if entry["dataset"] == "model_judgment":
            revision = entry["revision"]
            archive = archives.setdefault(revision, dict(rows=[], date=entry.get("committed_at"), hashes=[]))
            archive["rows"].extend(records)
            archive["hashes"].append(digest)
        else:
            questions.extend(records)
    catalog, changed = audit.question_catalog(questions)
    catalog = {qid: row for qid, row in catalog.items() if qid not in changed}
    releases = {r["release"] for r in json.loads((root / "audit.json").read_text())["releases"]}
    for archive in archives.values():
        records = archive.pop("rows")
        if any(not {"task", "category"}.issubset(row) for row in records):
            archive["selected"], archive["issues"] = {}, {"unsupported_legacy_schema_rows": len(records)}
        else:
            archive["selected"], archive["issues"], _ = audit.judgments(records, catalog)
    if PRIMARY not in archives:
        raise ValueError("Pinned August 2024 score archive is missing")
    return dict(catalog=catalog, releases=releases, archives=archives, sources=used,
                changed_questions=sorted(changed), undated_question_rows=sum(not q.get("livebench_release_date") for q in questions))


def panel_view(inputs, revision, battery, tasks=None, models=None):
    scores = inputs["archives"][revision]["selected"]
    raw = audit.make_panel(inputs["catalog"], scores, inputs["releases"], battery)
    tasks = list(tasks or raw["tasks"])
    candidates = raw["models"] if models is None else models
    models = [m for m in candidates if all(raw["values"].get((m, t)) is not None for t in tasks)]
    if len(models) < 3 or len(tasks) < 3:
        raise ValueError("Insufficient complete models/tasks")
    item_ids = [sorted(raw["expected"][t]) for t in tasks]
    items = [np.array([[scores[m, qid] for qid in ids] for m in models]) for ids in item_ids]
    return dict(revision=revision, battery=battery, models=models, tasks=tasks,
                item_ids=item_ids, items=items, scores=np.column_stack([a.mean(axis=1) for a in items]))


def fit_summary(fit):
    return {**{k: float(getattr(fit, k)) for k in FIT_FIELDS}, "N": fit.N, "df": fit.df,
            "chi2": fit.chi2, "n_params": fit.n_params, "boundary": fit.boundary,
            "iterations": fit.iterations, "gradient_norm": fit.gradient_norm,
            "groups": fit.groups, "gamma": fit.gamma.tolist(), "theta": fit.theta.tolist(),
            "standardized_g": fit.standardized_g.tolist(),
            "standardized_group": fit.standardized_group.tolist(), "sigma": fit.sigma.tolist()}


def fit_panel(view, groups=None):
    x = view["scores"]
    R = corr(standardize(x))
    fit = fit_higher_order(R, len(x), groups or [list(range(x.shape[1]))])
    return fit, point_g_scores(standardize(x), R, fit)


def read_families(path, models):
    with path.open() as f:
        records = list(csv.DictReader(f))
    mapping = {r["model"]: r for r in records}
    if len(mapping) != len(records) or any(m not in mapping for m in models):
        raise ValueError("Family mapping must cover every primary model exactly once")
    clusters = defaultdict(list)
    for i, model in enumerate(models):
        row = mapping[model]
        if not row["family"] or (row["status"] != "unresolved-singleton" and not row["source"]):
            raise ValueError(f"Missing family provenance for {model}")
        clusters[row["family"]].append(i)
    for family, members in clusters.items():
        if len(members) > 1 and any(mapping[models[i]]["status"] == "unresolved-singleton" for i in members):
            raise ValueError(f"Unresolved identities must remain singleton clusters: {family}")
    return list(clusters.values()), [mapping[m] for m in models]


def resample_items(items, rng):
    # One draw per task is shared by all models: paired item outcomes stay paired.
    return np.column_stack([a[:, rng.integers(0, a.shape[1], a.shape[1])].mean(axis=1) for a in items])


def family_rows(clusters, rng):
    return np.concatenate([clusters[i] for i in rng.integers(0, len(clusters), len(clusters))])


def bootstrap(view, clusters, groups, reps, seed):
    n, p = view["scores"].shape
    result, diagnostics = {}, []
    seeds = np.random.SeedSequence(seed).spawn(3)
    for mode, stream in zip(("item", "family_item"), seeds):
        rng = np.random.default_rng(stream)
        result[mode] = {str(N): dict(loadings=np.full((reps, p), np.nan), scores=np.full((reps, n), np.nan),
                                     metrics=np.full((reps, len(FIT_FIELDS)), np.nan)) for N in (1, 3)}
        for rep in range(reps):
            cells = resample_items(view["items"], rng)
            rows = np.arange(n) if mode == "item" else family_rows(clusters, rng)
            try:
                R = corr(standardize(cells[rows]))
                Zfull = standardize(cells)
                Rfull = corr(Zfull)
            except ValueError as exc:
                for N in (1, 3):
                    diagnostics.append(dict(mode=mode, replicate=rep, N=N, status="invalid-matrix", detail=str(exc)))
                continue
            for N in (1, 3):
                if N == 3 and groups is None:
                    diagnostics.append(dict(mode=mode, replicate=rep, N=N, status="no-point-hierarchy", detail=""))
                    continue
                try:
                    fit = fit_higher_order(R, len(rows), [list(range(p))] if N == 1 else groups)
                    if fit.boundary:
                        diagnostics.append(dict(mode=mode, replicate=rep, N=N, status="boundary", detail=""))
                        continue
                    values = result[mode][str(N)]
                    values["loadings"][rep] = fit.standardized_g
                    values["scores"][rep] = point_g_scores(Zfull, Rfull, fit)
                    values["metrics"][rep] = [getattr(fit, k) for k in FIT_FIELDS]
                    diagnostics.append(dict(mode=mode, replicate=rep, N=N, status="ok", detail=""))
                except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
                    diagnostics.append(dict(mode=mode, replicate=rep, N=N, status="fit-failed", detail=str(exc)))
            if (rep + 1) % 100 == 0:
                print(f"{mode}: {rep + 1}/{reps}", flush=True)
    return result, diagnostics, seeds[2]


def rediscover(view, clusters, reference, stream):
    rng = np.random.default_rng(stream)
    p = len(view["tasks"])
    assignment = np.full((GROUP_REPS, p), -1, dtype=int)
    records = []
    for rep in range(GROUP_REPS):
        cells = resample_items(view["items"], rng)
        rows = family_rows(clusters, rng)
        row = dict(replicate=rep, status="invalid-matrix", selected=None, one_bic=None, hierarchy_bic=None)
        try:
            R = corr(standardize(cells[rows]))
            one = fit_higher_order(R, len(rows), [list(range(p))])
            if not one.boundary:
                row.update(one_bic=one.bic, selected=1)
            groups = discover_groups(R, 3)
            if groups is None:
                row["status"] = "nonviable-groups"
            else:
                hierarchy = fit_higher_order(R, len(rows), groups)
                row["status"] = "boundary" if hierarchy.boundary else "ok"
                if not hierarchy.boundary:
                    row["hierarchy_bic"] = hierarchy.bic
                    row["selected"] = 3 if row["one_bic"] is None or hierarchy.bic < one.bic else 1
                    if reference:
                        agreement = np.array([[len(set(a) & set(b)) for b in groups] for a in reference])
                        old, new = linear_sum_assignment(-agreement)
                        for a, b in zip(old, new):
                            assignment[rep, groups[b]] = a
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            row["status"] = str(exc)
        records.append(row)
        if (rep + 1) % 50 == 0:
            print(f"rediscovery: {rep + 1}/{GROUP_REPS}", flush=True)
    return records, assignment


def sensitivity(inputs, primary):
    fits, matched, seen = [], [], set()
    for revision, archive in sorted(inputs["archives"].items(), key=lambda pair: pair[1]["date"] or ""):
        identity = tuple(sorted(archive["hashes"]))
        if identity in seen:
            continue
        seen.add(identity)
        releases = [r for r in inputs["releases"] if archive["date"] and r <= archive["date"][:10]]
        if not releases:
            continue
        battery = max(releases)
        try:
            view = panel_view(inputs, revision, battery)
            variants = [("full-battery", view)]
            raw = audit.make_panel(inputs["catalog"], archive["selected"], inputs["releases"], battery)
            candidate = audit.shortlist(raw)[0]
            if candidate["screen_pass"] and candidate["task_ids"] != view["tasks"]:
                variants.append(("coverage-selected", panel_view(inputs, revision, battery, candidate["task_ids"])))
            for label, v in variants:
                R = corr(standardize(v["scores"]))
                groups = discover_groups(R, 3)
                for N in (1, 3):
                    if N == 3 and groups is None:
                        continue
                    try:
                        fit, _ = fit_panel(v, groups if N == 3 else None)
                        fits.append(dict(revision=revision, archive_date=archive["date"][:10], battery=battery,
                                         panel=label, models=len(v["models"]), tasks=len(v["tasks"]),
                                         domains=len({t.split('/')[0] for t in v["tasks"]}), **fit_summary(fit)))
                    except (ValueError, RuntimeError, np.linalg.LinAlgError):
                        continue
        except (ValueError, RuntimeError, np.linalg.LinAlgError):
            continue
    # Same battery, same tasks, same item IDs, same exact model IDs for each pair.
    revisions = ["86ad8e20dc53bbf2549d6fddd91e183f23525a6a", "65fce612236e865cb87e0917db64702d9c856459", PRIMARY]
    for left, right in zip(revisions, revisions[1:]):
        a, b = panel_view(inputs, left, BATTERY), panel_view(inputs, right, BATTERY)
        common = sorted(set(a["models"]) & set(b["models"]))
        a = panel_view(inputs, left, BATTERY, primary["tasks"], common)
        b = panel_view(inputs, right, BATTERY, primary["tasks"], common)
        if a["item_ids"] != b["item_ids"]:
            raise ValueError("Matched comparison has different question IDs")
        fa, sa = fit_panel(a)
        fb, sb = fit_panel(b)
        matched.append(dict(left=left, right=right, models=len(common), tasks=len(a["tasks"]),
                            shared_item_ids=sum(map(len, a["item_ids"])),
                            changed_item_scores=sum(int(np.count_nonzero(x != y)) for x, y in zip(a["items"], b["items"])),
                            max_task_mean_change=float(np.abs(a["scores"] - b["scores"]).max()),
                            left_g_variance=fa.g_variance_share, right_g_variance=fb.g_variance_share,
                            max_loading_change=float(np.abs(fa.standardized_g - fb.standardized_g).max()),
                            max_relative_score_change=float(np.abs(sa - sb).max()),
                            max_rank_change=float(np.abs(rankdata(-sa) - rankdata(-sb)).max())))
    return fits, matched


def intervals(values, reps):
    valid = np.isfinite(values).all(axis=1)
    if valid.sum() < .9 * reps:
        return None
    return np.percentile(values[valid], [2.5, 97.5], axis=0)


def export_results(out, view, fits, points, boot, diagnostics, discovery, assignments, metadata):
    n, p = view["scores"].shape
    audit.write_csv(out / "matrix.csv", ["model", *view["tasks"]],
                    [dict(model=m, **dict(zip(view["tasks"], row))) for m, row in zip(view["models"], view["scores"])])
    audit.dump(out / "items.json", dict(zip(view["tasks"], view["item_ids"])))
    statistics = []
    for mode, draws in boot.items():
        for N, fit in fits.items():
            values = draws[str(N)]["metrics"]
            ci = intervals(values, metadata["resamples"])
            valid = int(np.isfinite(values).all(axis=1).sum())
            for j, field in enumerate(FIT_FIELDS):
                statistics.append(dict(mode=mode, N=N, metric=field, point=getattr(fit, field),
                                       ci_low=ci[0, j] if ci is not None else None, ci_high=ci[1, j] if ci is not None else None,
                                       admissible=valid, attempted=metadata["resamples"]))
    audit.write_csv(out / "fit_statistics.csv", ["mode", "N", "metric", "point", "ci_low", "ci_high", "admissible", "attempted"], statistics)
    rows = []
    for mode, draws in boot.items():
        for N in (1, 3):
            fit = fits.get(N)
            ci = intervals(draws[str(N)]["loadings"], metadata["resamples"])
            for j, task in enumerate(view["tasks"]):
                rows.append(dict(mode=mode, N=N, task=task, loading=fit.standardized_g[j] if fit else None,
                                 ci_low=ci[0, j] if ci is not None else None, ci_high=ci[1, j] if ci is not None else None))
    audit.write_csv(out / "loadings.csv", ["mode", "N", "task", "loading", "ci_low", "ci_high"], rows)
    if 3 in fits:
        fit = fits[3]
        hierarchy = []
        for j, task in enumerate(view["tasks"]):
            group = next(k for k, members in enumerate(fit.groups) if j in members)
            hierarchy.append(dict(task=task, group=group + 1, group_to_g=fit.gamma[group],
                                  first_order_loading=fit.loadings[j, group] / np.sqrt(fit.sigma[j, j]),
                                  g_loading=fit.standardized_g[j], specific_loading=fit.standardized_group[j, group],
                                  standardized_uniqueness=fit.theta[j] / fit.sigma[j, j]))
        audit.write_csv(out / "hierarchy.csv", ["task", "group", "group_to_g", "first_order_loading", "g_loading", "specific_loading", "standardized_uniqueness"], hierarchy)
    score_rows = []
    for mode, draws in boot.items():
        one, hier = draws["1"]["scores"], draws["3"]["scores"]
        pair_valid = np.isfinite(one).all(axis=1) & np.isfinite(hier).all(axis=1)
        shift = np.full_like(one, np.nan)
        if pair_valid.any():
            shift[pair_valid] = rankdata(-hier[pair_valid], axis=1) - rankdata(-one[pair_valid], axis=1)
        shift_ci = intervals(shift, metadata["resamples"])
        for N in (1, 3):
            values = draws[str(N)]["scores"]
            ci = intervals(values, metadata["resamples"])
            ranks = np.full_like(values, np.nan)
            valid = np.isfinite(values).all(axis=1)
            ranks[valid] = rankdata(-values[valid], axis=1)
            rank_ci = intervals(ranks, metadata["resamples"])
            point_ranks = rankdata(-points[N]) if N in points else np.full(n, np.nan)
            for i, model in enumerate(view["models"]):
                score_rows.append(dict(mode=mode, N=N, model=model, score=points[N][i] if N in points else None,
                                       ci_low=ci[0, i] if ci is not None else None, ci_high=ci[1, i] if ci is not None else None,
                                       rank=point_ranks[i] if N in points else None,
                                       rank_low=rank_ci[0, i] if rank_ci is not None else None,
                                       rank_high=rank_ci[1, i] if rank_ci is not None else None,
                                       rank_shift=(point_ranks[i] - rankdata(-points[1])[i]) if N == 3 and N in points else None,
                                       shift_low=shift_ci[0, i] if N == 3 and shift_ci is not None else None,
                                       shift_high=shift_ci[1, i] if N == 3 and shift_ci is not None else None))
    audit.write_csv(out / "scores.csv", ["mode", "N", "model", "score", "ci_low", "ci_high", "rank", "rank_low", "rank_high", "rank_shift", "shift_low", "shift_high"], score_rows)
    audit.write_csv(out / "bootstrap_diagnostics.csv", ["mode", "replicate", "N", "status", "detail"], diagnostics)
    audit.write_csv(out / "rediscovery.csv", ["replicate", "status", "selected", "one_bic", "hierarchy_bic"], discovery)
    stability = []
    for j, task in enumerate(view["tasks"]):
        group = next((k for k, members in enumerate(metadata["groups"] or []) if j in members), None)
        valid = assignments[:, j] >= 0
        stability.append(dict(task=task, group=group + 1 if group is not None else None, valid_assignments=int(valid.sum()),
                              same_group_given_valid=float(np.mean(assignments[valid, j] == group)) if valid.any() else None,
                              same_group_all_draws=float(np.mean(assignments[:, j] == group)) if group is not None else None))
    audit.write_csv(out / "group_stability.csv", ["task", "group", "valid_assignments", "same_group_given_valid", "same_group_all_draws"], stability)
    arrays = {f"{mode}_{N}_{key}": array for mode, models in boot.items() for N, values in models.items() for key, array in values.items()}
    arrays["assignments"] = assignments
    np.savez_compressed(out / "bootstrap.npz", **arrays)
    metadata["bootstrap_status"] = dict(Counter(f"{r['mode']}/N{r['N']}/{r['status']}" for r in diagnostics))
    metadata["fits"] = {str(N): fit_summary(fit) for N, fit in fits.items()}
    audit.dump(out / "metadata.json", metadata)


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def export_bias_diagnostics(out):
    """Expose finite-item/bootstrap shifts instead of assuming percentile calibration."""
    meta = json.loads((out / "metadata.json").read_text())
    score_rows = read_csv(out / "scores.csv")
    result = []
    with np.load(out / "bootstrap.npz", allow_pickle=False) as draws:
        for mode in ("item", "family_item"):
            for N, fit in meta["fits"].items():
                score_map = {r["model"]: r for r in score_rows if r["mode"] == mode and r["N"] == N}
                for kind, labels, point in [
                    ("metrics", list(FIT_FIELDS), [fit[k] for k in FIT_FIELDS]),
                    ("loadings", meta["tasks"], fit["standardized_g"]),
                    ("scores", meta["models"], [float(score_map[m]["score"]) for m in meta["models"]]),
                ]:
                    values = draws[f"{mode}_{N}_{kind}"]
                    valid = np.isfinite(values).all(axis=1)
                    if not valid.any():
                        continue
                    mean = values[valid].mean(axis=0)
                    sd = values[valid].std(axis=0, ddof=1)
                    low, high = np.percentile(values[valid], [2.5, 97.5], axis=0)
                    for j, label in enumerate(labels):
                        result.append(dict(mode=mode, N=int(N), kind=kind, field=label, point=point[j],
                                           bootstrap_mean=mean[j], bootstrap_sd=sd[j], bias=mean[j] - point[j],
                                           bias_over_sd=(mean[j] - point[j]) / sd[j] if sd[j] > 1e-12 else 0.,
                                           raw_percentile_low=low[j], raw_percentile_high=high[j],
                                           point_outside_percentile=point[j] < low[j] - 1e-8 or point[j] > high[j] + 1e-8,
                                           nominal_interval_reported=int(valid.sum()) >= .9 * meta["resamples"]))
    audit.write_csv(out / "bias_diagnostics.csv", ["mode", "N", "kind", "field", "point", "bootstrap_mean", "bootstrap_sd", "bias", "bias_over_sd", "raw_percentile_low", "raw_percentile_high", "point_outside_percentile", "nominal_interval_reported"], result)
    return result


def render_report(out):
    """Render only from exported results, so layout changes never rerun bootstraps."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
    meta = json.loads((out / "metadata.json").read_text())
    fits = meta["fits"]
    one, hier = fits["1"], fits.get("3")
    tasks = meta["tasks"]
    labels = [t.split("/", 1)[1] for t in tasks]
    matrix = np.array([[float(r[t]) for t in tasks] for r in read_csv(out / "matrix.csv")])
    R = corr(standardize(matrix))
    loading_rows = read_csv(out / "loadings.csv")
    score_rows = read_csv(out / "scores.csv")
    fit_rows = read_csv(out / "fit_statistics.csv")
    bias = export_bias_diagnostics(out)
    stability = read_csv(out / "group_stability.csv")
    discovery = read_csv(out / "rediscovery.csv")
    sens = json.loads((out / "sensitivity.json").read_text())
    matched = json.loads((out / "matched_cohorts.json").read_text())
    navy, orange = "#173f5f", "#d87827"
    page = 0

    def canvas(title, subtitle=""):
        nonlocal page
        page += 1
        fig = plt.figure(figsize=(11.7, 8.3), facecolor="white")
        fig.text(.04, .955, title, fontsize=18, weight="bold", color=navy)
        fig.text(.04, .918, subtitle, fontsize=9, color=".35")
        fig.text(.04, .025, "Public LiveBench | August 2024 panel | exploratory latent analysis", fontsize=8, color=".4")
        fig.text(.96, .025, str(page), ha="right", fontsize=8, color=".4")
        return fig

    def save(fig, pdf):
        pdf.savefig(fig)
        plt.close(fig)

    def text(ax, paragraphs, width=78, size=10):
        ax.axis("off")
        wrapped = "\n\n".join("\n".join(textwrap.wrap(p, width)) for p in paragraphs)
        ax.text(0, 1, wrapped, va="top", fontsize=size, linespacing=1.45, transform=ax.transAxes)

    def number(value, places=2):
        return f"{float(value):.{places}f}" if value not in (None, "") else "withheld"

    def fit_interval(N, metric):
        r = next(r for r in fit_rows if r["mode"] == "family_item" and int(r["N"]) == N and r["metric"] == metric)
        return f"{number(100 * float(r['point']), 1)}% [" + (f"{100 * float(r['ci_low']):.1f}, {100 * float(r['ci_high']):.1f}]" if r["ci_low"] else "CI withheld]")

    with PdfPages(out / "report.pdf", metadata={"Title": "Latent gAI on public LiveBench data", "Author": "public-gai", "CreationDate": None, "ModDate": None}) as pdf:
        fig = canvas("A strong shared factor; residual structure remains", "65 complete models | 18 tasks | 6 domains | 1,000 common question IDs")
        ax = fig.add_axes((.24, .18, .38, .67))
        image = ax.imshow(R, vmin=-1, vmax=1, cmap="RdBu_r")
        ax.set_yticks(range(len(tasks)), labels, fontsize=7)
        ax.set_xticks(range(len(tasks)), labels, rotation=90, fontsize=6)
        ax.set_title("Observed task correlations", fontsize=11)
        fig.colorbar(image, ax=ax, fraction=.035, pad=.03)
        paragraphs = [
            f"One-factor g accounts for {one['g_variance_share']:.1%} of standardized task variance. Family/item interval: {fit_interval(1, 'g_variance_share')}.",
            f"One factor: CFI {one['cfi']:.3f}; RMSEA {one['rmsea']:.3f}; residual RMS {one['residual_rms']:.3f}. High shared variance does not establish adequate one-factor fit.",
        ]
        if hier:
            paragraphs += [f"Three-group hierarchy: CFI {hier['cfi']:.3f}; RMSEA {hier['rmsea']:.3f}. BIC difference (hierarchy - one factor): {hier['bic'] - one['bic']:.1f}.",
                           f"Hierarchical g accounts for {hier['g_variance_share']:.1%} of task variance. Unit-composite omega_h is {hier['omega_h']:.3f}; these are different quantities."]
        paragraphs += ["These are statistical performance dimensions within a selected historical sample. They are neither human IQ nor evidence of an increase or decline in generality over time."]
        text(fig.add_axes((.67, .16, .29, .68)), paragraphs, width=37, size=10)
        save(fig, pdf)

        fig = canvas("General-factor task loadings", "Standardized loadings | thick intervals: family + paired items | thin intervals: paired items only")
        ax = fig.add_axes((.27, .15, .67, .70))
        y = np.arange(len(tasks))
        for N, color, offset in [(1, navy, -.15), (3, orange, .15)]:
            if str(N) not in fits:
                continue
            for mode, linewidth, alpha in [("item", 1, .4), ("family_item", 2.2, 1)]:
                rows = [r for r in loading_rows if int(r["N"]) == N and r["mode"] == mode]
                for j, row in enumerate(rows):
                    if row["ci_low"]:
                        ax.plot([float(row["ci_low"]), float(row["ci_high"])], [j + offset] * 2, color=color, lw=linewidth, alpha=alpha)
            ax.plot(fits[str(N)]["standardized_g"], y + offset, "o", color=color, ms=4, label=f"N={N}")
        ax.set_yticks(y, labels, fontsize=8)
        ax.invert_yaxis()
        ax.axvline(0, color=".7", lw=.7)
        ax.set_xlim(-.05, 1.05)
        ax.set_xlabel("Standardized g loading")
        ax.grid(axis="x", alpha=.15)
        ax.legend(loc="lower left")
        fig.text(.05, .075, "Intervals are withheld when fewer than 90% of bootstrap fits are admissible. No task was excluded for a weak or negative loading.", fontsize=8)
        fig.text(.05, .055, "Some item-only ranges exclude their point estimate; finite-item resampling bias is material. Coverage is not calibrated; see bias_diagnostics.csv.", fontsize=8)
        save(fig, pdf)

        fig = canvas("Residual correlations expose what g misses", "Observed correlation minus fitted correlation | diagonal omitted | identical color scales")
        for i, (N, fit) in enumerate(fits.items()):
            sigma = np.array(fit["sigma"])
            residual = R - sigma / np.sqrt(np.outer(np.diag(sigma), np.diag(sigma)))
            np.fill_diagonal(residual, 0)
            ax = fig.add_axes((.22 + .40 * i, .25, .31, .59))
            im = ax.imshow(residual, cmap="RdBu_r", vmin=-.3, vmax=.3)
            ax.set_xticks(range(len(tasks)), labels, rotation=90, fontsize=6)
            ax.set_yticks(range(len(tasks)), labels if i == 0 else [""] * len(tasks), fontsize=7)
            ax.set_title(f"N={N}: off-diagonal RMS {fit['residual_rms']:.3f}", fontsize=10)
        fig.colorbar(im, ax=fig.axes, shrink=.65, pad=.03)
        fig.text(.05, .10, "Task grouping is exploratory and uses the same sample. Better residual fit alone does not independently validate the hierarchy.", fontsize=9)
        save(fig, pdf)

        fig = canvas("The three-group hierarchy", "Existing PAF/varimax assignment and ML higher-order model | group names are neutral")
        if hier:
            ax = fig.add_axes((.08, .68, .84, .19))
            ax.axis("off")
            ax.text(.5, .95, "g", ha="center", va="center", fontsize=18, color=navy, weight="bold")
            for k, gamma in enumerate(hier["gamma"]):
                x = .16 + .34 * k
                ax.add_patch(FancyBboxPatch((x - .09, .04), .18, .25, boxstyle="round,pad=.02", facecolor="#edf3f7", edgecolor=navy))
                ax.text(x, .17, f"Group {chr(65 + k)}", ha="center", va="center", fontsize=11)
                ax.annotate("", xy=(x, .34), xytext=(.5, .8), arrowprops=dict(arrowstyle="->", color=navy))
                ax.text((x + .5) / 2, .57, f"{gamma:.3f}", ha="center", bbox=dict(facecolor="white", edgecolor="none", pad=1))
            membership = []
            for k, members in enumerate(hier["groups"]):
                membership.append(f"Group {chr(65 + k)} ({len(members)} tasks):")
                membership.extend("  " + labels[j] for j in members)
                membership.append("")
            ax = fig.add_axes((.05, .09, .40, .55));ax.axis("off")
            ax.text(0, 1, "\n".join(membership), va="top", fontsize=8, linespacing=1.35)
            loadings = np.column_stack([hier["standardized_g"], hier["standardized_group"]])
            ax = fig.add_axes((.67, .11, .26, .53))
            im = ax.imshow(loadings, aspect="auto", cmap="viridis", vmin=0, vmax=1)
            ax.set_yticks(range(len(tasks)), labels, fontsize=7)
            ax.set_xticks(range(4), ["g", "A specific", "B specific", "C specific"], rotation=30, fontsize=8)
            ax.set_title("Schmid-Leiman loadings", fontsize=10)
            fig.colorbar(im, ax=ax, fraction=.04, pad=.04)
        else:
            text(fig.add_axes((.08, .3, .8, .5)), ["No admissible three-group hierarchy was obtained. The one-factor analysis remains available. Two-group hierarchical g is not identified and was not substituted."])
        save(fig, pdf)

        fig = canvas("Bootstrap validity and group stability", f"{meta['resamples']} replicates per interval mode | {GROUP_REPS} rediscovery replicates | seed {meta['seed']}")
        ax = fig.add_axes((.25, .15, .33, .70))
        probs = [float(r["same_group_given_valid"]) if r["same_group_given_valid"] else np.nan for r in stability]
        ax.barh(np.arange(len(tasks)), probs, color=navy)
        ax.set_yticks(range(len(tasks)), labels, fontsize=7)
        ax.invert_yaxis(); ax.set_xlim(0, 1)
        ax.set_xlabel("Same group, conditional on valid rediscovery", fontsize=8)
        paragraphs = [f"{meta['family_clusters']} family clusters; {meta['unresolved_families']} unresolved model identities remain singleton clusters. This is a dependence sensitivity, not proof that clusters are independent."]
        for mode in ("item", "family_item"):
            for N in (1, 3):
                ok = meta["bootstrap_status"].get(f"{mode}/N{N}/ok", 0)
                boundary = meta["bootstrap_status"].get(f"{mode}/N{N}/boundary", 0)
                paragraphs.append(f"{mode}, N={N}: {ok}/{meta['resamples']} admissible; {boundary} boundary fits. {'Intervals withheld.' if ok < .9 * meta['resamples'] else 'Intervals reported.'}")
        paired = [r for r in discovery if r["one_bic"] and r["hierarchy_bic"]]
        wins = sum(float(r["hierarchy_bic"]) < float(r["one_bic"]) for r in paired)
        paragraphs += [f"Rediscovery: {len(paired)}/{GROUP_REPS} paired admissible comparisons; hierarchy has lower BIC in {wins}. Failed/nonviable hierarchies are not evidence against domain structure.",
                       "Fixed-group intervals condition on the discovered assignment. Group-stability bars are conditional on admissible rediscovery and align group labels before comparison."]
        text(fig.add_axes((.64, .13, .32, .72)), paragraphs, width=43, size=9)
        save(fig, pdf)

        family_scores = {N: {r["model"]: r for r in score_rows if r["mode"] == "family_item" and int(r["N"]) == N} for N in (1, 3)}
        ordered = sorted(family_scores[1], key=lambda m: float(family_scores[1][m]["rank"]))
        for start in range(0, len(ordered), 23):
            fig = canvas(f"Relative model scores and ranks ({start + 1}-{min(start + 23, len(ordered))})", "Family + paired-item intervals | positive rank shift = lower rank under the hierarchy")
            table = []
            for model in ordered[start:start + 23]:
                a, b = family_scores[1][model], family_scores[3][model]
                def ci(row):
                    return f"[{number(row['ci_low'])}, {number(row['ci_high'])}]" if row["ci_low"] else "withheld"
                def rank(row):
                    return f"{number(row['rank'], 0)} [{number(row['rank_low'], 0)}, {number(row['rank_high'], 0)}]" if row["rank_low"] else number(row["rank"], 0) + " [withheld]"
                shift = number(b["rank_shift"], 0)
                shift += f" [{number(b['shift_low'], 0)}, {number(b['shift_high'], 0)}]" if b["shift_low"] else " [withheld]"
                table.append([model, number(a["score"]), ci(a), rank(a), number(b["score"]), ci(b), rank(b), shift])
            ax = fig.add_axes((.025, .16, .95, .69));ax.axis("off")
            tab = ax.table(cellText=table, colLabels=["Model", "g1", "95% CI", "Rank [95%]", "g3", "95% CI", "Rank [95%]", "Rank shift [95%]"],
                           colWidths=[.32, .045, .105, .10, .045, .105, .10, .16], loc="upper left", bbox=[0, 0, 1, 1], cellLoc="left")
            tab.auto_set_font_size(False);tab.set_fontsize(6.7)
            for (row, col), cell in tab.get_celld().items():
                cell.set_edgecolor("#d9e0e5");cell.set_linewidth(.35)
                if row == 0:
                    cell.set_facecolor(navy);cell.set_text_props(color="white", weight="bold")
                elif row % 2 == 0:
                    cell.set_facecolor("#f0f4f7")
            fig.text(.05, .105, "Scores are centered and scaled within the original 65-model panel in each replicate. They have no absolute or human-IQ interpretation.", fontsize=8)
            fig.text(.05, .078, "Rank intervals are marginal; overlapping intervals are not a pairwise significance test. A point rank is not a precise ordering.", fontsize=8)
            save(fig, pdf)

        fig = canvas("Sensitivity and matched historical comparisons", "Changing cohorts and changing batteries must not be mistaken for evolution in gAI")
        lines = ["Archive       Models Tasks   g variance    CFI     RMSEA  Panel"]
        for row in sens:
            if row["N"] == 1:
                lines.append(f"{row['archive_date']} {row['models']:>6} {row['tasks']:>5} {row['g_variance_share']:>11.1%} {row['cfi']:>8.3f} {row['rmsea']:>8.3f}  {row['panel']}")
        ax = fig.add_axes((.05, .46, .91, .39));ax.axis("off")
        ax.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=8, linespacing=1.6)
        paragraphs = []
        for row in matched:
            paragraphs.append(f"Matched {row['left'][:8]} -> {row['right'][:8]}: {row['models']} common models, {row['tasks']} tasks, {row['shared_item_ids']} common question IDs; {row['changed_item_scores']} changed item scores. Maximum task-mean change {row['max_task_mean_change']:.4f}; maximum g-loading change {row['max_loading_change']:.4f}.")
        paragraphs.append("The matched comparisons hold the observed identities and battery fixed. Historical API versions/settings remain incompletely verified, so even changed item scores do not by themselves demonstrate model improvement.")
        text(fig.add_axes((.05, .09, .90, .31)), paragraphs, width=125, size=9)
        save(fig, pdf)

        fig = canvas("Methods, provenance and practical limits", "All inputs are public, pinned local files; this analysis makes no inference/API requests")
        paragraphs = [
            f"Input score revision: {PRIMARY}; battery: {BATTERY}. Exact model IDs are retained. Six incomplete models are excluded from the primary matrix; exclusions and item IDs are exported.",
            "One-factor and three-group covariance models are fitted by ML with analytic gradients and multiple starts. Group discovery uses PAF/varimax. Factor variances are fixed to one; signs are aligned positive. Hierarchies require three groups with at least three indicators each. Two-group hierarchical g is not identified and is excluded.",
            "The one-factor standardized loading-square mean is g-attributed task variance. Hierarchical ECV is g variance divided by total common variance. Omega_h is unit-weight composite reliability attributable to g. PCA variance is a separate exploratory statistic. Fit indices are approximate for bounded aggregate scores and this small, selected sample.",
            "Item bootstrap draws common question IDs jointly across models within each task. Family/item bootstrap additionally samples curated family clusters. Scores are standardized over the original panel. Group assignments stay fixed for intervals and are rediscovered separately. Item-only variance estimates shift downward: percentile ranges are nominal, uncalibrated sensitivity summaries, not coverage guarantees. Bias diagnostics are exported.",
            f"Seed {meta['seed']}; {meta['resamples']} replicates per interval mode; {GROUP_REPS} rediscovery replicates. Nonconvergence, singularity and boundary fits are recorded. Nominal intervals are withheld below 90% admissible replicates. No silent matrix regularization is used.",
            "Family provenance is in families.csv. Documented series are a clustering assumption, not proof of shared weights; unresolved aliases remain singleton clusters. Relations between clusters may remain. Historical generation settings, provider differences and repeated-run uncertainty are not fully identified.",
            "The broad usable archive covers only part of 2024. The latest HF judgment pool has three domains, and the newer export repository returned 404. Independent reproduction of published leaderboard totals remains pending. Data-card licensing is unspecified; this report does not clear raw-data redistribution.",
            "Sources: https://huggingface.co/livebench ; https://github.com/LiveBench/LiveBench . Per-file immutable URLs/checksums, code hashes and package versions are in metadata.json. Exact family-source links are in families.csv.",
        ]
        text(fig.add_axes((.05, .10, .90, .76)), paragraphs, width=140, size=8.8)
        save(fig, pdf)

    lines = ["# Latent gAI analysis on public LiveBench", "",
             f"Primary: 65 models, 18 tasks, six domains; archive `{PRIMARY}`, battery `{BATTERY}`.", "",
             f"- One factor: g-attributed standardized task variance {one['g_variance_share']:.1%}; CFI {one['cfi']:.3f}, RMSEA {one['rmsea']:.3f}."]
    if hier:
        lines += [f"- Three-group hierarchy: g variance {hier['g_variance_share']:.1%}; CFI {hier['cfi']:.3f}, RMSEA {hier['rmsea']:.3f}; BIC difference {hier['bic'] - one['bic']:.1f}.",
                  f"- Hierarchical ECV {hier['ecv']:.3f}, omega_h {hier['omega_h']:.3f}. These are not interchangeable variance/reliability metrics."]
    lines += ["", "## Uncertainty", "", f"{meta['resamples']} paired-item and {meta['resamples']} family/item bootstrap draws; {GROUP_REPS} group rediscoveries.",
              f"Family grouping: {meta['family_clusters']} clusters; {meta['unresolved_families']} unresolved identities retained as singletons.", ""]
    for mode in ("item", "family_item"):
        for N in (1, 3):
            ok = meta["bootstrap_status"].get(f"{mode}/N{N}/ok", 0)
            lines.append(f"- {mode}, N={N}: {ok}/{meta['resamples']} admissible; " + ("nominal intervals withheld." if ok < .9 * meta['resamples'] else "95% percentile intervals reported."))
    lines += ["", "## Interpretation", "",
              "Strong shared performance coexists with residual domain structure. The hierarchy is exploratory, discovered on the same small model sample, and remains conditional on its group assignment. Better BIC is not independent confirmation of the group structure.",
              "", "Matched score-archive comparisons hold observed model IDs, tasks and item IDs fixed; see matched_cohorts.json. Differences between unmatched archive fits cannot establish temporal growth or decline in generality.",
              "", "Scores are relative to this panel and have no human-IQ interpretation. Family clusters are a dependence sensitivity; unresolved or cross-family ancestry and historical provider/settings differences remain limitations. Independent validation against published leaderboard totals is still pending.",
              "", "Item-only refits attenuate g-attributed variance: some percentile ranges do not contain the original estimate. The intervals are nominal resampling sensitivity summaries; frequentist coverage has not been calibrated. Means, bias/SD and percentile diagnostics are in bias_diagnostics.csv. No significance claim is based on those shifted ranges.",
              "", "## Files and reproduction", "", "`report.pdf` contains the rendered analysis. `matrix.csv`, `fit_statistics.csv`, `loadings.csv`, `hierarchy.csv`, `scores.csv`, `group_stability.csv` and `sensitivity.csv` contain numeric results. `bootstrap.npz` stores numeric draws without pickle; `bootstrap_diagnostics.csv` records failures. `metadata.json` pins provenance, versions and code hashes.",
              "", "```sh", "uv run public_gai_factor.py --seed 0 --resamples 1000", "```", "",
              "PDF layout can be regenerated from exported results using `public_gai_factor.render_report(output_directory)` without rerunning the bootstrap.",
              "", "No new model evaluations, new benchmark collection, model-release cohorts or blog publication were performed."]
    (out / "README.md").write_text("\n".join(lines) + "\n")


def run(args):
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs(args.data)
    view = panel_view(inputs, PRIMARY, BATTERY)
    if view["scores"].shape != (65, 18):
        raise ValueError(f"Primary panel changed: {view['scores'].shape}")
    R = corr(standardize(view["scores"]))
    groups = discover_groups(R, 3)
    fits, points = {}, {}
    fits[1], points[1] = fit_panel(view)
    if groups is not None:
        try:
            fits[3], points[3] = fit_panel(view, groups)
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            print(f"Hierarchy unavailable: {exc}", flush=True)
            groups = None
    clusters, family_records = read_families(ROOT / "public_model_families.csv", view["models"])
    for N, fit in fits.items():
        print(f"N={N}: CFI={fit.cfi:.3f}, RMSEA={fit.rmsea:.3f}, g variance={fit.g_variance_share:.3f}, boundary={fit.boundary}", flush=True)
    boot, diagnostics, stream = bootstrap(view, clusters, groups, args.resamples, args.seed)
    discovery, assignment = rediscover(view, clusters, groups, stream)
    sens, matched = sensitivity(inputs, view)
    audit.dump(out / "sensitivity.json", sens)
    audit.dump(out / "matched_cohorts.json", matched)
    audit.write_csv(out / "families.csv", ["model", "family", "status", "source", "notes"], family_records)
    audit.write_csv(out / "sensitivity.csv", ["revision", "archive_date", "battery", "panel", "models", "tasks", "domains", "N", *FIT_FIELDS, "boundary"], sens)
    try:
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except subprocess.CalledProcessError:
        commit = None
    import matplotlib
    metadata = dict(primary_revision=PRIMARY, battery=BATTERY, models=view["models"], tasks=view["tasks"],
                    groups=groups, seed=args.seed, resamples=args.resamples, rediscovery_reps=GROUP_REPS,
                    family_clusters=len(clusters), unresolved_families=sum(r["status"] == "unresolved-singleton" for r in family_records),
                    code_commit=commit, code_hashes={p: audit.sha((ROOT / p).read_bytes()) for p in ["public_gai_factor.py", "factor_models.py", "livebench_feasibility.py", "public_model_families.csv"]},
                    input_manifest_sha256=audit.sha((args.data / "manifest.json").read_bytes()),
                    matrix_sha256=audit.sha(view["scores"].tobytes()), sources=inputs["sources"],
                    exclusions=dict(incomplete_models=sorted(set(m for m, q in inputs["archives"][PRIMARY]["selected"]) - set(view["models"])),
                                    judgment_issues=inputs["archives"][PRIMARY]["issues"], changed_questions=inputs["changed_questions"],
                                    undated_question_rows=inputs["undated_question_rows"],
                                    archive_issues={r: a["issues"] for r, a in inputs["archives"].items()}),
                    versions=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, matplotlib=matplotlib.__version__),
                    interval_rule="95% percentile; withheld below 90% admissible; scores restandardized over the original panel",
                    interpretation="exploratory; family clusters are a sensitivity assumption, not independent population draws")
    export_results(out, view, fits, points, boot, diagnostics, discovery, assignment, metadata)
    render_report(out)
    print(f"Wrote {out.resolve()}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "feasibility/livebench")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "output/public-gai")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--resamples", type=int, default=1000)
    args = parser.parse_args()
    if args.resamples < 2:
        parser.error("--resamples must be at least 2")
    run(args)


if __name__ == "__main__":
    main()
