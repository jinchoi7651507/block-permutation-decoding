# GroupKFold fold map: arm64 laptop vs x86 cloud CPU (2026-10-27 02:3x–02:4x KST)

Purpose: step 2 results note §6 (equivalence check) attributed the P2–P5 differences in the 8 random-design B 24 S-block cells to a platform-dependent block-to-fold map, "not verified on an x86 machine with the same versions (to be checked in the code package)". This is that check. No study data were used.

- Script: `foldmap_check.py` (GroupKFold(min(5, B)) on B blocks of 20 trials; also `np.argsort` of B equal values).
- arm64: the laptop, Python 3.12.3, numpy 2.5.4, scikit-learn 1.7.2 → `foldmap_arm64_laptop.json`.
- x86_64: Google Compute Engine c2d-standard-2 (AMD EPYC 7B13, AVX2, the CPU of the step 2 cloud run), Ubuntu 24.04, Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2 from PyPI → `foldmap_x86_c2d.json`, CPU line `foldmap_x86_c2d_cpu.txt`; run by `vm_foldmap.sh` (log `vm_foldmap.log`; VM deleted after the copy, 1 h cap).

| B (blocks) | fold of each block, arm64 | fold of each block, x86 | same |
|---|---|---|---|
| 4 | 3 2 1 0 | 3 2 1 0 | yes |
| 12 | 1 0 4 3 2 1 0 4 3 2 1 0 | 1 0 4 3 2 1 0 4 3 2 1 0 | yes |
| 24 | 3 2 3 4 0 1 2 3 4 0 1 2 3 4 0 1 2 3 4 0 1 2 1 0 | 3 2 1 0 4 3 2 1 0 4 3 2 1 0 4 3 2 1 0 4 3 2 1 0 | **no** |

- `np.argsort` of 24 equal values: x86 0, 1, …, 23 (identity); arm64 0, 21, 20, …, 1, 22, 23. scikit-learn 1.7.2 `GroupKFold` sorts the group sizes with `np.argsort(n_samples_per_group)[::-1]` (`model_selection/_split.py` line 639), so equal sizes keep the platform's tie order.
- Reading: consistent with the explanation in step 2 §6 (the cloud run's own machine record `step2-comparison/runs/MACHINE.txt` in `runs_cloud.tgz` gives the same CPU, AMD EPYC 7B13, and numpy 2.5.4 / scikit-learn 1.7.2); a replicate-level check (rerunning B 24 S-block replicates on the laptop with the x86 map as explicit folds and matching the cloud p values) was not done. The B 24 S-block cells use a different (equally valid, deterministic) fold map on the two platforms; the cloud rows are the result (RUN-PLATFORM). The B 12 map, used in addendum 3 §1 and recorded there, is the same on both. The public code should record the fold map with the results (or sort with a stable sort), so that a rerun on another platform reproduces the cells.

- Review (2026-10-27, code review): wording changed from "confirms" to "consistent with"; the script now also records numpy's CPU dispatch and the stable-sort map (not rerun on x86; the maps above are unchanged by this addition). `vm_foldmap.log` holds the cloud project ID, zone, an external IP and another instance name: not included in this repository.
- Update 2026-10-27 13:05 KST: the replicate-level check named above as not done is now done: `REPLICATE-CHECK.md` (x86 as is and laptop with the x86 map each reproduce all 800 cloud p values).
