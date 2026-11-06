#!/usr/bin/env python3
"""Compare the equivalence rows of two machines (addendum 2 §6): rows matched on (subject, arm, assignment, split);
reports the number of rows whose p values of all rules are identical, the largest absolute difference in observed
accuracy, and, over the 200 stored P5 null accuracies, the largest absolute difference and the share identical.

  python compare_equiv.py ../runs/equiv_laptop.jsonl ../runs/equiv_cloud.jsonl
"""
import json
import sys

import numpy as np


def rows(p):
    return {(d["subject"], d["arm"], d["assignment"], d["split"]): d for d in map(json.loads, open(p)) if not d.get("dropped")}


A, B = rows(sys.argv[1]), rows(sys.argv[2])
keys = sorted(set(A) & set(B))
same_p, dacc, dnull, same_null = 0, 0.0, 0.0, []
for k in keys:
    a, b = A[k], B[k]
    def eq(u, v):                                   # NaN on both machines counts as identical (re-check R5)
        return u == v or (isinstance(u, float) and isinstance(v, float) and u != u and v != v)
    same_p += all(eq(a.get(x), b.get(x)) for x in ("P1", "P2", "P3", "P4", "P5"))
    dacc = max(dacc, abs(a["acc"] - b["acc"]))
    na = np.array([np.nan if v is None else v for v in a["P5_null_acc"]], float)
    nb = np.array([np.nan if v is None else v for v in b["P5_null_acc"]], float)
    dnull = max(dnull, float(np.nanmax(np.abs(na - nb))))
    same_null.append(float(np.mean(na == nb)))
print(f"rows matched {len(keys)} (only in first {len(set(A) - set(B))}, only in second {len(set(B) - set(A))}); "
      f"all p identical in {same_p}; max |acc diff| {dacc:.3g}; P5 null max |diff| {dnull:.3g}; "
      f"share of identical null accuracies {np.mean(same_null):.4f}")
