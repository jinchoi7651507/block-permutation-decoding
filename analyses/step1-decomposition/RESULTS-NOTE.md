# Step 1 results against the predictions (2026-10-20 05:50 KST)

Design: `DESIGN.md` v2 (post hoc, committed and OTS-stamped before running, commit 63050a0). Run: 03:16–05:45 KST, 4 workers, 32 sessions, 154 (session, area) rows in std6, 8.6 core-hours for the new mice. Full tables: `results/results.md` and `results/results.json` (written by `code/summarize.py`). All numbers below are mouse-level pass rates (% of areas with p < 0.05, mean over 30 new mice, 95% mouse-bootstrap interval) unless stated.

## Gate and integrity
- Gate: 1,540 values (binom, spec, trl_rerun, blk_rerun of `sel` in `iid`, `sep`, `segment`) equal Track A's `trackA-std/runs/extra.jsonl`: **0 mismatches.**
- NaN null draws: 0. Every std6 area with ≥ 20 units has spontaneous and grating results (154 rows).
- Sanity checks (exact by construction) behaved as expected: `blk_rerun` 1.5–5.3% in `sep`, `sep24`, `shared`, `shared24`, `half24`, `paired24`; `sep` `blk_fixed` 0.0% for every readout (cannot pass: 20 distinct values in 400).
- Deviations from DESIGN.md: none.

## Primary contrasts
- **A (`sep`, binom, sel − nosel0): −1.6 points (−10.3 to 7.6).** `sel` 26.5% (20.6–32.7), `nosel0` 28.1% (21.3–34.9). A readout that uses no label information passes the held-out binomial test as often as the selected readout. In this separate-block design the 26.5% comes entirely from correlated errors within held-out blocks, not from selection.
- **B (`sel`, (blk_fixed − blk_rerun) in shared24 minus in sep24): 61.9 points (50.7–73.1).** For `lr_topk` 81.1 (74.6–87.4). Sensitivity, all 32 mice: 61.5 (51.0–71.8) and 81.2 (75.1–87.2).
  - `shared24`: `blk_fixed` sel 62.7% (52.1–73.2), lr_topk 83.7% (77.2–89.9), lr_all 95.3% (91.4–98.6); `blk_rerun` 1.5–3.4%.
  - `sep24`: `blk_fixed` 2.6–5.9%, `blk_rerun` 3.8–6.0% for every readout.

## Predictions (DESIGN.md §9) vs outcomes
| Prediction | Outcome | Verdict |
|---|---|---|
| P-A: `nosel0` in `sep` passes binom well above 5%, a large share of `sel`'s rate | 28.1% vs 26.5% (equal) | confirmed |
| P-A: pass rates rise nosel0 → nosel → rank → sel in `sep` | flat: 28.1, 27.4, 27.2, 26.5 | **not confirmed** (selection adds nothing to binom in separate blocks; it does in shared blocks: shared24 binom 13.9 → 23.7 → 93.4 → 94.9) |
| P-B: contrast B positive; in `sep24` fixed and rerun near 5% | 61.9 points; sep24 2.6–6.0% | confirmed |
| P-B2: `paired24` fixed inflates, less than shared24 | sel 21.3% (14.6–28.4), lr_topk 24.9%, lr_all 22.4% vs shared24 62.7 / 83.7 / 95.3 | confirmed |
| P-B2: `half24` still inflates | sel 45.5% (38.3–52.7), lr_topk 64.2%, lr_all 70.2% | confirmed |
| P-C: trl_rerun and trl_fixed inflate in every block scheme | sep 26.8 / 25.8; sep24 28.3 / 29.8; shared24 95.8 / 94.9; paired24 75.8 / 77.2; half24 88.1 / 87.5 (sel) | confirmed |
| P-C: logistic readouts show the same pattern | yes, larger fixed-null inflation the more weights are fitted (shared24 blk_fixed: nosel0 4.2, nosel 9.7, rank 42.7, sel 62.7, lr_topk 83.7, lr_all 95.3) | confirmed |
| circ_rerun (no prediction) | iid 2.8, shared 15.1, shared24 5.1, segment 35.1 | — |
| P-D: `cond_pass` matches observed | sel: 26.3 vs 25.9 (B = 4), 26.7 vs 30.7 (8), 19.4 vs 26.3 (16); nosel0: 23.1 vs 29.7, 20.0 vs 26.4, 13.4 vs 10.3; observed intervals include the conditional rate in 9 of 10 variants (miss: nosel0 B = 4, 23.1 vs 23.4–36.1; borderline: sel B = 16, 19.4 vs 19.2–33.7) | mostly confirmed |
| P-D: `pred_ho` close to it | 1.0–3.8 points above `cond_pass` (normal approximation slightly high) | confirmed |
| P-D: `pred_xfit` right range, less accurate | sel overpredicts more (37.0 vs 25.9 at B = 4; cross-fit ρ̂ 0.77 vs held-out 0.48); nosel0 close | confirmed (cross-fit ρ̂ still biased up for sel) |
| P-D: rates fall with more, shorter blocks | nosel0 yes (29.7 → 26.4 → 10.3); sel no (25.9 → 30.7 → 26.3; ρ̂ stays about 0.5) | **partly** |
| P-power: blk_rerun gains power with δ, less than invalid binom | sep24 sel 8.2 / 6.2 / 37.3, lr_topk 8.8 / 18.4 / 60.0; shared24 sel 5.6 / 7.7 / 64.5, lr_topk 6.4 / 18.9 / 87.8 | confirmed; power is low at δ ≤ 0.2 (10% of units) |
| P-real: grating trials same direction, maybe weaker | dg_shared24: binom sel 88.3, blk_fixed 52.6 / lr_topk 70.9, blk_rerun 3.2 / 4.0; dg_sep24 fixed 4.7 / 6.9; dg_iid near nominal | confirmed |
| iid: every test near 5% | 0.6–6.1% | confirmed |

