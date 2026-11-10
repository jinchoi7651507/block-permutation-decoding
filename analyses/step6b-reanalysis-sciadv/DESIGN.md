# Pre-specified reanalysis of PMC13418543: design, version 2 (after persona review, not yet time-stamped)

Status: v2 after the two v1 persona reviews (answered in section 9), written before any data file was downloaded, opened or read. Only the zip's central directory and the authors' code and readme were read (NOTES.md). The design becomes fixed when the main session commits and time-stamps it after a re-review. Changes after that are listed as deviations with dates. Author confirmation: section 0, its item-3 clarification and the Fig. 4D gate range are confirmed (2026-11-07; wording below section 0 item 3). Version 2 with the fixes of section 10, after the v2 re-review.

Study: Klee et al., "Shared striatal neurons exhibit context-specific dynamics for internally and externally driven actions", Science Advances (2026), doi 10.1126/sciadv.aed9386. Data and code: Zenodo record 16333867 (CC BY 4.0), one file `Klee_ScienceAdv_data_code.zip` (3,572,288,274 bytes, md5 18c4429be98ed9595009292caf478ded).

## 0. Decisions on the stage-1 open questions (2026-11-05 00:2x KST; Claude, under the author's go of 00:2x to proceed overnight with the recommended choices; recorded before review, author may reverse at any time before the stamp, afterwards only by a dated addendum)
Questions from `NOTES.md` section 5.
1. Fig. 4D gate: the curve is not digitised. The fatal gate items are the counts, the clusters and the behaviour (section 3.5). For Fig. 4D only the location of the peak (MATLAB bins 73-81) and real above the shuffle mean at the peak in at least 5 of 6 mice are fatal; the port's whole curve is reported descriptively beside the published figure.
2. ITI window: kept at -3.95 to -2.08 s before the reward threshold crossing (before any possible cue). The post-reward window is not added.
3. Drift check promoted to a pre-condition for reading a null block result: if the group mean accuracy of the same-condition first-vs-last decoders in the ITI window (section 4.6, trial shuffle) is 0.60 or more, a group block test with p >= 0.05 in that window is called "uninformative under drift" rather than "not above the block-arrangement null". The 0.60 threshold is fixed now, before data.
4. Alpha 0.05 per window, uncorrected (two separate claims), kept; both results reported.
5. D = 1,000 kept for both windows.
6. Neuron-count gate: 1,261 or 1,271, and equal to the length of the saved `clusterIDs`, kept.
7. Per-cluster decoders (Fig. 4J-L) and the cue-window decoder (Fig. 4E): not added.
Correction to the stage-1 notes in the main session (not to this design): the smallest group p (2/20)^6 = 10^-6 in section 2 is right; a later remark of 2026-11-04 that it should be 1/20^6 forgot the class swap.

Clarification of item 3 (2026-11-07, after the v1 reviews; the decision is unchanged, only its units and its conditions are made exact, and the author may reverse it): "0.60" means 60.0 percent, because `decode.py` reports accuracy in percent. The drift accuracy A_drift is the mean, over all mice that have the decoders and over both same-condition decoders (cued first vs last, self-paced first vs last), of the observed ITI-window accuracy in percent (section 4.6). The rule is applied in the verdict sentence (section 4.5).

Author confirmation (2026-11-07): all seven decisions of section 0 confirmed at 11:5x KST; the item-3 clarification (percent units, definition of A_drift) confirmed at 16:3x KST after Claude checked the units in the code; the Fig. 4D gate range (bins 60-90, review v2 M1) confirmed at 17:2x KST.
Author decision (2026-11-08 00:0x KST, before the stamp): the drift rule of item 3 also applies to the PERI window. Reason: T20 (fixed order C S C S C S, event-locked signal, strong drift sd 0.25) gave group block test power 0 of 20 (95% CI 0-17%), so a PERI non-rejection under strong drift would not show that the signal is absent. A_drift is measured in the ITI window; drift in the PERI window may differ, and the report says so. If PERI is called uninformative under drift, prediction 1 is marked not tested. Code: `summarize.py` `verdict()`; tests T16 and T21.

## 1. Question

