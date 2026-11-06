#!/usr/bin/env python3
"""Step 2 Allen summary (DESIGN.md §6, §7 contrast R, §15 Allen cells; addendum DESIGN-v2-ADDENDUM.md §4). Written
before any Allen cell was run.

Rates: per scheme x split x rule, mean over mice of each mouse's share of areas with p < 0.05, 95% mouse
bootstrap (B = 20,000, seed 20261015, as step 1). Primary set: the 30 new mice; sensitivity: all 32.
NaN p and P3 errors excluded (denominators reported; P3 also with errors counted as non-rejections).
Contrast R: shared24, S-main, per area hit(Pk) - hit(P5), averaged per mouse, mouse bootstrap.
Group-level column (§6): rejection rates of (a) t-test, (b) sign-flip, (c) a valid group test over the 200
fake-label experiments formed by the stored P5 null accuracies (see group_level; addendum 1 §4, review M3), plus
the observed experiment's p values. Splits: main, tool, block (beyond §15), pair (sep schemes, beyond §15).
Rows are deduplicated on (session, area, scheme, split); the number of areas per scheme x split is reported.

  python summarize_allen.py --rows ../runs_allen --out ../results
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
SESS = {r["session_id"]: r for r in csv.DictReader((HERE.parents[1] / "trackA-std" / "sessions_trackA.csv").open())}
RULES = ("P1", "P2", "P3", "P4", "P5")
BOOT_B, BOOT_SEED, G_B, G_SEED = 20000, 20261015, 10000, 20261023


def est(v):
    v = np.asarray(v, float)
    if len(v) == 0:
        return None
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(v), (BOOT_B, len(v)))
    lo, hi = np.percentile(v[idx].mean(1), [2.5, 97.5])
    return {"mean": float(v.mean()), "ci95": [float(lo), float(hi)], "n_mice": int(len(v))}


def per_mouse(rows, f):
    by = {}
    for r in rows:
        x = f(r)
        if x is None or not np.isfinite(x):
            continue
        by.setdefault(SESS[r["session"]]["specimen_id"], []).append(x)
    return [np.mean(by[m]) for m in sorted(by)], {m: by[m] for m in by}


def ok(p):
    return p is not None and np.isfinite(p)


def group_level(rows, n_null=1000):
    """Group-level column (§6) as rates (addendum 1 §4, review M3). Per area: observed accuracy and its 200 P5 null
    accuracies (refitted fake-label assignments drawn from the scheme's own set). For each null index j, the j-th null
    accuracy of every area plays the observed accuracy of a fake-label experiment; across mice: (a) one-sample t-test
    of the per-mouse mean against 0.5, (b) sign-flip permutation (1,000 flips), (c) valid group test with a group
    null built from the other 199 null accuracies (1,000 draws). Rejection rates over the 200 j are reported, with
    the observed experiment's three p values. (c) is a fixed-effects (global-null) test for these mice, not a test
    of a population mean (Allefeld et al. 2016)."""
    rs = [r for r in rows if ok(r.get("acc")) and r.get("P5_null_acc")]
    if not rs:
        return None
    mice = sorted({SESS[r["session"]]["specimen_id"] for r in rs})
    if len(mice) < 3:
        return None
    mi = {m: i for i, m in enumerate(mice)}
    M = np.zeros((len(rs), len(mice)))
    for k, r in enumerate(rs):
        M[k, mi[SESS[r["session"]]["specimen_id"]]] = 1
    Mb = M.copy()                                                        # area x mouse membership

    def mouse_mean(x):
        """x: (..., areas) -> (..., mice): per-mouse mean over the areas with a finite value."""
        v = np.isfinite(x)
        cnt = v.astype(float) @ Mb
        return np.where(cnt > 0, (np.where(v, x, 0.0) @ Mb) / np.maximum(cnt, 1), np.nan)
    N = np.array([[np.nan if v is None else v for v in r["P5_null_acc"]] for r in rs], float)
    obs = np.array([r["acc"] for r in rs])
    A, D = N.shape
    rng = np.random.default_rng(G_SEED)

    def tests(x_area, null_cols_excl):
        xm = mouse_mean(x_area)
        xm = xm[np.isfinite(xm)] if xm.ndim == 1 else xm
        tp = stats.ttest_1samp(xm, 0.5, alternative="greater").pvalue
        fl = rng.choice([-1, 1], (1000, len(xm)))
        sp = (1 + np.sum(((xm - 0.5)[None, :] * fl).mean(1) >= (xm - 0.5).mean())) / 1001
        cols = rng.integers(0, D - (1 if null_cols_excl is not None else 0), (n_null, A))
        if null_cols_excl is not None:
            cols = cols + (cols >= null_cols_excl)
        g = mouse_mean(N[np.arange(A)[None, :], cols])
        vp = (1 + np.sum(np.nanmean(g, axis=1) >= xm.mean())) / (n_null + 1)
        return float(tp), float(sp), float(vp)
    obs_p = tests(obs, None)
    hits = np.zeros(3)
    for j in range(D):
        hits += np.array(tests(N[:, j], j)) < 0.05
    return {"n_mice": len(mice), "n_areas": A, "observed": {"mean_acc": float(mouse_mean(obs).mean()), "t_p": obs_p[0],
            "signflip_p": obs_p[1], "valid_group_p": obs_p[2]},
            "rate_over_null_experiments": {"t_test": float(hits[0] / D), "sign_flip": float(hits[1] / D),
                                           "valid_group": float(hits[2] / D), "n_experiments": D}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(HERE.parent / "runs_allen"))
    ap.add_argument("--out", default=str(HERE.parent / "results"))
    args = ap.parse_args()
    raw = [json.loads(l) for f in sorted(Path(args.rows).glob("*.jsonl")) for l in f.read_text().splitlines()]
    uniq = {}
    for r in raw:
        uniq[(r["session"], r["area"], r["scheme"], r["split"])] = r
    rows = list(uniq.values())
    dup = len(raw) - len(rows)
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    res = {}
    for which in ("new", "all32"):
        sub = [r for r in rows if which == "all32" or SESS[r["session"]]["set"] == which]
        R = {}
        for sch in sorted({r["scheme"] for r in sub}):
            for sp in ("main", "tool", "block", "pair"):
                rs = [r for r in sub if r["scheme"] == sch and r["split"] == sp]
                if not rs:
                    continue
                cell = {"n_areas": len(rs), "n_nonconverged_rows": int(sum(1 for r in rs if r.get("n_nonconverged"))),
                        "one_p3_run_areas": int(sum(1 for r in rs if r.get("n_p3_runs") == 1))}
                for rule in RULES:
                    v, _ = per_mouse(rs, lambda r: float(r[rule] < 0.05) if ok(r.get(rule)) else None)
                    cell[rule] = est(v)
                v, _ = per_mouse(rs, lambda r: float(ok(r.get("P3")) and r["P3"] < 0.05))
                cell["P3_errors_as_nonreject"] = est(v)
                cell["P3_error_share_of_areas"] = float(np.mean([bool(r.get("P3_error")) for r in rs]))
                if sch == "shared24" and sp == "main":
                    for rule in ("P1", "P2", "P3", "P4"):
                        v, _ = per_mouse(rs, lambda r: (float(r[rule] < 0.05) - float(r["P5"] < 0.05))
                                         if ok(r.get(rule)) and ok(r.get("P5")) else None)
                        cell[f"contrast_R_{rule}-P5"] = est(v)
                if sch != "pos_dg24":
                    cell["group_level"] = group_level(rs)
                R[f"{sch}/{sp}"] = cell
        res[which] = R
    res["duplicates_removed"] = dup
    res["areas_per_scheme_split"] = {f"{r['scheme']}/{r['split']}": 0 for r in rows}
    for r in rows:
        res["areas_per_scheme_split"][f"{r['scheme']}/{r['split']}"] += 1
    (out / "allen_summary.json").write_text(json.dumps(res, indent=1))
    lines = ["# Step 2 Allen summary (summarize_allen.py)", "", "Mouse-level % of areas with p < 0.05 (30 new mice; 95% mouse bootstrap)", "",
             "| scheme/split | P1 | P2 | P3 | P4 | P5 | group-level rejection rate: t-test / sign-flip / valid |", "|---|---|---|---|---|---|---|"]

    def f(e):
        return "–" if not e else f"{100 * e['mean']:.1f} ({100 * e['ci95'][0]:.1f}–{100 * e['ci95'][1]:.1f})"
    for k, c in res.get("new", {}).items():
        g = c.get("group_level")
        gs = "–" if not g else (f"rates {100 * g['rate_over_null_experiments']['t_test']:.0f}% / "
                                f"{100 * g['rate_over_null_experiments']['sign_flip']:.0f}% / {100 * g['rate_over_null_experiments']['valid_group']:.0f}%")
        lines.append(f"| {k} | " + " | ".join(f(c.get(r)) for r in RULES) + f" | {gs} |")
    c = res.get("new", {}).get("shared24/main", {})
    lines += ["", "Contrast R (shared24, S-main): " + "; ".join(f"{r}-P5 {f(c.get(f'contrast_R_{r}-P5'))}" for r in ("P1", "P2", "P3", "P4"))]
    (out / "allen_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
