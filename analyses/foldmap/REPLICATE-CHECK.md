# Replicate-level check of the B 24 S-block platform difference (protocol written 2026-10-27 10:0x KST, before the full runs)

Why: the step 2 results note §6 attributes the P2–P5 differences in the eight random-design B 24 S-block cells (c009, c018, c027, c036, c044, c053, c062, c071) to a different GroupKFold block-to-fold map on the laptop (arm64) and the cloud machine (x86), and its correction line says "consistent with", because no replicate-level check was made (`RESULT.md` of this folder, code-package review S8). This is that check. It reruns simulated replicates only; no new result is opened and no reported number changes.

What runs (`replicate_check.py`, the step 2 runner `run_grid.py` and `sim.py` unchanged; same cell arguments as `run_sim_cells.py`; replicates 0–19 of each cell, all five rules):
1. **Laptop, x86 map:** the S-block folds for 24 blocks are replaced by the folds of `foldmap_x86_c2d.json` (fold k holds out the blocks the x86 map puts in fold k; checked beforehand that the same construction from the arm64 map reproduces GroupKFold's folds on the laptop exactly). Prediction: every p identical to the cloud rows (`runs_cloud/`), and different from the laptop rows (`runs/`) where those differ.
2. **x86 VM, code as is:** a small c2d machine (AMD EPYC, the cloud run's CPU family), Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2 from PyPI; 1 h cap, deleted after the copy. Prediction: every p identical to the cloud rows.
"Identical" = equal within 1e-12 (None for None). Reported: counts per cell and rule; any mismatch is reported as found.

Smoke test before this protocol (replicate 0 of each cell, 2026-10-27 10:0x): laptop as is = laptop rows 40/40, cloud rows 7/40; laptop with the x86 map = cloud rows 40/40, laptop rows 7/40.

Reading fixed now: if both predictions hold, the step 2 note's "consistent with" can be raised to "confirmed at the replicate level" in a dated correction line (the note's earlier text kept).

## Result (2026-10-27 13:05 KST)
- **x86 VM, code as is** (c2d-standard-8, AMD EPYC 7B13; Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2; `run_grid.py` and `sim.py` hashes equal to the cloud run's MACHINE.txt; `replicate_x86_rows/versions.txt`): identical to the cloud rows in **800 of 800** p values (8 cells × 20 replicates × 5 rules); identical to the laptop rows in 116 of 800. VM deleted after the copy; instances 0, disks 0 (`vm_replicate_check.log`).
- **Laptop, x86 map:** identical to the cloud rows in **800 of 800**; to the laptop rows in 116 of 800 (`replicate_laptop_compare.txt`). The run was stopped at 120 of 160 rows on low battery (10:10) and resumed at 13:03 with the same command (finished replicates skipped).
- Per cell and rule: `replicate_x86_compare.txt`, `replicate_laptop_compare.txt`.
- Reading (as fixed above): both predictions hold. The P2–P5 differences in these cells come from the block-to-fold map alone: with the x86 map the laptop reproduces every cloud p value, and the x86 machine reproduces them with the code as is.