The authors decode trial context (cued vs self-paced lever press) from dorsolateral striatum populations with a linear SVM, per mouse and per 66-ms bin, with 20-fold cross-validation over trials. Chance is estimated by shuffling the context labels across trials and retraining. Context is constant within blocks: each mouse did three cued blocks and three self-paced blocks in the fixed order C S C S C S on one day (about 30 rewards per block), and training and test trials come from the same blocks. The paper reports decoding above chance around movement and "slightly above chance during intertrial periods".

Our question: in two pre-specified windows, is context decoding above chance when the test permutes whole blocks, as it is under the trial-label shuffle? The question is what this design allows a test to show. It does not ask whether the study is right.

## 2. What the design can and cannot show

1. Arrangements per mouse. With six blocks, three per condition, there are C(6,3) = 20 arrangements of the block labels. Swapping the two classes leaves a refit two-class decoder's accuracy unchanged, so there are at most 10 distinct scores. The observed arrangement and its swap tie, so the smallest attainable per-mouse p is 2/20 = 0.1. No single mouse can reach p < 0.05 under the block test. Per-mouse block p values are reported as descriptions only.
2. Exchangeability. The order was fixed (always C S C S C S, starting with cued), not randomised. The block test is therefore model-based: it is valid if the six blocks are exchangeable under the null, that is, if no block-level signal follows the position of a block in the session. Slow drift that follows the order breaks this. Our synthetic checks (test_synthetic-v1.out, T9, full run) show which way this can go for this order: under one random-walk drift model with labels that carry no information, the group block test rejected in 0 of 60 simulated groups (95% CI 0-6%) with the alternating order, and in 3 of 60 (5.0%, 95% CI 1.0-13.9%) with random assignment (full run, `test_synthetic.out`). The null contains arrangements such as C C C S S S that line up with drift better than the observed order does. For a linear trend, 8 of the 20 arrangements separate the trend more than C S C S C S does, 6 tie with it (including the observed pair) and 6 separate it less. A session-wide trend shared by all mice (for example satiety or bleaching) breaks exchangeability in the same way in every mouse, and the group test adds these effects up. Both the conservative direction and this direction are possible, so the group block test is read as model-based in both directions.
3. Group level. Across six mice, if each mouse's arrangement is treated as independently uniform over its 20 arrangements, the exact null of the mean accuracy has 20^6 equally likely combinations. The smallest attainable group p is (2/20)^6 = 10^-6. This test is the primary one. It is also model-based, for the same reason as in item 2.
4. Power. The block test is valid for any block-level signal, but it pays for that. When block-level drift is strong, every arrangement decodes well and an event-locked context signal of moderate size can fail to beat the arrangement null (T10, strong drift; T10 used random assignment of block labels, so for the fixed order the power was not simulated there). T20 (`test_synthetic.out`, descriptive only, 20 groups of 6 mice per level, same seeds and amplitude) used the fixed order C S C S C S: the group block test rejected in 20 of 20 groups with weak drift (95% CI 83.2-100%) and in 0 of 20 with strong drift (95% CI 0.0-16.8%), against 20 of 20 and 5 of 20 (25.0%, 95% CI 8.7-49.1%) under random assignment, and the group trial shuffle rejected in 20 of 20 at both levels. A null result under the block test therefore does not show that context is absent. It shows that the decoding in that window is not larger than what the block arrangement alone gives.
5. What a positive result means. A group block-test p < 0.05 says that the observed alternating arrangement decodes better than the rearranged ones. It does not say why. In the intertrial window, the two block types also differ in trial timing, reward consumption, lever movement and required behaviour, and these differences are caused by the condition. In cued trials, the 1.5 to 2.5 s lever hold before the cue falls largely inside this window. In self-paced trials, the 1 to 2 s quiet period falls mostly after it, the previous reward can be as little as 3 s earlier, and unrewarded presses and licking can fall inside it more often than in cued blocks. More than half of presses were unrewarded (Fig. 1J), and these presses are not modelled.

## 3. Data, checks, and the reproduction gate

### 3.1 Data members to be used (stage 2 only)
- `Data Structures/Switching_2p_Struc_Main.mat` (246,543,320 bytes, CRC-32 aa84cac2): per-mouse imaging and events.
- `Data Structures/Switching_Behav_Struc.mat` (274,905,351 bytes, CRC-32 acf47a9f): per-block behaviour, for the gate.
- `Data Structures/clusters_fig2.mat` (2,800,261 bytes, CRC-32 923b18fb): the authors' saved cluster labels, for the gate.

