#!/usr/bin/env python3
"""Summarise within_train.py rows (DESIGN-ADDENDUM-within-train.md §4 and §6).

Stops before writing results if any observed accuracy differs from runs/rows.jsonl (gate).
Otherwise writes within_train.json and within_train.md: mouse-level pass rates with 95%
mouse-bootstrap intervals for trn_trl and trn_blk, next to step 1's blk_fixed, blk_rerun,
trl_fixed and trl_rerun from rows.jsonl, and contrast T.

  python3 summarize_within_train.py --rows ../runs/within_train_rows.jsonl --out ../results
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("summ", HERE / "summarize.py")
summ = importlib.util.module_from_spec(_s)
_s.loader.exec_module(summ)

SCHEMES = ("iid", "sep24", "paired24", "shared24", "half24", "dg_iid", "dg_sep24", "dg_shared24")
READOUTS = ("sel", "rank", "nosel", "lr_topk", "lr_all")
NEW = ("trn_trl", "trn_blk")
OLD = ("blk_fixed", "blk_rerun", "trl_fixed", "trl_rerun", "binom")


def gate(rows, ref):
    checked, bad, nan = 0, [], 0
    for r in rows:
        t = ref.get((r["session"], r["area"]))
        for k in SCHEMES:
            if k not in r:
                continue
            for ro, o in r[k].items():
                checked += 1
                a, b = o["acc"], (t or {}).get(k, {}).get(ro, {}).get("acc")
                if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)):
                    nan += 1
                    if not (a is not None and b is not None and math.isnan(a) and math.isnan(b)):
                        bad.append((r["session"], r["area"], k, ro, a, b))
                elif abs(a - b) > 1e-9:
                    bad.append((r["session"], r["area"], k, ro, a, b))
    return checked, bad, nan


def summarise(rows, ref):
    out = {}
    for k in SCHEMES:
        for ro in READOUTS:
            for t in NEW:
                e = summ.est(summ.animal_vals(rows, lambda r: summ.hit(summ.get(r, k, ro, t))))
                if e:
                    out[f"{k}/{ro}/{t}"] = e
            for t in OLD:
                e = summ.est(summ.animal_vals([ref[(r["session"], r["area"])] for r in rows if (r["session"], r["area"]) in ref],
                                              lambda r: summ.hit(summ.get(r, k, ro, t))))
                if e:
                    out[f"{k}/{ro}/{t}"] = e
    for ro in ("sel", "lr_topk"):
        def ct(r, ro=ro):
            v = [summ.hit(summ.get(r, s, ro, "trn_blk")) for s in ("shared24", "sep24")]
            return None if None in v else v[0] - v[1]
        out[f"contrast_T/{ro}"] = summ.est(summ.animal_vals(rows, ct))
    return out


def write_md(R, path):
    m = R["new/std6"]
    L = ["# Step 1 addendum: training-label-only permutation (30 new mice, std6 areas)\n",
         f"Gate: {R['gate']['checked']} observed accuracies checked against runs/rows.jsonl, {R['gate']['n_mismatch']} mismatches, "
         f"{R['gate']['n_nan']} NaN.\n",
         "Pass rate = mean over mice of the share of areas with p < 0.05 (95% mouse-bootstrap interval), %. "
         "Exact by construction (sanity checks): trn_blk in sep24 and dg_sep24; trn_trl in iid and dg_iid.\n",
         "## Contrast T (trn_blk: shared24 − sep24)",
         f"- sel: {summ.pct(m.get('contrast_T/sel'))} points; lr_topk: {summ.pct(m.get('contrast_T/lr_topk'))} points\n",
         "## All cells (step 1 columns from runs/rows.jsonl, same areas)"]
    cols = NEW + OLD
    for k in SCHEMES:
        L.append(f"\n### {k}\n| readout | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols))
        for ro in READOUTS:
            cells = [m.get(f"{k}/{ro}/{t}") for t in cols]
            if any(cells[:2]):
                L.append(f"| {ro} | " + " | ".join(summ.pct(c) for c in cells) + " |")
    L.append(f"\nTotal compute: {R['run_seconds_total'] / 3600:.1f} core-hours (all rows).")
    path.write_text("\n".join(L) + "\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = [json.loads(l) for l in Path(args.rows).read_text().splitlines()]
    ref = {(r["session"], r["area"]): r for r in map(json.loads, (HERE.parent / "runs" / "rows.jsonl").read_text().splitlines())}
    checked, bad, nan = gate(rows, ref)
    G = {"checked": checked, "mismatches": bad[:20], "n_mismatch": len(bad), "n_nan": nan, "pass": checked > 0 and not bad}
    print(f"gate: {checked} checked, {len(bad)} mismatches, {nan} NaN")
    if not G["pass"]:
        for b in bad[:20]:
            print("  MISMATCH", b)
        sys.exit("gate failed: no results written")
    R = {"gate": G, "new/std6": summarise(summ.subset(rows, "new"), ref), "all32/std6": summarise(summ.subset(rows, "all32"), ref),
         "run_seconds_total": float(sum(r.get("seconds", 0) for r in rows))}
    out = Path(args.out)
    (out / "within_train.json").write_text(json.dumps(R, indent=1))
    print(write_md(R, out / "within_train.md"))


if __name__ == "__main__":
    main()
