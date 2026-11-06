#!/usr/bin/env python3
"""Step 2b addendum 2 §6: equivalence check of the laptop and the cloud machine. Runs run_2b.main unchanged on the
subjects of eligibility/EQUIV-SUBJECTS.txt (first-round pilot subjects, in no main table), with the assignment list
cut to its first entries: balanced arm, S-main, assignments 0 and 1 (6 rows), and one balanced_graded row (fake labels,
assignment 0) with the noise rule N4 for the first subject, to exercise graded2.weaken2 without eyes-closed/eyes-open labels.
Use a fresh output file on each machine (run_2b.main skips rows already in the file). The rows are compared between machines by
compare_equiv.py; they are used in no table.

  python equiv_check.py --features <dir> --out ../runs/equiv_<machine>.jsonl
"""
import argparse
import sys

import graded2
import run_2b as r

ap = argparse.ArgumentParser()
ap.add_argument("--features", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
SUBS = str(r.HERE.parent / "eligibility" / "EQUIV-SUBJECTS.txt")
_orig = r.arm_assignments


def first(n):
    def f(arm, bcond, si):
        assigns, null, bmap = _orig(arm, bcond, si)
        return assigns[:n], null, bmap
    return f


graded2.install()
r.arm_assignments = first(2)
sys.argv = ["run_2b", "--features", a.features, "--subjects", SUBS, "--arms", "balanced", "--splits", "main", "--out", a.out]
r.main()
r.arm_assignments = first(1)
sys.argv = ["run_2b", "--features", a.features, "--subjects", SUBS, "--arms", "balanced_graded", "--splits", "main",
            "--graded-rule", "N4", "--out", a.out, "--worker", "0", "--of", "3"]
r.main()