The stamped package also contains `authors-code/` and `authors-code/EXTRACTED.tsv` (the authors' code and readme, byte-identical to the zip; five Bonsai files hold the authors' own paths, see NOTES.md). The authors' code (`authors-code/`, including files that contain the authors' local paths) is used only inside this working repository and is not copied into any public repository; the Zenodo record 16333867 and the member list with CRC-32 values identify it. No other data member is extracted. Members are extracted by HTTP range requests with `code/fetch_members.py --data`, which accepts only these three names. Each member's size and CRC-32 must match `manifest-zenodo-16333867.tsv` (written from the zip's central directory on 2026-11-04). The driver checks this again before reading.

### 3.2 What is read
From the 2p structure: `cells_raw_neurophil_corrected`, `EventID`, `EventTS`, `BlockType` per mouse (`code/loader.py`). The field layout is inferred from the authors' code and readme and must be checked on the real file. The first step in stage 2 is `run_reanalysis.py inspect`, which checks the manifest, prints the field names, types and shapes, and saves them to `out/fields.txt`. `gate` refuses to run unless that file exists, so no decoding precedes the printout.

### 3.3 Port of the authors' pipeline (`code/matlab_port.py`, `code/decode.py`)
dF/F as in `dF_Anya_test.m` (50th percentile in 60-s windows, linear interpolation; z-score over the session), the Figure 4 cell filter, trials cut at Hit events from -5 to +5 s, 2-frame bins, artefact trials (mean over cells above 10 at any time) flagged, cells with NaN dropped, a balanced subsample of the larger class, linear SVM with box constraint 1 and no standardisation, unstratified random 20-fold cross-validation.

### 3.4 Known differences from the MATLAB code (fixed now)
- Artefact trials are removed before subsampling. The MATLAB code keeps them as NaN rows, so they can enter the subsample. The gate reports how many there are per mouse.
- The SVM is scikit-learn's `SVC(kernel="linear", C=1)` (libsvm), not `fitcsvm` (SMO). The objective is the same; the solver tolerances differ.
- Random numbers differ, so subsamples and folds differ from the published ones.
- The Results text says the SVM was trained on 90% of the data and tested on the other 10%, and the Methods say 20-fold cross-validation over a 4-s peri-event window. The deposited code uses 20 folds and 150 bins (10 s, plotted from -1 to +1 s). The Methods mention Gaussian smoothing before the 50th-percentile baseline, and the deposited `dF_Anya_test.m` has none. The Methods report 18 neurons excluded as putative interneurons (3, 2, 5, 4, 3, 1 per mouse); we do not exclude cells beyond the Figure 4 filter, as in the code. The Methods give 1,271 neurons, the Results 1,261 (section 3.5). We follow the deposited code.

