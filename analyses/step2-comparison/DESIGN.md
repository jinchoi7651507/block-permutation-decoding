# Step 2: the permutation tests that decoding tools run — design v2 (stamped 2026-10-21; §15 is the stamped specification, v1 text kept above it)

Status: **v1, 2026-10-20 23:06 KST.** v0 (commit a7784c8) was reviewed by a statistician (`review-statistician.md`) and an experimentalist (`review-experimentalist.md`); §12 lists what changed. Written after step 1 and its addendum were known. Before any run: a compute pilot (§10), this document finalised, committed and OTS-stamped. Results are reported whatever they show. Context: BC plan §0, §5-1, §20-1, §30, §30-1, §32; `TOOLBOX-DEFAULTS.md` (corrected 23:05).

## 1. Questions
- **Q1 (main table).** Run as shipped (the tool's permutation rule with the tool's default split), and with one line changed, what false-positive rate and power do the common decoding tools give when labels follow recording blocks?
- **Q2 (design rule).** How do the rates depend on block length relative to the drift time scale (L/τ), the number of held-out blocks, and drift strength?
- **Q3 (boundary).** Do the same tools stay valid when labels vary trial by trial (interleaved) under the same drift? (negative control; most experiments)

## 2. One classifier for every row
- scikit-learn `Pipeline(StandardScaler fit on training folds, SelectKBest(f_classif, k = 20), LogisticRegression(C = 1, L2))`, refit inside every fold and every permutation. Only the split and the permutation rule change between rows.
- Gate before any new cell: on the Allen `shared24` scheme with odd/even split, this pipeline's held-out accuracy and `blk_fixed`/`blk_rerun`/`trl_rerun`/`trn_trl` p values must reproduce step 1 `lr_topk` within a stated tolerance (ranking by F vs |d′| and penalty conventions are checked first; differences are reported, not tuned away).

## 3. Rows: permutation rules (named after the tool whose rule they reproduce)
| Row | Rule | Implementation |
|---|---|---|
| P1 | binomial test of the held-out correct count (no permutation) | common practice |
| P2 | all labels permuted at trial level, whole CV rerun (scikit-learn `permutation_test_score` default; MNE; MVPA-Light) | library function (scikit-learn, pinned); MVPA-Light rule = same, checked line by line |
| P3 | labels permuted within runs at trial level, CV rerun (CoSMoMVPA `cosmo_randomize_targets` with chunk = run) | port, same permutation indices as the MATLAB code; Octave run if available |
| P4 | training-partition labels permuted per fold, refit, test labels kept (PyMVPA tutorial; ADAM `randompermutations`) | PyMVPA library if it installs; else port |
| P5 | reference: block labels permuted between blocks, training and held-out together, refit | ours (`block_permutation_test_score`, §9) |
| Sanity / footnote | scikit-learn `groups = block`: p = 1 by construction (groups used by `_shuffle`); not in the grid, one line in Methods | — |
| Figure 1 only (from step 1) | decoder held fixed, block-preserving permutation | step 1 `blk_fixed` (practice survey 0/14) |
| Extended Data | circular shift, refit (Nevjen & Dunn) | step 1 `circ_rerun`, a few cells |

## 4. Columns: splits
- **S-tool:** each tool's default split as shipped — scikit-learn/MNE `cv=None` (unshuffled StratifiedKFold(5), contiguous in time); MVPA-Light repeated shuffled 5-fold; CoSMoMVPA/PyMVPA leave-one-chunk-out (chunk = run).
- **S-main (primary column): shuffled 5-fold** (`KFold(shuffle=True)`), training and test trials share blocks — the split the surveyed studies used (14/14 shared).
- **S-block:** whole blocks held out (GroupKFold by block), with three permutation variants reported separately: (a) degenerate `groups` (footnote), (b) trial-level permutation on the precomputed folds (expected above 5%; step 1 addendum `sep24 trn_trl` 7–14%), (c) block-level permutation (P5).
- Odd/even split: Extended Data only; its Allen cells equal step 1 by construction and are cited as a gate, not rerun.

