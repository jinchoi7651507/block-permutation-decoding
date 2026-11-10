# Results note: pre-specified reanalysis of template decoding in PMC11574977 (Jahn et al., Cell 2024)

## 0. Written before any data output was read (2026-11-08 20:2x KST; the VM pipeline started at 20:18 KST and is downloading)

**Governing files.** `DESIGN.md` v2 with `DESIGN-v2.sha256` (block 974962, 2026-11-07 18:28:25 UTC); `ADDENDUM-1-2026-11-08.md` with `ADDENDUM-1.sha256` (suite fixes only) and `ADDENDUM-1b-2026-11-08.md` with `ADDENDUM-1b.sha256` (data fetch wrapper), both attested in block 975049 (2026-11-08 10:18:44 UTC). Run record `RUNNOTE.md`. Tables, verdict sentences and prediction marks come only from the stamped `code/summarize_cell.py` run on the pipeline output (`out/select.json`, `out/gate.json`, `out/test-*.json`), without editing.

**Seen before the data stages.** Only synthetic outputs (`test_synthetic*.out`, determinism), the member manifests and the Figure_2.zip central directory (refusal check). No data member, gate value or test value.

**Quantities fixed in the design (read in this order).**
1. Gate: stopping items G9, G1, G2, G3; true-template items G7, G8; accuracy items G4, G5 for each variant tried; descriptive G6, G10, G11. The adopted variant (`select.json`) or "not interpretable".
2. Primary (b): block permutation test, true template, 900 ms window, across decoder, per region (LIP, FEF, LPFC), Holm-adjusted p, and the generated verdict sentence (DESIGN section 5).
3. Fixed secondaries, no verdict: (c) trial shuffle, (d) estimated template option A, (e) 600 ms window, (f) adjacent-pair sensitivity.
4. Design counts per permutation (qualifying sessions, N_progression, N_neurons, undefined designs) and the share of chosen C at the upper edge.
5. Predictions P1-P7 marked held / not held / not tested by `summarize_cell.py`.

**Order of work.** Commit this section → pipeline ends → copy the outputs (`vm-out/`) → run `python -I code/summarize_cell.py --out <copied out>` unchanged → copy numbers and sentences only from its `summary.md` into section 1 → statistics persona review (Opus) with the summary code → judgement file. Wording limits of DESIGN section 8 ("under the block permutation test ...", exchangeability and the unmodelled penalty named next to every block-test result; never "wrong"). Results stay out of every public text until the NCS submission.

**Added 2026-11-09 02:2x KST, before any output of the rerun was read (section 0 above is not edited).** Governing files now include `ADDENDUM-2-2026-11-08.md` with `ADDENDUM-2.sha256` (earliest block 975069, 2026-11-08 13:37:49 UTC). The first VM run stopped at the gate (RUNNOTE 20:18-21:24). The rerun goes through `code/run_cell_a2.py`, output folder `out-a2/` on the VM (copied to `vm-out/`), summarized with `python -I code/summarize_cell.py --out <copied out-a2>`.

**Correction 2026-11-09 12:2x KST to the line above:** the copied outputs are in `vm-out-a2/` (not `vm-out/`).

## 1. Results (2026-11-09 12:1x KST; numbers and sentences copied from `vm-out-a2/summary.md`, written by the stamped `code/summarize_cell.py` from the copied outputs; observed values, null summaries and design ranges in 1.3 and 1.4 computed from `out-a2/test-*.json` by `note_tables.py` (output `vm-out-a2/note_tables.out`); G10, G11 from `out-a2/gate.json`; gate-run C counts from `out-a2/gate-runs/as_written.json` (`out-a2/` is inside `vm-out-a2/a2-out.tgz`); compare-names from `out-a2/a2_net_vs_combined.json`)

