# Results note: pre-specified reanalysis of PMC13418543 (Klee et al., Science Advances 2026)

## 0. Written before the test output was opened (2026-11-08 17:3x KST; `tests` still running, `out/tests.json` not yet written)

**Governing files.** `DESIGN.md` v2 with hash list `DESIGN-v2.sha256` (commit 7b6092e; earliest Bitcoin attestation block 974945, 2026-11-07 15:17:29 UTC). Run record `RUNNOTE.md`. The verdict sentences, tables and prediction marks come only from the stamped `code/summarize.py` run on `out/tests.json`, without editing.

**Seen before the tests.**
- Field structure (`out/fields.txt`).
- Gate run 1 (FAIL on clusters, 0.553) and gate run 2 (PASS): the gate items as listed in RUNNOTE (6 mice, block order C S C S C S in every mouse, 1,261 neurons, clusters 118/275/868 with agreement 1.0, behaviour Fig. 1F-J, Fig. 4D peak at MATLAB bin 77 with 6 of 6 mice above the shuffle mean).
- `out/gate.json` also holds the port's mean real and shuffle curves over all 150 bins (`fig4d_port`), which include the ITI and PERI bins. Claude read the gate items and the pass status; the curve values in the ITI window (bins 16-44) and the PERI window (bins 73-81) were not printed or read before this section was committed.
- The port fixes after gate run 1 (Figure2.m l.197 label lag, used only in the Figure 2 path; constant cells) and the author's decision on Figure4.m l.92 (event-type labels, as stamped in DESIGN 3.3).
- No accuracy or p value of any test in section 4 of the design.

**Quantities fixed in the design (read in this order).**
1. Per window (ITI, PERI): group trial-shuffle p (a) and group block-test p (c), the drift accuracy A_drift, and the verdict sentence that `summarize.py` writes from them (DESIGN 4.5; drift rule in both windows since 2026-11-08).
2. Per mouse and window: observed accuracy, trial-shuffle p, block p with its minimum (0.1), rank of the observed arrangement; reported, not used for the verdict.
3. Controls: movement decoder (per-mouse pass if p <= 0.05), drift decoders (first vs last block of the same condition, ITI).
4. Secondary: S1 held-out blocks, S2 ITI-clean trials; reported, not used for the verdict.
5. Predictions 1-4 marked held / not held / not tested with the definitions of DESIGN section 7.

**Order of work.** Commit this section → wait for `tests` to finish (exit line in `out/tests.log`) → run `code/summarize.py --out out` unchanged → copy numbers and sentences only from `out/SUMMARY.md` into section 1 → mark predictions → statistics persona review (Opus) with the summary code → judgement file. Wording limits of DESIGN section 6 apply ("under the block test the verdict is ...", never "wrong"; the exchangeability sentence stays with every block-test result). Results stay out of every public text before the NCS submission.

## 1. Results (2026-11-09 00:0x KST; every number below is copied from `out/SUMMARY.md`, written by the stamped `code/summarize.py` from `out/tests.json`)

### 1.1 Gate
Pass on every item (gate run 2, RUNNOTE): 6 mice, block order C S C S C S in every mouse, 1,261 neurons, clusters 118/275/868 with agreement 1.0, behaviour Fig. 1F-J as published, Fig. 4D peak at MATLAB bin 77 with 6 of 6 mice above the shuffle mean.

### 1.2 Verdict sentences (generated, not edited)
- "ITI window: under the trial-label shuffle, group-level context decoding is above chance (p = 1e-05); under the block test, it is above the block-arrangement null (p = 1.5e-05). The block test rests on an exchangeability model because the block order was fixed."
- "PERI window: under the trial-label shuffle, group-level context decoding is above chance (p = 1e-05); under the block test, it is above the block-arrangement null (p = 6e-06). The block test rests on an exchangeability model because the block order was fixed."
- Drift accuracy (mean over mice and both same-condition decoders): 51.4 %, below the 60.0 % threshold, so the "uninformative under drift" clause does not apply in either window. (This bullet is not generated; Claude wrote it from `out/SUMMARY.md`. The clause needs both a block p >= 0.05 and A_drift >= 60 %; the block p was below 0.05 in both windows, so it would not apply at any A_drift. A_drift is measured in the ITI window only.)

