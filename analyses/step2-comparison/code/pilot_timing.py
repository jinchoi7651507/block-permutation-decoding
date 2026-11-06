#!/usr/bin/env python3
"""Compute pilot (step 2 DESIGN.md §10): time one replicate of each rule in the primary-cell layout.
Timing only: p values are computed but NOT printed or saved (no false-positive rate is opened here).

  python pilot_timing.py [--n-perm 200] [--reps 3]
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

import sim

ap = argparse.ArgumentParser()
ap.add_argument("--n-perm", type=int, default=200)
ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--blocks", type=int, default=24)
ap.add_argument("--block-len", type=int, default=20)
args = ap.parse_args()

rng = np.random.default_rng([20261021, 0])
times = {k: [] for k in ("simulate", "P1", "P2", "P3", "P4", "P5")}
for rep in range(args.reps):
    blocks = sim.block_index(args.blocks, args.block_len)
    lab = sim.block_labels("random", args.blocks, rng)
    y = lab[blocks]
    t = time.time(); X = sim.simulate(len(y), tau=args.block_len, drift=0.3, rng=rng); times["simulate"].append(time.time() - t)
    est = sim.pipeline()
    fl = sim.folds("main", X, y, blocks, seed=rep)
    runs = blocks // (args.blocks // 4)
    t = time.time(); sim.p1_binomial(est, X, y, fl); times["P1"].append(time.time() - t)
    t = time.time(); sim.p2_sklearn(est, X, y, fl, args.n_perm, rep); times["P2"].append(time.time() - t)
    t = time.time(); sim.p3_within_run(est, X, y, fl, runs, args.n_perm, rng); times["P3"].append(time.time() - t)
    t = time.time(); sim.p4_train_only(est, X, y, fl, args.n_perm, rng); times["P4"].append(time.time() - t)
    t = time.time(); sim.block_permutation_test_score(est, X, y, blocks, fl, args.n_perm, rng); times["P5"].append(time.time() - t)
out = {k: float(np.median(v)) for k, v in times.items()}
out["per_replicate_s"] = sum(out.values())
out["settings"] = vars(args)
print(json.dumps(out, indent=1))
(Path(__file__).resolve().parent.parent / "pilot" ).mkdir(exist_ok=True)
(Path(__file__).resolve().parent.parent / "pilot" / "timing.json").write_text(json.dumps(out, indent=1))
