# PRECHECK: Cell 2024 (PMC11574977), Stage 0, no data opened

Run date and time: Sat Nov  7 12:01:28 KST 2026
Scope: Zenodo metadata, central-directory listings, authors' code and the full text only. No .mat or other data member was extracted or opened. No analysis was run. Paths below are relative to `paper-experiment/`; code line numbers refer to files under `results/reanalysis-cell/authors-code/`.

## 1. Zenodo record 10.5281/zenodo.10529801 (CC BY 4.0, published 2024-01-18)

| File | Size (bytes) | Checksum |
|---|---|---|
| READ_ME_zenodo.rtf | 7,903 | md5:1c33d21114d9b4645240775086b9a25d |
| Data.zip | 20,364,869,417 | md5:5a6bd3bd351bd02a5fd41ebd8636ddca |
| Figure_1.zip | 447,046 | md5:d07dd18a15675d305c2a45fbb0bb5ca7 |
| Figure_2.zip | 4,637,807 | md5:d3902559bde50b7f6706416765a64070 |
| Figures_3_and_4.zip | 1,262,764 | md5:b15d3e904fea1c80522f488a6246ec9f |
| Figure_5.zip | 1,940,310 | md5:032551eb5f279127e0bb5d52606fb0d7 |
| Figure_6.zip | 599,738 | md5:5a679ca11c4698d24f8edc70ab4fdefd |

(also `zenodo-files-10529801.tsv`). Record files were not downloaded in full, so these md5 values were not recomputed here.

**Range requests.** `Data.zip` answers HTTP range requests (HTTP 200 with `content-length`; the zip reader got HTTP 206 on every request). The central directory was read with 262,597 bytes fetched. It lists 1,672 entries (1,437 files after removing directories, `__MACOSX` and `.DS_Store`; 1,360 of them under `Data/FR_around_event/`). Saved as `manifest-zenodo-10529801.tsv` (name, size, compressed size, CRC-32, date). The five figure zips were listed the same way and saved as `manifest-zenodo-10529801-figure-zips.tsv`.

**What `Data.zip` contains (from the manifest).** It holds no code, only .mat files and folders (plus `__MACOSX` and `.DS_Store` entries).
- `Data/fitting_pipeline_validation/Fitting_pipeline_validation_results.mat`: 16.51 GB, 81% of the archive, not needed here.
- `Data/Behavior_and_models/<monkey>/...`: behavioural model fits and `bhv` files (about 1.54 GB).
- `Data/FR_around_event/<window>/ID_<n>.mat`: firing rates plus the `Conditions` struct, 80 window folders x 17 sessions, 2.38 GB in all. Session IDs map to dates in the README (Beaker 3, 8, 12, 14, 18, 20, 22, 26; Scooter 28, 30, 32, 34, 36, 38, 40, 42, 44).

The code and the saved plot data are in the five figure zips.

## 2. Code and documentation fetched

143 files (`authors-code/`, list with CRC-32 and SHA-256 in `authors-code/FETCHED.txt`): READ_ME_zenodo.rtf and all .m files from the five figure zips, except the third-party libraries CircStat2012a and Violinplot-Matlab-master. Extraction used `code/fetch_members.py` (adapted from the sciadv tool; `--data` is disabled, so a data member cannot be extracted). Verified afterwards: no non-.m file besides the README and the list.

Note for later publication: seven authors' files (Figure_1/code, behavioural fitting scripts) contain a personal home-directory path written by the authors. The grep requested below hits them. They are the authors' bytes and were left unchanged. Do not place `authors-code/` in a public repository as is, or substitute the paths with a recorded hash (rule 9-2).

## 3. Where the variables live and the exact decoding pipeline

**Data files.** One `ID_<n>.mat` per session and window folder. The pipeline loads `Conditions` and one of `LIP`, `FEF`, `PFC` (neurons x trials, per window) from each. Folder names in the code (`.../Restricted_FEF/Reset_RW_model/FR_<event>_300_window_from_<a>_to_<b>`) correspond to `Data/FR_around_event/FR_<event>_300_window_from_<a>_to_<b>/` on Zenodo (flattened). What "Restricted_FEF" restricts is not stated in the code or the README (to ask the authors).

