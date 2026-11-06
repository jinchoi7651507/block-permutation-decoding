# Step 1: decomposing the fake-label pass rate — design v2 (post hoc, designed before running)

Status: **post hoc analysis.** Designed on 2026-10-20 after the Track A fake-label results (C) were known. v1 of this document was reviewed by two persona reviewers before any run on recordings (`review-statistician.md`, `review-experimentalist.md`); v2 below answers them (§11 lists the changes). Design, code and predictions are committed before the analyses are run on the recordings. Results will be reported whatever they show. Context: `revised-manu/bc-reframe/BC-composition-plan.md` §12 step 1, §23, §23-7.

## 1. Questions and primary contrasts
- **Q-A (what produces the 26.5%).** With labels on separate calibration and held-out blocks, the selection cannot raise the expected held-out accuracy (held-out labels are randomised independently of the calibration ones). It can only change how strongly predictions within a held-out block agree. So the question is not "selection or correlated errors" but: how much of the binomial test's pass rate remains with a readout that uses **no label information at all**, and how does it grow with each step of label use (mapping only → ranking → ranking + cut search)?
  - **Primary contrast A:** in `sep`, pass rate of `binom` for `nosel0` vs `sel`.
- **Q-B (selection × block structure).** Does a block-permutation null need the readout refit in every draw? Expected: not when calibration and held-out trials come from separate blocks with independently assigned labels, yes when they share blocks (or when held-out labels depend on calibration labels).
  - **Primary contrast B:** for `sel`, (pass rate of `blk_fixed` − pass rate of `blk_rerun`) in `shared24` minus the same in `sep24` (24 blocks of about 37 s in both, so block length and number are matched).
- **Q-C (common alternatives and decoders).** How do a trial-label permutation that refits the readout (leakage-safe permutation), a circular shift, and the same tests with standard decoders (top-20 |d′| L2 logistic; L2 logistic on all units) behave?
- **Q-D (prediction).** Does the binomial test's false-positive rate follow the design effect, and can a practitioner predict it from data not used for the test?
- **Power.** Do the valid tests still detect a real (injected) signal?
- **Real trials.** Does the pattern hold on real drifting-grating presentations (fake labels, real trial structure)?

All other cells are secondary. Cells that are fixed by construction are **sanity checks**, not findings: `blk_rerun` in `sep`, `sep24`, `shared`, `shared24`, `half24` (the fake labels were drawn from the same assignments the null enumerates or samples, so the test is exact by randomisation); `blk_fixed` in `sep24` (held-out labels are independent of calibration, so it is also exact); `blk_fixed` in `sep` (only 20 distinct values among 400 assignments, smallest attainable p = 0.05, so it **cannot pass**; reported only to document this).

## 2. Data, units (unchanged from Track A C)
Allen Visual Coding Neuropixels, the 32 sessions of `trackA-std/sessions_trackA.csv`; estimates use the 30 new mice and the six standard areas (VISp, VISl, VISal, VISrl, VISam, VISpm). Units Allen labels good, rate ≥ 0.5 Hz on the trials used, ≥ 20 units per area. Spontaneous activity: three longest epochs (each ≥ 240 s), first 1 s dropped, cut into 4 (Track A, 12 blocks of about 74 s) or 8 (24 blocks of about 37 s) equal blocks per epoch; back-to-back 2-s pseudo-trials tile each block. Real trials: all drifting-grating presentations of the session in time order (2-s count window from onset; presentations are 2 s with 1 s grey between), cut into 24 contiguous blocks of equal trial count.