## 5. Data
### 5a. Simulation (design rule and ground truth)
- Noise is a **continuous-time process on trials**, not a block-mean process (fixes the circularity found in review): k = 3 Ornstein–Uhlenbeck latent factors with time constant τ plus a slow linear/sigmoidal trend, unit loadings from a Gaussian, Poisson spikes; n = 100 units; trial length 2 s.
- **Calibrated from Allen spontaneous activity:** τ and factor variance estimated from the 30 new mice (autocorrelation of the first principal components of 2-s counts), reported with the grid; "Allen-level drift" = median estimate.
- Label designs: (i) random block assignment; (ii) **fixed-order designs ABAB, ABBA, AABB** (so that P5 is a real test, not exact by randomisation); (iii) one block per condition (B = 2–8; smallest attainable p and power of P5); (iv) **interleaved trial labels** under the same drift (negative control, Q3).
- Grid at δ = 0 (false positives): L/τ ∈ {0.3, 1, 3} × held-out blocks ∈ {4, 12, 24} × drift ∈ {0, Allen level, 2 × Allen}; f = 0.1 of units carry signal when δ > 0.
- Power only in the primary cell: δ ∈ {0, middle, large}, chosen in the pilot so that P5 power spans about 20–90%. Invalid tests: power reported only as size-adjusted power (threshold set at each test's own 5% null quantile) or marked invalid.
- Replicates: 1,000 in the primary cell, 500 elsewhere; 200 permutation draws per test; common random numbers across rows (same data, same split, same draws where rules coincide) so that contrasts are paired.

### 5b. Allen Neuropixels (real noise, fake labels)
- Step 1 data (30 new mice, std6). Schemes `shared24`, `sep24`, real grating trials `dg_shared24`, `dg_sep24`. New cells only for S-main and S-tool splits; odd/even cells are step 1 (gate).
- Positive control: real drifting-grating direction labels arranged in blocks (block design built from interleaved trials).

### 5c. EEG (step 2b; separate design file `../step2b-eeg/DESIGN.md`)
- MPI LEMON resting EEG (PDDL; 16 min per subject, eyes closed / open alternating in 60-s blocks). Fake labels orthogonal to eyes closed/open (each fake class gets the same number of EC and EO blocks); EC/EO labels serve as the positive control. Standard preprocessing (high-pass, re-reference, 2-s epochs, log band power per channel). Group-level column below.

## 6. Group-level column (EEG practice)
- Per subject (or per mouse) held-out accuracy, then a one-sample t-test and a sign-flip permutation across subjects against chance. Reported for S-main and S-block. Prediction: inflates under shared splits for the same reason as P2.

## 7. Primary contrasts (fixed now; everything else descriptive)
- **Primary cell:** simulation, random-block design, S-main, L/τ = 1, 12 held-out blocks, Allen-level drift, δ = 0.
- **Contrast M (one per row):** false-positive rate of P1, P2, P3, P4 minus that of P5 in the primary cell, paired by common random numbers, 95% interval over replicates.
- **Contrast R:** the same on Allen `shared24` with S-main, mouse-level bootstrap.
- **Contrast Q3:** false-positive rate of P2 with interleaved labels under Allen-level drift (expected about 5%).

## 8. Sanity cells (exact or fixed by construction; reported as checks, not findings)
- P5 under random block assignment, any split (exact by randomisation; P5 is tested for real only in the fixed-order designs).
- P4 block form in separate-block designs; decoder-fixed null in separate-block designs; `groups = block` (p = 1).
- P2 with interleaved labels and no drift.

## 9. Deliverable for users
- `block_permutation_test_score(estimator, X, y, blocks, cv, n_permutations, ...)`: scikit-learn compatible; permutes the per-block label vector between exchangeable blocks (or draws from a user-given generator for pseudosessions) and reruns the whole CV. Tested with pytest on simulated data (size at α = 0.05 within MC error in the fixed-order designs).
- A one-line fix per tool, each run in the table: scikit-learn (use the function, or GroupKFold + block-level labels), MNE (same), CoSMoMVPA/PyMVPA (permute chunk-level labels across chunks, rerun), ADAM/PyMVPA (permute all labels, not only training labels).
- Diagnostic: "run your pipeline on fake block labels drawn like the experiment's blocks; the pass rate is its false-positive rate" (Extended Data recipe).

## 10. Compute pilot (before stamping)
- Time one replicate of each row in the primary cell; extrapolate the grid; cut cells until the total fits about 2–3 days on 6 cores. Cuts are decided before stamping and listed here.

## 11. Predictions (fixed before running; may be wrong)
- P1, P2: inflate under S-main in proportion to drift and L/τ; near 5% with interleaved labels (Q3).
- P2 under S-tool (unshuffled StratifiedKFold): less inflated than under S-main, still above 5% when held-out folds contain several blocks of each label.
- P3: inflates under shared splits; leave-one-chunk-out with chunk = run reduces it.
- P4: inflates under shared splits at least as much as the fixed decoder; S-block with trial-level permutation above 5%.
- P5: about 5% in fixed-order designs when blocks are exchangeable enough (L/τ ≥ 1); may deviate when L/τ < 1 (drift crosses blocks) — a real test of the reference.
- One block per condition: no test reaches useful power for B ≤ 4.
- Group-level t-test: inflates under shared splits.

## 12. Changes from v0
- Generator: block-mean AR(1) replaced by a continuous OU + trend process calibrated on Allen (statistician must 1).
- Exact-by-construction cells moved to §8; fixed-order designs added so the reference is tested (must 2).
- T10 turned into the S-block column with three variants; scikit-learn `groups` degeneracy explained (must 3).
- CoSMoMVPA rule corrected from the code; rows split by tool; MNE noted (must 4; experimentalist).
- Tool default splits added (S-tool); row names "rule of X" (must 5; experimentalist).
- Power: size-adjusted or invalid (must 6). One primary cell per contrast (must 7). One pipeline with a gate to step 1 (must 8). Paired contrasts; exact-conditional overlay only for separate-block columns (must 9).
- Interleaved-label negative control, group-level column, EEG preprocessing, positive controls, per-tool fixes and the function (experimentalist musts).
- Cut: odd/even, fixed decoder and circular shift out of the main table; one readout; reduced grid; running covariate and long blocks deferred.

## 13. Proposed changes for v2 (2026-10-21 11:21 KST; after the gate, the pilot and the Allen calibration; to be persona-reviewed before stamping; the v1 text above is kept)
- **Gate (§2) done: PASS** (`gate/GATE-RESULT.md`): the |d′| pipeline reproduces step 1 `lr_topk` (149/154 areas identical, three pass rates equal); the f_classif pipeline is within 0.6 points → **f_classif kept as designed**. LogisticRegression `max_iter = 1000` (lbfgs stopped early in 5/154 areas at the default).
- **Pilot (§10) done** (`pilot/PILOT.md`): 8.2 s per replicate of all rules → about 90–110 core-hours in total; **no cuts**.
- **Generator (§5a) — [v1 text superseded if accepted]: the single-time-scale OU cannot match Allen** (`calib/CALIBRATION-NOTE.md`): PC1 time constant 1.9 trials (≈ 4 s), but the slow excess variance (0.31 over 10-trial windows) is out of reach (0.24 at the largest drift). Proposal: fast OU (τ_f) + slow OU (τ_s) + linear trend; τ_f from PC1 lags 1–5; τ_s and the slow variance from the autocorrelation of 10-trial window means (lags 1–10 windows) or a two-exponential fit over lags 1–60; the two variance scales matched to the lag-1 autocorrelation of PC1 and the slow excess variance. The grid is defined on τ_s: L/τ_s ∈ {0.3, 1, 3}, drift ∈ {0, Allen, 2 × Allen} on the slow component. A new calibration script is written and committed before running.
- **"Held-out blocks" (§5a grid) — clarified:** the grid factor is the number of blocks per simulated session, B ∈ {4, 12, 24} (each with L trials); under S-main every block contributes trials to every test fold; under S-block, GroupKFold(5) (or GroupKFold(4) when B = 4) holds out whole blocks.
- **P3 runs (§3):** 4 runs of equal length (B/4 consecutive blocks; B = 4 → 4 runs of one block, so the CoSMoMVPA rule errors whenever a run lacks a class, which with one label per block is always: reported as "not applicable"). Error share and both denominators reported (as 2b S6).
- **S-tool (§4):** StratifiedKFold(5) is re-split on every permuted label vector, as scikit-learn does with a splitter object (`sim.Resplit`; 2b review S3a; code 5df150c). P4 keeps the observed folds (PyMVPA/ADAM behaviour).
- **P5 null set:** drawn from the same set as the observed design (random balanced assignment → exact by randomisation, sanity cell; fixed-order designs → all balanced assignments, the real test), as in 2b §5.
- **Unit of inference for Allen cells:** mouse-level bootstrap, as in step 1; for simulation cells, replicates are independent sessions.

## 14. Response to the v2 statistician review (`review-v2-statistician.txt`, 2026-10-21; Claude, 11:25 KST)
Musts:
1–2. **Calibration by matching the same estimators on simulated data with Allen's layout** (3 spontaneous epochs of their real lengths, with the gaps, means removed within epoch as for Allen). The OU parameters are not set equal to the PC1 estimates.
3. **Parameters and targets:** σ_f, τ_f (fast shared), σ_s, τ_s (slow shared), σ_u (unit-specific slow, must 4); trend set to 0 during calibration (absorbed by the slow component) and used only as a separate grid arm. Targets: PC1 autocorrelation curve over lags 1–40 within epochs (two-exponential summary), slow excess variance of 10-trial windows, PC1 variance share. Matching by simulation over a fixed parameter grid (written before running), distance = sum of standardised differences; per-mouse fits give the IQR. If τ_s is not identified (flat distance along τ_s), Allen level is reported as a range and the grid is presented as a sensitivity analysis.
4. Unit-specific slow term added (σ_u), PC1 variance share as a target.
5. **Grid:** L fixed at 20 trials; τ_s = L / {0.3, 1, 3} = {67, 20, 7} trials; slow SD fixed at the Allen-level value; the Allen-level τ_s is marked, the others are stated as hypothetical. Blocks per session B ∈ {4, 12, 24} (renamed from "held-out blocks").
6. **Fixed in sim.py:** an undefined observed statistic gives p = NaN, counted as an error (was a small p).
7. **Fixed in sim.py:** every permutation rule uses the mean of fold accuracies (scikit-learn's statistic); P1 uses the pooled count.
8. Grid runner to be written, validated on synthetic data (interleaved labels with drift 0, and P5 under random assignment, both near 5%), committed and stamped with the design.
Shoulds: trend sign randomised per replicate; P3 compared with P5 on the same surviving replicates, error share reported (B = 4: not applicable); leave-one-chunk-out (CoSMoMVPA/PyMVPA tutorials) and repeated shuffled 5-fold (MVPA-Light) added to `splitter()` for the S-tool column; P5 with B = 4 has 6 assignments (smallest p about 0.17) → reported as "cannot reject", not as 0%; fixed-order designs reported with trend on and off, and "P5 fails" defined before running as a rate above the Monte Carlo 99% band of 5% with trend off; n_units drawn from the Allen distribution of area sizes (20–100); NaN/error exclusion rules and denominators fixed per cell; a mouse split-half check of the calibration; the generator's block-label pass rate reported as validation only, never used for tuning.
Coulds: per-mouse parameter draws as a sensitivity arm; no claim that P2 shares permutation draws with the other rules; per-cell seed logs.

## 15. v2 as stamped (2026-10-21 11:51 KST; supersedes the conflicting parts of §1–§12; §13–§14 give the reasons)
**Code:** `code/sim.py` (rules, `simulate2`, `block_permutation_test_score`), `code/run_grid.py` (one cell per call), calibration `calib_v2/CALIBRATION_v2.json`. Hashes in `DESIGN-v2.sha256` (with OTS proof). Any later change to these files is a deviation and is logged.
**Generator:** `simulate2` at the calibrated Allen level (τ_f 1, σ_f 0.6, σ_s 0.4, σ_u 0.4; base rate 5.48; n_units drawn per replicate from the 154 Allen area sizes; trend 0 in the main grid, sign-randomised trend 0.5 as a secondary arm). τ_s is not identified by the calibration (10–160 trials), so it is a grid factor.
**Grid (δ = 0):** L = 20 trials; τ_s ∈ {7, 20, 67, 160} (L/τ_s = 3, 1, 0.3, 0.125); slow drift scale ∈ {0, 1, 2} (multiplies σ_s and σ_u; the fast component stays); blocks per session B ∈ {4, 12, 24}. Designs: random balanced assignment (all cells), fixed-order ABAB/ABBA/AABB (B = 12 and 24, τ_s 20 and 67, drift 1, with trend 0 and 0.5), interleaved labels (negative control, every τ_s, drift 0/1/2, B = 12). Splits: S-main (shuffled KFold 5), S-tool (StratifiedKFold 5 re-split per permutation), S-block (GroupKFold min(5, B) fixed). Replicates: 1,000 in the primary cell, 500 elsewhere; 200 permutation draws.
**Primary cell:** random design, S-main, τ_s = 20 (L/τ_s = 1), B = 12, drift 1, δ = 0. **Contrast M:** rate of P1, P2, P3, P4 minus P5, paired by replicate, 95% bootstrap interval over replicates.
**Iid baseline (from the validation):** P1 and P4 exceed 5% on independent data (8.3%, 10.3%); every P1/P4 rate is also reported minus its interleaved-label, drift-0 baseline in the same τ_s/B/split.
**P5:** random design → exact sanity cell; fixed-order designs → the real test; "P5 fails" = rate above the Monte Carlo 99% band of 5% with trend 0. B = 4 → 6 assignments, smallest p ≈ 0.17: reported as "cannot reject".
**P3:** runs = 4 equal runs (B/4 blocks each); B = 4 → not applicable; error share and both denominators reported; compared with P5 on the same surviving replicates.
**Power (primary cell layout only):** δ ∈ {0, middle, large} chosen on 50 pilot replicates of P5 only (target P5 power about 20–50% and 70–90%), then 1,000 replicates; invalid rules: size-adjusted power.
**Allen cells:** step 1 schemes shared24, sep24, dg_shared24, dg_sep24 with S-main and S-tool splits, all rules, mouse-level bootstrap; seeds per (session, area) as step 1 streams + 200.
**Seeds:** `default_rng([seed, rep])` with one seed per cell listed in the run log; no draws added after seeing results.
**Not done (stated):** leave-one-chunk-out and repeated shuffled 5-fold splitters (should item; time) — S-tool uses the scikit-learn/MNE default only; per-mouse parameter draws.
