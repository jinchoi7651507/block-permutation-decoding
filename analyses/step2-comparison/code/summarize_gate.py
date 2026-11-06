#!/usr/bin/env python3
"""Summarise the step 2 pipeline gate (criteria in ../gate/GATE-DESIGN.md) -> ../gate/GATE-RESULT.md."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
G = HERE.parent / "gate"
S1 = HERE.parents[1] / "step1-decomposition" / "runs" / "rows.jsonl"
TESTS = ("trl_rerun", "blk_fixed", "blk_rerun")


def mouse_rate(rows, get):
    by = {}
    for r in rows:
        v = get(r)
        if v is not None and np.isfinite(v):
            by.setdefault(r["session"], []).append(v < 0.05)
    return 100 * float(np.mean([np.mean(x) for x in by.values()])), len(by)


def main():
    g = [json.loads(l) for l in (G / "gate_rows.jsonl").read_text().splitlines()]
    s1rows = [r for r in map(json.loads, S1.read_text().splitlines()) if "shared24" in r]
    s1 = {(r["session"], r["area"]): r["shared24"]["lr_topk"] for r in s1rows}
    ntest = {(r["session"], r["area"]): r["shared24"]["n_test"] for r in s1rows}
    lines = [f"# Step 2 pipeline gate result", "", f"Areas: {len(g)} (step 1: {len(s1)}); integrity (step 1 lr_topk recomputed = rows.jsonl): {sum(r['integrity'] for r in g)}/{len(g)}", ""]
    ok = len(g) == len(s1) and all(r["integrity"] for r in g)
    for kind in ("A", "B"):
        same = sum(abs(r[kind]["acc"] - r["s1_acc_rows"]) < 1e-9 for r in g)
        maxdiff = max(abs(r[kind]["acc"] - r["s1_acc_rows"]) for r in g)
        samepred = sum(r[kind]["same_pred_as_s1"] for r in g)
        tight = sum(abs(r[kind]["acc_tight"] - r[kind]["acc"]) < 1e-9 for r in g)
        lines += [f"## Pipeline {kind}", f"- observed accuracy identical to step 1: {same}/{len(g)} ({100*same/len(g):.1f}%); identical predictions {samepred}/{len(g)}; max |difference| {maxdiff:.3f} points; tight-tolerance fit gives the same accuracy in {tight}/{len(g)}"]
        lines.append("| test | step 1 (mouse-level % p<0.05) | pipeline | difference |")
        lines.append("|---|---|---|---|")
        crit2 = True
        for t in TESTS:
            a, n = mouse_rate(g, lambda r: s1.get((r["session"], r["area"]), {}).get(t))
            b, _ = mouse_rate(g, lambda r: r[kind].get(t))
            lines.append(f"| {t} | {a:.1f} | {b:.1f} | {b - a:+.1f} |")
            crit2 &= abs(b - a) <= 3
        within1 = all(abs(r[kind]["acc"] - r["s1_acc_rows"]) <= 100 / ntest[(r["session"], r["area"])] + 1e-9 for r in g)
        crit1 = same / len(g) >= 0.95 and within1
        lines.append(f"- criterion 1 (≥ 95% identical): {'PASS' if crit1 else 'FAIL'}; criterion 2 (±3 points): {'PASS' if crit2 else 'FAIL'}")
        lines.append("")
        if kind == "A":
            ok &= crit1 and crit2
    a_rates = {t: mouse_rate(g, lambda r: r["A"].get(t))[0] for t in TESTS}
    b_rates = {t: mouse_rate(g, lambda r: r["B"].get(t))[0] for t in TESTS}
    use_b = all(abs(b_rates[t] - a_rates[t]) <= 3 for t in TESTS)
    lines.append(f"Gate (pipeline A): {'PASS' if ok else 'FAIL'}. Step 2 ranking: {'f_classif (B), as designed' if use_b else '|d′| (A), B differs by more than 3 points'} (criterion 3).")
    (G / "GATE-RESULT.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