## 3. Label schemes
| Scheme | Blocks | Labels | Calibration / held-out | Block null |
|---|---|---|---|---|
| `iid` | 12 | random per pseudo-trial | odd / even | — |
| `sep` (Track A random_blocks) | 12 | 3 of 6 calibration and 3 of 6 held-out blocks per label | blocks 1,2,5,6,9,10 / 3,4,7,8,11,12 | exact, 400 |
| `segment` (Track A) | 12 | blocks 1–6 vs 7–12 | odd / even | exact, 924 |
| `shared` | 12 | 6 of 12 blocks per label | odd / even (both halves in every block) | exact, 924 |
| `sep24` | 24 | half of the 12 calibration and half of the 12 held-out blocks per label | pairs of blocks alternate calibration / held-out | Monte Carlo, 1,000 |
| `paired24` | 24 | half of the calibration blocks per label; each held-out block inherits the label of the calibration block two before it | as `sep24` | Monte Carlo, 1,000 (same rule) |
| `shared24` | 24 | 12 of 24 blocks per label | odd / even | Monte Carlo, 1,000 |
| `half24` | 24 | as `shared24` | first half of each block / second half (shared blocks, less adjacency) | Monte Carlo, 1,000 |
| `dg_iid`, `dg_sep24`, `dg_shared24` | 24 (real trials) | as `iid`, `sep24`, `shared24` | as above | as above |
`paired24` separates "shared blocks" from "dependent labels": blocks are not shared, but held-out labels follow calibration labels.

## 4. Readouts (label use increases down the list)
| Readout | Uses labels for | Notes |
|---|---|---|
| `nosel0` | nothing | label-free random two pools (unit order and pool-to-class sign drawn once per area, streams 31/33/35), cut at n // 2 |
| `nosel` | pool-to-class mapping (1 bit) | same pools |
| `rank` | unit ranking by signed calibration d′ + mapping | cut fixed at n // 2 (no cut search) |
| `sel` | ranking + cut search + mapping | the planned Track A readout |
| `lr_topk` | top-20 units by calibration |d′| + L2 logistic weights | Track A `logistic_fit` (penalty 0.5‖w‖², λ = 1), k fixed (no inner CV, for run time) |
| `lr_all` | L2 logistic weights on all units | "no unit selection" for a standard decoder |
Also `spec` (random unit order + cut search, Track A) as a null for `sel` in the gate schemes. Real-trial schemes use `sel`, `nosel0`, `lr_topk` only; `sep` uses all readouts for `binom` but the permutation tests only for the cheap readouts.

