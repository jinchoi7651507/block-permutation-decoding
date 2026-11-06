# Step 2 pipeline gate result

Areas: 154 (step 1: 154); integrity (step 1 lr_topk recomputed = rows.jsonl): 154/154

## Pipeline A
- observed accuracy identical to step 1: 149/154 (96.8%); identical predictions 144/154; max |difference| 0.472 points; tight-tolerance fit gives the same accuracy in 149/154
| test | step 1 (mouse-level % p<0.05) | pipeline | difference |
|---|---|---|---|
| trl_rerun | 97.0 | 97.0 | +0.0 |
| blk_fixed | 84.2 | 84.2 | +0.0 |
| blk_rerun | 1.9 | 1.9 | +0.0 |
- criterion 1 (≥ 95% identical): PASS; criterion 2 (±3 points): PASS

## Pipeline B
- observed accuracy identical to step 1: 146/154 (94.8%); identical predictions 141/154; max |difference| 4.245 points; tight-tolerance fit gives the same accuracy in 148/154
| test | step 1 (mouse-level % p<0.05) | pipeline | difference |
|---|---|---|---|
| trl_rerun | 97.0 | 96.4 | -0.6 |
| blk_fixed | 84.2 | 84.2 | +0.0 |
| blk_rerun | 1.9 | 1.9 | +0.0 |
- criterion 1 (≥ 95% identical): FAIL; criterion 2 (±3 points): PASS

Gate (pipeline A): PASS. Step 2 ranking: f_classif (B), as designed (criterion 3).

## Notes (2026-10-21 01:36 KST)
- Mouse-level rates here average over all 32 sessions with shared24 rows (the step 1 headline numbers, e.g. blk_fixed lr_topk 83.7%, are over the 30 new mice); both columns use the same aggregation, so the comparison is like for like.
- Pipeline A differs from step 1 in 5 of 154 areas (max 0.47 points, i.e. one held-out trial or less) and in its predictions in 10 areas; the tight-tolerance run equals the default fit in 149/154, so part of the difference is lbfgs stopping early (default tol 1e-4, max_iter 100). For step 2, consider `max_iter=1000`; it would be stated in the step 2 design before the pilot.
- Pipeline B (f_classif) differs in observed accuracy in 8 areas (max 4.2 points, from different top-20 units when the classes are unbalanced in calibration) but its three pass rates are within 0.6 points of A, so step 2 keeps f_classif as designed (criterion 3). Both are reported.
- Not compared here: `trn_trl` (training-label-only permutation); step 2 runs it with the tool's own rule, and its gate is the step 1 addendum code.