Fields of `Conditions` used (names from the code, values not seen):
- (a) true template colour: `Conditions.rule`, in radians, per trial (`prepare_pseudopop_true_template_classifier_prog_restricted_FEF.m` L140, L243, L344; `models_FR_figure2_true_template.m` L85). Colour bin: thirds of the circle, `True_template_color` (same file L146-150, L249-253, L350-354).
- (b) block boundaries and trial order: `Conditions.block_nb` (block number per trial) and `Conditions.trial_in_block`. Progression in block = `trial_in_block / (trials in that block)` (`prepare_pseudopop_peak_belief_classifier_prog_restricted_FEF.m` L65-67). Trial order is the column order. Labels are taken from the next trial (`i+1`, L136-139) because the target-window rates of column i belong to trial i+1 (L98-110), and the model belief is the updated one after the reward.
- (c) model-estimated template: `Conditions.belief` (100 colour bins x trials; peak = argmax, L70-82; NaN if the belief is all zero), binned into thirds of the circle as `Belief_color` (L141-145). The belief comes from the Reset RW model fit per session; the per-session fit files are probably `Data/Behavior_and_models/<monkey>/<date>/Reset_RW_6_channels_VBMC.mat` (inferred from names, not confirmed in code). The estimated template changes within a block.
- (d) neural data for the decoder: `LIP`/`FEF`/`PFC` in the same files. The main analysis uses three 300 ms windows, list indices 8, 14 and 20. By L20-24 these are target windows starting at -600, -300 and 0 ms, so the 900 ms window of the Fig. 2 legend ("-600 to 300 ms") is the mean of their rates; `this_combination=2`, set in `plot_Fig2_ET_pseudo_pop.m` L45 (combination 1 is the 600 ms window of indices 8 and 14).

**Neuron and trial inclusion (prepare_pseudopop, L9-146).** 27 windows are loaded (7 reward_end windows from 0 ms, 20 target windows from -600 ms). A neuron is dropped if it is NaN in window 1, the reward_end 0-300 ms window (L126). On trials where any window is non-NaN, NaNs in other windows are set to 0 (L117-124), so the values in the three used windows depend on all 27 windows. LIP is excluded for sessions 30 and 34 and FEF for session 14 (L54, L155).

**Bootstrap construction (`prepare_bootstrap_peak_belief_classifier_across_time_prog.m`).**
- 3 progression levels (L59): first, middle, last third; note the middle and last rules overlap at progression exactly 2/3 (L71, L75), a detail to port as written.
- A neuron qualifies if it has at least 60 trials in each of the 9 cells (3 progression x 3 colour bins) (L127-153). Trials per cell used, `N_progression`, is the minimum across qualifying neurons of all regions (L156); the paper gives 61. `N_neurons` is the smallest count of qualifying neurons across regions (L157); the paper gives 100.
- 100 bootstrap draws (L160). Each draw: `N_neurons` neurons sampled with replacement (L164-168); for each neuron, progression and colour bin, `N_progression` trials sampled without replacement from that neuron's own session (L171-176). Trials are therefore not aligned across neurons (standard pseudo-population).
- 80/20 split per cell (`cvpartition(N,'Holdout',0.2)`, L178-186), so training and validation trials come from the same blocks.

**Classifier (`Run_belief_classifier_combined_time_prog_restricted_FEF.m`, one job per ROI and draw `n_tt`).**
- Features: mean of the 2 or 3 window rates per neuron (L88-92).
- Three one-versus-rest linear SVMs, one per colour bin; the "other" class is subsampled to equal size (L98-121).
- `fitcsvm`, linear, `OptimizeHyperparameters='auto'`, Bayesian optimisation, expected-improvement-plus, 10-fold CV partition (L123-131). `fitPosterior` turns scores into probabilities (L135).
- `Run_belief_classifier_combined_time_prog_NN_restricted_FEF.m`: a `fitcnet` (defaults) is trained on the three posteriors of the training trials (L102-107) and applied to validation trials per progression level (L117-141). This network output is what the paper reports (Methods). The variant "within" progression trains SVMs and network separately per level (`..._each_prog_restricted_FEF.m` L84-149; `..._each_prog_NN_...`).
- Statistic: for each draw, validation accuracy per progression level (mean of correct over 36 validation trials per level, 12 per colour bin, from the sizes above; to be confirmed when run). `plot_Fig2_ET_pseudo_pop.m` L169-187 gives a 3 x 100 matrix per ROI.

**Significance test (what the main text claims: "all p < 0.01, both across and within progression levels", Fig. 2D).** `plot_Fig2_ET_pseudo_pop.m` L367-378 calls `z_test_function_bootstrap` (L587-594): `z = (mean(acc) - 1/3) / std(acc)` over the 100 draws, `p = 1 - normcdf(z)`. Paper Eq. 21, same formula, with Bonferroni across time points for time series. The spread is draw-to-draw variation of neuron and trial resampling (and of the optimiser). It does not reflect sampling of blocks or sessions. The true-template version (Fig. S3G) uses the same function (`plot_FigS2_true_template_decoding.m` L331-333, L440-447; runner `Run_template_classifier_combined_time_prog_NN_restricted_FEF.m`). I could not read the S3G legend: the PMC full text does not include the supplement.

