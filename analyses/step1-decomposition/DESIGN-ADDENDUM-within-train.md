# Step 1 addendum: training-label-only permutation (Within(Train)) — design (post hoc, written before running)

Status: **post hoc addendum** to `DESIGN.md` v2 (commit 63050a0). Written 2026-10-20 after the step 1 results were known (`RESULTS-NOTE.md`). Reason: the claim (BC plan §0) covers only "decoder fixed" vs "whole pipeline refit"; the permutation scheme that toolboxes such as PyMVPA and ADAM implement, which permutes only the training labels and refits (Valente et al. 2021 "Within(Train)"), was not measured, and reviewers are likely to ask about it. Design and code are committed and OTS-stamped before the run. Results are reported whatever they show. Nothing in step 1 is changed: the addendum reads the same recordings, builds the same labels with the same random streams, and writes to a separate file.

## 1. Question and primary contrast
- **Q-T.** When calibration (training) and held-out trials share blocks, does a null that permutes only the training labels and refits the readout, while held-out labels stay as observed, keep the nominal rate? And when blocks are separate?
- **Primary contrast T (per readout `sel`, `lr_topk`):** pass rate of `trn_blk` in `shared24` minus in `sep24`.
- Secondary: `trn_trl` in every scheme; all readouts; real grating trials.

## 2. Tests (pass = p < 0.05, one-sided, Monte Carlo p = (1 + #{null ≥ obs} + #NaN)/(N + 1))
| Test | Null draw | Draws |
|---|---|---|
| `trn_trl` | calibration labels permuted across calibration trials (trial level); held-out labels unchanged; readout refit; held-out accuracy against the observed held-out labels | 200 |
| `trn_blk` | a new block assignment drawn from the scheme's block null (`Scheme._draw`, same rule as `blk_*`); its labels replace the calibration labels only; held-out labels unchanged; readout refit; held-out accuracy against the observed held-out labels | 200 |
The observed statistic is the step 1 held-out accuracy of the readout fit on the true labels (unchanged). Note: step 1's `trl_fixed` already equals Valente's Within(Test) (fixed predictions; only the held-out part of the permuted labels enters the score). Both tests here are single-split analogues of Within(Train), not Valente's repeated k-fold procedure.
- **Exact by construction (sanity checks, not findings):** `trn_blk` in `sep24` and `dg_sep24` (held-out labels are independent of calibration labels and the calibration labels are drawn from the same assignment rule) and `trn_trl` in `iid` and `dg_iid` (labels exchangeable across trials). Contrast T is therefore in effect "the `shared24` rate minus about 5%".
- `paired24`: replacing only the calibration labels breaks the design rule that held-out blocks inherit their labels from calibration blocks, so `trn_blk` there is not the design's randomisation distribution; it is reported as the analogue a user would run, not as an exact test.

## 3. Schemes, readouts, data
- Schemes (as `DESIGN.md` §3, same blocks, same label streams): `iid` (trn_trl only; no blocks), `sep24`, `paired24`, `shared24`, `half24`; real trials `dg_iid` (trn_trl only), `dg_sep24`, `dg_shared24`.
- Readouts: `sel`, `rank`, `nosel`, `lr_topk`, `lr_all` (spontaneous); `sel`, `lr_topk` (real trials). `nosel0` is skipped: it uses no labels, so its null equals the observation.
- Data and units: as step 1 (30 new mice, std6, 154 (session, area) rows; estimates on the 30 new mice, sensitivity all 32).
- Random streams: labels use the step 1 streams (unchanged). `trn_trl` draws use `rng_for(session, area, 140 + STREAMS[scheme])` (spontaneous) and `190 + STREAMS[scheme]` (real trials); `trn_blk` block assignments use `160 + STREAMS[scheme]` and `210 + STREAMS[scheme]` (set as the scheme's generator after the labels are drawn).

## 4. Gate
For every scheme and readout, the observed held-out accuracy recomputed here must equal `acc` in `runs/rows.jsonl` (|difference| ≤ 1e-9). `summarize_within_train.py` stops without writing results if any value differs.

## 5. Predictions (written before running; may be wrong)
- P-T1: in `shared24` and `half24`, `trn_blk` and `trn_trl` pass far above 5% for label-fitted readouts (the observed readout learns the block pattern shared with the held-out labels; null readouts trained on other labels do not), in the range of `blk_fixed` or higher; contrast T clearly positive.
- P-T2: in `sep24`, `trn_blk` is near 5% (exact). `trn_trl` direction uncertain: null readouts trained on trial-shuffled labels still give block-correlated predictions through drift (label-free `nosel0` passes the binomial test 28% in `sep`), while the observed readout picks drift-aligned units and may vary more across label assignments; if `trn_trl` is clearly above 5% here, a trial-level Within(Train) is invalid even with separate blocks.
- P-T3: in `iid`, `trn_trl` near 5% (exact by construction).
- P-T4: `paired24` in between (dependent labels without shared blocks).
- P-T5: real trials show the same direction.

## 6. Summary and reporting
As `DESIGN.md` §10: per cell, mean over the 30 new mice of each mouse's proportion of areas with p < 0.05, 95% mouse-bootstrap interval (B = 20,000, seed 20261015); contrast T per area, averaged per mouse, bootstrapped. Output `results/within_train.json`, `results/within_train.md`; raw rows `runs/within_train_rows*.jsonl`. Every cell is reported with the gate result, the number of areas with a NaN observed accuracy, and run time. Persona review before running: `review-addendum-statistician.md` (must items 1–2 and should items 3–5 applied; nice items 6–7 applied).