### 1.3 Per window
| Window | group mean accuracy (%) | trial-shuffle p (smallest possible 1e-05 = 1/100,001) | block test p (smallest possible 1e-06) | mice at the top arrangement |
|---|---|---|---|---|
| ITI | 53.42 | 1e-05 | 1.5e-05 | 4 of 6 (binomial p = 0.00127) |
| PERI | 65.28 | 1e-05 | 6e-06 | 4 of 6 (binomial p = 0.00127) |
Per mouse (accuracy, trial-shuffle p, block p and rank) are in `out/SUMMARY.md`. ITI: mice 5 and 6 had accuracies 50.92 and 49.84 with trial-shuffle p 0.193 and 0.468; every mouse ranked first or second of 10 distinct scores.

### 1.4 Controls
- Movement decoder: 69.6-89.8 % accuracy, p = 0.0099 (its minimum) in all 6 mice.
- Drift decoders (first vs last block of the same condition, ITI): cued 48.1-51.2 %, no mouse with p < 0.05; self-paced 47.8-59.0 %, p < 0.05 in mice 1, 3 and 4 (0.00498, 0.00498, 0.0149).

### 1.5 Secondary (not used for the verdict)
- S1 held-out blocks: ITI accuracy 52.59, block test p = 4e-06; PERI accuracy 60.68, block test p = 1e-06.
- S2 ITI-clean trials (previous reward at least 5 s earlier; 6 mice): accuracy 51.94, trial-shuffle p = 0.00013, block p = 0.0153.

### 1.6 Predictions (DESIGN section 7 definitions, applied by Claude to the numbers above)
| # | Prediction | Mark | Basis |
|---|---|---|---|
| 1 | PERI: trial-shuffle p at its minimum in most mice; observed arrangement first in most mice; group block p < 0.05; verdict unchanged | held | p = 0.000999 (= 1/1,001) in 6 of 6; rank 1 in 4 of 6; group block p = 6e-06; group (a) and (c) both < 0.05 |
| 2 | ITI: group trial-shuffle p < 0.05; group block test p >= 0.05 | not held | the trial-shuffle part held (p = 1e-05); the block part did not (p = 1.5e-05, below 0.05) |
| 3 | Drift check above chance in at least 3 of 6 mice for each of the two decoders | not held | "above chance" = per-mouse trial-shuffle p < 0.05; self-paced 3 of 6 (mice 1, 3, 4); cued 0 of 6 (smallest p 0.199) |
| 4 | Movement decoder passes in all six mice | held | p = 0.0099 in 6 of 6 |

### 1.7 Reading (revised 2026-11-09 00:4x KST after the statistics review, `review-results.txt`, `JUDGEMENT-results.md`; author: "as recommended" (translated from Korean); the first version is kept below as [superseded])
Under the block test, the context-decoding verdict does not change in either window. Group-level context decoding is above the block-arrangement null around movement (PERI, p = 6e-06) and in the intertrial window (ITI, p = 1.5e-05), as it is under the trial-label shuffle. The block test rests on an exchangeability model because the block order was fixed (C S C S C S). The ITI window is our reading of "intertrial periods": it lies outside a 4-s peri-event window and outside the plotted range of Fig. 4D, and test (a) is our formal version of a comparison the authors did not test formally.

What the positive result does not show (DESIGN section 2 item 5). A group block p below 0.05 says that the observed alternating arrangement decodes better than the rearranged ones; it does not say why. In the ITI window the two block types also differ in trial timing, reward consumption, lever movement and required behaviour, all caused by the condition. With trials whose previous reward was at least 5 s earlier (S2), the group block p was 0.0153 (accuracy 51.94 %). The drift accuracy (51.4 %) stayed below its 60 % threshold, so the drift clause did not apply, but the drift check does not show that blocks are exchangeable: the self-paced first-vs-last decoder was above chance (per-mouse trial-shuffle p < 0.05) in 3 of 6 mice (mice 1, 3 and 4, at 59.0, 57.7 and 56.4 %), above those mice's ITI context accuracy (55.49, 55.11 and 55.75 %); the cued decoder was above chance in none (smallest p 0.199). The comparison is rough (different labels, trials and class sizes). With blocks held out (S1), the group block p was 4e-06 (ITI) and 1e-06 (PERI). Drift was measured in the ITI window only; drift in the PERI window may differ.

