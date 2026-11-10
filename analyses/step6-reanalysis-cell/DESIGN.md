# Pre-specified reanalysis of template decoding in PMC11574977: design v2 (after the v1 review, with the re-review fixes N1, N3 and SHOULD of 2026-11-08 applied; platform (N2) still to be fixed by the author; not time-stamped)

Written 2026-11-08 (last `date` before writing the first part: Sun Nov 8 00:12 KST 2026). Status: v2 by an agent (Claude, Sonnet) after the Opus review of v1 (`review-v1.txt`, verdict "Not ready", 8 MUST), answered in section 12. The author's decisions of 2026-11-08 are recorded in section 0. Not re-reviewed, not time-stamped. No data member has been extracted, downloaded or opened. Everything about the data structure comes from the authors' public code and the supplement legend and is marked as inferred. The code in `code/` was run on synthetic data only (`test_synthetic.out`; the v1 output is kept as `test_synthetic-v1.out`; the v1 design is kept as `DESIGN-v1.md`). Paths are relative to `paper-experiment/results/reanalysis-cell/` unless stated.

## 0. Decisions (author decisions of 2026-11-08 00:0x KST; recorded before the re-review and the stamp; afterwards a change is a dated addendum)

Recorded from the author's instruction of 2026-11-08 00:0x KST:
- (c) trial-shuffle reference: run it. It is a fixed secondary.
- 600 ms window (pre-target, -600 to 0 ms): a fixed secondary.
- Within decoder: not run (stated in section 11).
- D6: standardisation is dropped from the default SVM grid. The paper names the box constraint and the kernel scale; the MATLAB default for Standardize is false. How often the chosen C sits at the upper edge of the grid is reported.
- D1 to D5 and D7 to D10: Claude's defaults of v1, confirmed by the author, with the comments of the review applied (section 12).

| # | Question | Decision | Alternative (not used) |
|---|---|---|---|
| D1 | Primary label | True template colour (`Conditions.rule`), binned in thirds, the S3G analysis (section 1). It inherits the pipeline gate and has its own core gate items G7 and G8 (section 6). | Estimated template as primary: not used, because no exact null exists for it (section 5d). |
| D2 | Time window and decoder of the primary | The 900 ms window (windows 8, 14, 20 of the code, mean of three 300 ms windows, -600 to 300 ms around target onset; it includes the 0 to 300 ms after the targets appear), decoder trained across progression levels, statistic = mean accuracy over the three levels. | 600 ms window: fixed secondary (5e). Within decoder: not run. |
| D3 | Decision rule and multiplicity | One test per region (LIP, FEF, LPFC), alpha = 0.05 with Holm over the three regions. Each secondary is its own Holm family and has no verdict. | Unadjusted alpha. |
| D4 | Permutations and draws | P = 1,000 permutations; every labelling (observed and permuted) uses D = 10 pseudo-population draws per region. The smallest Holm-adjusted p is about 0.003. | P = 5,000. |
| D5 | Label-dependent design steps | The qualifying-neuron set, trials per cell (N_progression) and neurons per population (N_neurons) are recomputed from the labels in every permutation, as the authors' code does. An undefined design in a permutation counts as an exceedance. An undefined design for the observed labelling means no test (section 5). | Fix them at the observed values (not possible in general). |
| D6 | Classifier port | Grid search over the box constraint C with 10-fold CV (7 values of log10 C from -6 to 1; kernel scale is equivalent to a rescaling of C for the linear kernel and is not searched separately; no standardisation), Platt calibration on cross-validated scores, one-hidden-layer MLP combiner, all refitted in every draw of every permutation (section 4). | Standardisation in the grid: dropped. |
| D7 | Data to extract | The 459 firing-rate members for all 27 windows (806.6 MB with the 68 minimum members), plus the gate file (3.9 MB). | The 68-member minimum (119.5 MB). Not used: it would change the authors' NaN rule (section 3). |
| D8 | First port variant and the ladder | "As written", described as "the training matrix as the code builds it" (section 4). Ladder if the accuracy items fail: V1 = "intended" placement with the same grid; V2 = as-written placement with the finer grid (22 values, three per decade, log10 C from -6 to 1). Exactly these three, in this order; no other combination (section 6). | Start with "intended". |
| D9 | Estimated-template null (secondary) | Option A of `PRECHECK.md` section 5: whole within-block label sequences are permuted among the blocks of a session, aligned by progression in block. Reported whatever it shows. | Options B, C of `PRECHECK.md`. |
| D10 | Sensitivity for the colour-selection penalty | Permutations restricted to those with the observed number of adjacent same-bin block pairs (rejection sampling). A fixed secondary; the verdict stays with the primary. Direction: under smooth drift, arrangements with many adjacent same-bin blocks raise the null, so the unrestricted primary is expected to be the more conservative (prediction P7). | Ask the authors for the penalty rule. |

Author confirmation (2026-11-08, 00:0x KST): the decisions above, as listed at the head of this section. The re-review and the stamp are still to come.

## 1. Question and what the design can show

**Target (Jahn et al., Cell 2024, PMC11574977).** The primary target is the analysis of Fig. S3G, the decoding of the true template, taken together with the paper's statement about randomisation. Fig. S3G legend (supplement, `S3-legend.txt`, fetched 2026-11-08): "True template classification accuracy for each third of the block, estimated on withheld trials (as in Figure 2D, left half, 113 neurons per region, trained/tested on 80%/20% of 76 trials per progression level [three levels] and estimated template color bin [three bins])." The Methods address drift in one sentence: "One concern might be that drift in neural responses over time lead to artifactual template information. To ensure this was not the case, templates were randomly chosen over time." The block permutation uses exactly this randomisation: the template colour was "randomly selected at the start of each block".

