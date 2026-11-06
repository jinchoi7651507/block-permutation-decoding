#!/usr/bin/env python3
"""Allen calibration v2 of the step 2 generator (DESIGN.md §13-§14; v2 statistician review musts 1-4).
Design written before running (2026-10-21 11:26 KST). Spontaneous activity only; no labels are used.

Targets (per Allen area, same 2-s pseudo-trial counts as step 1, means removed within each spontaneous epoch):
  acf   autocorrelation of the first principal component of the z-scored counts at lags 1, 2, 5, 10, 20, 40
        trials, computed within epochs and pooled
  slow  median over units of (var(10-trial window means) - mean/10) / mean**2, windows within epochs
  share fraction of the variance of the z-scored counts on the first principal component
Per mouse: median over its areas. Allen level: median over mice of each target; sd over mice scales the distance.
Simulation: generator `sim.simulate2` (fast shared OU + slow shared OU + unit-specific slow OU, trend 0) on the
median Allen layout (epoch lengths and gaps in trials, the process running through the gaps), n_units 89,
base rate = median Allen mean count. The SAME estimators are applied to simulated data.
Grid (fixed now): tau_f {1, 2, 4}; sigma_f {0.2, 0.4, 0.6}; tau_s {10, 20, 40, 80, 160}; sigma_s {0.2, 0.4, 0.6, 0.8};
sigma_u {0, 0.2, 0.4}; 20 simulated sessions per point; statistic = median over the 20.
Distance = sum over the 8 targets of ((sim - Allen) / sd over mice)**2. Best point = Allen level. Per-mouse best
points give the IQR. Identification check for tau_s: the profile (minimum distance over the other parameters) at
each tau_s value; if the best tau_s is within 1 distance unit of a neighbour, tau_s is reported as a range.
Split-half check: odd- vs even-indexed mice fitted separately.

  python calibrate_v2.py --dir <allen nwb folder> --out ../calib_v2
"""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np

import sim

HERE = Path(__file__).resolve().parent
S1 = HERE.parents[1] / "step1-decomposition"
_spec = importlib.util.spec_from_file_location("dec", S1 / "code" / "decompose.py")
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)
tax, emn = dec.tax, dec.emn
LAGS = (1, 2, 5, 10, 20, 40)
W = 10
GRID = dict(tau_f=(1, 2, 4), sigma_f=(0.2, 0.4, 0.6), tau_s=(10, 20, 40, 80, 160), sigma_s=(0.2, 0.4, 0.6, 0.8),
            sigma_u=(0, 0.2, 0.4))
N_SIM = 20


def stats(counts, ep):
    """counts units x trials; ep epoch index per trial. Returns 8 targets."""
    c = counts.astype(float).copy()
    for e in np.unique(ep):
        c[:, ep == e] -= c[:, ep == e].mean(1, keepdims=True)
    sd = counts.std(1, keepdims=True)
    z = c / np.where(sd > 0, sd, 1)
    u, s, vt = np.linalg.svd(z, full_matrices=False)
    share = float(s[0] ** 2 / np.sum(s ** 2))
    pc = vt[0] * s[0]
    acf = []
    for lag in LAGS:
        num = den = 0.0
        for e in np.unique(ep):
            x = pc[ep == e]
            if len(x) > lag:
                num += float((x[:-lag] * x[lag:]).sum()) / (len(x) - lag)
                den += float((x * x).sum()) / len(x)
        acf.append(num / den if den > 0 else np.nan)
    vals = []
    for i in range(counts.shape[0]):
        x, m = counts[i].astype(float), counts[i].mean()
        if m <= 0:
            continue
        wm = []
        for e in np.unique(ep):
            xe = x[ep == e]
            nw = len(xe) // W
            if nw:
                wm += list(xe[:nw * W].reshape(nw, W).mean(1))
        if len(wm) > 1:
            vals.append((np.var(wm, ddof=1) - m / W) / m ** 2)
    return acf + [float(np.median(vals)), share]


def layout(blk24, on24):
    """Epoch lengths (trials) and gaps (trials, from onset times at 2 s per trial)."""
    ep = blk24 // 8
    lens = [int((ep == e).sum()) for e in np.unique(ep)]
    starts = [on24[ep == e][0] for e in np.unique(ep)]
    ends = [on24[ep == e][-1] for e in np.unique(ep)]
    gaps = [max(0, int(round((starts[i + 1] - ends[i]) / tax.PSEUDO_TRIAL_S)) - 1) for i in range(len(lens) - 1)]
    return lens, gaps