## 5. Tests (pass = p < 0.05, one-sided)
| Test | Definition | Draws |
|---|---|---|
| `binom` | binomial test of the held-out correct count (counted directly) against the held-out majority rate | — |
| `blk_rerun` | block null (§3), readout refit in every draw | as §3; logistic readouts 200 (random subset of the enumeration or of the Monte Carlo draws) |
| `blk_fixed` | the same assignments, readout fixed at the fit on the true labels; held-out accuracy of its fixed predictions | as §3 |
| `trl_rerun` / `trl_fixed` | labels permuted across all trials, readout refit / fixed | 200 |
| `circ_rerun` (`sel`) | label vector circularly shifted along time-ordered pseudo-trials, readout refit; 200 shifts evenly spaced, excluding shifts shorter than the longest block; only in odd/even schemes (`iid`, `segment`, `shared`, `shared24`) | 200 |
| `spec` (`sel`, gate schemes) | Track A random-order null | 200 |
Monte Carlo p = (1 + #{null ≥ observed} + #NaN) / (N + 1); exact p = share of enumerated assignments (observed included) at or above the observed score. NaN counts are stored.

## 6. Positive control (power)
In `sep24` and `shared24`, a real signal is injected: on label-1 trials, Poisson(δ × the unit's mean count) extra spikes are added to 10% of units (at least 2), δ ∈ {0.1, 0.2, 0.4} (streams 70–72, 80–82). Readouts `sel` and `lr_topk`; tests `binom`, `blk_fixed`, `blk_rerun`, `trl_rerun` (200 draws each). Reported: pass rates (power) per δ.

## 7. Block-number sweep and predictions (Q-D)
Separate-block design (pairs of blocks alternate calibration / held-out; half of the calibration and half of the held-out blocks per label). Variants: 4, 8, 16 blocks per epoch (blocks of about 74, 37, 18 s; 6, 12, 24 held-out blocks), and two thinned variants that keep 4 blocks per epoch but shorten them (every 2nd of 8, every 4th of 16: 6 held-out blocks of about 37 s and 18 s), which separates block length from block number. Readouts `sel` and `nosel0`; test `binom`. Three predictions per area:
1. **Exact conditional rate** `cond_pass`: with the readout's held-out predictions fixed (they do not depend on the held-out labels), the share of admissible held-out labelings under which the binomial test passes (enumerated up to 20,000 labelings, else 20,000 Monte Carlo). Its mean over areas is the expected false-positive rate; the observed pass rate should match it (implementation check).
2. **Design effect from held-out predictions** `pred_ho`: ρ̂ = one-way ANOVA intraclass correlation of the held-out predictions within held-out blocks (labels unused), m̃ = Σm²/Σm (Kish), DEFF = 1 + (m̃ − 1)ρ̂, predicted rate = 1 − Φ(z₀.₉₅ / √DEFF). Tests whether the classical formula is accurate (compare with 1).
3. **Practitioner's prediction** `pred_xfit`: ρ̂ cross-fitted on calibration blocks only (fit the readout on alternate calibration blocks, ICC of its predictions on the others, both ways, averaged), same formula. Tests whether the rate can be predicted before looking at held-out data.
Unclipped ρ̂ is stored; negative ρ̂ is set to 0 in DEFF.

## 8. Gate
For `iid`, `sep` and `segment`, the `sel` readout consumes Track A's streams in Track A's order, so its `binom`, `spec`, `trl_rerun` (iid, segment) and `blk_rerun` must equal `q2_p`, `spec_p`, `full_p`, `block_p` in `trackA-std/runs/extra.jsonl` for every (session, area) in both files. `summarize.py` stops without writing results if any value differs by more than 1e-12.

## 9. Predictions (written before running; may be wrong)
- P-A: `nosel0` in `sep` passes `binom` well above 5%, a large share of `sel`'s rate; pass rates rise along `nosel0` → `nosel` → `rank` → `sel` as more label information shapes the predictions.
- P-B: contrast B is positive: in `shared24` `blk_fixed` passes far more than `blk_rerun`, while in `sep24` both are near 5%.
- P-B2: `paired24` `blk_fixed` also inflates (dependent labels suffice), less than `shared24`. `half24` still inflates (drift slower than half a block).
- P-C: `trl_rerun` and `trl_fixed` inflate in every block scheme; `lr_topk` and `lr_all` show the same pattern as `sel` for `binom`, `blk_fixed`, `blk_rerun`. No prediction for `circ_rerun`.
- P-D: `cond_pass` matches the observed rate; `pred_ho` is close to it; `pred_xfit` is in the right range but less accurate; rates fall with more, shorter blocks.
- P-power: `blk_rerun` gains power with δ but less than the invalid `binom`.
- P-real: the real-trial schemes show the same direction as the spontaneous ones, possibly weaker (gaps between presentations).
- `iid`: every test near 5%, fixed and rerun alike.

## 10. Summary statistics and reporting
Per cell: mean over the 30 new mice of each mouse's proportion of areas (std6) with p < 0.05, 95% mouse-bootstrap interval (B = 20,000, seed 20261015). Contrast B per area, averaged per mouse, bootstrapped. Sensitivity: all 32 mice. Areas within a mouse share drift; the mouse bootstrap handles that, and area proportions are not independent trials. Everything in §3–§7 is reported regardless of outcome, with the gate result, run times and any deviation from this document.

## 11. Changes from v1 after the persona reviews
- `blk_fixed` in `sep` cannot pass (20 distinct values / 400): Q-B moved to 24-block schemes (`sep24`, `shared24`), `sep` cell labelled.
- Q-A reframed (selection only changes within-block agreement in `sep`); `nosel0` (no label use) and `rank` added.
- The "ρ = 1 upper bound" was wrong (independent coins vs exactly balanced labels; not a bound): replaced by the exact conditional rate; ρ̂ on calibration was circular for `sel`: replaced by held-out-prediction ICC and a cross-fitted calibration ICC; Kish block size.
- Standard decoders (`lr_topk`, `lr_all`), positive control, real-trial schemes, `paired24` (dependent labels without shared blocks), `half24` (shared blocks with less adjacency), thinned sweep variants added.
- Circular shift restricted to odd/even schemes, cutoff at the longest block.
- Gate stops the summary; NaN counts stored; sanity-check cells labelled; primary contrasts fixed.
- Not done (reviewers' "should/nice"): running-speed covariates, random k-fold splits, longer blocks than 74 s (limited by 3 epochs of about 5 min), 1,000 draws for trial permutations.