Variants the authors also ran, to be pre-specified and reported if we reproduce: 4 colour bins, bins rotated by pi/3 (`..._rotated.m`), and removal of neurons with one block in a bin (`..._noOne.m`).

## 4. Dependencies, porting, gate

| Item | MATLAB | Faithful Python port? |
|---|---|---|
| `cvpartition` (holdout, 10-fold), `randsample` | Stats toolbox | Same design; draws cannot match bit for bit. |
| `fitcsvm` linear + `bayesopt` (BoxConstraint, KernelScale) | Stats toolbox | Model yes (`SVC(kernel="linear")`); optimiser no. Replace by a pre-specified search with 10-fold CV. Approximate. |
| `fitPosterior` | Stats toolbox | Sigmoid calibration with CV (sklearn or hand-written). Approximate; check against MATLAB docs. |
| `fitcnet` default | Stats toolbox (R2021a or later) | `MLPClassifier`, one hidden layer, ReLU, L-BFGS, no regularisation is my recollection of the defaults. Verify before use. Approximate. |
| `normcdf` z-test | base | Exact (`scipy.stats.norm.sf`). |
| VBMC, BADS, CircStat, Violinplot | Fig. 1 and plotting | Not needed: beliefs are stored in `Conditions`. |

Toolboxes: Statistics and Machine Learning (and Optimization for the single-neuron `fmincon` fits, not needed here). MATLAB version is not stated in the paper or README. No MATLAB on this machine.

**Seeds.** The analysis scripts set none (`grep` for `rng`, `'seed'`, `'state'` finds only `rng('shuffle')` in three Figure_1 recovery scripts). The authors' draws cannot be matched individually, so the gate has to compare distributions, not draws.

**Possible reproduction gates (names only; none opened).**
1. Counts from the data, deterministic: 17 sessions, 171 blocks (69 monkey B, 102 monkey S), 5-16 templates per session, neurons 492/231/167 (Fig. 2E uses 475/216/146), `N_progression` 61, `N_neurons` 100, mean blocks per bin 3.5/3.7/3.6 (LIP/FEF/LPFC; `check_number_of_blocks_in_bootstraps.m` computes this for the 4-bin variant).
2. Saved result file `Figure_2/plot_figure_2/Figure_2_decoding_accuracy.mat` (3.9 MB, in `Figure_2.zip`): by `Plot_Figure_2_github.m` L3-5 and L80-113 it holds the 3 x 100 accuracy matrices per ROI (`*_mean_classification_net`, `*_mean_classification_net_each_prog`). Gate: our port's 100-draw means and spreads fall within a tolerance fixed before the data are opened (set from Monte Carlo error of 100 draws plus an allowance for the optimiser and network differences). It is a data member of `Figure_2.zip`, not in the `Data.zip` manifest.
3. Reported p < 0.01 for all three regions and three levels under the z-test.

## 5. Were colours assigned at random? Is a block permutation exact?

Quotes from the full text (Methods, Task and behavior):
- "The template color was randomly selected at the start of each block."
- "To increase the likelihood of sampling from all colors during a session, we temporarily penalized the colors near already selected colors during the selection process such that they were less likely to be selected again."
- Fig. 1D legend: "Template color was pseudo-randomly chosen". Methods on drift: "templates were randomly chosen over time".
- Block end: "performance >= 80%/85% for 30 consecutive trials" (monkey B/S), so block length depends on learning.

Blocks: 8 sessions (monkey B, 8.6 +/- 2.7 templates per session) and 9 (monkey S, 11.3 +/- 3.4), 5 to 16 per session, 171 in total. The number of blocks per session and per colour bin is not in the code or the text; it needs `Conditions.rule` and `Conditions.block_nb`, which I did not open. Not determinable at Stage 0.

Exactness for the true template: a permutation of the template colours among the blocks of a session is exact if the real order is a uniform draw from the orderings of the colours used. The penalty rule makes later colours depend on earlier ones, so the order is not strictly exchangeable (its parameters are not in the shared code). The test is then close to exact, not exact. Two ways to handle it: state it, and run a sensitivity version that keeps only permutations the stated rule allows, if the authors give the rule. Block permutation is the right null for the shared-block validation split: block-specific drift that a decoder can use is present in the permuted labels as well.