The secondary target is the Fig. 2D claim for the estimated template (Results): "The multi-class classifier consistently decoded the template throughout learning in all three regions (…, all p < 0.01, both across and within progression levels of learning …)". The multi-class classifier is a network on the outputs of three linear classifiers that "discriminate one-third of the color wheel from the other two-thirds", trained on the estimated template. The Methods give the test: "Statistical significance was estimated with one-sided z-tests against chance level (1/3 …)", with the z-test "rather than a t-test because the sample size is defined arbitrarily by the number of bootstraps". The Fig. 2D numbers (100 neurons, 61 trials per cell) belong to the estimated-template gate (G3); the S3G numbers (113 neurons, 76 trials per cell) belong to the true-template gate (G7).

**Question.** The pseudo-population decoder trains and validates on trials from the same blocks (an 80/20 split of trials, per neuron, per cell), and the z-test measures the spread of 100 resampling draws, not the variation between blocks or sessions. What does a test that permutes the template among the blocks of each session, refitting the whole pipeline, let us conclude about the decoding accuracy in LIP, FEF and LPFC? This is a question about what the block design supports under this test. It is not a question about whether the study is right.

**What the design allows.**
- The task chose the template colour at random at the start of each block ("The template color was randomly selected at the start of each block"), with a penalty: "we temporarily penalized the colors near already selected colors during the selection process such that they were less likely to be selected again." Block ends depend on the animal's performance (80% or 85% over 30 consecutive trials).
- A block permutation of the true template within each session is therefore close to exact, not exact. Randomisation guarantees exchangeability of the order of block colours only if every ordering of the colours used is equally likely. The penalty makes adjacent blocks less likely to have close colours. Its parameters are not in the shared code. D10 gives a sensitivity analysis. The test is described as "near-exact under the colour-selection procedure as described, with the penalty unmodelled".
- The permutation moves labels between blocks and keeps each block's trials, lengths and neural data. Anything a decoder can use that is specific to a block (slow drift, block-specific offsets) is present in the permuted labellings as well. This is the property the trial-level z-test lacks.
- Counts per bin per session are kept (conditioning on the multiset of block labels).
- Per session, block counts are not known before the data are opened (5 to 16 templates per session, 171 blocks over 17 sessions). The number of distinct arrangements is the multinomial coefficient. For example 8 blocks split 3, 3, 2 give 560, 11 blocks split 4, 4, 3 give 11,550. The joint number over sessions exceeds 10^50 for sessions of this size (`test_synthetic.out`), so the group p is limited by P, not by combinatorics: smallest p = 1/(P + 1). The Fig. 2 decoder pools neurons over sessions, so there is no per-session p.
- Renaming the bins in all sessions at once leaves a refitted decoder's accuracy unchanged in distribution. Those renamings are among the arrangements only when the counts per bin in every session are equal. Their number is negligible against the joint count, and the Monte Carlo p is not affected. For a single session with equal counts the smallest exact p includes them (`code/cell_tests.py::min_p_session`, checked in `test_synthetic.out`).
- Power is limited by 3.5 to 3.7 blocks per bin on average (Methods, for the estimated template). A template effect is separable from block variation only if it is large compared with that variation. The power curve of the synthetic suite is not a forecast.
- Direction of error. When the observed arrangement is a random draw from the arrangements, the permuted labellings share the block offsets and drift with the observed one and the test keeps its size (`test_synthetic.out`: rejection rates with and without drift). A rejection means an association between population activity and the template bin beyond block-to-block variation, under block exchangeability. A non-rejection does not show that the template is absent.

## 2. Reading order and files read before this draft

`PRECHECK.md`, `REPORT-agent-precheck.md`, `JUDGEMENT-precheck.md` (with its dated correction about `increment` and the judgement of review-v1), `review-v1.txt`, `S3-legend.txt`, the manifests, the authors' Figure 2 code (listed in `NOTES.md`, including the combined-time scripts behind Fig. 2D and S3G), the Zenodo README, and the full PMC text (Results, Methods, legends, key resources table). The supplement is not in the PMC XML; the Fig. S3 legend was taken from the supplement PDF (sha256 in `S3-legend.txt`), which is kept outside the repository. Templates: the eLife and Science Advances designs of this project.

## 3. Data to extract later, and when

Only after this design is re-reviewed, committed and time-stamped, and the proof has a block. Extraction by range requests on `Data.zip` with `code/fetch_members.py` (data option off until then), each member checked against the CRC-32 below.

