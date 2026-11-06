#!/usr/bin/env python3
"""Summarise decompose.py rows (DESIGN.md v2, sections 8 and 10).

Stops before writing results if the gate fails. Otherwise writes results.json and results.md:
mouse-level pass rates (95% mouse-bootstrap intervals) for every scheme x readout x test,
primary contrasts A and B, positive control, block-number sweep with its three predictions.

  python3 summarize.py --rows rows.jsonl --out ../results
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parents[1] / "trackA-std"
SESS = {r["session_id"]: r for r in csv.DictReader((TA / "sessions_trackA.csv").open(encoding="utf-8"))}
BOOT_B, BOOT_SEED = 20000, 20261015
STD6 = ("VISp", "VISl", "VISal", "VISrl", "VISam", "VISpm")
SCHEMES = ("iid", "sep", "segment", "shared", "sep24", "paired24", "shared24", "half24", "dg_iid", "dg_sep24", "dg_shared24")
READOUTS = ("nosel0", "nosel", "rank", "sel", "lr_topk", "lr_all")
TESTS = ("binom", "blk_rerun", "blk_fixed", "trl_rerun", "trl_fixed", "circ_rerun", "spec")
TA_KEY = {"iid": "c_iid", "sep": "c_random_blocks", "segment": "c_segment"}
TA_TEST = {"binom": "q2_p", "spec": "spec_p", "trl_rerun": "full_p", "blk_rerun": "block_p"}
SWEEP = ("4", "8", "16", "8t2", "16t4")


def gate(rows):
    ta = {(r["session"], r["area"]): r for r in map(json.loads, (TA / "runs" / "extra.jsonl").read_text().splitlines())}
    checked, bad = 0, []
    for r in rows:
        t = ta.get((r["session"], r["area"]))
        if t is None:
            continue
        for sch, key in TA_KEY.items():
            if sch not in r or key not in t:
                continue
            for mine, theirs in TA_TEST.items():
                if theirs in t[key]:
                    checked += 1
                    a, b = r[sch]["sel"].get(mine), t[key][theirs]
                    if a is None or abs(a - b) > 1e-12:
                        bad.append((r["session"], r["area"], sch, mine, a, b))
    return checked, bad


def animal_vals(rows, f):
    by = {}
    for r in rows:
        v = f(r)
        if v is None or not np.isfinite(v):
            continue
        by.setdefault(SESS[r["session"]]["specimen_id"], []).append(v)
    return np.array([np.mean(by[a]) for a in sorted(by)])


def est(v):
    if len(v) == 0:
        return None
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(v), (BOOT_B, len(v)))
    lo, hi = np.percentile(v[idx].mean(1), [2.5, 97.5])
    return {"mean": float(v.mean()), "ci": [float(lo), float(hi)], "n_animals": int(len(v))}


def get(r, *path):
    for p in path:
        if not isinstance(r, dict) or p not in r:
            return None
        r = r[p]
    return r


def hit(p):
    return None if p is None else float(p < 0.05)


def subset(rows, which):
    return [r for r in rows if (which == "all32" or SESS[r["session"]]["set"] == which) and r["area"] in STD6]


def summarise(rows):
    out = {}
    for sch in SCHEMES:
        for ro in READOUTS:
            for t in TESTS:
                e = est(animal_vals(rows, lambda r: hit(get(r, sch, ro, t))))
                if e:
                    out[f"{sch}/{ro}/{t}"] = e

    def contrast_b(r, ro="sel"):
        v = [hit(get(r, s, ro, t)) for s in ("shared24", "sep24") for t in ("blk_fixed", "blk_rerun")]
        return None if None in v else (v[0] - v[1]) - (v[2] - v[3])
    out["contrast_B/sel"] = est(animal_vals(rows, contrast_b))
    out["contrast_B/lr_topk"] = est(animal_vals(rows, lambda r: contrast_b(r, "lr_topk")))

    def contrast_a(r):
        v = [hit(get(r, "sep", ro, "binom")) for ro in ("sel", "nosel0")]
        return None if None in v else v[0] - v[1]
    out["contrast_A/sel_minus_nosel0"] = est(animal_vals(rows, contrast_a))
    for sch in ("pos_sep24", "pos_shared24"):
        for d in ("0.1", "0.2", "0.4"):
            for ro in ("sel", "lr_topk"):
                for t in ("binom", "blk_fixed", "blk_rerun", "trl_rerun"):
                    e = est(animal_vals(rows, lambda r: hit(get(r, sch, d, ro, t))))
                    if e:
                        out[f"{sch}/{d}/{ro}/{t}"] = e
    for v in SWEEP:
        for ro in ("sel", "nosel0"):
            out[f"sweep/{v}/{ro}/pass"] = est(animal_vals(rows, lambda r: hit(get(r, "sweep", v, ro, "binom"))))
            for k in ("cond_pass", "pred_ho", "pred_xfit", "rho_ho", "rho_xfit"):
                out[f"sweep/{v}/{ro}/{k}"] = est(animal_vals(rows, lambda r: get(r, "sweep", v, ro, k)))
        out[f"sweep/{v}/block_s"] = est(animal_vals(rows, lambda r: get(r, "sweep", v, "block_s")))
    secs = [r.get("seconds", 0) for r in rows]
    out["run_seconds_total"] = float(np.sum(secs))
    return out


def pct(e):
    return "–" if not e else f"{100 * e['mean']:.1f} ({100 * e['ci'][0]:.1f}–{100 * e['ci'][1]:.1f})"


def write_md(R, path):
    m = R["new/std6"]
    L = [f"# Step 1 results (30 new mice, std6 areas)\n",
         f"Gate: {R['gate']['checked']} values checked against Track A, {R['gate']['n_mismatch']} mismatches.\n",
         "Pass rate = mean over mice of the share of areas with p < 0.05 (95% mouse-bootstrap interval), %. "
         "Sanity-check cells (exact by construction; `sep` blk_fixed cannot pass) are marked in DESIGN.md §1.\n",
         "## Primary contrasts",
         f"- A (`sep`, binom): sel − nosel0 = {pct(m.get('contrast_A/sel_minus_nosel0'))} points; "
         f"sel {pct(m.get('sep/sel/binom'))}, nosel0 {pct(m.get('sep/nosel0/binom'))}",
         f"- B (sel): (blk_fixed − blk_rerun) in shared24 minus in sep24 = {pct(m.get('contrast_B/sel'))} points; "
         f"lr_topk: {pct(m.get('contrast_B/lr_topk'))}\n", "## All cells"]
    for sch in SCHEMES:
        L.append(f"\n### {sch}\n| readout | " + " | ".join(TESTS) + " |\n|---|" + "---|" * len(TESTS))
        for ro in READOUTS:
            cells = [m.get(f"{sch}/{ro}/{t}") for t in TESTS]
            if any(cells):
                L.append(f"| {ro} | " + " | ".join(pct(c) for c in cells) + " |")
    L.append("\n## Positive control (power)\n| scheme | δ | readout | binom | blk_fixed | blk_rerun | trl_rerun |\n|---|---|---|---|---|---|---|")
    for sch in ("pos_sep24", "pos_shared24"):
        for d in ("0.1", "0.2", "0.4"):
            for ro in ("sel", "lr_topk"):
                L.append(f"| {sch} | {d} | {ro} | " + " | ".join(pct(m.get(f"{sch}/{d}/{ro}/{t}")) for t in ("binom", "blk_fixed", "blk_rerun", "trl_rerun")) + " |")
    L.append("\n## Block-number sweep (separate blocks; binom)\n| variant | block s | readout | observed | exact conditional | DEFF (held-out ICC) | DEFF (cross-fit) | ρ̂ held-out | ρ̂ cross-fit |\n|---|---|---|---|---|---|---|---|---|")
    for v in SWEEP:
        bs = m.get(f"sweep/{v}/block_s")
        for ro in ("sel", "nosel0"):
            g = lambda k: m.get(f"sweep/{v}/{ro}/{k}")
            r1, r2 = g("rho_ho"), g("rho_xfit")
            L.append(f"| {v} | {'–' if not bs else round(bs['mean'])} | {ro} | {pct(g('pass'))} | {pct(g('cond_pass'))} | {pct(g('pred_ho'))} | "
                     f"{pct(g('pred_xfit'))} | {'–' if not r1 else f'{r1['mean']:.3f}'} | {'–' if not r2 else f'{r2['mean']:.3f}'} |")
    L.append(f"\nTotal compute: {m['run_seconds_total'] / 3600:.1f} core-hours (new mice, std6).")
    path.write_text("\n".join(L) + "\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = [json.loads(l) for l in Path(args.rows).read_text().splitlines()]
    checked, bad = gate(rows)
    G = {"checked": checked, "mismatches": bad[:20], "n_mismatch": len(bad), "pass": checked > 0 and not bad}
    print(f"gate: {checked} checked, {len(bad)} mismatches")
    if not G["pass"]:
        for b in bad[:20]:
            print("  MISMATCH", b)
        sys.exit("gate failed: no results written")
    R = {"gate": G, "new/std6": summarise(subset(rows, "new")), "all32/std6": summarise(subset(rows, "all32"))}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(R, indent=1))
    print(write_md(R, out / "results.md"))


if __name__ == "__main__":
    main()