def keep_index(lens, gaps):
    idx, t, ep = [], 0, []
    for i, L in enumerate(lens):
        idx += list(range(t, t + L)); ep += [i] * L
        t += L + (gaps[i] if i < len(gaps) else 0)
    return np.array(idx), np.array(ep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(exist_ok=True)
    rows = [json.loads(l) for l in (S1 / "runs" / "rows.jsonl").read_text().splitlines()]
    want = {}
    for r in rows:
        if "shared24" in r:
            want.setdefault(r["session"], []).append(r["area"])
    per, lays = [], []
    for sid in sorted(want):
        path = Path(args.dir) / f"session_{sid}.nwb"
        ids, spikes, area, onset, ori = emn.load_session(path)
        good, _ = tax.unit_table(path)
        area = np.where(good, area, "excluded-quality")
        on24, blk24 = dec.spont_onsets(path, 8)
        ep = blk24 // 8
        lays.append(layout(blk24, on24))
        for a in sorted(want[sid]):
            c24, _ = tax.area_counts(spikes, np.where(area == a)[0], on24)
            per.append({"session": sid, "area": a, "n_units": int(c24.shape[0]), "t": stats(c24, ep),
                        "mean_count": float(np.median(c24.mean(1)))})
        print(sid, flush=True)
    (out / "allen_targets.json").write_text(json.dumps({"rows": per, "layouts": lays}, indent=1))
    sids = sorted({r["session"] for r in per})
    mouse = np.array([np.median([r["t"] for r in per if r["session"] == s], axis=0) for s in sids])
    allen, sdm = np.median(mouse, 0), mouse.std(0, ddof=1)
    base = float(np.median([r["mean_count"] for r in per]))
    lens = [int(np.median([l[0][i] for l in lays])) for i in range(3)]
    gaps = [int(np.median([l[1][i] for l in lays])) for i in range(2)]
    keep, ep_sim = keep_index(lens, gaps)
    rng = np.random.default_rng([20261021, 2])
    table = []
    keys = list(GRID)
    for combo in itertools.product(*[GRID[k] for k in keys]):
        p = dict(zip(keys, combo))
        st = [stats(sim.simulate2(len(keep), rng, base_rate=base, keep=keep, **p).T, ep_sim) for _ in range(N_SIM)]
        table.append({"params": p, "stat": np.median(np.array(st), 0).tolist()})
    S = np.array([t["stat"] for t in table])

    def best(target):
        d = np.nansum(((S - target) / sdm) ** 2, axis=1)
        return int(np.argmin(d)), d

    bi, d = best(allen)
    prof = {ts: float(min(d[i] for i, t in enumerate(table) if t["params"]["tau_s"] == ts)) for ts in GRID["tau_s"]}
    order = sorted(prof, key=prof.get)
    tau_s_range = [ts for ts in GRID["tau_s"] if prof[ts] <= prof[order[0]] + 1.0]
    per_mouse = [table[best(m)[0]]["params"] for m in mouse]
    half = {h: table[best(np.median(mouse[h::2], 0))[0]]["params"] for h in (0, 1)}
    res = {"targets": ["acf%d" % l for l in LAGS] + ["slow", "pc1_share"], "allen": allen.tolist(), "sd_over_mice": sdm.tolist(),
           "n_mice": len(sids), "base_rate": base, "layout": {"epoch_lengths": lens, "gaps": gaps},
           "best": table[bi]["params"], "best_stat": table[bi]["stat"], "best_distance": float(d[bi]),
           "tau_s_profile": prof, "tau_s_within_1": tau_s_range,
           "per_mouse_iqr": {k: [float(np.quantile([pm[k] for pm in per_mouse], q)) for q in (0.25, 0.5, 0.75)] for k in keys},
           "split_half": half, "at_grid_edge": {k: table[bi]["params"][k] in (GRID[k][0], GRID[k][-1]) for k in keys}}
    (out / "CALIBRATION_v2.json").write_text(json.dumps(res, indent=1))
    (out / "sim_table.json").write_text(json.dumps(table))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
