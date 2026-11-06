# Step 2 compute pilot (DESIGN.md §10; 2026-10-21 01:39 KST; timing only, no rate opened)

Run: `code/pilot_timing.py --n-perm 200 --reps 3` (scikit-learn 1.7.2, one process, OMP_NUM_THREADS=1, laptop with other jobs running). Layout: 24 blocks × 20 trials (480 trials), 100 units, random block design, shuffled 5-fold, the one pipeline (StandardScaler, SelectKBest f_classif k = 20, LogisticRegression C = 1, max_iter 1000). p values were computed and discarded.

| Part | Median s per replicate |
|---|---|
| simulate | 0.004 |
| P1 binomial | 0.01 |
| P2 sklearn permutation_test_score (200) | 2.1 |
| P3 within-run permutation (200) | 2.0 |
| P4 training labels only (200) | 2.0 |
| P5 block permutation, rerun (200) | 2.1 |
| **one replicate, all rules** | **8.2** |

## Extrapolation (before the design was finalized)
- δ = 0 grid (3 L/τ × 3 block numbers × 3 drift levels = 27 cells; 1,000 replicates in the primary cell, 500 elsewhere ≈ 13,500 replicates) on S-main: about 31 core-hours.
- S-tool and S-block columns (S-block with its three permutation variants): roughly 2–2.5 × S-main → 60–80 core-hours in total for the grid.
- Fixed-order designs, interleaved control, one block per condition, power (3 δ × 1,000 in the primary cell): about 15–20 core-hours.
- Allen cells (154 areas, two schemes plus grating trials, two splits): per area the gate took about 2 s for 2 × 1,400 fits; with five rules × 200 draws × 5 folds roughly 10–20 s per area per scheme → under 10 core-hours.
- Total roughly 90–110 core-hours ≈ 15–20 h on 6 cores (the laptop is shared with other jobs, so plan 1–1.5 days). Within the "2–3 days on 6 cores" budget: **no cuts needed**. Larger designs (more trials or units) scale roughly linearly in trials × fits.
- Open before stamping: Allen calibration of τ and drift (DESIGN.md §5a), definition of "held-out blocks" in §5a (number of blocks per session, 4/12/24), the run (chunk) definition for P3 (4 runs of equal length), and `max_iter = 1000` (gate note).
