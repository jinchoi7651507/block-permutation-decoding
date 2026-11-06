#!/usr/bin/env python3
"""Step 2 addendum 3 §1 summary: the cells beyond §15 (fixed-order and interleaved designs under S-tool and S-block).
Written before any of these cells was run. Per cell and rule, as summarize_sim.cell_summary (rate of p < 0.05,
Wilson 95% interval, Monte Carlo 99% band of 5%, P3 error share, P5 fails for fixed-order trend-0 cells). For the
fixed-order cells, P1 and P4 minus the pooled interleaved drift-0 baseline of the same B and split (cells 144-175 of
the main grid, read from --main-runs), 95% bootstrap as summarize_sim (2,000 draws, seed 20261022 + 3). These cells
are reported as cells beyond §15 (descriptive).

  python summarize_add3.py --runs ../runs_add3 --main-runs ../runs_cloud --out ../results
"""
import argparse
import json
from pathlib import Path

import numpy as np

from summarize_sim import BOOT_SEED, cell_summary, finite, load


def f(r):
    return "–" if not r or r.get("rate") is None else f"{100 * r['rate']:.1f}"


def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent.parent
    ap.add_argument("--runs", default=str(root / "runs_add3"))
    ap.add_argument("--main-runs", default=str(root / "runs_cloud"))
    ap.add_argument("--out", default=str(root / "results"))
    args = ap.parse_args()
    runs, main_runs, out = Path(args.runs), Path(args.main_runs), Path(args.out)
    out.mkdir(exist_ok=True)
    cells = json.loads((runs / "CELLS-ADD3.json").read_text())
    main_cells = json.loads((main_runs / "CELLS.json").read_text())
    brng = np.random.default_rng(BOOT_SEED + 3)

    def baseline(B, split):
        return [r for c in main_cells if c["design"] == "interleaved" and c["drift"] == 0 and c["trend"] == 0
                and c["B"] == B and c["split"] == split for r in load(main_runs, c)]

    def diff_ci(a_rows, b_rows, rule):
        a = np.array([float(r[rule] < 0.05) for r in a_rows if finite(r.get(rule))])
        b = np.array([float(r[rule] < 0.05) for r in b_rows if finite(r.get(rule))])
        if len(a) == 0 or len(b) == 0:
            return None
        dd = a[brng.integers(0, len(a), (2000, len(a)))].mean(1) - b[brng.integers(0, len(b), (2000, len(b)))].mean(1)
        lo, hi = np.percentile(dd, [2.5, 97.5])
        return {"diff": float(a.mean() - b.mean()), "ci95": [float(lo), float(hi)], "n_cell": int(len(a)),
                "n_baseline": int(len(b)), "baseline_rate": float(b.mean())}

    res = {"cells": {}}
    for c in cells:
        rows = load(runs, c)
        s = {"cell": c, **cell_summary(rows, c)}
        if c["design"] != "interleaved":
            base = baseline(c["B"], c["split"])
            s["minus_baseline"] = {r: diff_ci(rows, base, r) for r in ("P1", "P4")}
        res["cells"][c["name"]] = s
    res["incomplete_cells"] = [k for k, v in res["cells"].items() if v["incomplete"]]
    (out / "add3_summary.json").write_text(json.dumps(res, indent=1))

    def pts(x):
        return "–" if x is None else f"{100 * x['diff']:.1f}"
    lines = ["# Step 2 addendum 3 §1: cells beyond §15 (summarize_add3.py)", ""]
    if res["incomplete_cells"]:
        lines.append(f"INCOMPLETE CELLS ({len(res['incomplete_cells'])}): " + ", ".join(res["incomplete_cells"][:10]))
    lines += ["| cell | reps | P1 | P2 | P3 (err) | P4 | P5 | P5 fails | P1−base | P4−base |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for k, s in res["cells"].items():
        mb = s.get("minus_baseline", {})
        e3 = s.get("P3", {}).get("error_share")
        p3 = f(s.get("P3")) + ("" if e3 is None else f" ({100 * e3:.0f}%)")
        lines.append(f"| {k} | {s['n_reps']} | {f(s.get('P1'))} | {f(s.get('P2'))} | {p3} | {f(s.get('P4'))} | "
                     f"{f(s.get('P5'))} | {s.get('P5_fails', '–')} | {pts(mb.get('P1'))} | {pts(mb.get('P4'))} |")
    (out / "add3_summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:3]))


if __name__ == "__main__":
    main()
