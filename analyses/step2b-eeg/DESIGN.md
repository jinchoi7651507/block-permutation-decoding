# Step 2b: the same permutation rules on human resting EEG (MPI LEMON) — design v2 (stamped before the subject list and any EEG download)

Status: **v2, 2026-10-21 12:17 KST** (v1 11:17 KST, after two persona reviews). v0 (commit 2e718d0) was reviewed by a statistician (`review-statistician.txt`) and an EEG experimentalist (`review-eeg.txt`); §12 lists what changed. No EEG data has been downloaded or opened. Before running: eligibility check from the small marker files (§2), subject list drawn and stamped, this design finalised together with step 2 v2, committed and OTS-stamped. Results are reported whatever they show. Context: BC plan §30 (second recording modality), §27-2 (White & Power 2023 used fake block labels on EEG with accuracy only).

## 1. Questions
- **Q1.** With labels that follow 60-s recording blocks and carry no information, what false-positive rate do the step 2 rules (P1–P5) give on real EEG under shared-block splits, the tool's default split and whole-block splits?
- **Q2.** Power: with graded real signal (§4), do the valid rules keep power, and how much do the invalid ones gain (size-adjusted)?
- **Q3.** Group level: does the common across-subject t-test of per-subject accuracy inflate under shared-block splits, and does a valid group test not?
- **Scope (E5):** resting EC/EO alternation gives each block a strong state signature, so these rates may be an upper bound relative to task EEG. The result shows whether a rule fails on this kind of data, not how often it fails in a typical experiment. EC-only and EO-only arms (§4) remove the EC/EO signature.

## 2. Data and subjects
- MPI LEMON raw resting EEG (BrainVision, 61 EEG + VEOG, 2,500 Hz), 16 blocks of about 60 s alternating EC/EO. Licence PDDL (NITRC page); re-check the data use terms before download.
- **Eligibility from the marker files first (E3):** download only `.vhdr`/`.vmrk` for all subjects; eligible = 16 condition segments that alternate, each 50–80 s long between consecutive condition onsets, condition read from the marker text (server EEG_Info: S200 = eyes open, S210 = eyes closed), `.eeg` present. Extra markers (boundary, New Segment, impedance) handled and counted.
- **Subject draw (E4):** 40 subjects drawn at random from the eligible IDs with `default_rng(20261021)`, stratified by the age bin in the public meta file (young = age bin starting below 55, old = 55 and above, in proportion to the eligible counts); the script stops if a stratum has too few eligible subjects; list stamped before any `.eeg` download. Report EC-first vs EO-first counts. A subject that fails preprocessing (§3) is replaced by the next in the seeded order, reported.
- Every marker file found so far starts with S210 (eyes closed), whereas EEG_Info says half of the participants started with eyes closed; the EC/EO labels are therefore treated as unverified until the data check. After download: confirm EC/EO from the data (posterior alpha EC > EO per subject); a subject where it fails is reported, kept in the fake-label table, dropped only from the positive-control plot (E12).

## 3. Preprocessing (primary = cleaned; minimal = sensitivity arm) (E1, E2, E9)
MNE-Python and scikit-learn versions pinned and printed. Crop to the 16-min span, then resample to 250 Hz.
- **Cleaned (primary):** band-pass 1–45 Hz with a 50 Hz notch (PSD checked); bad channels by a rule fixed before running (flat, or z-scored log variance > 5) interpolated before the average reference; ICA (20 components, fit on the 1 Hz high-passed data) with ocular components chosen by correlation with VEOG (|r| > 0.5); epoch rejection by peak-to-peak 150 µV after ICA.
- **Minimal (sensitivity):** the v0 pipeline (1–45 Hz, average reference, 300 µV threshold, no ICA).
- Epochs: non-overlapping 2-s windows within each block, skipping the first 5 s and the last 2 s (sensitivity run with 2/2 s). Subjects with fewer than 20 epochs in any block are dropped (reported).
- Features: log band power per channel (delta 1–4, theta 4–8, alpha 8–13, beta 13–30, gamma 30–45 Hz; Welch, 1-s windows, 50% overlap) → 305 features. Gamma is kept but not read as neural.

## 4. Labels
- **Fake labels, balanced (Q1):** per subject, the 16 blocks are split into two classes with 4 EC + 4 EO blocks each, uniformly among the 4,900 such assignments (2,450 distinct up to the A/B swap), drawn without replacement; 50 assignments per subject; seed `default_rng([2026, 2, subject_index, draw])`. Constant within a block.
- **EC-only and EO-only arms (S8, E5):** labels within one state: the 8 EC (or 8 EO) blocks split 4 + 4 (70 assignments, 35 distinct); only epochs of that state used. Smallest attainable P5 p reported (about 1/35).
- **Fixed-order fake designs (S2):** EC/EO-balanced drift-aligned patterns: (i) first half vs second half (blocks 1–8 vs 9–16, 4 EC + 4 EO each), (ii) quarter patterns (AABB at the level of block pairs), (iii) ABBA (orthogonal to a linear trend; control pattern). P5 null set: all balanced assignments. Reported as the pooled p-value distribution across subjects (uniformity), not only the rate.
- **Long-block arm (S11, E10; secondary):** 120-s fake blocks (pairs of consecutive real blocks, EC/EO balanced by construction; 8 blocks, 70 assignments, 35 distinct). 240 s is not run (P5 cannot reach p < 0.05); stated.
- **Graded positive control (S7, E5; Q2):** EC/EO labels with the signal weakened so that P5 power spans about 20–90% (features restricted to frontal channels, or epochs subsampled), the rule chosen on 5 pilot subjects who are excluded from the main table and fixed before the main run. The full EC/EO control (at ceiling) is reported as a pipeline check under all splits.

