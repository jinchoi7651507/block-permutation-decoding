# Step 2b preprocessing QC (qc_summary.py; QC files only, no label-dependent result)

## main (40 of 40 preprocessed)
- first condition: EC 40, EO 0
- bad channels per subject: median 1, max 4; Fp1/Fp2 flagged in 19, O1/Oz/O2 flagged in 0; flat channels in 0; MAD zero in 0
- ICA: not converged in 0 ; no component removed in 0 
- VEOG ptp (uV): min 228, max 979
- 50 Hz / 40-44 Hz power ratio: max 0.342
- epochs per block (cleaned 5/2 s): subjects below 20 in some block: [('sub-010029', 4), ('sub-010319', 16)]
- posterior alpha EC > EO: 40 of 40 (100%) -> codes kept; failing subjects left out of the positive-control plot only
- failing the alpha check: []

## pilot (5 of 5 preprocessed)
- first condition: EC 5, EO 0
- bad channels per subject: median 1, max 3; Fp1/Fp2 flagged in 3, O1/Oz/O2 flagged in 0; flat channels in 0; MAD zero in 0
- ICA: not converged in 0 ; no component removed in 0 
- VEOG ptp (uV): min 278, max 612
- 50 Hz / 40-44 Hz power ratio: max 0.265
- epochs per block (cleaned 5/2 s): subjects below 20 in some block: none
- posterior alpha EC > EO: 4 of 5 (80%) -> (pilot: not in the main tables)
- failing the alpha check: ['sub-010308']

## Reading (2026-10-22 19:03 KST; QC files and the graded-pilot output only, no main-arm result)
- **EC/EO codes (addendum §3):** posterior alpha EC > EO in 40 of 40 main subjects, so the marker codes are kept (S210 = eyes closed). All 40 recordings start with eyes closed (EC-first 40/40), although the dataset description says about half of the participants started with eyes closed; recorded, no action.
- **Epoch rule (DESIGN §3, addendum §3):** sub-010029 (4 epochs in one block) and sub-010319 (16) have fewer than 20 epochs in some block of the primary variant and are dropped without replacement. The analysis set is 38 subjects.
- Bad channels: Fp1/Fp2 flagged in 19 of 40 subjects, as the stress test anticipated (blink variance at the edge of the montage); O1/Oz/O2 in none; no flat channel; ICA converged and removed at least one component in every subject.
- **Pilot subjects:** sub-010308 fails the alpha check (pilot only; not in any main table).
- **Graded positive control (addendum §5): not achieved.** Pooled P5 power: R1 1.00, R2 0.90, R4 0.97, R3 0.84, R5 0.85, Q30–Q48 0.00. R2, R3 and R5 are within [0.20, 0.90] pooled but have per-subject power strictly between 0.05 and 0.95 in only 2 of 5 pilot subjects (3 required). By the stamped rule, pos_graded and balanced_graded are not run, and the graded control is reported as not achieved (`runs/graded_pilot.json`).
- To check before the results note (not a change to the stamped rule): every mixing step gives P5 power 0.00 in every pilot subject, a jump from 0.84–0.97 to 0. This is unexpected for Q30, where the attainable accuracy is still about 0.70, and is to be explained (for example by checking the weakening and the null on synthetic data) before it is reported as a property of the data.

## Resolution of the open item (2026-10-22 19:24 KST; `review-graded-pilot-statistician.txt`)
- No code bug. The mixing steps are a design error found after the pilot: they exchange epochs between the paired opposite-state blocks 2j and 2j + 1, so the observed EC/EO vector, which splits every pair, is the least favourable member of the P5 null set. In null assignments that give both blocks of a pair the same label the exchange costs nothing, and under shuffled folds a decoder that uses block-level structure scores higher than under the true labels. The test stays valid but is strongly conservative (synthetic check under H0: mean p 0.97), so its power was 0.
- The "attainable accuracy about 0.70" at Q30 is right for the observed labels, but the null attains more. Observed and null accuracies were not stored in the pilot output, so the real-data mechanism is inferred from the p pattern (Q30 median p 0.49, rising with q: Q35 0.65, Q40 0.90, Q45 0.97) and synthetic data.
- Q45 and Q48 were the same weakening in 4 of 5 pilot subjects (cap (n - 1) // 2), so the ladder had fewer distinct steps than listed.
- The main arms do not call the weakening; only pos_graded and balanced_graded do, and they are not run under the stamped rule.

## Second-round pilot subjects (addendum 2 §3; QC files only, written 2026-10-23 04:2x KST)
- Downloaded 00:21–00:34 KST (`eligibility/EEG-MANIFEST-PILOT2.sha256`), preprocessed 00:34–00:35 KST with the stamped `preprocess.py` on the laptop (`runs/prep2.out`).
- All 5 have 16 blocks starting with eyes closed; ICA converged in all; no flat channel; no MAD-zero case.
- Epoch rule (cleaned 5/2 s, at least 20 epochs in every block): passed by all 5 (smallest per-block counts 26, 21, 26, 20, 24 for sub-010216, sub-010305, sub-010164, sub-010092, sub-010041). No replacement is needed; the pilot is evaluated on exactly these 5.
- Bad channels: sub-010216 Fp2; sub-010305 Fp2, CP1, CP2; sub-010041 Fp1, AF7; none in the other two.
- Posterior alpha EC > EO in 5 of 5 (reported only; does not exclude).
- sub-010041 has a large VEOG peak-to-peak (2,919 uV; others 385–500 uV); recorded, no action (the rules have no VEOG criterion). sub-010216 (500 Hz recording) and sub-010305 (ground impedance 71 kOhm) show line ratios 0.23 and 0.21, like the others.
- The laptop chain's last log line failed (it wrote to a relative path after changing folder); preprocessing itself finished, as the QC files and `runs/prep2.out` show.
