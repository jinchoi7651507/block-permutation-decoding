#!/usr/bin/env python3
"""Step 2b, DESIGN §6 E6 (alpha-power slope over the 16 min), as defined in RESULTS-NOTE.md §6 (specified at results
time, written before this script ran). Descriptive only.

  python posthoc_alpha_slope.py --features <features dir> --rows ../runs_cloud_2b_rerun49/runs --out ../results/alpha_slope.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

POSTERIOR = ("O1", "Oz", "O2", "PO3", "POz", "PO4", "PO7", "PO8", "P3", "Pz", "P4")


def slope(t, a, cond=None):
    X = np.column_stack([np.ones_like(t), t] + ([cond] if cond is not None else []))
    return float(np.linalg.lstsq(X, a, rcond=None)[0][1])


def boot_spearman(x, y, B=20000, seed=20261026):
    rng = np.random.default_rng(seed)
    n = len(x); r = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        if np.ptp(x[i]) > 0 and np.ptp(y[i]) > 0:
            r.append(stats.spearmanr(x[i], y[i]).statistic)
    return [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))], len(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p2 = {}; p5_half = {}; lbc = {}
    for f in sorted(Path(a.rows).glob("rows.w*.jsonl")):
        for l in f.read_text().splitlines():
            r = json.loads(l)
            if r.get("dropped") or r.get("variant") != "cleaned_s5" or r.get("readout") != "main" or r.get("split") != "main":
                continue
            if r["arm"] == "balanced" and r.get("P2") is not None:
                p2.setdefault(r["subject"], []).append(r["P2"] < 0.05)
                lbc.setdefault(r["subject"], []).append(abs(r["label_block_corr"]))
            if r["arm"] == "fixed_half":
                p5_half[r["subject"]] = r["P5"]
    subs = sorted(p2)
    out = {"definition": "RESULTS-NOTE.md §6", "subjects": []}
    for s in subs:
        z = np.load(Path(a.features) / f"{s}.npz")
        X, blk, cond = z["cleaned_s5_X"].astype(float), z["cleaned_s5_block"], z["cleaned_s5_cond"]
        chs = list(z["channels"]); n = len(chs)
        post = [chs.index(c) for c in POSTERIOR if c in chs]
        alpha = X[:, 2 * n:3 * n][:, post].mean(axis=1)
        t = np.empty(len(blk))
        for b in np.unique(blk):
            idx = np.where(blk == b)[0]
            t[idx] = b + (np.arange(len(idx)) + 0.5) / len(idx)
        ec = cond == 1
        out["subjects"].append({"subject": s, "slope": slope(t, alpha, cond.astype(float)),
                                "slope_ec": slope(t[ec], alpha[ec]), "slope_eo": slope(t[~ec], alpha[~ec]),
                                "p2_rate": float(np.mean(p2[s])), "fixed_half_p5": p5_half.get(s),
                                "mean_abs_label_block_corr": float(np.mean(lbc[s])), "n_post_channels": len(post)})
    S = out["subjects"]
    sl = np.array([x["slope"] for x in S]); ab = np.abs(sl); rate = np.array([x["p2_rate"] for x in S])
    h = np.array([x["fixed_half_p5"] for x in S], float)
    out["summary"] = {
        "n": len(S), "slope_median": float(np.median(sl)), "slope_range": [float(sl.min()), float(sl.max())],
        "share_negative": float(np.mean(sl < 0)),
        "slope_ec_median": float(np.median([x["slope_ec"] for x in S])), "slope_eo_median": float(np.median([x["slope_eo"] for x in S])),
        "spearman_abs_slope_vs_p2_rate": float(stats.spearmanr(ab, rate).statistic), "ci95_p2_and_valid_draws": boot_spearman(ab, rate),
        "spearman_abs_slope_vs_fixed_half_p5": float(stats.spearmanr(ab, h).statistic), "ci95_half_and_valid_draws": boot_spearman(ab, h)}
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main()