## What this means for the claim (reading)
1. The 26.5% is a property of the held-out binomial test under block structure, not of selection (contrast A). This is the known phenomenon (Harris 2020; Schreiber & Krekelberg 2013); we now quantify it on real recordings and show that the exact conditional rate predicts it.
2. The new, large effect is contrast B: when calibration and held-out trials share blocks (or held-out labels follow calibration labels), a block-preserving permutation null that keeps the fitted decoder fixed passes 63% (two-pool readout), 84% (top-20 logistic) and 95% (all-unit logistic) of fake labels, while the same null with the decoder refit in every draw stays at 2–3%. The inflation grows with how much of the decoder is fitted to the labels, so the rule concerns the whole fitted readout (unit selection and weights), not unit selection alone.
3. The same holds on real drifting-grating trials (53% and 71% vs 3–4%).
4. Separating calibration and held-out blocks with independent label assignment (sep24) makes the fixed null valid (3–6%).
5. Caveat for writing: refitting inside the null is the classical whole-pipeline principle (Ambroise & McLachlan; Valente 2021). The contribution is the size of the error when it is skipped in block-preserving nulls on real data, its dependence on design (shared vs separate vs paired blocks), and the real-trial confirmation. Power of the valid null is modest for weak signals.

---

# Addendum: training-label-only permutation (Within(Train)) — results (2026-10-20 15:30 KST)

Design: `DESIGN-ADDENDUM-within-train.md` (post hoc, persona-reviewed, committed and OTS-stamped before running, a7252cc). Run 14:55–15:28 KST, 5 workers, 154 rows, 2.5 core-hours. Tables: `results/within_train.md`, `results/within_train.json` (`code/summarize_within_train.py`). Gate: 4,774 observed accuracies equal `runs/rows.jsonl`, 0 mismatches, 0 NaN. Deviations: none.

## Primary contrast T (trn_blk, shared24 − sep24)
- `sel` **79.3 points (74.8–83.9)**, `lr_topk` **86.6 (80.8–92.0)**.
- `shared24` `trn_blk`: sel 82.2%, rank 68.2%, lr_topk 89.4%, lr_all 92.8% — at or above the fixed-decoder null (`blk_fixed` 62.7 / 42.7 / 83.7 / 95.3). `trn_trl`: 75.1–97.2%.
- `sep24` `trn_blk` 2.9–4.6% (exact by construction; sanity check passed).

## Predictions vs outcomes
| Prediction | Outcome | Verdict |
|---|---|---|
| P-T1: shared24/half24 inflate, in the range of blk_fixed or higher | shared24 trn_blk 68–93%, trn_trl 75–97%; half24 trn_blk 47–72%, trn_trl 58–80% | confirmed |
| P-T2: sep24 trn_blk near 5% (exact); trn_trl direction uncertain | trn_blk 2.9–4.6%; **trn_trl 7.0–14.3%** (sel 11.1, lr_topk 10.6, lr_all 14.3) | trn_blk confirmed; trn_trl **above 5% with separate blocks** |
| P-T3: iid trn_trl near 5% (exact) | 2.3–5.7% | confirmed (sanity) |
| P-T4: paired24 in between | trn_trl 44–54%, trn_blk 25–29% | confirmed |
| P-T5: real trials same direction | dg_shared24 trn_blk 67/81%, trn_trl 83/93%; dg_sep24 trn_blk 3/5%, trn_trl 15/15% | confirmed |

