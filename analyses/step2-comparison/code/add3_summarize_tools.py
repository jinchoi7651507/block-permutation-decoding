#!/usr/bin/env python3
"""Step 2 addendum 3 §2b summary (written before any tool or reference row exists).

Rows: CoSMoMVPA (variants main, zscore, unbal), PyMVPA (main, zscore, chunks; p_tool as returned, and p_mc),
P3 port, P4 port, P5 (reference, undefined in L3). Per layout and row:
- n expected (500), n present, n usable (finite p, no error), errors, missing (absent from every output file);
- rate A = rejections (p < 0.05) / usable, with the Monte Carlo 99% band of 5% at that n;
- rate B = rejections / expected, errors and missing counted as non-rejections (the second denominator);
- paired difference to P5 on the same replicates (survivors; and all with errors = non-rejection), 95% bootstrap
  interval over replicates (B = 10,000, seed 2029);
- difference to the same row's L3 rate (the interleaved drift-0 baseline of the rule; unpaired bootstrap).
Error classes (§2b): expected = CoSMoMVPA errors (any variant) in L1 on replicates where the P3 port also returns
None; anything else (any PyMVPA error, any error in L2, L3, L4, a CoSMoMVPA error where P3 is defined, a missing
row) is UNEXPECTED: listed at the top and the run is not complete until it is investigated and rerun.
Headline comparisons (§2b): L4 CoSMoMVPA and PyMVPA, main and zscore, each minus P5 and minus L3; the rest descriptive.

  python add3_summarize_tools.py --tools ../runs_add3/tools > ../runs_add3/tools/SUMMARY-TOOLS.md
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

N_EXPECTED = 500
LAYOUTS = (1, 2, 3, 4)


def band99(n):
    return stats.binom.ppf(0.005, n, 0.05) / n, stats.binom.ppf(0.995, n, 0.05) / n


def read_tool(files, kind):
    rows = {}
    for f in files:
        for l in Path(f).read_text().splitlines():
            if not l.strip():
                continue
            c = l.split(",")
            j, rep, var = int(c[0]), int(c[1]), c[2]
            if kind == "cosmo":
                rows[(f"CoSMoMVPA {var}", j, rep)] = (float(c[3]), int(c[5]), c[8] if len(c) > 8 else "")
            else:
                rows[(f"PyMVPA {var}", j, rep)] = (float(c[3]), int(c[7]), c[10] if len(c) > 10 else "")
                rows[(f"PyMVPA {var} p_mc", j, rep)] = (float(c[4]), int(c[7]), c[10] if len(c) > 10 else "")
    return rows


def boot(a, rng, B=10000):
    bs = [a[rng.integers(0, len(a), len(a))].mean() for _ in range(B)]
    return np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", required=True)
    ap.add_argument("--expected", type=int, default=N_EXPECTED)
    args = ap.parse_args()
    d = Path(args.tools)
    ref = {}
    for f in sorted(d.glob("ref.w*.jsonl")):
        for r in map(json.loads, f.read_text().splitlines()):
            ref[(r["layout"], r["rep"])] = r
    tool = {**read_tool(sorted(d.glob("cosmo*.csv")), "cosmo"), **read_tool(sorted(d.glob("pymvpa*.csv")), "pymvpa")}
    for (j, rep), r in ref.items():
        tool[("P3 port", j, rep)] = (r["P3port"] if r["P3port"] is not None else float("nan"), int(r["P3port_error"]), "")
        tool[("P4 port", j, rep)] = (r["P4port"], 0, "")
        if r["P5"] is not None:
            tool[("P5", j, rep)] = (r["P5"], 0, "")
    names = sorted({k[0] for k in tool})
    unexpected = []
    for (name, j, rep), (p, e, msg) in tool.items():
        if e == 1:
            p3none = ref.get((j, rep), {}).get("P3port_error", False)
            ok = name.startswith("CoSMoMVPA") and j == 1 and p3none
            if name == "P3 port" and j == 1:
                ok = True
            if not ok:
                unexpected.append((name, j, rep, msg))
    expected_names = ["CoSMoMVPA main", "CoSMoMVPA zscore", "PyMVPA main", "PyMVPA zscore", "PyMVPA chunks",
                      "P3 port", "P4 port", "P5"]
    for name in sorted(set(names) | set(expected_names)):
        for j in LAYOUTS:
            if name == "P5" and j == 3:
                continue
            if name.endswith(" p_mc"):
                continue
            present = {k[2] for k in tool if k[0] == name and k[1] == j}
            if len(present) != args.expected:
                unexpected.append((name, j, "missing", f"{args.expected - len(present)} replicates"))
    if unexpected:
        print(f"**UNEXPECTED ERRORS OR MISSING ROWS: {len(unexpected)} (run not complete)**\n")
        for u in unexpected[:50]:
            print("-", u)
        print()
    rng = np.random.default_rng(2029)
    rate3 = {}
    for name in names:
        reps = [k[2] for k in tool if k[0] == name and k[1] == 3]
        rej = np.array([tool[(name, 3, r)][0] < 0.05 for r in reps if tool[(name, 3, r)][1] == 0
                        and np.isfinite(tool[(name, 3, r)][0])], float)
        rate3[name] = rej
    print("| layout | row | present | usable | errors | rate A (usable) | 99% band | rate B (all) | minus P5 survivors | minus P5 all | minus L3 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for j in LAYOUTS:
        for name in names:
            if name == "P5" and j == 3:
                continue
            reps = sorted(k[2] for k in tool if k[0] == name and k[1] == j)
            if not reps:
                continue
            use = [r for r in reps if tool[(name, j, r)][1] == 0 and np.isfinite(tool[(name, j, r)][0])]
            nerr = sum(tool[(name, j, r)][1] for r in reps)
            rej = np.array([tool[(name, j, r)][0] < 0.05 for r in use], float)
            lo, hi = band99(max(1, len(use)))
            rate_b = rej.sum() / args.expected
            dp5s = dp5a = dl3 = "—"
            if name != "P5" and j != 3:
                both = [r for r in use if ("P5", j, r) in tool]
                if both:
                    a = np.array([tool[(name, j, r)][0] < 0.05 for r in both], float) - \
                        np.array([tool[("P5", j, r)][0] < 0.05 for r in both], float)
                    l_, h_ = boot(a, rng)
                    dp5s = f"{100 * a.mean():+.1f} ({100 * l_:+.1f}, {100 * h_:+.1f})"
                allr = [r for r in reps if ("P5", j, r) in tool]
                if allr:
                    a = np.array([(tool[(name, j, r)][1] == 0 and tool[(name, j, r)][0] < 0.05) for r in allr], float) - \
                        np.array([tool[("P5", j, r)][0] < 0.05 for r in allr], float)
                    l_, h_ = boot(a, rng)
                    dp5a = f"{100 * a.mean():+.1f} ({100 * l_:+.1f}, {100 * h_:+.1f})"
                b3 = rate3.get(name)
                if b3 is not None and len(b3) and len(rej):
                    bs = [rej[rng.integers(0, len(rej), len(rej))].mean() - b3[rng.integers(0, len(b3), len(b3))].mean()
                          for _ in range(10000)]
                    dl3 = f"{100 * (rej.mean() - b3.mean()):+.1f} ({100 * np.percentile(bs, 2.5):+.1f}, {100 * np.percentile(bs, 97.5):+.1f})"
            head = " **(headline)**" if j == 4 and name in ("CoSMoMVPA main", "PyMVPA main", "CoSMoMVPA zscore", "PyMVPA zscore") else ""
            print(f"| L{j} | {name}{head} | {len(reps)} | {len(use)} | {nerr} | {100 * rej.mean() if len(rej) else float('nan'):.1f}% | "
                  f"{100 * lo:.1f}-{100 * hi:.1f}% | {100 * rate_b:.1f}% | {dp5s} | {dp5a} | {dl3} |")


if __name__ == "__main__":
    main()