### 1.1 Gate
Selection: interpretable (variant `as_written`, the first of the ladder; no other variant tried). Every core item passed:
- G9 validation size: 900 values, multiples of 1/36, rule round, 12 validation trials per cell.
- G1: 460 members checked, 0 problems. G2: 17 sessions, 171 blocks, 5 to 16 per session.
- G3 estimated template: N_neurons 100, N_progression 61 (as stated). G7 true template (Fig. S3G): N_neurons 113, N_progression 76, 15 validation trials per cell (as stated). G8: labels constant within blocks in all 17 sessions.
- G4 accuracy: region mean differences LIP 0.0061, FEF 0.0098, LPFC 0.0031 (tolerance 0.03); 9 of 9 cells within 0.05.
- G5 z-test as published: all 9 cells p < 0.01 (largest 0.00032).
- G6 (not core): port SD / published SD 1.11, 1.03, 0.95.
- G10 (descriptive): true-template blocks per bin LIP 3.42, FEF 3.40, LPFC 3.35. G11 (descriptive): true-template port accuracy LIP 0.757, FEF 0.749, LPFC 0.724; per progression level LIP 0.714, 0.786, 0.772, FEF 0.713, 0.785, 0.749, LPFC 0.704, 0.727, 0.742.
- Gate file: `Figure_2/plot_figure_2/Figure_2.mat` (holds the three `*_mean_classification_net` variables; `Figure_2_PCA.mat` does not; `a2-gatefile-check.out`, 2026-11-09, wrapper's own function on fresh copies with the listed CRC-32). `compare-names`: the largest absolute difference between `*_net` and `*_combined` is 0.0 in all three regions, so the two names hold the same values.

### 1.2 Verdict sentences (generated, not edited; published Fig. 2D verdict, estimated template: "all p < 0.01")
- "LIP: under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, template decoding is not established (Holm-adjusted p = 0.6434). With 3 to 4 blocks per bin the test has limited power and this result does not show that the template is absent."
- "FEF: under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, template decoding is not established (Holm-adjusted p = 0.4795). With 3 to 4 blocks per bin the test has limited power and this result does not show that the template is absent."
- "LPFC: under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, template decoding is not established (Holm-adjusted p = 0.6434). With 3 to 4 blocks per bin the test has limited power and this result does not show that the template is absent."

### 1.3 Tests (P = 1,000, D = 10; chance 1/3; smallest raw p 0.000999; block tests assume blocks exchangeable under the null, colour-selection penalty unmodelled)
| Test | Region | observed accuracy | null mean (SD) | null 5th-95th percentile | raw p | Holm p |
|---|---|---|---|---|---|---|
| (b) primary: block, true template, 900 ms | LIP | 0.7570 | 0.7537 (0.0424) | 0.6812-0.8213 | 0.4785 | 0.6434 |
| | FEF | 0.7526 | 0.6975 (0.0529) | 0.6120-0.7875 | 0.1598 | 0.4795 |
| | LPFC | 0.7393 | 0.7181 (0.0439) | 0.6444-0.7897 | 0.3217 | 0.6434 |
| (c) trial shuffle, true template, 900 ms | LIP | 0.7689 | 0.3335 (0.0139) | 0.3102-0.3563 | 0.000999 | 0.0030 |
| | FEF | 0.7733 | 0.3335 (0.0136) | 0.3119-0.3570 | 0.000999 | 0.0030 |
| | LPFC | 0.7156 | 0.3333 (0.0135) | 0.3111-0.3548 | 0.000999 | 0.0030 |
| (e) block, true template, 600 ms pre-target | LIP | 0.6830 | 0.6981 (0.0447) | 0.6203-0.7692 | 0.6334 | 1.0000 |
| | FEF | 0.7111 | 0.6481 (0.0501) | 0.5657-0.7378 | 0.1249 | 0.3746 |
| | LPFC | 0.6415 | 0.6696 (0.0434) | 0.5991-0.7462 | 0.7363 | 1.0000 |
| (f) block, adjacent-pair restricted | LIP | 0.7363 | 0.7324 (0.0422) | 0.6620-0.8000 | 0.4795 | 0.4855 |
| | FEF | 0.7556 | 0.6738 (0.0567) | 0.5872-0.7657 | 0.0819 | 0.2458 |
| | LPFC | 0.7185 | 0.6898 (0.0419) | 0.6222-0.7599 | 0.2428 | 0.4855 |
| (d) estimated template, option A, 900 ms | LIP | 0.6750 | 0.7014 (0.0460) | 0.6222-0.7759 | 0.7323 | 1.0000 |
| | FEF | 0.6917 | 0.6563 (0.0535) | 0.5681-0.7473 | 0.2597 | 0.7792 |
| | LPFC | 0.6694 | 0.6711 (0.0466) | 0.5970-0.7500 | 0.5155 | 1.0000 |
Observed values differ between tests of the same labels and window because each test has its own seeds (DESIGN section 8).

### 1.4 Design counts and the C grid
- Observed design: true template N_progression 76, N_neurons 113; estimated template 61 and 100.
- Permutations with a design different from the observed one: primary 998 of 1,000, trial 960, 600 ms 999, adjacent 1,000, estimated 995; none undefined. Primary null: N_progression 60 to 102 (median 64), N_neurons 61 to 135 (median 105).
- Share of SVM fits with chosen C at the upper edge: at most 0.003 in every test and region; 0 of 300 per region in the estimated-template gate run and in G11.

### 1.5 Predictions (marked by `summarize_cell.py`)
| # | Mark | Basis |
|---|---|---|
| P1 gate passes with `as_written` | held | adopted variant as_written |
| P2 z-test p < 0.01 in all 9 cells | held | G5 in as_written |
| P3 trial shuffle at its minimum in all regions | held | p = 0.000999 in all three |
| P4 primary: Holm p < 0.05 in at least one region | not held | 0 of 3 regions |
| P5 estimated template: Holm p >= 0.05 in at least one region | held | 3 of 3 regions |
| P6 design counts vary under permutation | held | 998 of 1,000 |
| P7 adjacent-pair p no larger than the primary's in at least 2 of 3 regions | held | 2 of 3 regions |

### 1.6 Reading (within the wording limits of DESIGN section 8)
The port reproduced the published Fig. 2D accuracies and the z-test pattern (G4, G5). Under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, template decoding is not established in LIP, FEF or LPFC (Holm-adjusted p = 0.64, 0.48, 0.64). The z-test in the paper and this test answer different questions: the spread of resampling draws and the variation between blocks. With the same true-template labels and the same pipeline, the trial-level shuffle gives a null mean of 0.33 and its smallest p in every region; template labels permuted among the blocks of each session give null means of 0.75, 0.70 and 0.72 (LIP, FEF, LPFC), against observed 0.76, 0.75 and 0.74.

This result does not show that the template is absent. There is a mean of 3.35 to 3.42 blocks per bin (G10). Power was not estimated on these data; a first Holm rejection (smallest raw p below 1/60) needs accuracy above about 0.80 to 0.84, by region, under these block permutation nulls (post hoc, `vm-out-a2/note_tables.out`). A non-rejection says that the decoding accuracy in this window lies within the range obtained when template labels are moved between blocks.

Scope. The 900 ms window includes the 0 to 300 ms after the targets appear; the 600 ms pre-target secondary, under the same block permutation model, gives raw p 0.63, 0.12, 0.74. Only the across decoder was tested, so the paper's statement "both across and within progression levels" is tested for the across decoder only. The 4-bin, rotated and noOne variants were not run. The decoder is a port with the APPROX items and the as-written training matrix of DESIGN section 4; D = 10 draws per labelling against the authors' 100. Test (d) is reported under this block-sequence permutation, which treats the within-block estimated-template sequences as exchangeable between blocks; it is not a randomisation null. Under permutation the design counts differ from the observed labelling (1.4), which leaves test size unchanged under exchangeability. Post hoc (`vm-out-a2/note_tables.out`, descriptive), null accuracy rises with N_neurons, and the primary null mean is 0.015 to 0.022 below its fitted value at the observed design, so the design difference does not explain the non-rejection.

### 1.7 Deviations and run facts
1. Addendum 1 (2026-11-08): test-suite fixes only. Addendum 1b (2026-11-08): data fetch wrapper. Addendum 2 (2026-11-08): gate file `Figure_2.mat`, fallback `Figure_2_PCA.mat`, through `code/run_cell_a2.py`, no stamped file changed. Earliest blocks: DESIGN v2 974962; Addenda 1 and 1b 975049; Addendum 2 975069 (2026-11-08 13:37:49 UTC).
2. First data run (2026-11-08 20:18-21:24 KST) stopped at the gate on the variable names (logs `vm-out/vm-out.tgz`); no value read.
3. Hash check on the VM before the rerun (2026-11-09 02:15 KST): 44 of 45 listed files match. `JUDGEMENT-addendum1.md` differs: the listed version is in git b93d7f9, and it was edited on 2026-11-08 at 17:39 after its list was stamped. It is a judgement record, not code, data or a rule (RUNNOTE).
4. Rerun 2026-11-09 02:16:34 to 06:49:22 KST on GCP c2d-highcpu-56 (AMD EPYC 7B13, Linux x86_64, Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, h5py 3.14.0, 56 workers); every stage through the wrapper without `--addendum`; every stage exit 0. The outputs headers hash only the stamped runner files.
5. Outputs: `vm-out-a2/a2-out.tgz` (no cached sessions; sha256 a5804b912ef5f9cb775e966925fecb57684538eb2d36718a0abdd901138ad9c2) and `vm-out-a2/summary.md`, `summary.json`. The VM stopped at 06:53 KST and was deleted at 12:16 KST after the copy was checked; no instance, disk, address, snapshot or image remains.

6. Not produced by the stamped code: qualifying sessions per permutation (`design_null` holds only N_progression and N_neurons; DESIGN section 4 and section 0 item 4 above promise it) and the true-template z-test of DESIGN section 5a (G11 saved means only). Filled on 2026-11-09 by Addendum 3 (section 1.8), which also reports the BLAS thread setting.
7. The tables of 1.3 and 1.4 were computed by `note_tables.py`, written after the summary ran, because the summary script does not print them (a departure from the order in section 0). The design-count figures in 1.6 are post hoc and descriptive.

### 1.8 Addendum 3 (run 2026-11-09 14:26-15:22 KST; the two items of 1.7 item 6, written after the results above were read; `vm-out-a3/note_tables.out`, `vm-out-a3/a3-out.tgz`)
Hash list `ADDENDUM-3.sha256`, earliest block 975126 (2026-11-09 03:44:43 UTC). New VM of the same type, image family and pinned packages; `python_build` equal to the Addendum 2 run. G1: 460 members checked, 0 problems. No test was rerun and no verdict changes.
- Design replay. Every labelling of the five tests was rebuilt from its stamped seed without the decoder: the replayed N_progression and N_neurons equal the saved values in 1,000 of 1,000 permutations and in the observed labelling for all five tests.
- Qualifying sessions (primary, observed; permutations minimum/median/maximum): LIP 11 (7/11/13), FEF 13 (9/12/14), LPFC 13 (9/13/15). Qualifying neurons (observed; permutations): LIP 113 (61/105/135), FEF 200 (134/188/220), LPFC 354 (246/354/432). The other tests are in the output file.
- True-template z-test (DESIGN 5a, descriptive, no verdict; the G11 draws, level means equal to the saved G11 means with largest difference 0.0): all nine region-level cells p < 2.1e-6 (LIP 8.7e-08, 5.0e-16, 6.0e-10; FEF 1.1e-07, 3.2e-09, 3.8e-08; LPFC 2.0e-06, 3.5e-07, 2.2e-08). So the authors' z-test, applied to the port's true-template draws, gives p < 0.01 in every cell, while under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, template decoding is not established (1.2); the two tests answer different questions: the spread of resampling draws and the variation between blocks.
- BLAS threads. In the import order of `run_cell_a2.py`, measured on the Addendum 3 VM in the main process and in a forked pool worker (`blas-a2-order.out`), numpy's OpenBLAS was set to 56 threads and the OpenBLAS of scipy and scikit-learn's OpenMP to 1. By this measurement, on a VM of the same type, the Addendum 2 run did not have numpy's BLAS set to 1 thread as DESIGN section 8 states; its output records show only the thread variables. In Addendum 3 (cell_env first) numpy's BLAS had 1 thread, and the G11 level means were identical to those of the Addendum 2 run (largest difference 0.0), so the thread setting did not change those level means, the only Addendum 2 values saved for comparison; the five tests themselves were not rerun with 1 thread. The setting applies to every labelling alike.
- Extraction. The first attempt stopped on HTTP 500 from Zenodo after 113 of 460 members (`a3-fetch.log`); it was resumed with `code/fetch_data_retry.py` (unchanged `fetch_data.run` and allow-list, in small batches; one HTTP 500 and one incomplete read, retried, `a3-fetch-retry.log`; this wrapper and `code/run_data_a3b.sh` were written after the stamp and are not in `ADDENDUM-3.sha256`). G1 checked all members. The VM side-script did not write its marker on the first attempt (a missing file) and the VM powered off; no data value was computed then. VM deleted 2026-11-09 15:25 KST; no instance, disk, address, snapshot or image remains.

Statistics review done (`review-results.txt`, judgement `JUDGEMENT-results.md`); items applied 2026-11-09 12:2x KST (overnight instruction of the author); Opus re-check of the changed lines: one wording fix, applied (`review-results-recheck.txt`).


**Added 2026-11-09 17:2x KST (author):** in the manuscript, the exchangeability assumption and the unmodeled color-selection penalty are stated in the limitations paragraph, Methods and the Extended Data Fig. 3 legend, not next to each block-test sentence of the Results; this departs from the wording rule of the design (DESIGN section 8 for Cell, section 6 for Sci Adv), for readability (blind round 35).
