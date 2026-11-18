# Replicate-level check of the B 24 S-block platform difference (protocol written 2026-10-27, before the full runs)

Why: the equivalence check of the two platforms (Supplementary Note 4) attributes the P2–P5 differences in the eight random-design B 24 S-block cells (c009, c018, c027, c036, c044, c053, c062, c071) to a different GroupKFold block-to-fold map on the laptop (arm64) and the cloud machine (x86); `RESULT.md` of this folder found this consistent with the fold maps, without a replicate-level check. This is that check. It reruns simulated replicates only. Folder names are those of the machine that ran it: `runs_cloud/` holds the cloud rows (`runs/` after `REPRODUCE.md` §2) and `runs/` the laptop rows (`runs_laptop/`).

What runs (`replicate_check.py`, the step 2 runner `run_grid.py` and `sim.py` unchanged; same cell arguments as `run_sim_cells.py`; replicates 0–19 of each cell, all five rules):
1. **Laptop, x86 map:** the S-block folds for 24 blocks are replaced by the folds of `foldmap_x86_c2d.json` (fold k holds out the blocks the x86 map puts in fold k; checked beforehand that the same construction from the arm64 map reproduces GroupKFold's folds on the laptop exactly). Prediction: every p identical to the cloud rows (`runs_cloud/`), and different from the laptop rows (`runs/`) where those differ.
2. **x86 VM, code as is:** a small c2d machine (AMD EPYC, the cloud run's CPU family), Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2 from PyPI; 1 h cap, deleted after the copy. Prediction: every p identical to the cloud rows.
"Identical" = equal within 1e-12 (None for None). Reported: counts per cell and rule; any mismatch is reported as found.

Smoke test before this protocol (replicate 0 of each cell, 2026-10-27): laptop as is = laptop rows 40/40, cloud rows 7/40; laptop with the x86 map = cloud rows 40/40, laptop rows 7/40.

Reading: if both predictions hold, the fold-map explanation of `RESULT.md` is confirmed at the replicate level.

## Result (2026-10-27)
- **x86 VM, code as is** (c2d-standard-8, AMD EPYC 7B13; Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2; `replicate_x86_rows/versions.txt`): identical to the cloud rows in **800 of 800** p values (8 cells × 20 replicates × 5 rules); identical to the laptop rows in 116 of 800.
- **Laptop, x86 map:** identical to the cloud rows in **800 of 800**; to the laptop rows in 116 of 800 (`replicate_laptop_compare.txt`).
- Per cell and rule: `replicate_x86_compare.txt`, `replicate_laptop_compare.txt`.
- Reading (as fixed above): both predictions hold. The P2–P5 differences in these cells come from the block-to-fold map alone: with the x86 map the laptop reproduces every cloud p value, and the x86 machine reproduces them with the code as is.
