#!/usr/bin/env python3
"""Step 2 simulation driver (DESIGN.md §15). Lists every simulation cell of §15 with its seed, writes the list to
runs/CELLS.json before anything runs, then runs each cell with run_grid.py split over worker processes
(--worker k --of W; one output file per worker; resumable because run_grid.py skips replicates already written).
It does not change sim.py or run_grid.py (stamped). Power cells (δ > 0) are not here: δ is chosen first on a
P5-only pilot (§15 "Power").

Cells (δ = 0, L = 20, 200 permutation draws):
  random design: tau_s {7, 20, 67, 160} x drift {0, 1, 2} x B {4, 12, 24} x split {main, tool, block};
                 1,000 replicates in the primary cell (tau_s 20, drift 1, B 12, main), 500 elsewhere.
  fixed order:   ABAB, ABBA, AABB x B {12, 24} x tau_s {20, 67} x drift 1 x trend {0, 0.5}; split main; 500.
  interleaved:   tau_s {7, 20, 67, 160} x drift {0, 1, 2}; B 12; split main; 500 (P5 not defined).
  baselines:     interleaved, drift 0, every tau_s x B x split not above (cells 144-175; appended 2026-10-21).
Seed of cell i (0-based, in the order above, primary cell first) = 2026000 + i.

  python run_sim_cells.py --list            # write runs/CELLS.json only
  python run_sim_cells.py --workers 6       # run all cells in order
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"


def cells():
    out = []
    prim = dict(design="random", B=12, tau_s=20, drift=1.0, trend=0.0, split="main", reps=1000)
    out.append(prim)
    for tau in (7, 20, 67, 160):
        for drift in (0.0, 1.0, 2.0):
            for B in (4, 12, 24):
                for split in ("main", "tool", "block"):
                    c = dict(design="random", B=B, tau_s=tau, drift=drift, trend=0.0, split=split, reps=500)
                    if all(c[k] == prim[k] for k in ("design", "B", "tau_s", "drift", "split")):
                        continue
                    out.append(c)
    for design in ("ABAB", "ABBA", "AABB"):
        for B in (12, 24):
            for tau in (20, 67):
                for trend in (0.0, 0.5):
                    out.append(dict(design=design, B=B, tau_s=tau, drift=1.0, trend=trend, split="main", reps=500))
    for tau in (7, 20, 67, 160):
        for drift in (0.0, 1.0, 2.0):
            out.append(dict(design="interleaved", B=12, tau_s=tau, drift=drift, trend=0.0, split="main", reps=500))
    # Appended 2026-10-21 22:13 KST (commit ef0b45e), before they run (cells 144+; indices of earlier cells unchanged): interleaved,
    # drift 0 baselines for every tau_s x B x split not covered above. §15 subtracts from every P1/P4 rate "its
    # interleaved-label, drift-0 baseline in the same tau_s/B/split", but its interleaved arm lists only B 12 / main.
    for tau in (7, 20, 67, 160):
        for B in (4, 12, 24):
            for split in ("main", "tool", "block"):
                if B == 12 and split == "main":
                    continue
                out.append(dict(design="interleaved", B=B, tau_s=tau, drift=0.0, trend=0.0, split=split, reps=500))
    # Appended 2026-10-21 22:38 KST (commit f0dc09a; addendum 1 §1, a cell beyond §15, before it runs): the primary-cell layout with
    # the sign-randomised trend 0.5 (§15 "secondary arm"; the §15 grid gave trend 0.5 only to the fixed-order designs).
    out.append(dict(design="random", B=12, tau_s=20, drift=1.0, trend=0.5, split="main", reps=500))
    for i, c in enumerate(out):
        c["seed"] = 2026000 + i
        c["name"] = (f"c{i:03d}_{c['design']}_B{c['B']}_tau{c['tau_s']}_d{c['drift']:g}_t{c['trend']:g}_{c['split']}")
    return out


DELTAS_PILOT = (0.1, 0.2, 0.3, 0.5, 0.8)


def power_pilot_cells():
    """Addendum 1 §1b: P5-only pilot, primary-cell layout, 50 replicates per delta, seeds 2027000 + i."""
    out = []
    for i, d in enumerate(DELTAS_PILOT):
        out.append(dict(design="random", B=12, tau_s=20, drift=1.0, trend=0.0, split="main", reps=50, delta=d,
                        rules="P5", seed=2027000 + i, name=f"pp{i}_delta{d:g}"))
    return out


def power_cells(d_mid, d_large):
    """Addendum 1 §1b: all rules, primary-cell layout, 1,000 replicates at the two chosen deltas."""
    return [dict(design="random", B=12, tau_s=20, drift=1.0, trend=0.0, split="main", reps=1000, delta=d,
                 rules="P1,P2,P3,P4,P5", seed=2027100 + j, name=f"pw{j}_delta{d:g}") for j, d in enumerate((d_mid, d_large))]


def run_cell(c, workers, py):
    procs = []
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1", PYTHONWARNINGS="ignore::UserWarning")  # sklearn "groups ignored" warnings only
    for k in range(workers):
        out = RUNS / f"{c['name']}.w{k}.jsonl"
        cmd = [py, str(HERE / "run_grid.py"), "--design", c["design"], "--B", str(c["B"]), "--L", "20",
               "--tau-s", str(c["tau_s"]), "--drift", str(c["drift"]), "--trend", str(c["trend"]),
               "--split", c["split"], "--reps", str(c["reps"]), "--n-perm", "200", "--seed", str(c["seed"]),
               "--worker", str(k), "--of", str(workers), "--out", str(out),
               "--delta", str(c.get("delta", 0.0)), "--rules", c.get("rules", "P1,P2,P3,P4,P5")]
        procs.append(subprocess.Popen(cmd, env=env, stderr=open(RUNS / f"{c['name']}.w{k}.err", "a")))
    return [p.wait() for p in procs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", default=None, help="comma-separated cell indices, or a range a-b")
    ap.add_argument("--power-pilot", action="store_true")
    ap.add_argument("--power", default=None, help="d_mid,d_large (chosen from the pilot by choose_delta.py)")
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    cs = cells()
    (RUNS / "CELLS.json").write_text(json.dumps(cs, indent=1))
    print(len(cs), "cells;", sum(c["reps"] for c in cs), "replicates")
    if args.list:
        return
    if args.power_pilot:
        sel = power_pilot_cells()
        (RUNS / "POWER_PILOT_CELLS.json").write_text(json.dumps(sel, indent=1))
    elif args.power:
        dm, dl = (float(x) for x in args.power.split(","))
        sel = power_cells(dm, dl)
        (RUNS / "POWER_CELLS.json").write_text(json.dumps(sel, indent=1))
    elif args.only is None:
        sel = cs
    elif "-" in args.only:
        a, b = (int(x) for x in args.only.split("-"))
        sel = cs[a:b + 1]
    else:
        sel = [cs[int(i)] for i in args.only.split(",")]
    log = RUNS / "run.log"
    for c in sel:
        t = time.time()
        with log.open("a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} start {c['name']} seed {c['seed']}\n")
        rc = run_cell(c, args.workers, sys.executable)
        with log.open("a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} done  {c['name']} rc {rc} {time.time() - t:.0f} s\n")


if __name__ == "__main__":
    main()