- **List:** `data-members.tsv` (generated from the manifests by `code/make_member_list.py`; no member opened). 460 rows: the gate file, the minimum members and the NaN-rule members. The Zenodo record is 10.5281/zenodo.10529801; the record and the member list identify every file used.
- **Minimum, 68 members, 119.5 MB (119,469,780 bytes):** `Data/FR_around_event/<window>/ID_<n>.mat` for the windows `FR_reward_end_300_window_from_0_to_300`, `FR_target_300_window_from_-600_to_-300`, `-300_to_0`, `0_to_300`, 17 sessions each. Window 1 gives `Conditions` and the neuron filter; the three target windows give the features.
- **Faithful NaN rule, 391 further members, 687.2 MB (687,174,873 bytes):** the other 24 windows of the code (6 reward_end windows from 50, 17 target windows from -550 to 350). The authors set NaN rates to 0 on any trial where any of the 27 windows is not NaN, so a neuron's retained trials, and the values in the three used windows, can depend on all 27 windows (`PRECHECK.md` section 3). D7 uses the faithful set: the cost is 0.7 GB. The review confirmed that neuron retention depends on window 1 after the NaN fill from all 27 windows.
- **Gate file:** `Figure_2.zip` member `Figure_2/plot_figure_2/Figure_2_decoding_accuracy.mat` (3,934,334 bytes, CRC-32 cf78041e, range-extracted from the 4.6 MB zip). Per `Plot_Figure_2_github.m` it should hold `LIP/FEF/PFC_mean_classification_net` (3 x 100: mean over the validation trials of a level, per bootstrap draw) for the **estimated** template. A true-template result file (Fig. S3G) is not in the figure zips. If the variable names differ, the gate stops until a dated addendum maps them.
- **Not extracted:** the behaviour fits and the 16.5 GB validation file. `Conditions.belief` is read from the firing-rate files; the model fit files are not needed.
- Fields (inferred, "to verify on the real files"): `Conditions.block_nb`, `trial_in_block`, `rule` (radians), `belief` (100 x trials); `LIP`, `FEF`, `PFC` (neurons x trials). `code/cell_loader.py` reads older `.mat` files and v7.3 (HDF5) files (`read_mat`; the v7.3 reader transposes arrays back to MATLAB orientation and stops with a message on object references, such as a struct array). The `inspect` stage of the runner writes `out/fields.txt` with the fields and shapes found; the gate refuses to run without it. If a field is missing, the loader stops and lists the fields found, and a dated addendum maps the names.
- Sessions and ROIs follow the code: 17 sessions; LIP excludes IDs 30 and 34, FEF excludes ID 14.
- **The authors' code** (`authors-code/`) stays in this working repository and is not copied into any public repository, because it contains the authors' local paths (seven Figure_1 files). The Zenodo record and the member list identify it.

## 4. Port, label-dependent steps and feasibility

**What the code does (file and line references in `PRECHECK.md` section 3; checked again for this draft).**
- Column j of a session pairs the target-window rates of trial j+1 with the labels of trial j+1 (the shift in `prepare_pseudopop_*`). Progression is `trial_in_block / (number of trials of that block)`; levels are the first, middle and last third, and a trial at exactly 2/3 is in both levels 2 and 3. Colour bins are thirds of the circle.
- A neuron qualifies if its session has at least 60 trials in each of the 9 cells (3 levels x 3 bins). Neurons of one session share these counts. N_progression is the smallest cell count over all qualifying sessions of all regions (the paper: 61 for the estimated template, 76 in the S3G legend for the true template). N_neurons is the smallest number of qualifying neurons over regions (100 and 113).
- Per draw: N_neurons neurons with replacement; per neuron and cell N_progression trials without replacement from its own session; 80/20 holdout per neuron and cell.
- Three one-versus-rest linear SVMs, trained on the three levels pooled, with `OptimizeHyperparameters='auto'` (bayesopt, 10-fold CV), `fitPosterior`, then `fitcnet` on the three posteriors of all training trials; accuracy per level on the validation trials (round(0.2 x 61) = 12 per cell, 36 per level, for the estimated template; round(0.2 x 76) = 15 for the true template). The gate checks the validation size from the published accuracies before any port run (G9).
- **What the training matrix looks like as the code builds it (D8).** In the combined-time scripts behind Fig. 2D and Fig. S3G (for example `Run_belief_classifier_combined_time_prog_restricted_FEF.m`, `..._each_prog_...`, and `Run_true_template_classifier_combined_time_prog_restricted_FEF.m`), `increment=1;` stands inside the loop over neurons when the examples of the two "other" bins are assembled. For the first of the two "other" bins, only neuron 1 is written at offset 0, and for neurons 2 and up the first bin is overwritten by the second. The training matrix as the code builds it therefore has, in each level, half of the "other" rows equal to the first other bin for neuron 1 only (the other features are zero, from array growth, cleared at each classifier k) and half equal to the second other bin for all neurons. In the across-time scripts (for example `Run_belief_classifier_across_time_each_prog_restricted_FEF.m`), `increment=1;` stands after the neuron loop and both other bins are filled for all neurons; those scripts are not the ones behind Fig. 2D or S3G. The saved Fig. 2D values come from the combined-time files (`plot_Fig2_ET_pseudo_pop.m`), which is why "as written" is the first variant. This is a reading of the code, not a verified description of how the saved figure was made. The effect applies to every labelling alike: it bears on the fidelity of the port and on power, not on the validity of the permutation test. The synthetic suite checks that the port builds exactly this matrix when `as_written=True`.

