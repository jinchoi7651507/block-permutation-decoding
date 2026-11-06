#!/usr/bin/env python3
"""Step 2 addendum 3 §2b reference rows: on the same replicate files as the tools, the stamped pipeline and the
stamped sim.py rules with leave-one-run-out folds: P3 port (within-run), P4 port (training labels only), P5
(block labels permuted between blocks, training and held-out together, rerun) with 200 fresh draws from the
layout's randomisation set: L1 and L2 any balanced assignment of the 12 blocks (run_grid.balanced_draw, as the
stamped §15 runner: exact by randomisation for L1, an approximation of the full enumeration for L2), L4 the order
of the two blocks of each run flipped at random (the L4 design's own randomisation); undefined for L3. 200 draws,
one rng default_rng([2029000 + j, rep, 5]) shared by P3, P4, P5 in that order (P4 draws depend on whether P3
errored; harmless). One JSON line per replicate; resumable.

  python add3_reference.py --data ../runs_add3/tools/data --out ../runs_add3/tools/ref.w<k>.jsonl [--worker k --of n]
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from scipy.io import loadmat

import sim
from run_grid import balanced_draw


def load(f):
    m = loadmat(f)
    y = m["targets"].ravel().astype(int) - 1
    runs = m["chunks"].ravel().astype(int) - 1
    blocks = m["blocks"].ravel().astype(int)
    return m["X"].astype(float), y, runs, blocks


def loro_folds(runs):
    return [(np.where(runs != r)[0], np.where(runs == r)[0]) for r in np.unique(runs)]


def row(f, n_perm):
    j, rep = map(int, re.match(r"L(\d)_r(\d+)\.mat", f.name).groups())
    X, y, runs, blocks = load(f)
    est, fl = sim.pipeline(), loro_folds(runs)
    rng = np.random.default_rng([2029000 + j, rep, 5])
    out = {"layout": j, "rep": rep}
    p3 = sim.p3_within_run(est, X, y, fl, runs, n_perm, rng)
    out["P3port"], out["P3port_error"] = (None, True) if p3 is None else (p3, False)
    out["P4port"] = sim.p4_train_only(est, X, y, fl, n_perm, rng)
    if j == 3:
        out["P5"] = None
    elif j == 4:
        nr = len(np.unique(blocks)) // 2
        def flip(r):                                     # block labels: per run, (0, 1) or (1, 0)
            return np.concatenate([r.permutation([0, 1]) for _ in range(nr)])
        _, _, out["P5"] = sim.block_permutation_test_score(est, X, y, blocks, fl, n_perm, rng, draw=flip)
    else:
        _, _, out["P5"] = sim.block_permutation_test_score(est, X, y, blocks, fl, n_perm, rng,
                                                           draw=balanced_draw(len(np.unique(blocks))))
    out["obs_acc"] = sim.cv_correct(est, X, y, fl)[1]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    args = ap.parse_args()
    out = Path(args.out)
    done = {(r["layout"], r["rep"]) for r in map(json.loads, out.read_text().splitlines())} if out.exists() else set()
    files = sorted(Path(args.data).glob("L*_r*.mat"))
    for i, f in enumerate(files):
        if i % args.of != args.worker:
            continue
        j, rep = map(int, re.match(r"L(\d)_r(\d+)\.mat", f.name).groups())
        if (j, rep) in done:
            continue
        r = row(f, args.n_perm)
        with out.open("a") as fh:
            fh.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
