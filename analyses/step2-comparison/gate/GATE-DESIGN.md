# Step 2 pipeline gate against step 1 `lr_topk` (design written before running; 2026-10-21 01:29 KST; code tested on one session for integrity and timing only, its outputs not compared with the criteria before the full run)

Purpose (step 2 `DESIGN.md` v1 §2): before any new step 2 cell, the single scikit-learn pipeline used for every row must reproduce step 1's `lr_topk` readout on Allen `shared24` (odd/even split inside each of 24 blocks), for the held-out accuracy and the `trl_rerun`, `blk_fixed` and `blk_rerun` p values. This is a reproduction of known values; no new result is opened. Differences are reported, not tuned away.

## What is reproduced exactly
- Same sessions/areas (step 1 `runs/rows.jsonl`, 154 rows, std6, ≥ 20 units), same spike counts (step 1 code: `spont_onsets(path, 8)`, `tax.area_counts`), same label vector, split and null draws: `Scheme("shared24", blk24, rng_for(session, area, 24))`, then 200 trial permutations, 1,000 block assignments and the 200-index subset for logistic refits, consumed in the order of step 1 `run_scheme` (the `lr_topk` subset is drawn before `lr_all`'s).
- Integrity check: step 1's own `Readouts.fit("lr_topk")` recomputed here must equal `rows.jsonl` accuracy in every area (else stop).

## Pipelines compared
- **A (gate):** `Pipeline(StandardScaler(), SelectKBest(score_func=|d′| as step 1: mean difference over sqrt of the average of the two ddof-1 variances, k = 20), LogisticRegression(C = 1))`. StandardScaler and LogisticRegression C = 1 match step 1 conventions (calibration z-score with ddof 0; penalty 0.5·||w||² + C·Σ log-loss, intercept unpenalised). Solver default (lbfgs, tol 1e-4, max_iter 100); one extra run of the observed fit with tol 1e-10, max_iter 10,000 to separate optimiser effects.
- **B (design pipeline):** the same with `SelectKBest(f_classif, k = 20)`. F ranks like |t|, which differs from |d′| when the two classes have unequal calibration counts.

## Gate criteria (fixed now)
1. A: observed held-out accuracy identical to step 1 in ≥ 95% of the 154 areas, and within one held-out trial in all others.
2. A: mouse-level pass rates at α = 0.05 (per session the fraction of areas with p < 0.05, then the mean over sessions; computed the same way for step 1 from `rows.jsonl`) for `trl_rerun`, `blk_fixed`, `blk_rerun` within ±3 percentage points of step 1.
3. B is reported with the same statistics. If B differs from A by more than 3 points in any of the three tests, step 2 uses A's ranking (|d′|) in its pipeline and states this in Methods; if not, B is used as designed. Either way both are reported.
If A fails 1 or 2, stop and find the cause before any step 2 compute.

## Run
`code/gate_pipeline.py` (scikit-learn 1.7.2, numpy 2.5.4, venv `trackA-school/venv-step2`), one process, `OMP_NUM_THREADS=1`. Output `gate/gate_rows.jsonl`, `gate/GATE-RESULT.md`.