Smallest attainable p (illustrative, from combinatorics, since the statistic depends only on the bin vector). With b blocks in a session split as evenly as possible over 3 bins, the number of distinct bin assignments is b!/(n1! n2! n3!): b=5 (2,2,1): 30, p_min 0.033; b=8 (3,3,2): 560, 0.0018; b=9: 1,680, 0.0006; b=11 (4,4,3): 11,550, 0.0001; b=16 (6,5,5): 2.0 million. If class relabelling gives identical accuracy, p_min is up to 6 times larger. A per-session p below 0.05 is attainable in every session with at least 5 blocks. These are the values for a session-level test (as in the Fig. 3 analysis); the Fig. 2 decoder pools sessions, so no per-session p exists there. Group level: the joint number of assignments across 17 sessions is about 3.5e58 for the example of 8 sessions with 8 blocks and 9 with 11 blocks, so p_min is set by the number of Monte Carlo permutations P, namely 1/(P+1).

**Estimated template needs a design choice.** The estimated label changes within a block and depends on the monkey's choices and rewards, which depend on the true template. Re-simulating the model under a permuted template is not possible from the stored data. Options for Stage 1 (author decides):
- A. Permute whole-block label sequences of the estimated template among blocks of a session, aligned by progression in block (block lengths differ, 30-306 trials). Keeps the within-block structure and the bin counts per progression level.
- B. Primary test on the true template (exact), and report the estimated-template result only under the original z-test plus A as secondary.
- C. Rotate labels circularly within session (changes the bin balance).
My recommendation: B with A as a pre-specified secondary, reported whatever the result.

Also note for the design: the code recomputes which neurons qualify (at least 60 trials in each of 9 cells) from the labels, so a permutation changes the neuron set and `N_progression`. Fix them from the real labelling (state this) or recompute per permutation.

## 6. Download, compute, risks, recommendation

**Download for the reanalysis.**
- Minimum: 4 window folders of `Data/FR_around_event` (reward_end 0-300 for neuron inclusion and `Conditions`; target -600 to -300, -300 to 0, 0 to 300), 17 sessions each: 119.5 MB.
- Faithful to the authors' NaN handling (all 27 windows): 806.6 MB.
- Optional: behaviour fits `Reset_RW_6_channels_VBMC.mat` per session, 41.2 MB, only if `Conditions.belief` needs checking.
- Gate file `Figure_2_decoding_accuracy.mat`: 3.9 MB.
- Not needed: the 16.5 GB validation file (so the 20.4 GB archive is not required).
All via range requests on `Data.zip` with checked CRC-32; allowed members to be listed in DESIGN.md before any extraction.

**Compute (estimates, not measured).** Authors' per-draw job: 3 SVMs with Bayesian optimisation (default 30 evaluations x 10-fold on a few hundred x 100 matrix), plus a small network, per ROI and variant; 100 draws x 3 ROI x several variants on a cluster. For a permutation null in Python with a fixed-C linear SVM and sigmoid calibration, one draw is about 1-3 s, so P = 1,000 permutations x 10 inner draws x 3 ROI is about 30,000 fits, roughly 10-25 core-hours, a few hours on 8 cores. Memory is small (the data are about 0.1-0.8 GB).

**Main risks.**
1. Port fidelity: optimiser, calibration and network are not replicated bit for bit; the gate is by distribution only, and a threshold must be fixed before data are opened.
2. Estimated-template null needs a design choice (section 5); the exact test applies cleanly only to the true template (Fig. S3G, supplement not in the XML, to be read from the supplement PDF).
3. Colour penalty makes the order not strictly exchangeable.
4. Blocks per bin per session unknown until `Conditions.rule` is opened; some sessions may have a bin with one block, which limits the per-session test.
5. Neuron set depends on labels (at least 60 trials in 9 cells).
6. No seeds, no MATLAB version, and "Restricted_FEF" undefined.
7. Our earlier note says the original z-test is the most liberal type; a changed verdict is possible but not known. The permutation result is a verdict under the block test, not a statement that the paper is wrong.

**Recommendation: GO**, conditional on (i) a design file fixing the primary test (true-template block permutation per ROI at group level, plus a session-level test where b allows), the secondary estimated-template test (option A), the gate tolerance and the report-all commitment, reviewed and stamped before any data member is extracted, and (ii) the download limited to the members above. Reasons: the data needed are about 0.1-0.8 GB, not 20 GB; code for every step of the claim is public and short; the null is available in exact form for the true template; compute is moderate. Do not promise a bit-exact reproduction.
