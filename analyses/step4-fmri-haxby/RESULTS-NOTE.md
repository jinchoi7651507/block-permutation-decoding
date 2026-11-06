# Step 4 results note: the step 2 permutation rules on block-design fMRI (Haxby et al. 2001)

## 0. Status (written 2026-11-03 01:0x KST, while the last two subjects are still running and before any row is opened or the summary is run)
This section is committed before `code/summarize.py --step 4` is run and before any row file is opened. Sections 1 onward are filled in afterwards from the summary output only, and report every pre-specified quantity whatever it shows. Author 2026-11-03 01:0x: go ahead with the results note when the runs finish.

**What governs.** `DESIGN.md` v2 with `code/` (hash list `DESIGN-v2.sha256`, OpenTimestamps proof `DESIGN-v2.sha256.ots`): earliest Bitcoin block 974245 at 2026-11-02 10:42:58 UTC (19:42:58 KST; `prereg/ots_verify_public.py`, ALL OK). The design is post hoc with respect to steps 1–3 (DESIGN §0). `RUNNOTE.md`; `code/chain_45.sh` (orchestration only, not under the timestamp).

**Order of events (from `runs/chain.log`, KST):** chain start 2026-11-02 18:50:51; attestation fetched and hash lists checked (all OK) 20:32:24–20:32:27, so the block (19:42:58) precedes every download; fetch 20:32:27; preparation finished 20:37:12; six runs started 20:37 (one process per subject, `OMP_NUM_THREADS=1`).

**Seen before this note (no p value, accuracy or rate):**
- `runs/fetch.log`: MD5 checks passed for the six tarballs; `MANIFEST.sha256` of the 18 files used (in the data folder outside the repository; copy to be added to `runs/` with the results).
- `runs/prepare.log` (inclusion, decided before any decoding): all six subjects included; 96 blocks per subject and 88 for subj5; run numbers 0..11; subj5 run 8 dropped by `DROP` (its 121 volumes were all labelled `rest` in the distributed `labels.txt`); VT voxels 577, 464, 307, 675, 422, 348 (subj1–6); volumes kept per block m = 9 for every subject.
- Row counts per file and file modification times (progress only), process states, and the tails of `runs/run.subj*.err`: repeated scikit-learn `UserWarning: The groups parameter is ignored by KFold`; no traceback or error in any of the six files.
- Power and sleep state of the laptop: on battery from about 21:06 the machine cycled between sleep and dark wake; `caffeinate -i -s -w 28254` from 22:54 (author); AC power from 00:07. The runs continued (CPU time about 87% of wall time at 22:53); this affects only the run time.

### 0a. Pre-specified quantities (DESIGN §8–§9; copied, nothing added)
1. Unit = subject; per subject the share of its 30 assignments with p < 0.05 (strict; undefined p left out and counted); mean over subjects; subject percentile bootstrap 95% interval (B = 20,000, fresh `default_rng(20261102)` per quantity). "Inflated" = lower bound above 10%. Per rule: subjects with at least 5 rejections of 30.
2. **Primary E4:** E = 1[p_P2 < 0.05] − 1[p_P5 < 0.05], fake labels, S-main, `detrended`; mean per subject, then over subjects; "positive" = lower bound above 0; per-subject E, number of subjects with E > 0 and the exact one-sided sign test; no decision with fewer than 5 subjects with a defined E.
3. Secondary (no decision): every rule under every split and both preprocessings; P3 under S-run (CoSMoMVPA tutorial configuration) and P4 under S-run (PyMVPA tutorial configuration); positive control (face vs house, `detrended`, S-main and S-run).
4. Predictions 1–5 of DESIGN §9, each marked held / not held / not tested; prediction 2 is an implementation check.
5. Wording limits (DESIGN §1): P5 is exact by construction (its rate is an implementation check); category signal shared within blocks is a source of the other rules' excess alongside drift, not separated; no claim about drift as such.