## 5. Rules and splits (step 2 code, `../step2-comparison/code/sim.py`, same pipeline)
- Rows P1–P5 as step 2 §3; pipeline StandardScaler → SelectKBest(f_classif, k = 20) → LogisticRegression(C = 1, max_iter 1000); sensitivity runs with all 305 features (k = all) and with LDA without selection (E8). 200 permutation draws; per-draw accuracies stored with seeds (S12).
- **P5 null set (S1):** labels drawn from the same set as the observed assignment (balanced 4 + 4 sets; state-only sets for the EC-only/EO-only arms). Under random assignment P5 is exact by randomisation: it is the sanity reference, and the contrast "P2 − P5" is read as "P2 against nominal 5%".
- **S-tool (S3a):** StratifiedKFold(5) unshuffled, re-split on every permuted label vector (as scikit-learn does with a splitter object; `sim.Resplit`).
- **S-block (S3b):** GroupKFold(4) by block, deterministic (the same block-to-fold map in every replicate), passed as fixed folds.
- **P3 (S6):** runs of 4 consecutive blocks; runs lacking a class give the CoSMoMVPA error. Reported: error share, rate among non-errors, and rate with errors counted as non-rejections.
- Columns: S-main shuffled 5-fold, S-tool, S-block.

## 6. Outcomes and primary contrast (fixed now) (S4, S5)
- Unit of inference = subject. Per subject the rate of p < 0.05 over its 50 assignments; average over subjects; subject-level bootstrap (B = 20,000) for intervals. (Subject, assignment) pairs are never pooled into a binomial interval.
- **Primary contrast E:** false-positive rate of P2 minus P5 under S-main, balanced arm, cleaned pipeline; paired at (subject, assignment); subject-level bootstrap interval. "Inflated" = lower bound of the subject-level interval of the rule's rate above 10%.
- Secondary: P1, P3, P4 minus P5 under S-main; all rules under S-tool and S-block; EC-only/EO-only arms; fixed-order p-value distributions; long-block arm; minimal pipeline and 2-s skip; k = all and LDA readouts; graded positive control (size-adjusted power for invalid rules).
- **Group level (Q3):** per subject the S-main held-out accuracy for one assignment; (a) one-sample t-test against 0.5; (b) a valid group test: a Stelzer-style group null from each subject's P5 null accuracies (mean over subjects of one random null draw each, 10,000 times). Repeated over the 50 assignment draws; subjects bootstrapped for the interval. Both reported side by side.
- Per subject (E6): correlation of the fake labels with block index and with the alpha-power slope over the 16 min, logged; inflation reported against them. Per-block epoch counts reported (E7); balanced accuracy where epoch rejection unbalances classes (S9).

## 7. Predictions (fixed before running; may be wrong)
- P1, P2, P4 inflate under S-main in the balanced arm; less, but above 5%, in the EC-only/EO-only arms.
- P5 near 5% under random balanced assignment (exact by construction). For the drift-aligned fixed pattern (first vs second half), P5 with the full balanced null may reject more than 5% under vigilance drift (a finding, reported); ABBA near 5%.
- S-block: P5 exact; trial-level permutation on block folds above 5%.
- Graded positive control: P5 power in the 20–90% band by construction; invalid rules higher raw power, similar size-adjusted power.
- Group t-test inflates under S-main; the valid group test does not.
- Rates may be lower than in Allen spiking data if EEG drift is weaker relative to block length (reported either way).

## 8. Compute
Per subject: preprocessing with ICA about 2–3 min; at most 448 epochs × 305 features; one assignment of all rules about 8 s (step 2 pilot scale). 40 subjects × 50 assignments × 3 splits ≈ 13 core-hours for the main arm; arms and sensitivities about the same again → about 30 core-hours. Download: marker files first (small), then about 13 GB for 40 subjects.

## 9. Not done / out of scope
CSP or Riemannian tangent-space readouts (E8 alternative), relative band power (E11), task EEG.

## 12. Changes
- v1 → v2 (2026-10-21 12:17): the segment-length criterion 55–65 s was too strict (a check of the marker files alone, no EEG, left 31 of 220 subjects although 181 have 16 alternating segments); widened to 50–80 s; the draw stops instead of returning fewer subjects; the S210-first observation added to §2.

### v0 → v1 (review items)
- Statistician: S1 P5 null set named and drawn from the observed set; contrast read against nominal. S2 drift-aligned fixed patterns added, ABBA kept as control, p-value distributions, prediction restricted. S3 S-tool re-split per permutation (`sim.Resplit`, sim.py 5df150c), GroupKFold(4) deterministic. S4 subject as the unit, 50 assignments, subject bootstrap, "inflated" defined. S5 valid group test added. S6 P3 error denominator. S7 graded positive control. S8 EC-only/EO-only arms. S9 balanced accuracy. S10 40 subjects × 50, k = all run. S11 120-s arm, 240 s not run. S12 per-draw storage.
- EEG: E1 cleaned pipeline primary (interpolation, ICA with VEOG, 150 µV), minimal as sensitivity. E2 50 Hz notch, Welch 1-s/50%. E3 eligibility from markers, condition from marker text and data, 5-s skip with 2-s sensitivity. E4 seeded stratified subject draw, stamped. E5 scope statement, state-only arms, weakened positive control. E6 vigilance and label–time correlations logged. E7 epoch counts, subject drop rule. E8 LDA and k = all. E9 crop then resample, versions pinned. E10 120-s arm. E12 alpha-ratio check.
- Not taken: E11 relative band power (out of scope); CSP/Riemannian (time).