**Port (`code/cellport.py`).** Approximations are marked APPROX in the code and listed here.
- Hyperparameters (APPROX of `bayesopt`): 10-fold CV over a fixed grid of the box constraint, log10 C in {-6, -4.5, -3, -2, -1, 0, 1} (7 settings; V2 uses 22 settings, three per decade). For a linear kernel, dividing predictors by KernelScale s equals multiplying C by 1/s^2 (checked in `test_synthetic.out`), so KernelScale is not searched separately. Standardisation is not searched (D6). The upper end of C is capped at 10 because a fit at C = 1,000 took 5.8 s on a noise matrix of the real size (324 x 30), against 0.1 s at C = 10. Ties go to the first setting in grid order. The share of SVM fits whose chosen C is at the upper edge is saved for the gate runs and every test and reported.
- Calibration (APPROX of `fitPosterior`): Platt scaling with smoothed targets on 10-fold cross-validated scores of the chosen SVM. MATLAB's exact variant is to verify.
- Combiner (APPROX of `fitcnet` defaults): one hidden layer of 10 ReLU units, no regularisation, L-BFGS, 1,000 iterations (recalled, to verify).
- z-test: exact (`z = (mean - 1/3) / std`, ddof 1, `p = 1 - normcdf(z)`).
- The authors set no seeds, so draws cannot be matched one by one. The gate compares distributions.

**Steps fitted to labels, all repeated in every draw of every permutation:** the qualifying neurons, N_progression and N_neurons (once per labelling), the sampling of neurons and trials, the choice of C, the SVM, the calibration, and the combiner. Fixing any of these at its value for the observed labels is not acceptable. The review found no issue in this: every label-fitted step is refitted per labelling, regions share one permutation per session, ties and undefined designs count as exceedances, and Holm holds under dependence.

**Consequence for the null.** A permuted labelling can change which sessions qualify, N_progression and N_neurons, and so the accuracy for reasons unrelated to template information. This is part of the statistic as the authors' pipeline defines it, and the observed labelling goes through the same function. It does not bias the test under exchangeability; it can change power. The number of qualifying sessions, N_progression and N_neurons are saved for every permutation and reported. If no neuron qualifies in some region for a permuted labelling, the statistic is undefined and counts as an exceedance (as in `blockperm`).

**Statistic.** For a labelling and a region, S = mean validation accuracy over D = 10 draws and the three progression levels (equal weights; each level has the same number of validation trials). The observed S and every permuted S use the same D, so they have the same distribution under exchangeability.

## 5. Tests

**Rule for an undefined observed design (fixed now).** If the observed labelling has no defined design (no session qualifies in some region, so N_progression or N_neurons does not exist), no test is run for that analysis. It is reported as "no test: the observed design is undefined", with the design counts. Nothing is substituted. The code gives p = NaN and the status text; the summary script writes the sentence.

**(a) The authors' z-test as published.** The 100-draw 3 x 100 accuracy matrices per region for the estimated template, "across" decoder, p per level from `z_test`. Reproduced in the gate (G5), reported for the true template too (G11, descriptive).

