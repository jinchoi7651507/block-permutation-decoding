#!/usr/bin/env python3
"""Step 2 addendum 3 §2a: write the replicate datasets that the real tools (CoSMoMVPA, PyMVPA) and the Python
reference rows read. Same generator lines as run_grid.one (copied; the stamped file is not edited).

  python add3_tools_data.py --out ../runs_add3/tools/data [--layouts 1,2,3] [--reps 500] [--worker k --of n]

Layouts: L1 random balanced B 12, L2 fixed order AABB B 12 (both tau_s 20, drift 1), L3 interleaved labels B 12,
tau_s 20, drift 0, L4 balanced runs B 12 (6 runs of 2 blocks, one per class, order random within each run; tau_s 20,
drift 1). L = 20, trend 0. Seed of layout j: default_rng([2029000 + j, rep]). One .mat per replicate: X (trials x
units counts), targets (1/2), chunks (runs: L1-L3 four runs of three consecutive blocks, L4 six runs of two), blocks
(0-based), n_units, seed. Written atomically (temporary name, then rename); existing files are skipped (resumable);
the content does not depend on the worker split. --manifest writes the SHA-256 of every file (after all workers).
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.io import savemat

import sim

HERE = Path(__file__).resolve().parent
LAYOUTS = {1: dict(design="random", B=12, tau_s=20.0, drift=1.0),
           2: dict(design="AABB", B=12, tau_s=20.0, drift=1.0),
           3: dict(design="interleaved", B=12, tau_s=20.0, drift=0.0),
           4: dict(design="balanced_runs", B=12, tau_s=20.0, drift=1.0)}
L_TRIALS, TREND = 20, 0.0


def calibration():
    cal = json.loads((HERE.parent / "calib_v2" / "CALIBRATION_v2.json").read_text())
    tgt = HERE.parent / "calib_v2" / "allen_targets.json"
    cal["_rows"] = json.loads(tgt.read_text())["rows"] if tgt.exists() else [{"n_units": 89}]
    return cal


def replicate(j, rep, cal, seed_base=2029000):
    """Same lines as run_grid.one up to the counts (design, B, L, tau_s, drift, trend, delta 0)."""
    lay = LAYOUTS[j]
    rng = np.random.default_rng([seed_base + j, rep])
    p = dict(cal["best"])
    p["tau_s"] = lay["tau_s"]
    p["sigma_s"] *= lay["drift"]
    p["sigma_u"] *= lay["drift"]
    sizes = [r["n_units"] for r in cal["_rows"]]
    n_units = int(rng.choice(sizes))
    B, L = lay["B"], L_TRIALS
    blocks = sim.block_index(B, L)
    if lay["design"] == "interleaved":
        y = rng.permutation(np.arange(B * L) % 2)
    elif lay["design"] == "balanced_runs":                    # new layout (not in run_grid): one A and one B block per run
        lab = np.concatenate([rng.permutation([0, 1]) for _ in range(B // 2)])
        y = lab[blocks]
    else:
        lab = sim.block_labels(lay["design"], B, rng)
        y = lab[blocks]
    X = sim.simulate2(B * L, rng, n_units=n_units, base_rate=cal["base_rate"], trend=TREND, labels=None, delta=0.0, **p)
    runs = blocks // 2 if lay["design"] == "balanced_runs" else blocks // max(1, B // 4)
    return X, y, blocks, runs, n_units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--layouts", default="1,2,3,4")
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--seed-base", type=int, default=2029000, help="synthetic tests only; the study uses 2029000")
    ap.add_argument("--manifest", action="store_true", help="write MANIFEST.sha256 of all files and exit")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.manifest:
        import hashlib
        lines = [f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}" for f in sorted(out.glob("L*_r*.mat"))]
        (out / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
        print(len(lines), "files")
        return
    cal = calibration()
    k = 0
    for j in map(int, args.layouts.split(",")):
        for rep in range(args.reps):
            k += 1
            if (k - 1) % args.of != args.worker:
                continue
            f = out / f"L{j}_r{rep:03d}.mat"
            if f.exists():
                continue
            X, y, blocks, runs, n_units = replicate(j, rep, cal, args.seed_base)
            tmp = f.with_name(f.name + ".tmp")
            savemat(tmp, {"X": X, "targets": (y + 1).astype(float)[:, None], "chunks": (runs + 1).astype(float)[:, None],
                        "blocks": blocks.astype(float)[:, None], "n_units": float(n_units),
                        "seed": np.array([args.seed_base + j, rep], float)}, do_compression=True)
            tmp.rename(f)


if __name__ == "__main__":
    main()
