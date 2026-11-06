# Step 5 results note: the step 2 permutation rules on non-neural wearable-sensor recordings (PAMAP2)

## 0. Status (written 2026-11-03 01:3x KST, while the runs are in progress and before any row is opened or the summary is run)
This section is committed before `../step4-fmri-haxby/code/summarize.py --step 5` is run and before any row file is opened. Sections 1 onward are filled in afterwards from the summary output only, and report every pre-specified quantity whatever it shows. Author 2026-11-03 01:0x: go ahead with the results notes when the runs finish.

**What governs.** `DESIGN.md` v2 with `code/` and the shared step 4 engine, summary and synthetic checks (hash list `DESIGN-v2.sha256`, proof `DESIGN-v2.sha256.ots`): earliest Bitcoin block 974245 at 2026-11-02 10:42:58 UTC (19:42:58 KST; `prereg/ots_verify_public.py`, ALL OK). Post hoc with respect to steps 1–3 (DESIGN §0). `../step4-fmri-haxby/RUNNOTE.md` (shared run note); `../step4-fmri-haxby/code/chain_45.sh` (orchestration only).

**Order of events (`../step4-fmri-haxby/runs/chain.log`, KST):** attestation checked 2026-11-02 20:32:27; step 5 fetch 2026-11-03 01:31:44, after step 4 finished; preparation finished 01:34:58; runs in two batches (subjects 101–106, then 107–109; 109 is excluded and its runner stops at the inclusion check).

**Seen before this note (no p value, accuracy or rate):**
- `runs/fetch.log`: the nine protocol files with their SHA-256 (`MANIFEST.sha256` in the data folder outside the repository; copy to be added to `runs/`).
- `runs/prepare.log` (inclusion, decided before any decoding): subjects 101–108 included, 109 excluded ("42 windows retained, fewer than 480", as DESIGN §3 expected). Retained windows 1,882, 2,235, 1,264, 1,647, 1,873, 1,808, 1,567, 2,040 (101–108); windows per block 78, 93, 52, 68, 78, 75, 65, 85; dropped windows: none for gaps or heart rate, one for too few valid IMU rows (subject106). No timestamp gap above 0.015 s was found inside any window; the loader's checks (54 columns, increasing timestamps) passed.
- Row-file names and process states (progress only).

### 0a. Pre-specified quantities (DESIGN §8–§9; copied, nothing added)
1. Unit = subject; per subject the share of its 30 assignments with p < 0.05 (strict; undefined p left out and counted); mean over subjects; subject percentile bootstrap 95% interval (B = 20,000, fresh `default_rng(20261102)` per quantity). "Inflated" = lower bound above 10%. Per rule: subjects with at least 5 rejections of 30.
2. **Primary E5:** E = 1[p_P2 < 0.05] − 1[p_P5 < 0.05], fake labels, S-main; mean per subject, then over subjects; "positive" = lower bound above 0; per-subject E, number with E > 0 and the exact one-sided sign test; no decision with fewer than 5 subjects with a defined E.
3. Secondary (no decision): every rule under every split (S-main, S-tool, S-block); positive-control power at δ 0.5 and 1.0 (S-main).
4. Predictions 1–4 of DESIGN §9, each marked held / not held / not tested; prediction 2 is an implementation check; predictions 3 and 4 are descriptive.
5. Wording (DESIGN §1): P5 is exact under the null by construction; the empirical content is how far P1–P4 exceed 5% and P5's power in the injected-signal control.

### 0b. Order of work
(1) commit this section; (2) after `chain.log` shows "step 5 runs finished", run `python ../step4-fmri-haxby/code/summarize.py --step 5 --rows runs --features <data>/pamap2/features --out results` unchanged; (3) fill sections 1 onward from `results/summary.md` / `summary.json` only; (4) statistician persona review and re-review; (5) commit rows, summary and note.

## Sections 1–5 (written 2026-11-03 06:46 KST from `results/summary.md` / `summary.json` only; the stamped `../step4-fmri-haxby/code/summarize.py --step 5` run unchanged, rc 0)
Chain (`../step4-fmri-haxby/runs/chain.log`): "step 5 runs finished" and "chain done" 2026-11-03 03:38:43 KST. 1,200 rows (150 per included subject: 90 fake + 60 control); every check of the summary passed. subject109's runner stopped at the inclusion check, as designed; no traceback in any run log. Copies added to `runs/`: the inclusion JSONs and `MANIFEST-pamap2.sha256`. Rates are means over the 8 included subjects of the per-subject share of 30 tests with p < 0.05, with subject-bootstrap 95% intervals; no undefined p in any cell.

