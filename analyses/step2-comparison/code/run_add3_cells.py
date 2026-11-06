#!/usr/bin/env python3
"""Step 2 addendum 3 §1: simulation cells beyond §15 (author decision 2026-10-22): the fixed-order designs and the
interleaved-label designs under S-tool and S-block (§15 and addendum 1 ran them under S-main only). Lists every cell
with its seed, writes the list to runs_add3/CELLS-ADD3.json before anything runs, then runs each cell with the
stamped run_grid.py through run_sim_cells.run_cell (unchanged), writing to runs_add3/ instead of runs/.

  python run_add3_cells.py --list            # write runs_add3/CELLS-ADD3.json only
  python run_add3_cells.py --workers 56      # run every cell (resumable: run_grid.py skips replicates already written)

Cells (64, 500 replicates each, 200 permutation draws): fixed order ABAB/ABBA/AABB x B 12, 24 x tau_s 20, 67 x trend
0, 0.5, drift 1 (the §15 fixed-order arm) x split tool, block; interleaved labels, B 12, tau_s 7, 20, 67, 160 x drift
1, 2 x split tool, block (the drift-0 interleaved cells under tool and block are cells 144-175 of runs/CELLS.json).
Seed of cell i = 2,028,000 + i. Log: runs_add3/run.log (return code of every worker).
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_sim_cells  # noqa: E402

OUT = HERE.parent / "runs_add3"


def cells():
    out = []
    for split in ("tool", "block"):
        for design in ("ABAB", "ABBA", "AABB"):
            for B in (12, 24):
                for tau in (20, 67):
                    for trend in (0.0, 0.5):
                        out.append(dict(design=design, B=B, tau_s=tau, drift=1.0, trend=trend, split=split, reps=500))
        for tau in (7, 20, 67, 160):
            for drift in (1.0, 2.0):
                out.append(dict(design="interleaved", B=12, tau_s=tau, drift=drift, trend=0.0, split=split, reps=500))
    for i, c in enumerate(out):
        c["seed"] = 2028000 + i
        c["name"] = (f"a{i:03d}_{c['design']}_B{c['B']}_tau{c['tau_s']}_d{c['drift']:g}_t{c['trend']:g}_{c['split']}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    run_sim_cells.RUNS = OUT                       # run_cell writes its files and .err logs under RUNS
    cs = cells()
    (OUT / "CELLS-ADD3.json").write_text(json.dumps(cs, indent=1))
    print(len(cs), "cells;", sum(c["reps"] for c in cs), "replicates")
    if args.list:
        return
    py = sys.executable
    for c in cs:
        with (OUT / "run.log").open("a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} start {c['name']} seed {c['seed']}\n")
        t = time.time()
        rc = run_sim_cells.run_cell(c, args.workers, py)
        with (OUT / "run.log").open("a") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} done  {c['name']} rc {rc} {time.time() - t:.0f} s\n")


if __name__ == "__main__":
    main()
