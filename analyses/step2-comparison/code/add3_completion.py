#!/usr/bin/env python3
"""Step 2 addendum 3 completion rule (counts only; no p value or rate is printed). §1: every cell of CELLS-ADD3.json
has 500 replicates and a last `done` line with every return code 0 in runs_add3/run.log. §2: per tool, variant and
layout, rows present (expected 500 each), error flags, and the error classes of add3_summarize_tools (expected =
CoSMoMVPA errors in L1 where the P3 port returns None); the reference rows (2,000). Complete = all counts as
expected and no unexpected error.

  python add3_completion.py --tools ../runs_add3/tools
"""
import argparse
import collections
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", required=True)
    args = ap.parse_args()
    t = Path(args.tools)
    a3 = t.parent
    cells = json.loads((a3 / "CELLS-ADD3.json").read_text())
    last = {}
    for l in (a3 / "run.log").read_text().splitlines() if (a3 / "run.log").exists() else []:
        if " done  " in l:
            name = l.split(" done  ")[1].split(" rc ")[0]
            last[name] = l.split(" rc ")[1].rsplit(" ", 2)[0]
    bad_cells = []
    for c in cells:
        n = 0
        for f in a3.glob(f"{c['name']}.w*.jsonl"):
            n += len({json.loads(x)["rep"] for x in f.read_text().splitlines() if x})
        rc_ok = c["name"] in last and set(json.loads(last[c["name"]])) == {0}
        if n != c["reps"] or not rc_ok:
            bad_cells.append((c["name"], n, rc_ok))
    print(f"§1 cells: {len(cells)}; incomplete or nonzero rc: {len(bad_cells)}", bad_cells[:5])
    ref = {}
    for f in t.glob("ref.w*.jsonl"):
        for r in map(json.loads, f.read_text().splitlines()):
            ref[(r["layout"], r["rep"])] = r
    print(f"reference rows: {len(ref)} (expected 2000)")
    unexpected = 0
    short = []
    for kind, pat, ecol in (("CoSMoMVPA", "cosmo_*.w*.csv", 5), ("PyMVPA", "pymvpa_*.w*.csv", 7)):
        cnt, err = collections.Counter(), collections.Counter()
        seen, errset = set(), set()
        for f in t.glob(pat):
            for l in f.read_text().splitlines():
                if not l:
                    continue
                c = l.split(",")
                key = (c[2], int(c[0]), int(c[1]))
                if key in seen:
                    continue
                seen.add(key)
                cnt[(c[2], int(c[0]))] += 1
                if int(c[ecol]) == 1:
                    err[(c[2], int(c[0]))] += 1
                    errset.add((c[2], int(c[0]), int(c[1])))
                    expected = kind == "CoSMoMVPA" and int(c[0]) == 1 and ref.get((1, int(c[1])), {}).get("P3port_error")
                    unexpected += 0 if expected else 1
        variants = ("main", "zscore") if kind == "CoSMoMVPA" else ("main", "zscore", "chunks")
        for v in variants:
            for j in (1, 2, 3, 4):
                print(f"{kind} {v} L{j}: rows {cnt[(v, j)]} (expected 500), errors {err[(v, j)]}")
                if cnt[(v, j)] != 500:
                    short.append((kind, v, j, cnt[(v, j)]))
        if kind == "CoSMoMVPA":
            for v in variants:
                cos_err = {r for (vv, jj, r) in errset if vv == v and jj == 1}
                p3none = {r for (jj, r), x in ref.items() if jj == 1 and x.get("P3port_error")}
                print(f"CoSMoMVPA {v} L1 errors vs P3 port None: only CoSMoMVPA {len(cos_err - p3none)}, "
                      f"only P3 port {len(p3none - cos_err)}, both {len(cos_err & p3none)}")
                if cos_err != p3none:
                    short.append(("L1 error sets differ", v))
    print("unexpected errors:", unexpected, "; short or mismatched:", short)
    ok = not bad_cells and len(ref) == 2000 and unexpected == 0 and not short
    print("COMPLETE" if ok else "NOT COMPLETE")


if __name__ == "__main__":
    main()