## 1. Primary contrast E5 (fake labels, S-main)
**E = P2 − P5: 95.0 points (95% 91.2 to 97.9): positive.** All 8 subjects have E > 0 (per-subject E, subject101–108: 96.7, 93.3, 100.0, 100.0, 96.7, 96.7, 83.3, 93.3 percentage points; exact one-sided sign test p = 0.0039, the smallest possible with 8 subjects); no pair left out.

## 2. All rules and splits (fake labels)
| split | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|
| main (shuffled KFold 5) | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 100.0 (100.0–100.0) | 5.0 (2.1–8.8) |
| tool (unshuffled StratifiedKFold 5) | 56.2 (47.1–65.0) | 57.5 (49.6–65.8) | 57.1 (47.5–66.2) | 24.6 (16.7–33.8) | 2.9 (1.2–4.6) |
| block (whole blocks, fold = block mod 4) | 12.9 (9.2–16.7) | 12.5 (8.8–15.8) | 13.3 (9.2–17.5) | 33.8 (28.7–38.8) | 5.0 (2.9–7.5) |
- **Inflated** (lower bound above 10%): P1–P4 under main and tool; under block P4 only. Under block, P1–P3 reject 12.5–13.3% with lower bounds 8.8–9.2%, below the 10% criterion, so they are not flagged. P5 is not inflated in any split.
- Subjects with at least 5 of 30 rejections (P1, P2, P3, P4, P5): main 8, 8, 8, 8, 1; tool 8, 8, 8, 5, 0; block 3, 3, 3, 8, 0. The one P5 subject under main is subject107 (5 of 30).
- **P5** (exact under the null by construction; implementation check): 2.9–5.0% in the three splits; per subject under main 0–16.7%.
- Training-label permutation (P4) under whole-block folds: 33.8%, all 8 subjects at 5 or more of 30, while P1–P3 fall to 12.5–13.3%.

## 3. Positive control (injected signal, S-main; descriptive)
Raw power at δ 0.5: P1–P4 100%, P5 99.6% (98.8–100.0; one test of 240 not rejected, subject108); at δ 1.0: every rule 100%. P5 detects both injected signals. The control does not compare the rules' power, because P1–P4 also reject every fake-label test under S-main and both strengths are at or near ceiling.

## 4. Predictions (DESIGN §9)
1. P1, P2, P4 inflated under S-main: **held** (100%).
2. (Implementation check) P5 not inflated, upper bound at or below 10%, under every split: **held** (upper bounds 4.6–8.8%).
3. Under S-block, P2 and P4 lower than under S-main (paired per-subject difference, descriptive): **held** (P2 12.5 vs 100.0%, lower in all 8 subjects, per-subject differences 80.0–96.7 points; P4 33.8 vs 100.0%, lower in all 8 subjects, per-subject differences 56.7–76.7 points; differences computed from the per-subject shares in `summary.json`).
4. P5 power higher at δ 1.0 than at δ 0.5 (descriptive): **held** (100.0 vs 99.6%, a difference of one test in 240; both at or near ceiling).

## 5. Limits and wording (DESIGN §1, §10)
One non-neural dataset (8 of 9 subjects; 24 consecutive blocks of 2-s windows per subject, 4 runs of 6), post hoc with respect to steps 1–3. The blocks are cut from continuous recordings of a fixed activity protocol. The design does not test what makes blocks distinguishable (for example activity, posture or slow sensor changes). By construction P5 rejects at most 5% of null tests in expectation (random within-run assignment, labels permuted within the same group). The measured quantities are how far P1–P4 exceed 5% and P5's power in the injected-signal control. With 8 subjects the percentile bootstrap intervals are approximate. Where every subject rejects every test (S-main, P1–P4) the interval has zero width and expresses no uncertainty. Not done: activity labels as targets, the `Optional` recordings, other sensor datasets.

**Review:** statistician persona review (`review-note-statistician.txt`): 3 MUST and 6 SHOULD, checked against `summary.json` and applied (2026-11-03 06:4x KST). The reviewer could not open `../step4-fmri-haxby/code/summarize.py` (tool permission outside this folder); that script was reviewed and timestamped before the run.
Re-review (`review-note-statistician-2.txt`): ready; the time "06:4x" follows the project rule (last `date` output 06:48, rounded down to ten minutes).
