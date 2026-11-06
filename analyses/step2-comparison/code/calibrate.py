#!/usr/bin/env python3
"""Allen calibration of the step 2 generator (DESIGN.md §5a), written before running (2026-10-21 01:40 KST).

What: per (session, std6 area) with step 1 shared24 rows, the same 2-s spontaneous pseudo-trial counts as
step 1 (spont_onsets(path, 8), tax.area_counts). Two statistics:
  tau_hat  time constant (in trials) of the first principal component of the z-scored counts: autocorrelation
           at lags 1..5 computed within each spontaneous epoch (contiguous trials), fitted by least squares with
           exp(-lag / tau) on the lags whose autocorrelation is positive.
  slow     median over units of the excess variance of 10-trial window means, normalised by the squared mean:
           (var(window means) - mean / 10) / mean**2  (Poisson part removed).
Then the generator's drift scale is chosen so that the same `slow` statistic on simulated data (same tau_hat,
base rate = median Allen mean count, 480 trials, 100 units, trend 0.5) matches the Allen median; grid search
over drift in 0.02 steps, 200 simulated sessions per grid value.
Summary: per-mouse median of each statistic, then the median over mice ("Allen level"); quartiles reported.
This calibrates a nuisance parameter of the simulation; no test result is computed.

  python calibrate.py --dir <allen nwb folder> --out ../calib
"""
import argparse
import importlib.util
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
W = 10


def epochs_of(blk24):
    return blk24 // 8                     # spont_onsets: block = epoch * 8 + k


def tau_hat(counts, ep):
    z = (counts - counts.mean(1, keepdims=True)) / np.where(counts.std(1, keepdims=True) > 0, counts.std(1, keepdims=True), 1)
    u, s, vt = np.linalg.svd(z - z.mean(1, keepdims=True), full_matrices=False)
    pc = vt[0] * s[0]
    rho = []
    for lag in range(1, 6):
        num = den = 0.0
        for e in np.unique(ep):
            x = pc[ep == e]
            x = x - x.mean()
            if len(x) > lag:
                num += float((x[:-lag] * x[lag:]).sum())
                den += float((x * x).sum()) * (len(x) - lag) / len(x)
        rho.append(num / den if den > 0 else np.nan)
    rho = np.array(rho)
    lags = np.arange(1, 6)
    ok = np.isfinite(rho) & (rho > 0)
    if ok.sum() < 2:
        return float("nan"), rho.tolist()
    slope = np.sum(lags[ok] * -np.log(rho[ok])) / np.sum(lags[ok] ** 2)      # least squares through 0 on -log rho
    return float(1 / slope) if slope > 0 else float("inf"), rho.tolist()


def slow_stat(counts, ep):
    vals = []
    for u in range(counts.shape[0]):
        x, m = counts[u], counts[u].mean()
        if m <= 0:
            continue
        wm = []
        for e in np.unique(ep):
            xe = x[ep == e]
            nw = len(xe) // W
            wm += list(xe[:nw * W].reshape(nw, W).mean(1))
        vals.append((np.var(wm, ddof=1) - m / W) / m ** 2)
    return float(np.median(vals))


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
    per = []
    for sid in sorted(want):
        path = Path(args.dir) / f"session_{sid}.nwb"
        ids, spikes, area, onset, ori = emn.load_session(path)
        good, _ = tax.unit_table(path)
        area = np.where(good, area, "excluded-quality")
        on24, blk24 = dec.spont_onsets(path, 8)
        ep = epochs_of(blk24)
        for a in sorted(want[sid]):
            c24, _ = tax.area_counts(spikes, np.where(area == a)[0], on24)
            t, rho = tau_hat(c24.astype(float), ep)
            per.append({"session": sid, "area": a, "n_units": int(c24.shape[0]), "tau": t, "rho": rho,
                        "slow": slow_stat(c24.astype(float), ep), "mean_count": float(np.median(c24.mean(1)))})
            print(sid, a, round(t, 2), round(per[-1]["slow"], 4), flush=True)
    (out / "calib_rows.json").write_text(json.dumps(per, indent=1))

    def mouse_median(key):
        by = {}
        for r in per:
            if np.isfinite(r[key]):
                by.setdefault(r["session"], []).append(r[key])
        m = np.array([np.median(v) for v in by.values()])
        return float(np.median(m)), [float(q) for q in np.quantile(m, [0.25, 0.75])], len(m)

    tau, tau_q, nm = mouse_median("tau")
    slow, slow_q, _ = mouse_median("slow")
    base, _, _ = mouse_median("mean_count")
    rng = np.random.default_rng([20261021, 7])
    grid = np.round(np.arange(0.02, 1.0001, 0.02), 2)
    sims = {}
    for d in grid:
        v = []
        for _ in range(200):
            X = sim.simulate(480, tau=max(tau, 1e-3), drift=float(d), rng=rng, base_rate=base)
            v.append(slow_stat(X.T, np.repeat(np.arange(3), 160)))
        sims[float(d)] = float(np.median(v))
    best = min(sims, key=lambda d: abs(sims[d] - slow))
    edge = best in (float(grid[0]), float(grid[-1]))
    res = {"tau_trials": tau, "tau_iqr_over_mice": tau_q, "slow": slow, "slow_iqr_over_mice": slow_q, "n_mice": nm,
           "base_mean_count": base, "drift_allen": best, "drift_2x": 2 * best, "sim_slow_by_drift": sims,
           "trial_s": 2.0, "window_trials": W, "best_at_grid_edge": edge}
    (out / "CALIBRATION.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "sim_slow_by_drift"}, indent=1))


if __name__ == "__main__":
    main()