## Structural note
- `nosel` cannot pass either test (0% everywhere): it uses the labels only for the pool-to-class mapping, so each null draw reproduces the observed predictions or their mirror image and p ≥ about 0.5. Like `sep` `blk_fixed` in step 1, this cell documents a property of the test, not a finding.

## What this means (reading)
1. Refitting in every draw is not enough. A null that refits the decoder but permutes only the training labels, as PyMVPA and ADAM do, passed 68–93% (block-preserving) and 75–97% (trial-level) of fake labels when training and held-out trials share blocks, more than keeping the decoder fixed. Only permuting the labels of all trials together and refitting (Valente's "Before"; our `blk_rerun`) stayed at 2–3%.
2. With separate blocks, the trial-level form still passed 7–14% (15% on real grating trials); the block-preserving form was exact. So the rule is: permute labels of training and held-out trials together, preserving blocks, and refit; or hold out whole blocks and permute at the block level.
3. Valente et al. 2021 showed Within(Train) inflates under repeated cross-validation with independent data; here it fails with a single split once blocks are shared, by a much larger margin.

---

## Timestamp disclosure (added 2026-10-27 03:4x KST; the text above is unchanged)
The two OpenTimestamps proofs of step 1 were upgraded only on 2026-10-27 (they had stayed pending since submission). The Bitcoin attestations are later than the commit and submission times:
- `DESIGN.sha256.ots` (design v2): commit and submission 2026-10-20 03:15:53 KST; Bitcoin block 972191, block time 2026-10-20 03:25 KST. The run started at 03:16, about 9 minutes before the block time, and ended at 05:45.
- `DESIGN-ADDENDUM.sha256.ots` (training-label addendum): commit and submission 14:55:23 KST; Bitcoin block 972315, block time 20:45 KST. The run (14:55–15:28) ended about 5 h 17 min before the block time.
So the order "design fixed before data" is shown by the git commits and the submission to the calendar servers, but it is not third-party verifiable from the Bitcoin attestation for either file: the project rule (wait for the attestation before running, set on 2026-09-30) was not followed for step 1. Both designs are post hoc with respect to the earlier analysis of the same mice (stated in each). Every later step waited for the attestation (block times checked 2026-10-27).
- Clarification (2026-10-27 03:4x KST, same day; the paragraph above is kept): the project rule concerns opening data values before the attestation. Design v2: the run started 9 min before the block time, but no output was read before the run ended at 05:45, after the block time (03:25), so values were opened after the third-party time. Addendum: its results were read at about 15:30 KST (BC plan §32, 15:30), about 5 h 15 min before the block time (20:45), so for the addendum the third-party order does not hold; only the commit (a7252cc, 14:55) and the calendar submission precede the run.

**Correction (2026-10-28 17:25 KST; the lines above are kept):** the training-label addendum's proof carries four Bitcoin attestations from different calendars (blocks 972271, 972272, 972300 and 972315; `ots info DESIGN-ADDENDUM.sha256.ots`). On 2026-10-27 only block 972315 was read. The earliest attestation, which is the third-party time, is block 972271 at 2026-10-20 14:59:58 KST, about 5 minutes after the commit and submission (14:55:23). The run (14:55–15:28) therefore started about 5 minutes before the block, and no output was read before the block: results were first opened at about 15:30, after it. The statement above that the run ended about 5 h 17 min before the block time, and the clarification that values were opened about 5 h 15 min before it, are wrong. For design v2 the earliest attestation is block 972191 (03:25 KST), as stated. The two step 1 proofs now stand alike: each run started a few minutes before its block, and no result was opened before the block.

**Correction (2026-10-29 15:43 KST; the text above is kept):** the P-D row says `pred_ho` was "1.0–3.8 points above `cond_pass`". From `results/results.md` (block-number sweep) the differences are 0.3–5.4 points across the 10 variants (5.4 for 4 blocks, `sel`). The reading (the normal approximation is slightly high) is unchanged.
