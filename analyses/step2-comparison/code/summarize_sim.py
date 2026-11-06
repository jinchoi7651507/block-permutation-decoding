#!/usr/bin/env python3
"""Step 2 simulation summary (DESIGN.md §7, §8, §15; addendum DESIGN-v2-ADDENDUM.md §3). Written before any study
cell was read.

Per cell (runs/CELLS.json) and rule P1-P5: replicates, rate of p < 0.05 with a Wilson 95% interval, and the
Monte Carlo 99% band of a 5% rate at that number of replicates. NaN p (undefined observed statistic) counts as an
error and is excluded from the rate (denominators reported). P3: error share, rate among non-errors, rate with
errors counted as non-rejections, and P5 on the same surviving replicates.
Contrast M (primary cell): per replicate hit(Pk) - hit(P5), mean and 95% bootstrap interval over replicates
(B = 10,000, seed 20261022); P3 on the replicates where it ran.
P5 fails (fixed-order designs, trend 0): rate above the upper end of the 99% band.
B = 4: P5 has 6 balanced assignments, and an assignment and its swap give the same accuracy (3 distinct values), so the
smallest attainable p is about 1/3 (DESIGN §15 says 0.17: corrected in addendum 1); printed as "cannot reject".
Baselines (addendum 1 §3): at drift 0 the generator does not depend on tau_s, so the four tau_s copies of a drift-0
cell are pooled (2,000 replicates); primary baseline = pooled interleaved drift-0 rate for the same B and split;
second, descriptive baseline = pooled random-design drift-0 rate. Differences get a 95% bootstrap interval.
Q3 primary cell: interleaved, tau_s 20, drift 1, B 12, S-main (the others descriptive).
Cells with fewer replicates than planned are flagged; the summary stops if the primary cell is incomplete.

  python summarize_sim.py --runs ../runs --out ../results
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

RULES = ("P1", "P2", "P3", "P4", "P5")
BOOT_B, BOOT_SEED = 10000, 20261022


def wilson(k, n):
    if n == 0:
        return [None, None]
    z = 1.959963985
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(c - h), float(c + h)]


def band99(n):
    if n == 0:
        return [None, None]
    lo, hi = stats.binom.ppf([0.005, 0.995], n, 0.05)
    return [float(lo / n), float(hi / n)]


def load(runs, c):
    rows = {}
    for f in sorted(runs.glob(f"{c['name']}.w*.jsonl")):
        for l in f.read_text().splitlines():
            r = json.loads(l)
            rows[r["rep"]] = r
    return [rows[k] for k in sorted(rows)]


def rate(rows, rule):
    v = [r.get(rule) for r in rows]
    err = sum(1 for x in v if x is None or (isinstance(x, float) and not np.isfinite(x)))
    ok = [x for x in v if x is not None and np.isfinite(x)]
    k = int(sum(1 for x in ok if x < 0.05))
    n = len(ok)
    out = {"n": n, "errors": err, "hits": k, "rate": (k / n if n else None), "wilson95": wilson(k, n),
           "band99_of_5pct": band99(n)}
    if ok:
        out["min_p"] = float(min(ok))
    return out


def finite(x):
    return x is not None and np.isfinite(x)


def cell_summary(rows, c):
    s = {"n_reps": len(rows), "n_expected": c["reps"], "incomplete": len(rows) < c["reps"]}
    for rule in RULES:
        if rule == "P5" and c["design"] == "interleaved":
            continue
        s[rule] = rate(rows, rule)
    if "P3" in s:
        n_all = len(rows)
        s["P3"]["error_share"] = s["P3"]["errors"] / n_all if n_all else None
        s["P3"]["rate_errors_as_nonreject"] = s["P3"]["hits"] / n_all if n_all else None
        if "P5" in s:
            surv = [r for r in rows if finite(r.get("P3"))]
            s["P3"]["P5_on_same_reps"] = rate(surv, "P5")
    if c["design"] != "interleaved" and c["B"] == 4:
        s["P5_note"] = "B = 4: 3 distinct null values; smallest attainable p about 1/3; cannot reject"
    if c["design"] in ("ABAB", "ABBA", "AABB") and c["trend"] == 0 and s.get("P5", {}).get("n"):
        s["P5_fails"] = bool(s["P5"]["rate"] > s["P5"]["band99_of_5pct"][1])
    return s


def size_adjusted(null_rows, alt_rows, rule):
    """Addendum 1 §1b: threshold q = 5% quantile of the rule's p in the delta = 0 primary cell (P3 errors and NaN
    count as p = 1, i.e. never reject). Randomised at the tie: reject if p < q, and if p == q with probability
    g = (0.05 - P0(p < q)) / P0(p == q), so the realised size is exactly 5% in expectation. Reports raw power, the
    realised size of the plain rule p <= q, g, and the expected size-adjusted power P1(p < q) + g P1(p == q)."""
    def ps(rows):
        return np.array([r[rule] if finite(r.get(rule)) else 1.0 for r in rows])
    p0, p1 = ps(null_rows), ps(alt_rows)
    q = float(np.quantile(p0, 0.05, method="lower"))
    lt0, eq0 = float(np.mean(p0 < q - 1e-12)), float(np.mean(np.abs(p0 - q) <= 1e-12))
    g = 0.0 if eq0 == 0 else min(1.0, max(0.0, (0.05 - lt0) / eq0))
    lt1, eq1 = float(np.mean(p1 < q - 1e-12)), float(np.mean(np.abs(p1 - q) <= 1e-12))
    return {"raw_power": float(np.mean(p1 < 0.05)), "threshold_q": q, "size_plain_le_q": lt0 + eq0, "tie_prob_g": g,
            "size_adjusted_power": lt1 + g * eq1, "n_null": int(len(p0)), "n_alt": int(len(p1))}


def power_summary(pcells, null_rows, runs):
    out = {}
    for c in pcells:
        rows = load(runs, c)
        out[c["name"]] = {"delta": c["delta"], "n_reps": len(rows), "incomplete": len(rows) < c["reps"],
                          **{r: size_adjusted(null_rows, rows, r) for r in RULES}}
    return out


def contrast_m(rows):
    rng = np.random.default_rng(BOOT_SEED)
    out = {}
    d = np.array([float(finite(r.get("P3")) and r["P3"] < 0.05) - float(r["P5"] < 0.05) for r in rows if finite(r.get("P5"))])
    if len(d):
        idx = rng.integers(0, len(d), (BOOT_B, len(d)))
        lo, hi = np.percentile(d[idx].mean(1), [2.5, 97.5])
        out["P3(errors as non-rejections)-P5"] = {"mean": float(d.mean()), "ci95": [float(lo), float(hi)], "n": int(len(d))}
    for rule in ("P1", "P2", "P3", "P4"):
        d = [float(r[rule] < 0.05) - float(r["P5"] < 0.05) for r in rows
             if r.get(rule) is not None and r.get("P5") is not None and np.isfinite(r[rule]) and np.isfinite(r["P5"])]
        d = np.array(d)
        if len(d) == 0:
            continue
        idx = rng.integers(0, len(d), (BOOT_B, len(d)))
        lo, hi = np.percentile(d[idx].mean(1), [2.5, 97.5])
        out[f"{rule}-P5"] = {"mean": float(d.mean()), "ci95": [float(lo), float(hi)], "n": int(len(d))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(Path(__file__).resolve().parent.parent / "runs"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "results"))
    args = ap.parse_args()
    runs, out = Path(args.runs), Path(args.out)
    out.mkdir(exist_ok=True)
    cells = json.loads((runs / "CELLS.json").read_text())
    res = {"cells": {}}
    data = {}
    for c in cells:
        rows = load(runs, c)
        data[c["name"]] = rows
        res["cells"][c["name"]] = {"cell": c, **cell_summary(rows, c)}
    prim = cells[0]
    if res["cells"][prim["name"]]["incomplete"]:
        raise SystemExit(f"primary cell incomplete: {len(data[prim['name']])} of {prim['reps']} replicates")
    res["contrast_M"] = contrast_m(data[prim["name"]])
    res["contrast_M"]["cell"] = prim["name"]
    def pooled(design, B, split):
        rs = [r for c in cells if c["design"] == design and c["drift"] == 0 and c["B"] == B and c["split"] == split
              and c["trend"] == 0 for r in data[c["name"]]]
        return rs
    brng = np.random.default_rng(BOOT_SEED + 1)

    def diff_ci(a_rows, b_rows, rule):
        a = np.array([float(r[rule] < 0.05) for r in a_rows if finite(r.get(rule))])
        b = np.array([float(r[rule] < 0.05) for r in b_rows if finite(r.get(rule))])
        if len(a) == 0 or len(b) == 0:
            return None
        ia = brng.integers(0, len(a), (2000, len(a)))
        ib = brng.integers(0, len(b), (2000, len(b)))
        dd = a[ia].mean(1) - b[ib].mean(1)
        lo, hi = np.percentile(dd, [2.5, 97.5])
        return {"diff": float(a.mean() - b.mean()), "ci95": [float(lo), float(hi)], "n_cell": int(len(a)), "n_baseline": int(len(b)),
                "baseline_rate": float(b.mean())}
    for c in cells:
        if c["design"] == "interleaved":
            continue
        cs = res["cells"][c["name"]]
        own = {id(r) for r in data[c["name"]]}
        base_i = pooled("interleaved", c["B"], c["split"])
        base_r = [r for r in pooled("random", c["B"], c["split"]) if id(r) not in own]   # exclude the cell's own rows
        cs["minus_baseline"] = {r: diff_ci(data[c["name"]], base_i, r) for r in ("P1", "P4")}
        cs["minus_random_drift0"] = {r: diff_ci(data[c["name"]], base_r, r) for r in ("P1", "P4")}
    res["incomplete_cells"] = [k for k, v in res["cells"].items() if v["incomplete"]]
    q3 = [c for c in cells if c["design"] == "interleaved" and c["B"] == 12 and c["split"] == "main"]
    prim_q3 = next(c for c in q3 if c["tau_s"] == 20 and c["drift"] == 1)
    res["Q3"] = {"primary": {"cell": prim_q3["name"], **res["cells"][prim_q3["name"]]["P2"]},
                 "descriptive": {c["name"]: res["cells"][c["name"]].get("P2") for c in q3 if c is not prim_q3}}
    pw = runs / "POWER_CELLS.json"
    if pw.exists():
        res["power"] = power_summary(json.loads(pw.read_text()), data[prim["name"]], runs)
    (out / "sim_summary.json").write_text(json.dumps(res, indent=1))
    lines = ["# Step 2 simulation summary (summarize_sim.py)", "",
             f"Primary cell {prim['name']}: contrast M (rate of Pk minus P5, paired by replicate, 95% bootstrap)", ""]
    q = res["Q3"]["primary"]
    lines.insert(2, f"Q3 primary cell {q['cell']}: P2 {100 * q['rate']:.1f}% (99% band of 5%: {100 * q['band99_of_5pct'][0]:.1f}–{100 * q['band99_of_5pct'][1]:.1f})" if q.get("rate") is not None else "Q3: no rows")
    if res["incomplete_cells"]:
        lines.insert(2, f"INCOMPLETE CELLS ({len(res['incomplete_cells'])}): " + ", ".join(res["incomplete_cells"][:10]))
    for k, v in res["contrast_M"].items():
        if k != "cell":
            lines.append(f"- {k}: {100 * v['mean']:.1f} points ({100 * v['ci95'][0]:.1f} to {100 * v['ci95'][1]:.1f}), n = {v['n']}")
    lines += ["", "| cell | reps | P1 | P2 | P3 (err) | P4 | P5 | P1−base | P4−base |", "|---|---|---|---|---|---|---|---|---|"]

    def p5txt(c, s):
        if c["design"] != "interleaved" and c["B"] == 4:
            mp = s.get("P5", {}).get("min_p")
            return "cannot reject" + ("" if mp is None else f" (min p {mp:.2f})")
        return f(s.get("P5"))

    def pts(x):
        return "–" if x is None else f"{100 * x:.1f}"

    def f(s):
        return "–" if not s or s.get("rate") is None else f"{100 * s['rate']:.1f}"
    for c in cells:
        s = res["cells"][c["name"]]
        mb = {k: (None if v is None else v["diff"]) for k, v in s.get("minus_baseline", {}).items()}
        p3 = s.get("P3", {})
        lines.append(f"| {c['name']} | {s['n_reps']} | {f(s.get('P1'))} | {f(s.get('P2'))} | {f(p3)} ({p3.get('errors', '–')}) | "
                     f"{f(s.get('P4'))} | {p5txt(c, s)} | "
                     f"{pts(mb.get('P1'))} | {pts(mb.get('P4'))} |")
    (out / "sim_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
