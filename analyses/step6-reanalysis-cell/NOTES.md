# NOTES: Cell reanalysis, stage 1 (written 2026-11-07, agent Claude Sonnet; last `date` before writing: Sat Nov 7 16:34 KST 2026, a later check is in the report)

## 1. What was read

Read in full: `PRECHECK.md`, `REPORT-agent-precheck.md`, `JUDGEMENT-precheck.md`, `zenodo-files-10529801.tsv`, the Zenodo README (`authors-code/READ_ME_zenodo.rtf`), the full PMC11574977 XML text (Results, Discussion, STAR Methods, figure legends, key resources table; the supplement is not in the XML). Authors' Figure 2 code read line by line: `prepare_pseudopop_true_template_classifier_prog_restricted_FEF.m`, `prepare_bootstrap_true_template_classifier_across_time_prog.m`, `Run_true_template_classifier_combined_time_prog_restricted_FEF.m`, `Run_template_classifier_combined_time_prog_NN_restricted_FEF.m`, `Run_belief_classifier_combined_time_prog_restricted_FEF.m`, `Run_belief_classifier_combined_time_each_prog_restricted_FEF.m`, `Run_belief_classifier_combined_time_each_prog_NN_restricted_FEF.m`, the z-test and accuracy aggregation parts of `plot_Fig2_ET_pseudo_pop.m`, `plot_FigS2_true_template_decoding.m` and `Plot_Figure_2_github.m`. Not read line by line: the 4-bin, rotated and noOne variants, the cross-temporal and PCA scripts, Figures 1, 3 to 6.
Templates: `../reanalysis-elife/DESIGN.md`, `../reanalysis-elife/code/elife_tests.py`, `../reanalysis-sciadv/DESIGN.md` (head), `../../code-package/blockperm/blockperm.py`.
No data member was extracted or opened; the manifests were read to build `data-members.tsv`. Nothing was committed or stamped.

## 2. Findings from the code that change the design

1. **The saved gate file is for the estimated template, not the true template.** `Plot_Figure_2_github.m` loads `Figure_2_decoding_accuracy.mat` for the Fig. 2D violins (label "Expected template classification accuracy"). The true-template result (Fig. S3G, `plot_FigS2_true_template_decoding.m`) has no saved result in the figure zips. So the primary test (true template, D1) cannot be gated on a published true-template distribution. The design gates the estimated-template pipeline and lets the true-template pipeline inherit it.
2. **The quoted claim is about the estimated template.** A verdict on the true template is not a verdict on that claim. This is open decision D1 for the author.
3. **The `increment=1` placement (corrected 2026-11-08 after review-v1, MUST 1).** In the combined-time scripts behind Fig. 2D and S3G (`Run_belief_classifier_combined_time_prog_restricted_FEF.m`, `..._each_prog_...`, `Run_true_template_classifier_combined_time_prog_restricted_FEF.m`), `increment=1;` stands inside the loop over neurons when the "other" examples are assembled, so the training matrix as the code builds it has, in each level, half of the "other" rows equal to the first other bin for neuron 1 only (other features zero, from array growth) and half equal to the second other bin for all neurons. In the across-time scripts (for example `Run_belief_classifier_across_time_each_prog_restricted_FEF.m`), `increment=1;` stands after the neuron loop and both other bins are filled for all neurons; those scripts do not make Fig. 2D or S3G. The port reproduces the combined-time behaviour (`as_written=True`) and has an "intended" variant. I read this from the code only; I did not run MATLAB (none available). The earlier text of this item said "every Run_* classifier script", which was wrong for the across-time scripts (see the dated correction in `JUDGEMENT-precheck.md`).
4. **Neurons of one session share cell counts.** Qualification (at least 60 trials in all 9 cells) is therefore per session and region, and a permutation changes which sessions qualify, N_progression and N_neurons. The design recomputes them per permutation (D5) and saves the counts.
5. **The z-test spread** is the draw-to-draw variation only; the same 100 draws are not sensitive to blocks or sessions.
6. **Trial at progression exactly 2/3** is in levels 2 and 3 in the authors' code (ported as written). Floating-point equality of `trial/size` with `2/3` is assumed to behave the same in Python and MATLAB.
7. **Label alignment.** Column j pairs the target windows of trial j+1 with labels of trial j+1. Reward-end windows of trial j (not used for the features) enter only the NaN rule and the neuron filter.
8. `cvpartition(N,'Holdout',0.2)`: the validation size is assumed round(0.2 x N) (12 of 61). To verify on the real files.

## 3. Open questions for reviewers

- D1 to D10 in `DESIGN.md` section 0, especially D1 (true or estimated template as primary), D3 (multiplicity: 3 regions, Holm), D5 (recompute versus fix the design per permutation), D7 (0.7 GB for the faithful NaN rule).
- Is a per-labelling statistic with D = 10 draws acceptable, given that the gate uses 100? (The observed labelling uses the same D, so the test is valid; power is the issue.)
- Is the grid for C (log10 -6 to 1, 14 settings with standardisation) a fair substitute for `bayesopt`? Any step fitted to labels is refitted in every permutation, but the substitute may be weaker or stronger than the authors' search; the gate checks accuracy only.
- Is conditioning on counts per bin per session, and treating all regions as sharing one permutation per session, the right null? An alternative is permuting separately per region (not possible: the same blocks).
- Option A for the estimated template changes the within-block sequence by resampling positions; is this a fair null? It does not re-simulate behaviour.
- Does the tolerance of G4 (+/- 0.03 on region means, +/- 0.05 per cell, at least 8 of 9) have the right size? It is fixed from Monte Carlo error plus an allowance, without data.
- Counting of undefined designs as exceedances is conservative; is the observed labelling certain to be defined (G3)?