### 0b. Order of work
(1) commit this section; (2) after `chain.log` shows "step 4 runs finished", run `python code/summarize.py --step 4 --rows runs --features <data>/haxby/features --out results` unchanged (from this folder's `code/` with the relative paths of DESIGN §11); (3) fill sections 1 onward from `results/summary.md` / `summary.json` only; (4) statistician persona review and re-review before the note is used anywhere; (5) commit rows, summary and note.

## Sections 1–5 (written 2026-11-03 01:33 KST from `results/summary.md` / `summary.json` only; the stamped `code/summarize.py --step 4` run unchanged, rc 0)
Chain: "step 4 runs finished" 2026-11-03 01:31:44 KST; 1,452 rows (242 per subject; 240 fake + 2 control); every check of the summary passed (key sets, 200 draws, one package version, no test rows). No traceback in any run log. Copies added to `runs/`: the inclusion JSONs and `MANIFEST-haxby.sha256`. Rates are means over the 6 subjects of the per-subject share of 30 tests with p < 0.05, with subject-bootstrap 95% intervals; no undefined p in any cell (P3 never failed: every run holds both classes by construction).

## 1. Primary contrast E4 (fake labels, S-main, detrended)
**E = P2 − P5: 82.2 points (95% 73.9 to 90.0): positive.** All 6 subjects have E > 0 (subj1–6: 90.0, 86.7, 66.7, 96.7, 73.3, 80.0 points; exact one-sided sign test p = 0.016, the smallest possible with 6 subjects); no pair left out. E4 quantifies a known mechanism on fMRI (DESIGN §1): when training and test volumes share blocks, P2 rejects far more often than P5. Slow drift and category signal shared within blocks are both possible sources; the design does not separate them.

## 2. All rules, splits and preprocessings (fake labels)
| split | prep | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|
| main (shuffled KFold 5) | detrended | 91.1 (85.0–96.7) | 90.0 (82.8–96.7) | 87.2 (78.9–95.0) | 91.1 (85.0–96.7) | 7.8 (4.4–10.0) |
| main | raw | 83.9 (77.8–89.4) | 76.1 (68.3–83.3) | 90.6 (84.4–95.6) | 85.0 (78.3–91.1) | 5.0 (2.8–7.8) |
| tool (unshuffled StratifiedKFold 5) | detrended | 24.4 (20.6–28.9) | 20.0 (14.4–25.0) | 20.6 (15.0–26.1) | 15.0 (11.1–20.0) | 3.9 (1.7–6.1) |
| tool | raw | 18.3 (12.2–25.6) | 25.6 (17.8–33.9) | 17.8 (11.1–25.6) | 14.4 (8.3–21.7) | 4.4 (1.1–8.9) |
| run (leave one run out) | detrended | 20.6 (15.6–25.6) | 12.8 (6.7–18.3) | 11.1 (5.6–16.1) | 10.6 (5.6–15.0) | 3.3 (1.1–6.1) |
| run | raw | 21.7 (17.8–25.0) | 15.6 (12.8–17.8) | 17.8 (15.0–20.6) | 15.0 (12.2–17.8) | 5.0 (2.2–7.8) |
| block (whole blocks, fold = block mod 5) | detrended | 21.1 (16.7–26.7) | 18.3 (13.3–25.0) | 16.7 (13.9–21.1) | 22.8 (17.8–29.4) | 3.9 (1.7–6.1) |
| block | raw | 1.1 (0.0–2.2) | 1.1 (0.0–2.2) | 1.7 (0.6–2.8) | 0.6 (0.0–1.7) | 5.6 (3.9–7.8) |
- **Inflated** (lower bound above 10%): P1–P4 in every main and tool cell except P4 tool/raw (lower bound 8.3); under run: P1 in both preprocessings, P2–P4 raw only (detrended P2 12.8, P3 11.1, P4 10.6 have lower bounds 5.6–6.7); under block: P1–P4 detrended. P5 is not inflated in any cell. Subjects with at least 5 of 30 rejections (P1, P2, P3, P4): main 6, 6, 6, 6 in both preprocessings; tool detrended 6, 4, 5, 2 and raw 2, 5, 2, 2; run detrended 5, 2, 2, 2 and raw 5, 4, 4, 3; block detrended 5, 4, 3, 5 and raw 0, 0, 0, 0. P5: 0 in every cell.
- **Tutorial configurations** (secondary): P3 under S-run, the CoSMoMVPA tutorial set-up, 11.1% (5.6–16.1) detrended and 17.8% (15.0–20.6) raw; P4 under S-run, the PyMVPA tutorial set-up, 10.6% (5.6–15.0) detrended and 15.0% (12.2–17.8) raw. Blocks lie within runs, so leave-one-run-out never puts volumes of one block in both training and test. These rates are lower than under S-main but above 5% in every cell (10.6–17.8%), with 2 to 4 subjects at 5 or more of 30; detrended, the lower bounds (5.6) stay below 10%, so these cells are not called inflated.
- **Raw under whole-block folds:** P1–P4 at 0.6–1.7%, below nominal (conservative), while P5 is 5.6%. With detrending, the same split gives P1–P4 16.7–22.8%. Not interpreted further here (not pre-specified).
- **P5** (implementation check, exact by construction): 3.3–7.8% across the 8 cells; the highest, 7.8% (detrended, main; 14 of 180 tests: four subjects at 3 of 30, one at 2 and one at 0), has its upper bound at 10.0%.

## 3. Positive control (face vs house, detrended)
Every rule rejected in 6 of 6 subjects under S-main and under S-run, P5 included (one test per subject and split). The pipeline detects a real category difference. P5's exactness for this control depends on the category order having been randomized across runs, which the distribution does not document (DESIGN §4); the control is a pipeline check.

## 4. Predictions (DESIGN §9)
1. P1, P2, P4 inflated under S-main, detrended and raw: **held** (76–91%). Under S-tool: not predicted (observed 14–26%, all inflated except P4 raw).
2. (Implementation check) P5 not inflated, upper bound at or below 10%, under every split: **held**; the upper bound is exactly 10.0% in the detrended S-main cell and at most 8.9% elsewhere.
3. Under S-run, P2 and P4 lower than under S-main: **held** (detrended 12.8 and 10.6 vs 90.0 and 91.1; raw 15.6 and 15.0 vs 76.1 and 85.0). Whether they stay above 10% was not predicted: raw yes (lower bounds 12.8, 12.2), detrended not by the 10% rule.
4. Raw inflates at least as much as detrended: **not held** (point estimates; DESIGN §9 fixes no criterion). Raw is lower under S-main for P1, P2, P4 (83.9, 76.1, 85.0 vs 91.1, 90.0, 91.1) and higher for P3 (90.6 vs 87.2); under S-tool lower for P1, P3, P4 (18.3, 17.8, 14.4 vs 24.4, 20.6, 15.0) and higher for P2 (25.6 vs 20.0); under S-run higher for P1–P4 (21.7, 15.6, 17.8, 15.0 vs 20.6, 12.8, 11.1, 10.6); under whole-block folds far lower (0.6–1.7% vs 16.7–22.8%).
5. Positive control: P1–P4 reject in most subjects under S-main and S-run: **held** (6 of 6); P5 rejects in most subjects if the category order was randomized: **not tested**, because that condition is not documented (section 3); P5 rejected in 6 of 6.

## 5. Limits and wording (DESIGN §1, §11)
One public dataset (6 subjects, ventral temporal mask, the PyMVPA tutorial data); post hoc with respect to steps 1–3. With 6 subjects the percentile bootstrap intervals are approximate and cannot exceed the largest per-subject share (P5, detrended S-main: upper bound 10.0% equals the largest subject's share). The fake labels split real categories differently in each assignment, so category signal shared within blocks and slow drift are both possible sources of the other rules' excess. The design does not separate them and makes no claim about drift as such. P5's 5% is guaranteed by the random within-run assignment; the measured quantity is the other rules' excess. Not done: the real CoSMoMVPA and PyMVPA tools on these data, other fMRI datasets, searchlight or whole-brain analyses, hemodynamic shift. Convergence warnings are stored per row but are not part of the pre-specified summary and were not tabulated.

**Review:** statistician persona review (`review-note-statistician.txt`): 6 MUST and 4 SHOULD, all checked against `summary.json` and applied (2026-11-03 01:35 KST). Re-review (`review-note-statistician-2.txt`): all ten resolved; one SHOULD (§5 drift sentence) applied; its note on the §0 time "01:0x" needs no action (the project's time rule writes the last `date` output rounded down to ten minutes, here 01:02).