**(b) Primary: block permutation test, true template, per region.**
- Labels: `true_bin` (thirds of the circle of `Conditions.rule`). The permutation moves the per-block label among the labelled blocks of every session at once (all regions share the permutation), keeping counts per bin per session.
- For each of P permutations: recompute the design, draw D pseudo-populations per region, refit everything, record S per region. Same procedure for the observed labelling.
- p = (1 + #{S_perm >= S_obs} + #{undefined}) / (P + 1) per region.
- Decoder: 900 ms window, across levels, in the variant adopted by the select step (section 6). Seeds in section 8.

**Decision rule (fixed now).** Three tests (LIP, FEF, LPFC), Holm-adjusted p at alpha = 0.05 (D3).
- Holm-adjusted p < 0.05 for a region: "Under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, the null hypothesis of no association between [region] population activity and the template bin is rejected (Holm-adjusted p = x)."
- Otherwise: "Under the block permutation test, which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled, template decoding from [region] is not established (Holm-adjusted p = x). With 3 to 4 blocks per bin the test has limited power and this result does not show that the template is absent."
- The sentences are generated by `code/summarize_cell.py` from the saved output, not edited by hand. The verdict sits next to the published verdict ("all p < 0.01").
- A verdict needs the gate (section 6) to have passed its core items. Otherwise the results are saved and labelled "not interpretable", and no verdict is written.

**(c) Fixed secondary: trial-level label shuffle with refit.** Same function with labels permuted among the labelled trials of a session (counts kept), true template, 900 ms, P = 1,000. Reported next to (b) as a reference for how far a trial-level null sits from the block null. Not used for a verdict.

**(d) Fixed secondary: estimated template.** Labels from the peak of `Conditions.belief`, same pipeline and statistic, 900 ms, P = 1,000.
- Test as published: the z-test (a) on the 100-draw gate output.
- Block null, option A (D9): within-block label sequences permuted among the blocks of a session, aligned by progression in block (`permute_block_sequences`). This null keeps the within-block structure and the bin counts per level approximately, but does not re-simulate the animal's behaviour under a permuted template, so it is a model-based test. Belief follows each block's own choices and rewards, which neurons encode, so this test can reject without template coding. It is not a randomisation null. It is reported whatever it shows, with the wording: "under this block-sequence permutation, which treats the within-block estimated-template sequences as exchangeable between blocks".
- Same decision machinery (Holm over three regions), labelled secondary.

**(e) Fixed secondary: 600 ms window.** The primary test (b) with the pre-target window of -600 to 0 ms (windows 8 and 14 of the code, this_combination 1), true template, P = 1,000. Secondary, no verdict.

**Not run (fixed).** The "within" decoder (separate SVMs and network per level), the 4-colour-bin, rotated-by-pi/3 and noOne variants of the authors, and any other window. The paper's statement "both across and within progression levels" is therefore tested here for the across decoder only (section 11).

**(f) Fixed secondary: sensitivity to the colour-selection penalty (D10).** (b) repeated with permutations restricted to the observed number of adjacent same-bin block pairs (`kind="block_adjacent"`), true template, P = 1,000. Reported, not used for the verdict.

## 6. Reproduction gate (run first; nothing below is interpreted if a stopping or core item fails)

The gate runs the authors' own pipeline on the estimated template (the labels of the saved file), 100 draws per region, 900 ms window, across decoder, in the variants of the ladder. The true-template pipeline inherits the pipeline gate (G4, G5); only the labelling differs (`color_bin(rule)` instead of the peak of belief), and the label code is unit-tested. G7 and G8 are the true-template items.

| Gate | Published or stated | Pass if | Core | On failure |
|---|---|---|---|---|
| G9 validation size (checked first, before any port run) | accuracies in the gate file are means over 3 x n_val trials | fixed rule, data-driven: if every value in `*_mean_classification_net` is a multiple of 1/36, the validation size is `round(0.2 N)` (12 per cell for N = 61); if every value is a multiple of 1/39, it is `ceil(0.2 N)` (13); 1/36 is tried first; the rule found is saved in `select.json` and in the header of every resume file | yes | stop everything only if neither grid fits (the smallest grid that fits is reported) |
| G1 file integrity | CRC-32 in `data-members.tsv` | every extracted member equal (malformed hash lines and missing files fail) | yes | stop everything |
| G2 sessions and blocks | 17 sessions, 171 blocks, 5 to 16 templates per session (the split 69/102 by monkey is not in the files) | all equal | yes | stop everything |
| G3 design counts, estimated-template labels | N_neurons 100, N_progression 61 (Methods, Fig. 2D) | both equal | yes | stop everything |
| G7 design counts, true-template labels (Fig. S3G) | 113 neurons per region, 76 trials per progression level and colour bin, three levels, three bins, 80/20 split (so 15 validation trials per cell with rule round, 16 with rule ceil) | N_neurons 113, N_progression 76, 15 (round) or 16 (ceil) validation trials per cell by the G9 rule, three levels, three bins | yes | stop the true-template tests (b, c, e, f); (d) still runs; the report quotes the S3G legend wording "estimated template color bin" next to the failure |
| G8 true-template labelling | none (our check) | observed labels constant within every block of every session, and a defined design | yes | stop the true-template tests; report "not interpretable" |
| G4 accuracy, across decoder | 3 x 100 matrices per region in the gate file | for each region, the mean over levels and draws of the port is within +/- 0.03 of the published mean; for each of the 9 region-level cells the port's mean is within +/- 0.05 in at least 8 cells | yes | try the next variant |
| G5 verdict pattern | all p < 0.01 (z-test, 9 cells) | the z-test on the port's 100 draws gives p < 0.01 in all 9 cells | yes | try the next variant |
| G6 spread | published SD per region (from the file) | the port's SD over draws is within a factor of 2 | no | report |
| G10 block counts per bin | 3.5, 3.7, 3.6 blocks per bin (LIP, FEF, LPFC; estimated template) | descriptive (true-template blocks per bin reported) | no | report |
| G11 true-template accuracy | no saved file | descriptive: mean accuracy per region and level, design counts, 100 draws | no | report |

**Validation size rule (2026-11-08, after the re-review of v2).** The holdout size is not assumed. The port, G7 and G9 all use the rule that G9 finds in the published gate values: round for multiples of 1/36, ceil for multiples of 1/39 (G7: 15 or 16 validation trials for 76 trials per cell), applied by `cellport.n_val`. Values that fit both grids (only multiples of 1/3) take round. The rule is fixed here, before any data; the data only choose between the two named options.

The "within" decoder item of v1 (old G7) is dropped because the within decoder is not run (D2).

The tolerance in G4 is fixed now from the Monte Carlo error of 100 draws (about 0.004 for a mean, from SD of 0.03 to 0.04 per draw) plus an allowance of 0.03 for the optimiser, calibration and network differences.

**Variant ladder and the select step (D8).** G4 and G5 are evaluated for the variants in this order: `as_written` (as-written placement, 7-value grid), `V1_intended` (both other bins for all neurons, 7-value grid), `V2_fine_grid` (as-written placement, 22-value grid). The first variant that passes G4 and G5 is adopted by `code/cell_select.py`; the tests refuse any other variant (`require_variant`), and refuse a test that a failed G7 or G8 blocks. All variants tried are reported with every gate value. If no variant passes G4 and G5, the tests are run with `as_written`, saved, and labelled "not interpretable"; no verdict is written. The variant choice uses the estimated labels, which correlate with the true labels (section 11).

## 7. Compute

Measured on synthetic noise matrices of the real shapes, one core, this laptop, thread variables = 1, 7-value grid (2026-11-08, after the suite): one draw of the across decoder (three SVM searches of 7 settings x 10 folds, calibration, network) took 1.7 s at 100 neurons and 62 trials per cell (the estimated-template shape) and 3.7 s at 113 neurons and 76 trials per cell (the true-template shape); with the 22-value grid (V2) 4.0 s and 8.8 s. These are 2 to 4 times the v1 figure (0.9 s at 14 settings), which was measured with several BLAS threads; fit time also depends on the data, so the table is an estimate, not a forecast.

| Run | Draws | Core-hours | 6 laptop cores | Cloud VM, 64 vCPU |
|---|---|---|---|---|
| Gate: 100 draws x 3 regions, as_written (V1 adds the same, V2 about 0.3 core-hours); G11 true template 300 draws | 600 to 1,200 | 0.4 to 1.0 | 5 to 10 min | minutes |
| Primary (b): P = 1,000 + 1 labellings x 3 regions x D = 10, true template | 30,030 | 31 | about 5 h | about 30 min |
| (c) trial shuffle, true template | 30,030 | 31 | about 5 h | about 30 min |
| (e) 600 ms window, true template | 30,030 | 31 | about 5 h | about 30 min |
| (f) adjacent-pair sensitivity, true template | 30,030 | 31 | about 5 h | about 30 min |
| (d) estimated template, option A | 30,030 | 14 | about 2.4 h | about 13 min |
| Total | about 151,000 | about 138 | about 23 h | about 2.2 h |

Platform (author's decision, 2026-11-08 02:3x KST): a Google Cloud VM, machine type c2d-highcpu-56 (56 vCPU, AMD EPYC), region asia-northeast3, image Ubuntu 24.04 LTS (x86_64), Python 3.12.3 with the pinned package versions of `code/cell_env.py`; platform string "Linux x86_64". Before any data member is read, the full synthetic suite (0 failed) and the determinism stage must pass on this VM on the stamped code (the suite was not completed on the stamped code locally; `test_synthetic.out` in the repository is the output of the code before the review fixes of 2026-11-08). If either fails, the run stops; any code fix is a dated addendum and the suite is rerun before any data. Every data stage refuses another platform than "Linux x86_64" unless a dated addendum is given, and the test stage refuses when gate.json records another platform, Python build or package versions; the inspect, gate, select and all test stages run on the same VM image. The VM instance name, image and creation time are recorded in the run note. The VM is deleted after the run. The cloud column of the table applies. If the table is right, the five tests need about 23 hours on 6 laptop cores or about 2.2 hours on a 64 vCPU cloud VM. Reducing P to 500 or D to 5 would halve it; that is a decision for the author (not made here). Memory is below 4 GB. The data are 0.8 GB.

## 8. Seeds, environment and what is reported

- **Pinned environment** (checked at run time by `cell_env.check_environment`; the runner stops if one differs): Python 3.12.3; numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, h5py 3.14.0 (the versions installed in `.venv`). `blockperm` is not called; the permutation logic is in `code/cell_tests.py`, which follows `code-package/blockperm/blockperm.py` in counting and p-value conventions.
- **Threads:** `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS` and `MKL_NUM_THREADS` are set to 1 inside the code on import (`code/cell_env.py`), before numpy is loaded, so that MLP L-BFGS and the SVM fits do not depend on the number of cores; the suite checks that values of 8 set outside are overridden.
- **Platform:** recorded in every output file (system, machine, Python build, package versions, thread variables, seed). Fixed: "Linux x86_64" on the VM of section 7 (author, 2026-11-08). `cell_env.DEFAULT_PLATFORM` holds this string; every data stage (inspect, gate, select, test) refuses to run while the placeholder is present. The output has a flag that says whether the run matched it. Results on another platform are reported with that flag; no claim of byte-identical results across platforms is made.
- **Master seed 20261107**, fixed in `cell_env.MASTER_SEED`. Every random stream is `numpy.random.SeedSequence([seed, purpose, kind, labelling index])` (`cell_tests.rng_for`). Purpose codes: primary 1, trial shuffle 2, 600 ms window 3, estimated template 4, adjacent-pair 5, gate draws 21 (estimated) and 22 (true). A labelling's output does not depend on the number of workers. A partial run resumes from `out/<test>.partial.jsonl` and gives identical output. The first line of that file is a header (test, variant, grid, window, P, D, validation size rule, master seed, platform record, sha256 of every code file used, addendum name); a resume with a different header, or a file without one, is refused. P = 1,000 and D = 10 are the design's values; other values are refused unless `--addendum <dated name>` is given, which is recorded in the header and in the output.
- **Determinism test:** the suite reruns three synthetic labellings (observed, block-permuted, trial-permuted), serially and in two worker processes, and requires identical output (`run_cell.py determinism`, and in `test_synthetic.out`).
- **Stages and files:** `code/run_cell.py` (stages `determinism`, `inspect`, `gate`, `select`, `test`), `code/cell_gate.py`, `code/cell_select.py`, `code/summarize_cell.py`, `code/cell_loader.py`, `code/cell_env.py`, `code/cellport.py`, `code/cell_tests.py`. Outputs go to `out/` (not committed: it holds the cached sessions).
- Everything in sections 5 and 6 is reported, whatever it shows, including failed gates, variants tried, the design counts of every permutation, undefined designs, the share of chosen C at the upper edge, and the secondary results.
- Any change after the stamp is a dated addendum. Tests, windows, seeds and decision rules are not changed after accuracies are seen.

**Wording limits.** We do not say that the study is wrong. Verdicts are written "under the block permutation test, the verdict is …". The exchangeability model and the unmodelled penalty are named next to every block-test result. A rejection means an association between population activity and the template bin under block exchangeability; it is not described as "most blocks" or "most sessions". The z-test in the paper and our test are described as answering different questions: the spread of resampling draws and the variation between blocks. The 900 ms window includes the 0 to 300 ms after the targets appear; a result in it is not described as pre-target.

## 9. Predictions (written before the data; may be wrong)

Each prediction is marked held, not held or not tested by `summarize_cell.py` with these rules.

| # | Prediction | held | not held | not tested |
|---|---|---|---|---|
| P1 | The gate passes with the as-written variant (low confidence about the size of the allowance). | `as_written` is adopted | V1 or V2 adopted, or no variant passes | the gate stopped before the accuracy items |
| P2 | The port's z-test gives p < 0.01 in all 9 cells (the published claim; small spread over draws). | G5 passes in the last variant tried | G5 fails there | no variant was tried |
| P3 | The trial-shuffle reference (c) gives p at its minimum in all regions for the true template. | raw p = 1/(P + 1) in all three regions | otherwise | test absent or no test |
| P4 | Primary: Holm-adjusted p < 0.05 in at least one region (moderate to low confidence: plausible if template information is large compared with block variation). | at least one region | none | absent, undefined, or not interpretable |
| P5 | Estimated template under option A (d): Holm-adjusted p >= 0.05 in at least one region (low confidence). | at least one region | none | absent, undefined, or not interpretable |
| P6 | Design counts under permutation vary: some permutations leave a different N_progression or N_neurons, or an undefined design, than the observed labelling. | at least 1 of the P permutations of (b) differs | none differs | (b) absent |
| P7 | D10 direction: the adjacent-pair restricted test (f) gives a raw p no larger than the primary's in at least two of three regions (the unrestricted null is the more conservative, if the observed arrangement has fewer adjacent same-bin pairs than a typical arrangement). | at least 2 of 3 regions | fewer | either test absent or undefined |

No prediction is made for the 600 ms window, G6, G10 and G11.

## 10. Synthetic checks (`code/test_synthetic.py`, output `test_synthetic.out`)

Unit checks: colour bins, progression levels (including 2/3), peak belief, the column shift and NaN rule, KernelScale equivalence, Platt scaling, the as-written "other" matrix, block and trial permutation, block-sequence permutation, adjacent-pair matching, arrangement counts, smallest p with and without class-renaming twins (exact enumeration), undefined values, Holm, qualification and design counts, pseudo-population shapes. Decoder checks: no information near 1/3, positive control, within and intended variants. Added in v2: the grids (7 and 22 values, no standardisation) and the recording of the chosen C; the label check of G8; the no-test status for an undefined observed design; gate items G1 (with negative tests for a wrong CRC, a missing member and a malformed hash), G2, G3, G7, G8, G9, G4 and G5; gate draws independent of the number of workers; the select step (order, adoption, refusals, stopping items); the loader on the same synthetic session as v5 and as v7.3 files; the environment (versions, threads forced to 1, platform record); the determinism test; the runner's test stage with resume and refusal of another variant; the prediction marks and the generated sentences. Size and power with a cheap stand-in decoder (the pipeline, labelling and permutation code are the real ones): no information with and without block offsets and drift, the z-test and trial shuffle against the block test. A full-pipeline block test on a positive control, and a full-pipeline null study over 60 datasets. Results of the v2 run: `test_synthetic.out` (66 checks, 0 failed, full mode, 1,685 s on 6 cores); v1 results: `NOTES.md` section 6 and `test_synthetic-v1.out`.

## 11. Limits

- The null is model-based (section 1): near-exact under the colour-selection procedure as described, with the penalty unmodelled.
- The decoder is a port, not the authors' MATLAB (section 4, APPROX items).
- No saved true-template result exists. The true-template pipeline inherits the gate of the estimated-template pipeline (G4, G5) and has the count gates G7 and G8.
- **Selection step.** The variant is chosen on the estimated-template labels (gate), which correlate with the true-template labels. This is a small selection step before the primary test; the rule is fixed in code and every variant tried is reported.
- **Within decoder not run.** The claim in Results states "both across and within progression levels of learning"; this design tests the across decoder only. A non-rejection or rejection here says nothing about the within decoder.
- The 4-bin, rotated and noOne variants of the authors are not run.
- D = 10 draws per labelling makes the statistic noisier than the authors' 100. The observed labelling uses the same D, so the test is valid; power is the issue.
- The 900 ms window includes 0 to 300 ms after target onset; the 600 ms secondary is the pre-target window.
- Under smooth drift, arrangements with many adjacent same-bin blocks raise the null, so the primary is expected to be the more conservative of (b) and (f); the verdict stays with (b).
- The estimated-template block null (d) is not a randomisation null (section 5d).
- The share of SVM fits with chosen C at the upper edge (log10 C = 1) is reported; a high share means the grid cap may bind.
- Review and author status: v1 was reviewed (`review-v1.txt`); v2 has not been re-reviewed.

## 12. Response to the v1 review (2026-11-08; `review-v1.txt`, `JUDGEMENT-precheck.md`)

Review verdict: "Not ready", 8 MUST. Items cited as M1 to M8 and S for SHOULD. Author decisions: section 0.

### 12.1 MUST items
| Item | What changed | Where |
|---|---|---|
| M1 `increment` location and effect | Corrected: the zero rows occur in the combined-time scripts (behind Fig. 2D and S3G), not in the across-time scripts, where `increment=1;` follows the neuron loop. "As written" stays the first variant. The effect is described as "the training matrix as the code builds it", applies to every labelling alike, and bears on fidelity and power, not validity. NOTES section 2.3 corrected the same way. | 4; NOTES 2.3 |
| M2 target claim | The primary target is the S3G analysis plus the randomisation statement; the legend is quoted. The S3G numbers (113 neurons per region, 76 trials per level and colour bin, three levels, three bins, 80/20) are core gate item G7. The Fig. 2D numbers (100, 61) stay in G3, the estimated-template gate. | 1, 6 |
| M3 true template primary, gate G8 | True template stays primary and inherits the pipeline gate. New core G8: observed true-template labels constant within blocks and a defined design, else stop and report "not interpretable". The estimated template is not made primary (option A is not a randomisation null). | 0 (D1), 5d, 6 |
| M4 optional or conditional analyses | None left. (c) trial shuffle: run, fixed secondary. 600 ms window: fixed secondary. Within decoder: not run. 4-bin, rotated, noOne: not run. V2 defined exactly: as-written placement with the 22-value grid. | 0, 5, 6, 11 |
| M5 predictions | Seven predictions with held, not held, not tested rules (as in the Sci Adv design, section 7), coded in `summarize_cell.py`. | 9 |
| M6 D6 grid | Standardisation dropped from the grid; 7 values of log10 C (V2: 22); the share of chosen C at the upper edge is saved and reported. | 0 (D6), 4 |
| M7 code before the stamp | Written: `run_cell.py` (runner), `cell_gate.py` (gate), `cell_select.py` (select), `summarize_cell.py` (summary), `cell_env.py`, `synthetic_data.py`; master seed fixed; thread variables set to 1 inside the code; platform recorded in every output; determinism test of three labellings; pinned versions checked at run time; loader for v7.3 and older files. | 8, 10; `code/` |
| M8 undefined observed design | Rule: no test, reported as such; coded (status text, NaN p) and tested. | 5 |

### 12.2 SHOULD items
| Item | What changed | Where |
|---|---|---|
| D10 direction | Stated (prediction P7 and Limits); the verdict stays with the primary. | 0, 9, 11 |
| Validation size from the gate file | New core G9, evaluated first, before any port run. | 6 |
| Selection step | Listed in Limits. | 11 |
| Wording of a rejection | "association between population activity and the template bin under block exchangeability". | 1, 5, 8 |
| 900 ms window includes 0 to 300 ms after targets | Stated in D2, 8, 11. | 0, 8, 11 |
| v7.3 reader | Written and tested on a synthetic v7.3 file. | 3; `cell_loader.py` |
| D2, D3, D4, D5, D7, D9 agree | Kept. D9 stays a secondary with the caveat of M3. | 0 |
| Validity, platform, paths (no issue found) | No change. `authors-code/` stays internal (section 3). | 3 |

### 12.2b Re-review of v2 (2026-11-08)

Items N1, N2, N3 and SHOULD of the section "Re-review of v2" in `review-v1.txt`. Code and tests changed; no data member opened. Previous suite output: `test_synthetic-v2a.out`.

| Item | What changed | Where |
|---|---|---|
| N1 P and D can change after the stamp | The resume file starts with a header line (test, variant, grid, window, P, D, validation size rule, master seed, platform record, sha256 of the seven code files used, addendum). A resume with a differing header, or without a header, is refused. P and D other than 1,000 and 10 are refused unless `--addendum <dated name>` is given; the name is recorded in the header and in `test-<name>.json`. Tests: differing header refused (one field at a time), file without header refused, wrong P or D refused, undated addendum refused, matching header resumes. | 8; `run_cell.py` |
| N2 platform | Chosen by the author (2026-11-08): GCP c2d-highcpu-56, asia-northeast3, Ubuntu 24.04 LTS, Python 3.12.3 with the pins, platform string "Linux x86_64" (sections 7 and 8, `cell_env.DEFAULT_PLATFORM`); the data stages refused to run while the placeholder was present | 7, 8; `cell_env.py`, `run_cell.py` |
| N3 holdout rounding | Fixed, data-driven rule: multiples of 1/36 give `round(0.2 N)`, multiples of 1/39 give `ceil(0.2 N)`, stop only if neither fits. Applied to the port (`cellport.n_val`), G7 (15 or 16 for 76) and G9; saved in `select.json` and the header. Tests on synthetic gate values (36, 39, 35, 1/3 grids), on `n_val`, on G7 and on the port draw. | 6; `cell_gate.py`, `cellport.py` |
| SHOULD G7 legend | The G7 failure detail quotes the S3G legend wording "estimated template color bin"; the summary table shows it. Tested. | 6; `cell_gate.py` |

### 12.3 For the author
1. A mismatch in G7 stops the true-template tests (the S3G legend names "estimated template color bin" in its wording while the panel shows the true template; the gate tests the counts with the true-template labels). A dated addendum would be needed to change this.
2. The pass thresholds of G4 and G5 are unchanged from v1.
3. The re-review and the stamp are still to come.


### 12.3 Changed-lines check before the stamp (2026-11-08)
| Item | Change |
|---|---|
| F1 platform not enforced | `cell_env.require_platform_fixed(addendum)` refuses any platform other than DEFAULT_PLATFORM without a dated addendum, in inspect, gate, select and test; the test stage compares platform, Python build and versions with gate.json |
| F2 suite not run on the stamped code | Stated in section 7; full suite (0 failed) and determinism stage on the VM before any data; failure stops the run; fixes only by dated addendum |
| SHOULD CPU model | `platform_record()` records the CPU model (/proc/cpuinfo or sysctl), so it is in every header |
