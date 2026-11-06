#!/usr/bin/env python3
"""Replicate-level check of the step 2 platform difference (REPLICATE-CHECK.md). Reruns the first replicates of the
eight random-design B 24 S-block cells with the step 2 runner unchanged (`run_grid.py`, `sim.py`), and compares
every rule's p value with the cloud rows (`runs_cloud/`) and the laptop rows (`runs/`).

  python replicate_check.py run --mode asis   --reps 20 --workers 4 --out DIR   # stamped code as is (x86 VM)
  python replicate_check.py run --mode x86map --reps 20 --workers 6 --out DIR   # laptop, GroupKFold replaced by
                                                                                # the x86 block-to-fold map
  python replicate_check.py compare --rows DIR --reps 20

--mode x86map replaces only the folds of the S-block split for 24 blocks: fold k holds out the blocks that
foldmap_x86_c2d.json assigns to fold k (GroupKFold's own fold order), with train and test indices in ascending
order as GroupKFold returns them. Everything else (data, seeds, rules) is the stamped code.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEP2 = Path(os.environ.get("STEP2_DIR", HERE.parents[1] / "results" / "step2-comparison"))
CELLS = ["c009", "c018", "c027", "c036", "c044", "c053", "c062", "c071"]
RULES = ["P1", "P2", "P3", "P4", "P5"]


def cell_list():
    cells = json.loads((STEP2 / "runs_cloud" / "CELLS.json").read_text())
    return [c for c in cells if c["name"][:4] in CELLS]


def patch_folds():
    """Make sim.folds('block', ...) with 24 blocks return the x86 map's folds."""
    import numpy as np
    import sim
    fmap = json.loads((HERE / "foldmap_x86_c2d.json").read_text())["maps"]["24"]
    orig = sim.folds

    def folds(kind, X, y, blocks, seed, n_block_folds=5):
        ub = np.unique(blocks)
        if kind != "block" or len(ub) != 24 or n_block_folds != 5:
            return orig(kind, X, y, blocks, seed, n_block_folds)
        pos = np.searchsorted(ub, blocks)
        f_of_trial = np.asarray(fmap)[pos]
        idx = np.arange(len(blocks))
        return [(idx[f_of_trial != k], idx[f_of_trial == k]) for k in range(5)]
    sim.folds = folds


def worker_main(argv):
    """Child process: optional patch, then the stamped run_grid.main() with the given argv."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(STEP2 / "code"))
    mode = argv.pop(0)
    if mode == "x86map":
        patch_folds()
    import run_grid
    sys.argv = ["run_grid.py"] + argv
    run_grid.main()


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1")
    procs = []
    for c in cell_list():
        for k in range(args.workers):
            cmd = [sys.executable, __file__, "_worker", args.mode, "--design", c["design"], "--B", str(c["B"]),
                   "--L", "20", "--tau-s", str(c["tau_s"]), "--drift", str(c["drift"]), "--trend", str(c["trend"]),
                   "--split", c["split"], "--reps", str(args.reps), "--n-perm", "200", "--seed", str(c["seed"]),
                   "--worker", str(k), "--of", str(args.workers), "--delta", "0.0", "--rules", "P1,P2,P3,P4,P5",
                   "--out", str(out / f"{c['name']}.w{k}.jsonl")]
            procs.append(subprocess.Popen(cmd, env=env))
            if len(procs) >= args.jobs:
                procs.pop(0).wait()
    for p in procs:
        p.wait()
    print("rows:", sum(len(f.read_text().splitlines()) for f in out.glob("*.jsonl")))


def rows_of(folder, name, reps):
    d = {}
    for f in Path(folder).glob(f"{name}.w*.jsonl"):
        for r in map(json.loads, f.read_text().splitlines()):
            if r["rep"] < reps:
                d[r["rep"]] = r
    return d


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= 1e-12 or (a != a and b != b)


def compare(args):
    tot = {"cloud": [0, 0], "laptop": [0, 0]}
    print("| cell | rule | identical to cloud | identical to laptop |\n|---|---|---|---|")
    for c in cell_list():
        mine = rows_of(args.rows, c["name"], args.reps)
        cloud = rows_of(STEP2 / "runs_cloud", c["name"], args.reps)
        lap = rows_of(STEP2 / "runs", c["name"], args.reps)
        reps = sorted(set(mine) & set(cloud) & set(lap))
        assert len(reps) == args.reps, (c["name"], len(mine), len(cloud), len(lap))
        for rule in RULES:
            nc = sum(same(mine[r].get(rule), cloud[r].get(rule)) for r in reps)
            nl = sum(same(mine[r].get(rule), lap[r].get(rule)) for r in reps)
            tot["cloud"][0] += nc; tot["cloud"][1] += len(reps)
            tot["laptop"][0] += nl; tot["laptop"][1] += len(reps)
            print(f"| {c['name']} | {rule} | {nc}/{len(reps)} | {nl}/{len(reps)} |")
    for k, (a, n) in tot.items():
        print(f"total identical to {k}: {a}/{n}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_worker":
        return worker_main(sys.argv[2:])
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--mode", choices=("asis", "x86map"), required=True)
    r.add_argument("--reps", type=int, default=20)
    r.add_argument("--workers", type=int, default=4, help="worker processes per cell")
    r.add_argument("--jobs", type=int, default=8, help="processes at once")
    r.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--rows", required=True)
    c.add_argument("--reps", type=int, default=20)
    a = ap.parse_args()
    run(a) if a.cmd == "run" else compare(a)


if __name__ == "__main__":
    main()