### 3.5 Reproduction gate
The tests in section 4 are run only if every fatal item passes. If any fatal item fails, we report the failure and the values, and no test is interpreted. Port bugs may be fixed only by comparison with the authors' code, never by looking at test results (the tests are not run before the gate passes). Each fix is logged with its date and cites the MATLAB line it corrects. Every gate run is saved with its timestamp (`out/gate-runs/`) and all runs are reported, with the fix that followed each failed run. Some fixes change the PERI decoding itself, and the gate shows the port's whole curve, including the ITI bins, before the tests run. This is why the fix rule (authors' code only) and the full list of runs are fixed now.

| Item | Published | Pass if | Fatal |
|---|---|---|---|
| Members | manifest | size and CRC-32 match | yes |
| Mice | 6 | 6 | yes |
| Block order | C S C S C S | equal per mouse | no (report; a mouse without six blocks in this order is listed, its S1 and drift checks are skipped, its block test uses its own arrangements, and the stated minimum p values are recomputed for it) |
| Neurons (Figure 2 pipeline) | 1,261 (Results; 1,271 in Methods) | 1,261 or 1,271, and equal to the length of `clusterIDs` in `clusters_fig2.mat` | yes |
| Clusters | 118 / 868 / 275 | at least 99% agreement with the saved `clusterIDs` (best label matching); sizes equal when n = 1,261 | yes |
| Reaction time from trial start (Fig. 1F) | cued 0.30 s, self-paced 6.0 s, Wilcoxon p = 0.03 | means equal at the printed precision; p fatal only if it falls on the other side of 0.05 from the published p | yes |
| Press rate (Fig. 1G) | 16.9 and 16.0 per min, p = 0.69 | same rule | yes |
| Reward rate (Fig. 1H) | 7.49 and 7.0 per min, p = 0.84 | same rule | yes |
| Rewarded fraction (Fig. 1J) | 0.49 and 0.45, p = 0.68 | same rule | yes |
| Fig. 4D curve | peak "at and just after movement onset" | the peak of the six-mouse mean real curve within the plotted range of Fig. 4D (MATLAB bins 60-90; the authors' Figure4.m sets xl=[60,90]) lies in bins 73-81, and at that bin real exceeds that mouse's 50-shuffle mean in at least 5 of 6 mice | yes |

Behaviour p values. With six mice, the exact two-sided signed-rank p values are multiples of 1/32 (0.031, 0.063, ...), so 0.03, 0.69 (22/32 = 0.6875) and 0.84 (27/32) are attainable and the published 0.68 for Fig. 1J is not; we do not know how the authors obtained it. The test is computed on mice with no NaN (MATLAB `signrank` drops NaN pairs), the number of pairs, zero differences and tied absolute differences are recorded, and the absolute difference from the published p is reported for every row. Python rounding of 0.6875 gives 0.68 and would otherwise fail Fig. 1G.

Fig. 4D gives no numbers and is not digitised (section 0, item 1). The port runs Panel D with the authors' settings for the gate: one balanced subsample, 20 folds, 50 shuffles, all 150 bins computed. The gate peak is searched only within the plotted range of Panel D, MATLAB bins 60-90 (0-based 59 to 89); a higher value outside that range does not matter for the gate. The port's mean real and shuffle curves are reported beside the published figure, descriptively. The per-mouse Figure 4 cell counts, trial counts and artefact counts are reported with the gate.

## 4. Tests

All tests use the same statistic. For a window W, accuracy is the 20-fold cross-validated accuracy per bin, averaged over the bins of W and over R = 4 repeats of (balanced subsample, folds). The subsample and folds are redone for every label vector, real or permuted, so every step that depends on the labels is refit. The observed statistic is computed once per mouse and window, and the same value enters tests (a), (b) and (c).

### 4.1 Primary windows (times relative to the reward threshold crossing, the authors' alignment event)
- ITI: MATLAB bins 16-44, centres -3.95 to -2.08 s. This window ends before the earliest possible cue (the response window is 2 s), so it contains no cue in cued trials. This is where a block-level signal would show. Caveat fixed now: in self-paced blocks the previous reward can be as little as 3 s earlier, so reward consumption can fall inside this window more often than in cued blocks (secondary S2 addresses this). This window lies outside a 4-s peri-event window centred on the event and outside the plotted range of Fig. 4D (-1 to +1 s). It is our reading of "intertrial periods", not necessarily the window behind that sentence, and test (a) is our formal version of a comparison the authors did not test formally.
- PERI: MATLAB bins 73-81, centres -0.15 to +0.38 s. The published accuracy peaks "at and just after movement onset"; this signal is event-locked.

### 4.2 (a) The authors' rule, made formal
Per mouse and window: permute the context labels across all trials (class counts kept), then redo subsample, folds and fits; D = 1,000 draws; p = (1 + #{null >= observed}) / (D + 1). Group: the mean accuracy over mice against 100,000 random combinations of the per-mouse null draws. The paper compares the mean real curve with the mean shuffle curve and gives no formal test; this is our formal version of that comparison. Group p = (1 + #{null means >= T}) / 100,001, smallest 1/100,001 (about 1.0e-5); per-mouse smallest 1/1,001.

### 4.3 (b) Block permutation test, per mouse
Enumerate all 20 arrangements of the six block labels with three per class. For each arrangement, give every trial the label of its block (training and test trials together) and refit the whole pipeline. Each class-swap pair is scored once with the same seed, so the null has 20 entries in 10 tied pairs. p = (1 + #{other arrangements >= observed}) / 20, smallest value 0.1. The enumeration agrees with `blockperm.block_permutation_test_score` (exact mode) on a case both can run (test T8).

### 4.4 (c) Group block test (primary)
T = mean over the six mice of the observed accuracy. Null: the exact distribution of the mean when each mouse's arrangement is independently uniform over its 20 arrangements (computed by convolution on an integer grid of 1e-6 percent, so that sums are exact and the observed combination is always counted, and checked against brute-force enumeration and against unrounded float nulls in T7; the code asserts that p is not below its attainable minimum). p = P(T_null >= T). Model-based (section 2). Secondary group summary: the number of mice whose observed arrangement is at the top of its null, against a binomial with success probability 0.1.

### 4.5 Decision rule (one per window, written now)
Primary contrast in each window: the group block test (c), one-sided, alpha = 0.05. The two windows answer separate questions and are not corrected for multiplicity; both results are reported. The verdict sentence is filled in from the two group p values (a) and (c) and, in both windows, the drift accuracy A_drift (sections 0 item 3 and 4.6; extended to PERI on 2026-11-08, see the line below section 0):
- "In the [ITI / PERI] window, under the trial-label shuffle, group-level context decoding is [above / not above] chance (p = ...); under the block test, it is [above / not above] the block-arrangement null (p = ...)."
- If (a) is below 0.05 and (c) is not, the report says: "under the block test, the [window] decoding is not distinguishable from what the block arrangement alone gives". It does not say the effect is absent (section 2, item 4).
- Both windows (ITI, and PERI since 2026-11-08): if A_drift is 60.0 percent or more and (c) has p >= 0.05, the block clause reads: "under the block test, the result is uninformative under drift (same-condition first-vs-last accuracy ... %; p = ...)". This takes precedence over the previous bullet. If no drift decoder is available, the clause is not used and the report says so.
- Every verdict sentence ends with: "The block test rests on an exchangeability model because the block order was fixed." (`summarize.py` writes the sentences without editing; T13 checks them.)

### 4.6 Controls
- Positive control, movement decoder (labels vary within trials): the authors' Panel F (press bin vs the bin at -2.02 s of the same trials) over the PERI bins, with a within-trial label-swap null (D = 100, R = 2). Expected: large accuracy and p at its minimum in every mouse. The control fails in a mouse if its p > 0.05 (smallest p 1/101 = 0.0099). A failing mouse stays in every group test and is marked in the tables.
- Drift check, same condition: decode the first vs the last cued block, and the first vs the last self-paced block, in the ITI window (trial shuffle, D = 200). These labels carry no condition difference. Accuracy above chance here measures block-specific signal (drift) that the trial-label shuffle would count as decodable. A_drift is the mean of the observed accuracies of the two decoders (cued first vs last, self-paced first vs last) over the mice that have them, in percent, computed in `run_reanalysis.py` and used only as stated in section 4.5.

### 4.7 Secondary analyses (reported, not used for the verdict)
- S1, held-out blocks: cross-validation that holds out one cued/self-paced pair of blocks at a time (3 folds), so test trials come from blocks the decoder never saw, with the exact block null per mouse and the exact group null. The k-th cued block is paired with the k-th self-paced block; S1 is skipped for a mouse without the layout C S C S C S.
- S2, ITI-clean trials: the ITI window restricted to trials whose previous reward was at least 5 s earlier, block test and trial shuffle (D = 200); run if each mouse keeps at least 20 trials per condition, and the number of mice is reported. The previous reward is the previous Hit in the full event list, before edge and artefact trials are removed. S2 mainly removes self-paced trials, because the minimum gap in cued blocks is already above 5 s.
- The published Fig. 4D curve from the port (gate output), shown with the trial-shuffle band, for orientation only.

## 5. Seeds, draws, compute

- Master seed 20261104. Every random step draws from a generator keyed by (master seed, test, mouse, window, arrangement or draw, repeat), so any number can be recomputed alone (`decode.rng_for`).
- R = 4 repeats; D = 1,000 trial-shuffle draws (primary), 200 (controls, S2), 100 (movement control); 20 enumerated arrangements per mouse; 100,000 combinations for the group trial-shuffle null.
- Smallest attainable p: per-mouse trial shuffle 1/1,001; group trial shuffle 1/100,001; drift and S2 1/201; movement control 1/101; per-mouse block test 2/20 = 0.1; group block test (2/20)^6 = 1e-6.
- Pins: `code-package/blockperm/blockperm.py` has sha256 4a5f8009e1d49d5bf1e30cb47a08f25f745e712bcc99b690456dd1c2081f4a08, and the packages are numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2. `decode.check_environment` stops the driver on a mismatch (T15 checks it). The code finds `blockperm.py` relative to its own location in this repository; a public copy with another layout must place the same file there, and the hash check applies.
- Compute: one linear SVM fit on 171 trials by 210 cells took about 2 ms here (T12 in test_synthetic.out). The primary tests need about 3.1 million fits per mouse, about 1.9 CPU-hours, so about 11 CPU-hours for six mice. The controls and S1/S2 need about 1.46 million fits per mouse (drift 932,640, S2 489,520, movement 36,360, S1 4,560), about 0.9 CPU-hours per mouse and 5.3 for six. The gate (Panel D with 50 shuffles, 918,000 fits) takes about 0.6 CPU-hours. In total about 17 CPU-hours (primary 11, controls and secondary 5.3, gate 0.6), about 3 to 4 hours on 6 cores if fully parallel. T12 prints the primary part and the total.

## 6. What is reported, whatever it shows

Everything in sections 3-4: the gate table with every value; per mouse and window the observed accuracy, the trial-shuffle p, the block p with its minimum, and the rank of the observed arrangement among the 10 distinct scores; both group p values per window; the controls; S1 and S2; all deviations with dates. `code/summarize.py` writes the tables and the verdict sentences from the JSON output, without editing.

Wording limits: we do not write "wrong", "error" or "flawed" about the study. We write "under the block test the verdict is ...", and we state that the block test here rests on an exchangeability model because the order was fixed. The ITI window is our reading of "intertrial periods" and lies outside a 4-s peri-event window and the plotted range of Fig. 4D; test (a) is our formal version of a comparison the authors did not test formally (section 4.1). We state that the authors' cluster, D1/D2, trajectory and movement-decoder results are outside this reanalysis (the movement decoder is used only as a control). The cue-period decoder of Fig. 4E (the cue-period window of -495 to -165 ms before the press, in the figure legend) and the abstract's statement that population dynamics diverged before movement are not tested here (section 0, item 7).

## 7. Predictions (written now; may be wrong)

1. PERI: the trial shuffle gives p at its minimum in most mice; the observed arrangement ranks first in most mice under the block test (p = 0.1), and the group block test gives p < 0.05. Verdict unchanged. Moderate confidence: T10 shows that strong drift could reduce the power of the block test even here.
2. ITI: the trial shuffle gives p < 0.05 at the group level (as published). Under the group block test we expect p >= 0.05, with low confidence. Two things pull against each other: the 60-s percentile baseline in the authors' dF/F removes much slow drift, which would leave less block-level signal; the reward-timing difference in self-paced blocks (section 4.1) is a real condition effect that the block test would credit.
3. Drift check: first vs last block of the same condition decodes above chance under the trial shuffle in at least half of the mice.
4. Movement decoder: passes in all six mice.

Definitions for marking the predictions (added in the v2 re-review, before data): "Most" means at least 4 of 6 mice; "at least half" means at least 3 of 6 mice for each of the two drift decoders; "at its minimum" means p = 1/1,001; "verdict unchanged" means group (a) p < 0.05 and group (c) p < 0.05. Each prediction is marked held, not held or not tested. If the PERI verdict is 'uninformative under drift', prediction 1 is marked not tested.

## 8. Open points for the reviewer
Listed in NOTES.md, section 5. Items 1 to 7 there were decided in section 0 and confirmed by the author on 2026-11-07 (see the confirmation line below section 0 item 3).

## 9. Response to the v1 reviews (2026-11-07; `review-v1-stat.txt`, `review-v1-domain.txt`)
Both reviews said "Not ready". Code changes after the reviews are in commit aa98f70 (written before this text) and in the two changes listed under "Code changes in v2" below. Review items are cited as stat Mn/Sn and domain Mn/Sn.

### 9.1 MUST items
| Item | What changed | Where |
|---|---|---|
| stat M1, domain M1: Fig. 4D gate contradicted section 0 item 1 | Table row and paragraph replaced as the reviews wrote them; the 5-of-6 rule is coded; `--fig-ref`, the tolerances and the digitising step are removed | 3.5 table and paragraph; `run_reanalysis.py gate()` and `main()` |
| stat M2, domain M2: drift rule missing from the decision rule, units, ambiguity | Units and the exact definition of A_drift added as a dated clarification below section 0 item 3 (the decision itself is unchanged, see "For the author"); the rule and the exchangeability sentence added to 4.5; A_drift defined in 4.6; `verdict(window, p_trial, p_block, drift_acc)` writes the clauses; T13 checks them | 0 (clarification), 4.5, 4.6; `summarize.py`, `run_reanalysis.py` (`group.drift_accuracy`); T13 |
| stat M3: group block p could fall below its minimum through rounding | Integer grid of 1e-6 percent, exact sums, an assertion that p is not below its attainable minimum; T7 case with unrounded float nulls, every mouse at the top, expects p = 1e-6 | 4.4; `decode.py` `_q`, `exact_group_null`, `group_block_p`; T7 |
| stat M4, domain M3: behaviour gate failed a correct port (0.6875 rounds to 0.68; 0.68 not attainable for n = 6; NaN) | The two reviews differ on the rule (stat: within 0.008; domain: same side of 0.05). We use the domain rule, fatal only if p falls on the other side of 0.05, and report the absolute difference to the published p in every row, which also shows the stat rule (0.0075 for Fig. 1J, 0.0025 for Fig. 1G). NaN pairs dropped; pairs, zero differences and tied absolute differences recorded | 3.5 rows and paragraph; `run_reanalysis.py signrank_pairs`; T14 |
| stat M5: ITI window is outside the authors' analysis window | Sentence added to 4.1 and to the wording limits | 4.1, 6 |
| domain M2 (duplicate of stat M2) | See stat M2 | |

### 9.2 SHOULD items
| Item | What changed | Where |
|---|---|---|
| stat S1: compute | Controls and S1/S2 counted by fit; total about 18 CPU-hours, 3 to 4 hours on 6 cores | 5 |
| stat S2: overstated T9 sentence, linear trend counts | Replaced by "0 of 60 (95% CI 0-6%) under one random-walk drift model", the 2 of 60 under random assignment, and the 8 / 6 / 6 arrangement counts for a linear trend (recomputed by enumeration), plus the shared-trend sentence | 2 item 2 |
| stat S3, domain S9: other differences between the block types | Cued hold, self-paced quiet period, reward consumption, lever movement, unrewarded presses (named as differences; the count promise was dropped in v2, section 10) | 2 item 5 |
| stat S4, domain S5: "fails" undefined | p > 0.05, smallest p 1/101; the mouse stays in every group test and is marked; coded as `movement_failed` and printed | 4.6; `run_reanalysis.py`, `summarize.py` |
| stat S5, domain S6: layout assumption | Mice with another layout are listed; S1 and drift skipped; block test uses its own arrangements; S1 pairs the k-th cued with the k-th self-paced block | 3.5 table, 4.7; `run_reanalysis.py` (`standard`) |
| stat S6, domain S4: previous reward from cleaned trials | Previous Hit from the full event list | 4.7; `run_reanalysis.py` |
| stat S7, domain S7: smallest p values | Listed | 4.2, 5 |
| stat S8, domain S1: blockperm path and pin | sha256 and package versions pinned and checked at run time (T15). The path resolves to `code-package/blockperm` in this repository; a public copy with another layout must place the same file there. No code change | 5; `decode.py check_environment` |
| stat S9, domain S3: port fixes after a failed gate | Every gate run saved and reported; each fix cites the MATLAB line; fix rule stated | 3.5; `out/gate-runs/` |
| stat S10: author confirms section 0; move the correction line; Fig. 4E not tested | Pending line in the status paragraph; the correction line stays in section 0 (unchanged) and is copied to NOTES.md; Fig. 4E and the abstract's pre-movement statement named as not tested | header, 6, NOTES.md |
| domain S2: `inspect` stage | `inspect` writes `out/fields.txt`; `gate` refuses without it | 3.2; `run_reanalysis.py` |
| domain S8: text-versus-code differences | 90/10 split vs 20 folds, 4-s window vs 150 bins, Gaussian smoothing, 18 excluded interneurons, 1,261 vs 1,271 | 3.4 |
| domain S10: author confirmation | See stat S10 | header |
| domain S11: T10 used random assignment | Stated in 2 item 4; no new simulation (see "For the author") | 2 item 4 |
| domain S12: authors' code in the stamped package | Stated in 3.1 | 3.1 |

### 9.3 Code changes in v2 (this stage), besides commit aa98f70
1. `run_reanalysis.py`: new function `signrank_pairs(d)` (drops NaN pairs, returns p, pairs kept, zero differences, tied absolute differences); `gate()` uses it and stores `n_zero_differences` and `n_tied_abs_differences` per behaviour row.
2. `test_synthetic.py`: new `t_gate_helpers` (T14 signed-rank grid, NaN drop, tie count; T15 pinned environment).
No other code changed.

### 9.4 For the author (not changed here)
1. Section 0 item 3: the reviews asked to replace "0.60" with "60.0 percent" inside section 0. Section 0 is kept as written, and the clarification is a dated line below it. Confirmed by the author on 2026-11-07 (16:3x KST).
2. Section 0 itself: all 7 decisions confirmed by the author on 2026-11-07 (11:5x KST).
3. Whether a simulation of the group block test with an event-locked signal under the fixed order C S C S C S is wanted (domain S11 offered it as an alternative to stating the limit). Done (T20), descriptive only: no decision rule, gate or prediction depends on it (2026-11-08).
4. Whether the five Bonsai files with the authors' paths go in the public copy (domain S12). Done (2026-11-08): they do not; see section 3.1.

## 10. Response to the v2 re-review (2026-11-07; `review-v2.txt`, `review-v2-claude.md`, `JUDGEMENT-v2.md`)
All items were approved by the author on 2026-11-07. Nothing in section 0's seven decisions changed.

| Item | What changed | Where |
|---|---|---|
| M1 gate peak searched over all 150 bins | Peak searched only within MATLAB bins 60-90 (0-based 59 to 89), the plotted range of Fig. 4D; pass if it lies in bins 73-81; T19 checks that a higher value outside the range does not matter | 3.5; `run_reanalysis.py` (`PLOT_LO`, `PLOT_HI`); T19 |
| M2 predictions undefined | "Most", "at least half", "at its minimum", "verdict unchanged" defined; each prediction marked held, not held or not tested | 7 |
| M3 author confirmation not recorded | Confirmation line below the item-3 clarification; status line, sections 8 and 9.4, NOTES.md section 7 updated | header, 0, 8, 9.4; NOTES.md 7 |
| S1 NaN or missing drift accuracy | `verdict()` treats None or NaN as unavailable and appends "(drift check not available)" to the ITI block clause; T16 | `summarize.py`; T16 |
| S2 unrewarded-press count promised, not coded | Promise dropped; unrewarded presses remain a named difference between block types, not counted; no code added | 2 item 5, 9.2 |
| S3 seed keys held np.int64 text | Partition keys cast to Python int; T17 checks that the key text has no "np.int64". Seeds of the block test therefore differ from those of the v1 quick run | `decode.py canonical_partitions`; T17 |
| S4 `round()` ties in the behaviour means | Means compared with abs(mean - published) <= 0.5 * 10**-nd + 1e-9 (`means_match`); T18 on rounding boundaries | 3.5; `run_reanalysis.py`; T18 |
| S5 compute wording; full suite on the fixed code | "About 17 CPU-hours (primary 11, controls and secondary 5.3, gate 0.6)"; T12 prints the total; the full suite (G = 60) was run on the fixed code in the pinned environment | 5; T12; `test_synthetic.out` |
| Claude SHOULD 2 (power under the fixed order), SHOULD 3 (authors' code stays internal) | Done: T20 (descriptive, 2026-11-08); section 3.1 | 2 item 4, 3.1, 9.4 |
| PERI drift rule (author decision 2026-11-08 after T20) | The drift rule of section 0 item 3 applies to both windows; PERI clause notes that the drift accuracy is measured in the ITI window; prediction 1 not tested if PERI is uninformative under drift | line below section 0, 4.5, 7; `summarize.py` verdict(); T16, T21 |

### 10.1 Code changes in this stage
`run_reanalysis.py` (gate peak range, `means_match`), `decode.py` (int partition keys), `summarize.py` (`verdict`), `test_synthetic.py` (T16 to T19, T12 total). No other code changed. The quick v2 output is kept as `test_synthetic-v2-quick.out`.


Text corrections before the stamp (Claude, 2026-11-07 23:5x KST; re-check note in `review-v2.txt`): section 2 item 2 now cites the full run (3 of 60 under random assignment; 0 of 60 with the alternating order) and says "rejected" (the earlier "did not reject in 0 of 60" was a wording slip); the controls-and-secondary compute is 5.3 CPU-hours as printed by T12. The S2 fit count (489,520 here, 487,200 by the reviewer's count) is left as is; it changes no rule.
