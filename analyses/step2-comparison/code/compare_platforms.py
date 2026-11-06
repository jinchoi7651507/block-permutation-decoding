#!/usr/bin/env python3
"""Equivalence check of RUN-PLATFORM.md: laptop rows (runs/) against cloud rows (runs_cloud/). Changes nothing in
the result. Rows are matched on (cell name, replicate index); worker file numbers differ between the two machines
(6 and 56 workers) and are ignored. For every matched replicate it compares n_units, the P3 error flag and the p
value of each rule (P1-P5), and prints, per rule, the number of matched replicates, the share with identical p
values (None on both machines counts as identical) and the largest absolute difference. Only these summaries are
printed; no p value of any cell is shown. The power files are compared only if both machines have them and the
two delta choices are equal; the two choice files are printed either way.

  python code/compare_platforms.py runs runs_cloud > equiv/EQUIV-PLATFORM.txt
"""
import json
import re
import sys
from pathlib import Path

RULES = ("P1", "P2", "P3", "P4", "P5")


def load(d, power):
    """{(cell name, rep): row} from the c* files (simulation cells) or the pp*/pw* files (power)."""
    pat = re.compile(r"^(pp|pw)" if power else r"^c\d{3}_")
    out, bad = {}, 0
    for f in sorted(Path(d).glob("*.w*.jsonl")):
        if not pat.match(f.name):
            continue
        cell = f.name.rsplit(".w", 1)[0]
        for line in f.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                bad += 1
                continue
            out[(cell, r["rep"])] = r
    return out, bad


def same(u, v):
    return u == v or (isinstance(u, float) and isinstance(v, float) and u != u and v != v)


def compare(A, B, label):
    keys = sorted(set(A) & set(B))
    print(f"[{label}] matched replicates {len(keys)}; only laptop {len(set(A) - set(B))}; "
          f"only cloud {len(set(B) - set(A))}; cells matched {len({k[0] for k in keys})}")
    if not keys:
        return
    nu = sum(A[k]["n_units"] == B[k]["n_units"] for k in keys)
    e3 = [k for k in keys if "P3" in A[k] or "P3" in B[k]]
    pe = sum(A[k].get("P3_error") == B[k].get("P3_error") for k in e3)
    print(f"  n_units identical {nu}/{len(keys)}; P3 error flag identical {pe}/{len(e3)}")
    for r in RULES:
        ks = [k for k in keys if r in A[k] or r in B[k]]
        if not ks:
            continue
        eq = sum(same(A[k].get(r), B[k].get(r)) for k in ks)
        diffs = [abs(A[k][r] - B[k][r]) for k in ks
                 if isinstance(A[k].get(r), (int, float)) and isinstance(B[k].get(r), (int, float))]
        one_sided = sum((A[k].get(r) is None) != (B[k].get(r) is None) for k in ks)
        cells_diff = len({k[0] for k in ks if not same(A[k].get(r), B[k].get(r))})
        print(f"  {r}: replicates {len(ks)}; identical p {eq} ({eq / len(ks):.4f}); "
              f"largest |p difference| {max(diffs, default=0.0):.4g}; None on one machine only {one_sided}; "
              f"cells with any difference {cells_diff}")


def main():
    lap, cld = Path(sys.argv[1]), Path(sys.argv[2])
    A, ba = load(lap, False)
    B, bb = load(cld, False)
    print(f"laptop {lap}: {len(A)} simulation-cell rows ({ba} unreadable lines); "
          f"cloud {cld}: {len(B)} rows ({bb} unreadable lines)")
    compare(A, B, "simulation cells")
    ca, cb = lap / "POWER_CHOICE.json", cld / "POWER_CHOICE.json"
    for name, f in (("laptop", ca), ("cloud", cb)):
        print(f"{name} delta choice: {f.read_text().strip() if f.exists() else 'none'}")
    PA, _ = load(lap, True)
    PB, _ = load(cld, True)
    if PA and PB and ca.exists() and cb.exists() and json.loads(ca.read_text()) == json.loads(cb.read_text()):
        compare(PA, PB, "power pilot and power cells")
    elif PA and PB:
        pilot = lambda D: {k: v for k, v in D.items() if k[0].startswith("pp")}
        compare(pilot(PA), pilot(PB), "power pilot only (delta choices differ)")
    else:
        print("power: not compared (laptop has no power rows)" if not PA else "power: not compared (cloud has no power rows)")


if __name__ == "__main__":
    main()
