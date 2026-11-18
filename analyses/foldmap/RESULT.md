# GroupKFold fold map: arm64 laptop vs x86 cloud CPU (2026-10-27)

Purpose: the equivalence check of the two platforms (Supplementary Note 4) attributed the P2–P5 differences in the 8 random-design B 24 S-block cells to a platform-dependent block-to-fold map, not yet verified on an x86 machine with the same versions. This is that check. No study data were used.

- Script: `foldmap_check.py` (GroupKFold(min(5, B)) on B blocks of 20 trials; also `np.argsort` of B equal values).
- arm64: the laptop, Python 3.12.3, numpy 2.5.4, scikit-learn 1.7.2 → `foldmap_arm64_laptop.json`.
- x86_64: Google Compute Engine c2d-standard-2 (AMD EPYC 7B13, AVX2, the CPU of the step 2 cloud run), Ubuntu 24.04, Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2 from PyPI → `foldmap_x86_c2d.json`, CPU line `foldmap_x86_c2d_cpu.txt`; run by `vm_foldmap.sh`.

| B (blocks) | fold of each block, arm64 | fold of each block, x86 | same |
|---|---|---|---|
| 4 | 3 2 1 0 | 3 2 1 0 | yes |
| 12 | 1 0 4 3 2 1 0 4 3 2 1 0 | 1 0 4 3 2 1 0 4 3 2 1 0 | yes |
| 24 | 3 2 3 4 0 1 2 3 4 0 1 2 3 4 0 1 2 3 4 0 1 2 1 0 | 3 2 1 0 4 3 2 1 0 4 3 2 1 0 4 3 2 1 0 4 3 2 1 0 | **no** |

- `np.argsort` of 24 equal values: x86 0, 1, …, 23 (identity); arm64 0, 21, 20, …, 1, 22, 23. scikit-learn 1.7.2 `GroupKFold` sorts the group sizes with `np.argsort(n_samples_per_group)[::-1]` (`model_selection/_split.py` line 639), so equal sizes keep the platform's tie order.
- Reading: consistent with that explanation (the cloud run's own machine record `step2-comparison/runs/MACHINE.txt` in `runs_cloud.tgz` gives the same CPU, AMD EPYC 7B13, and numpy 2.5.4 / scikit-learn 1.7.2); the replicate-level check is in `REPLICATE-CHECK.md`. The B 24 S-block cells use a different (equally valid, deterministic) fold map on the two platforms; the cloud rows are the result. The B 12 map, used in the further simulation cells and recorded there, is the same on both. On arm64, a rerun reproduces the cells only with the recorded fold map passed as explicit folds (`ENVIRONMENT.md`).