## 4. What was not determined

- Number of blocks per session and per colour bin, true-template bin counts, any session with a single block in a bin (needs `Conditions.rule` and `block_nb`).
- Whether the saved file holds the variables named in `Plot_Figure_2_github.m`; whether the `Data.zip` .mat files are v7.3 (the loader stops with a message if so).
- MATLAB version; `fitcnet` defaults, `fitPosterior` details, whether `fitcsvm` `auto` optimises KernelScale and Standardize for the linear kernel (all from recollection).
- What "Restricted_FEF" restricts, and whether the Zenodo `FR_around_event` folders are the restricted versions.
- The colour-selection penalty parameters (the authors would have to give them).
- The Fig. S3G legend and true-template numbers: now in `S3-legend.txt` (2026-11-08); the design gates on them (G7).
- Real-data fit time per draw (synthetic: 0.9 s at the real matrix size).

## 5. Housekeeping

- `.venv/` holds numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1. It is not git-ignored in the repository; do not commit it.
- `authors-code/` contains the authors' personal home paths in seven Figure_1 files (see `PRECHECK.md`); keep it out of any public copy.
- `test_synthetic-run1-one-failed-check.out` is the first full run (37 checks, 1 failed). The failed check was a single-dataset descriptive check (no information, full pipeline, P = 19, p = 0.050 at the floor by chance, about the 5% expected). It was removed as redundant with the 60-dataset rate and the suite was rerun; the rerun is `test_synthetic.out`. Kept for the record.
- Files written here: `DESIGN.md`, `NOTES.md`, `data-members.tsv`, `test_synthetic.out`, `code/cellport.py`, `code/cell_tests.py`, `code/cell_loader.py`, `code/make_member_list.py`, `code/test_synthetic.py`.
- Not yet written (stamp stage): the gate and run scripts and the summary script that generates the verdict sentences.

## 6. Synthetic results (`test_synthetic.out`, 36 checks, 0 failed, 2,895 s wall on this laptop with 6 workers, partly shared with other work; about 48 min)

Cheap stand-in decoder (nearest centroid; the labelling, design, permutation and test code are the real ones), rejection rate at 0.05 under no information, 240 datasets, 99 permutations:
- no drift, no block offsets: block test 0.042, trial shuffle 0.033, authors' z-test 0.000;
- block offsets, drift and random walk: block test 0.054, trial shuffle 1.000, authors' z-test 1.000.
Positive control (signal 0.8, same block variation, 120 datasets): block test 1.000. Full pipeline (grid SVM, Platt, MLP; P = 19, D = 2, datasets with block offsets and drift, no information): rejection 1 of 60 (0.017; floor of p is 0.05). Full-pipeline positive control reaches the floor. Unit checks: class-renaming twins and the exact smallest p (6/90 for 2,2,2), as-written "other" matrix, KernelScale equivalence, Platt, column shift and NaN rule.
These are checks of the code and of the size of the test in a Gaussian model with the assumed block variation; they are not forecasts for the real data. The cheap decoder is not the analysis decoder. The size study has binomial error of about 0.014 (n = 240).

## 7. Update for design v2 (2026-11-08)

Written after `review-v1.txt` and the author's decisions of 2026-11-08 (DESIGN.md section 0). Code added: `code/cell_env.py` (threads = 1, pinned versions, platform record), `code/run_cell.py` (runner: determinism, inspect, gate, select, test), `code/cell_gate.py`, `code/cell_select.py`, `code/summarize_cell.py`, `code/synthetic_data.py` (generator moved out of the suite); `code/cell_loader.py` now reads v5 and v7.3 files; `code/cellport.py` has no standardisation grid and records the chosen C. The "Not yet written" item of section 5 is therefore done. `.venv/` now also holds h5py 3.14.0. Section 6 above describes the v1 synthetic run (`test_synthetic-v1.out`); the v2 run is `test_synthetic.out` (see DESIGN.md section 10 and the end of this file after the run).

v2 suite (`test_synthetic.out`, full mode, started 2026-11-08 01:58 KST, 6 workers, pinned environment): 66 checks, 0 failed, 1,685 s wall. Size and power with the cheap decoder are unchanged from v1 (block test 0.042 without drift, 0.054 with drift and offsets, trial shuffle and z-test 1.000 under drift). Full pipeline, no information, drift: rejection 0.017 in 60 datasets (P = 19). Determinism of three labellings: identical serial and in 2 workers. Two test-harness faults were found and fixed on the way (not faults of the analysis code): worker processes started with the 60-trial rule instead of the scaled-down 18 (now passed through the `CELL_MIN_TRIALS` variable, which the run-time environment check refuses outside the suite), and the entry scripts did not find their own folder under `python -I` (now added to the path). Measured draw times (1.7 s and 3.7 s) are in DESIGN.md section 7.
