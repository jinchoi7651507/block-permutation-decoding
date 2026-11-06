#!/usr/bin/env python3
"""Step 2 grid runner (DESIGN.md §5a, §13-§14). One call = one cell; one JSON line per replicate with the p of
every rule, error flags and seeds. Rules: P1 binomial, P2 sklearn permutation_test_score, P3 within-run
(CoSMoMVPA rule; None = the tool's error), P4 training labels only, P5 block permutation (rerun).

  python run_grid.py --design random --B 12 --L 20 --tau-s 20 --drift 1 --split main --reps 1000 --out cell.jsonl
       [--delta 0 --n-perm 200 --seed 1 --worker 0 --of 1 --calib ../calib_v2/CALIBRATION_v2.json]

Generator parameters come from the calibration file (Allen level); --drift scales the slow components
(sigma_s and sigma_u) by {0, 1, 2}; --tau-s overrides the slow time constant (grid on tau_s, L fixed);
n_units is drawn per replicate from the Allen area sizes in the calibration targets; trend sign random (trend
from --trend, default 0). P5 null set: for 'random' designs a fresh balanced random assignment per draw (exact
by randomisation, sanity cell); for fixed-order designs all balanced assignments (the real test); for
'interleaved' P5 is not defined (labels vary within blocks).
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

import sim


def balanced_draw(B):
    def draw(rng):
        a = np.zeros(B, int)
        a[rng.choice(B, B // 2, replace=False)] = 1
        return a
    return draw


def one(args, cal, rep):
    rng = np.random.default_rng([args.seed, rep])
    p = dict(cal["best"])
    if args.tau_s is not None:
        p["tau_s"] = args.tau_s
    p["sigma_s"] *= args.drift
    p["sigma_u"] *= args.drift
    sizes = [r["n_units"] for r in cal["_rows"]]
    n_units = int(rng.choice(sizes))
    B, L = args.B, args.L
    blocks = sim.block_index(B, L)
    if args.design == "interleaved":
        y = rng.permutation(np.arange(B * L) % 2)
    else:
        lab = sim.block_labels(args.design, B, rng)
        y = lab[blocks]
    X = sim.simulate2(B * L, rng, n_units=n_units, base_rate=cal["base_rate"], trend=args.trend,
                      labels=y if args.delta > 0 else None, delta=args.delta, **p)
    est = sim.pipeline()
    if args.split == "main":
        fl = sim.folds("main", X, y, blocks, seed=rep)
    elif args.split == "tool":
        fl = sim.Resplit(sim.splitter("tool", rep), blocks)
    elif args.split == "block":
        fl = sim.folds("block", X, y, blocks, seed=rep, n_block_folds=min(5, B))
    else:
        raise ValueError(args.split)
    runs = blocks // max(1, B // 4)
    out = {"rep": rep, "n_units": n_units, "seed": [args.seed, rep]}
    R = set(args.rules.split(","))
    if "P1" in R:
        out["P1"] = sim.p1_binomial(est, X, y, fl)
    if "P2" in R:
        out["P2"] = sim.p2_sklearn(est, X, y, fl, args.n_perm, rep)
    if "P3" in R:
        p3 = sim.p3_within_run(est, X, y, fl, runs, args.n_perm, rng)
        out["P3"], out["P3_error"] = (None, True) if p3 is None else (p3, False)
    if "P4" in R:
        out["P4"] = sim.p4_train_only(est, X, y, fl, args.n_perm, rng)
    if "P5" not in R:
        pass
    elif args.design == "interleaved":
        out["P5"] = None
    else:
        draw = balanced_draw(B) if args.design == "random" else balanced_draw(B)
        _, _, out["P5"] = sim.block_permutation_test_score(est, X, y, blocks, fl, args.n_perm, rng, draw=draw)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True, choices=("random", "ABAB", "ABBA", "AABB", "interleaved"))
    ap.add_argument("--B", type=int, required=True)
    ap.add_argument("--L", type=int, default=20)
    ap.add_argument("--tau-s", type=float, default=None)
    ap.add_argument("--drift", type=float, default=1.0)
    ap.add_argument("--trend", type=float, default=0.0)
    ap.add_argument("--split", default="main", choices=("main", "tool", "block"))
    ap.add_argument("--delta", type=float, default=0.0)
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--rules", default="P1,P2,P3,P4,P5", help="subset of rules (validation runs use P5 only in study cells)")
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--calib", default=str(Path(__file__).resolve().parent.parent / "calib_v2" / "CALIBRATION_v2.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cal = json.loads(Path(args.calib).read_text())
    tgt = Path(args.calib).with_name("allen_targets.json")
    cal["_rows"] = json.loads(tgt.read_text())["rows"] if tgt.exists() else [{"n_units": 89}]
    out = Path(args.out)
    done = {json.loads(l)["rep"] for l in out.read_text().splitlines()} if out.exists() else set()
    for rep in range(args.reps):
        if rep % args.of != args.worker or rep in done:
            continue
        t = time.time()
        row = one(args, cal, rep)
        row["cell"] = {k: v for k, v in vars(args).items() if k not in ("worker", "of", "out", "calib")}
        row["seconds"] = round(time.time() - t, 2)
        with out.open("a") as fh:
            fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