Scope. The authors' cluster, D1/D2, trajectory and movement-decoder results are outside this reanalysis (the movement decoder is used only as a control). The cue-period decoder of Fig. 4E and the abstract's statement that population dynamics diverged before movement are not tested; per-cluster decoders were not run. Known difference from the authors' code: in mice 1-3 the authors' Figure 4 decoding includes the first 2, 1 and 1 Go trials in the self-paced class (`TStype(Clocal)` lag, Figure4.m l.92); the port uses event-type labels, constant within blocks (DESIGN 3.3; author's decision, RUNNOTE 2026-11-08 16:4x). Other differences from the MATLAB code are listed in DESIGN 3.4.

### 1.8 Deviations and run facts (added 2026-11-09 00:4x KST after the statistics review)
1. Gate run 1 (2026-11-08 03:08) failed on clusters (agreement 0.553, sizes 206/429/626). Two port fixes from the authors' code followed (Figure2.m l.197 label lag, in the Figure 2 path only; Figure2.m l.169 with `dF_Anya_test.m`, constant cells), and gate run 2 (11:33) passed (RUNNOTE). Runs 1 and 2 have the same Figure 4 cells, trials and artefact counts and identical Fig. 4D port curves (checked 2026-11-09 from `out/gate-runs/`), so the fixes left the gate's Figure 4 outputs unchanged.
2. Gate values: behaviour |p - published| 0.00125, 0.0025, 0.00375 and 0.0075 (Fig. 1F, G, H, J); Figure 4 cells per mouse 175, 115, 270, 312, 231, 78; trials (self-paced/cued) 87/85, 75/86, 88/85, 87/87, 89/89, 93/88; artefact trials 0 in every mouse; the port's Fig. 4D curves are in `out/gate.json` (`fig4d_port`).
3. Download route: the whole Zenodo zip by `curl` with the record's md5, then local extraction of the three members with CRC-32 checked, instead of range requests (RUNNOTE 2026-11-08 02:1x-03:06). What is analysed is unchanged.
4. Environment addition after the stamp (2026-11-08 03:07): mat-io 1.0.2 with h5py 3.16.0 and pandas 3.1.1 (not pinned). The pinned packages (numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2) and the `blockperm.py` hash were checked by the driver (`out/gate.json`).
5. Files that now differ from `DESIGN-v2.sha256`: `code/matlab_port.py` and `code/run_reanalysis.py` (the gate fixes of item 1) and `NOTES.md` (stamp record appended).
6. Run: the first `tests` call with `python -I` stopped at import (nothing computed); the rerun ran 2026-11-08 16:44:59 to 2026-11-09 00:04:18 KST with 6 workers, exit 0 (`out/tests.log`); `code/summarize.py` ran unchanged.
7. Provenance: outputs committed in 26b1510 (`out/tests.json`, `out/SUMMARY.md`, logs). `code/__pycache__/` was committed after the stamp; it is kept out of public copies.

### 1.7 [superseded 2026-11-09 00:4x] first version
Under the block test, the verdict for this study does not change in either window: context decoding is above the block-arrangement null both around movement and in the intertrial window (our reading of "intertrial periods", outside the published 4-s window). The block test rests on an exchangeability model because the order was fixed (C S C S C S); the drift check stayed below its threshold, and the result held with blocks held out (S1) and with ITI trials far from the previous reward (S2, p = 0.0153). Known difference from the authors' code: in mice 1-3 the authors' Figure 4 decoding labels the first 2, 1 and 1 Go trials as self-paced; the port uses event-type labels (RUNNOTE 2026-11-08 16:4x).

Statistics review done (`review-results.txt`, judgement `JUDGEMENT-results.md`); MUST and SHOULD items applied 2026-11-09 00:4x (author: "as recommended", translated from Korean); changed lines sent to an Opus re-check.

**Added 2026-11-09 17:2x KST (author):** in the manuscript, the exchangeability assumption and the unmodeled color-selection penalty are stated in the limitations paragraph, Methods and the Extended Data Fig. 3 legend, not next to each block-test sentence of the Results; this departs from the wording rule of the design (DESIGN section 8 for Cell, section 6 for Sci Adv), for readability (blind round 35).
