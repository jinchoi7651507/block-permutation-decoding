#!/usr/bin/env python3
"""Step 2b addendum 2: main run of the graded arms with a noise rule chosen by graded_pilot2.py. Registers the N rules
(graded2.install) and then runs run_2b.main unchanged, e.g.

  python run_graded2.py --features <dir> --subjects ../eligibility/SUBJECTS.txt --arms pos_graded,balanced_graded \
         --splits main --graded-rule N4 --out ../runs/rows_graded2.w0.jsonl --worker 0 --of 1
"""
import graded2
import run_2b

if __name__ == "__main__":
    graded2.install()
    run_2b.main()
