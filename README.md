# Block permutation tests for decoders when training and test trials share recording blocks

This repository holds the code and the outputs behind the paper "Common decoding tests fail when training and test trials share recording blocks" (preprint: Zenodo, https://doi.org/10.5281/zenodo.24012190).

**In short.** When training and test trials come from the same recording blocks, the permutation rules that decoding toolboxes ship and teach call labels with no information decodable in most tests, and the toolboxes run as shipped call about one in five decodable with one block of each class per run. Permuting the labels of all trials together, block by block, and refitting the decoder stays near the nominal 5% when conditions are assigned to blocks at random. The test is provided as a function in `blockperm/` (`pip install blockperm`), with a two-minute demo that runs in the browser ([Colab](https://colab.research.google.com/github/jinchoi7651507/block-permutation-decoding/blob/main/blockperm/examples/blockperm_demo.ipynb)).

To use the test, see [Using the test](#using-the-test); to check the results, see [How to reproduce](#how-to-reproduce) and `REPRODUCE.md`. First run: `pip install -r requirements/quick-path.txt` (Python 3.12), then `REPRODUCE.md` §1 and §2 (10 to 25 minutes, no data download).

*Archived at https://doi.org/10.5281/zenodo.24008938.*

## What the paper shows

Decoding studies often present conditions in blocks of consecutive trials and draw training and test trials from the same blocks. In a survey of 14 recent open-access studies that decoded block-structured variables from neuronal recordings, all 14 used such a split and 11 assessed significance with a test that ignores the blocks.

We assigned labels with no information to the recording blocks of mouse Neuropixels recordings (30 mice), human resting EEG (38 participants) and simulations calibrated on the mouse data, and ran the significance tests that decoding toolboxes provide. The expected rate is 5%.

- Trial-level permutation (the scikit-learn rule), with shuffled five-fold cross-validation, called 98% of these labels decodable in the mouse recordings and 92% in EEG.
- Permuting labels between whole blocks with the trained decoder held fixed called 84% decodable (top-20 logistic decoder).
- Permuting only the training labels and refitting, the rule in the PyMVPA tutorial, called 99% (mouse) and 94% (EEG) decodable.
- CoSMoMVPA and PyMVPA, run as shipped on simulated recordings with one block of each class per run, called 18–21% decodable.
- Permuting the labels of all trials together, block by block, and refitting the decoder (the block permutation test) called about 5% decodable. Here this is valid, because the labels were assigned to blocks at random.
- With whole blocks held out (mouse, top-20 logistic decoder), the binomial test and trial-level permutation still called about a quarter of the labels decodable (24.4% and 25.6%), and the block permutation test 3.8%.
- In two post hoc analyses, block-design fMRI (Haxby et al. 2001, 6 participants) and wearable-sensor recordings (PAMAP2, 8 participants) gave the same pattern. With shared blocks, trial-level permutation and training-label permutation called 90–100% of the labels decodable (detrended fMRI and sensors), and the block permutation test 8% and 5%.

In the International Brain Laboratory brain-wide recordings (1,359 brain regions analyzed in single sessions, 118 mice), we decoded which side the task's block structure favored. On the real block structure, the scikit-learn rule called 75% of the regions decodable and the pseudosession test (decoders refit on block sequences drawn from the task's own generator) 10%. For 884 regions (65%), only the scikit-learn rule called the block side decodable.

What to do: assign conditions to blocks at random, with several blocks per condition, and test with the block permutation test.

## Using the test

```python
from blockperm import block_permutation_test_score
score, null_scores, p = block_permutation_test_score(pipeline, X, y, blocks=block_id, cv=cv)
```

Install with `pip install ./blockperm` (Python 3.10 or later), or `pip install blockperm` from PyPI, or copy `blockperm/blockperm.py` into a project. A two-minute demo runs in the browser: [open it in Colab](https://colab.research.google.com/github/jinchoi7651507/block-permutation-decoding/blob/main/blockperm/examples/blockperm_demo.ipynb). Put every step that is fitted to the labels (scaling, feature selection, the decoder) in one scikit-learn `Pipeline` and give one block identity per trial. The function permutes the labels of whole blocks, reruns the cross-validation for every permutation and returns the observed score, the null scores and the p value. `blockperm/README.md` explains the arguments, when the test is valid, the smallest attainable p value for few blocks, and the change for each toolbox. `blockperm/docs/TUTORIAL.md` is a step-by-step guide (folds, strata, pseudosessions, few blocks, fixed block orders, checking a pipeline with labels with no information). `blockperm/matlab/` holds a MATLAB and Octave port that takes a function returning the cross-validated score for a label vector. It was not used for any result in this repository; on real EEG its exact null agrees with the Python one to 2.2e-16 (`blockperm/matlab/README.md`).

## Results and where they are reproduced

| Result in the paper | Value | Output | `REPRODUCE.md` |
|---|---|---|---|
| Survey: shared-block splits; trial-level tests | 14 of 14; 11 of 14 | `analyses/practice-survey/SUMMARY.md` | §2 (recount) |
| Fig. 1a, row 1: trial-level permutation | 98% mouse, 92% EEG | `analyses/step2-comparison/results/allen_summary.md`, `analyses/step2b-eeg/results/summary_2b.md` | §2 |
| Fig. 1a, row 2: block permutation, decoder held fixed (post hoc) | 84%; 43–95% across decoders fitted to the labels | `analyses/step1-decomposition/results/results.md` | §2 |
| Fig. 1a, row 3: training labels only, refit | 99% mouse, 94% EEG | as row 1 | §2 |
| Fig. 1a, row 4: block permutation test | near 5% (5.2% mouse, 4.9% EEG, 5.7% simulation) | as row 1; `analyses/step2-comparison/results/sim_summary.md` | §2 |
| Fig. 1b: whole blocks held out (mouse; post hoc) | about a quarter for the binomial test and trial-level permutation (24.4%, 25.6%); 4.9% with the decoder fixed and 3.8% for the block permutation test | `analyses/step1-decomposition/results/results.json` (`new/std6`, `sep24/lr_topk`) | §2 |
| Block permutation test with a fixed block order | 0–2.4% in simulation; 95% and 29% in EEG | `analyses/step2-comparison/results/sim_summary.md`; `analyses/step2b-eeg/results/summary_2b.md` | §2 |
| Fig. 2a: CoSMoMVPA and PyMVPA as shipped (simulation; post hoc) | 18–21%, against 4% | `analyses/step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md` | §2 |
| Group-level tests on shared-block splits | t-test 100%; null built from the block permutation test 4–7% (shared-block splits) | `analyses/step2b-eeg/results/summary_2b.md`, `analyses/step2-comparison/results/allen_summary.md` | §2 |
| Power of the block permutation test; size-adjusted power of the other tests (EEG post hoc) | 7% and 66% (simulation); size-adjusted, simulation: binomial test 7% and 67% against 6% and 62% for the block permutation test, the other tests 5%; EEG 88–93% for the trial-level tests and 57% for training-label permutation, against 85% | `analyses/step2-comparison/results/sim_summary.json` (`power`: power), `analyses/step2-comparison/results/size_adjusted_exact.json` (size-adjusted power), `analyses/step2b-eeg/results/summary_2b.json` | §2 |
| Fig. 2b: IBL, fake block sequences | 70% against 5% | `analyses/step3-ibl/runs/SUMMARY.md` | §2 |
| Fig. 2b: IBL, real block structure | 884 of 1,359 verdicts differ (65%) | as above | §2 |
| Post hoc: block-design fMRI (Haxby et al. 2001) | shared blocks: trial-level permutation 90%, training-label permutation 91%, block permutation test 8% (detrended) | `analyses/step4-fmri-haxby/results/summary.md` | §2 |
| Post hoc: wearable sensors (PAMAP2) | shared blocks: 100%, 100%, 5% | `analyses/step5-pamap2/results/summary.md` | §2 |
| GroupKFold fold map differs between platforms (post hoc) | 800 of 800 p values match with the x86 map | `analyses/foldmap/REPLICATE-CHECK.md` | §2 |

Every number in the paper is traced to a file and key in `NUMBERS.md`.

## Reanalyses of published studies

| Study | Design | Result of the primary test | Output | `REPRODUCE.md` |
|---|---|---|---|---|
| Template decoding, macaque LIP, FEF and LPFC (Jahn et al. 2024, *Cell*; 17 sessions, 171 blocks, template drawn at random per block) | block permutation test, true template, 900 ms window, Holm over three regions | the reproduction check (gate) matched the published Fig. 2D accuracy and z-test; trial-level permutation at its smallest p; under the block permutation test, which assumes that blocks are exchangeable with the color-selection penalty and the performance-based block ends unmodeled, template decoding not established in any region (Holm 0.64, 0.48, 0.64); limited power (a mean of 3 to 4 blocks per bin) and not evidence of absence | `analyses/step6-reanalysis-cell/vm-out-a2/summary.md`, `vm-out-a2/note_tables.out` | §3 |
| Context decoding, mouse dorsolateral striatum (Klee et al. 2026, *Science Advances*; 6 mice, fixed order cued, self-paced, repeated three times) | group block permutation test, intertrial (ITI) and peri-movement (PERI) windows | under the block permutation test, which rests on an exchangeability model because the order was fixed, context decoding is above the block-arrangement null in both windows (p = 1.5e-05 and 6e-06); with a fixed order this cannot exclude slow drift | `analyses/step6b-reanalysis-sciadv/out/SUMMARY.md` | §3 |

### Extended Data, Supplementary Information and figures

| Item | Content | Source (in `analyses/` unless stated) |
|---|---|---|
| Figs 1, 2a, 2b; Extended Data Figs 1–10 | the plotted values and the scripts that draw them | `figures/` (`figures_values.txt`; `REPRODUCE.md` §2) |
| Extended Data Fig. 1 | decoders and splits in the mouse recordings | `step1-decomposition/results/results.md`, `within_train.md` |
| Extended Data Fig. 2 | real drifting-grating trials | `step1-decomposition/results/results.md` (`dg_*`), `step2-comparison/results/allen_summary.md` (`dg_shared24`) |
| Extended Data Fig. 3 | group-level tests | `step2b-eeg/results/summary_2b.md`, `step2-comparison/results/allen_summary.md` (group-level column) |
| Extended Data Fig. 4 | simulation grid | `step2-comparison/results/sim_summary.md` |
| Extended Data Fig. 5 | toolboxes in all layouts; agreement gate | `step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md`; gate result `runs_add3/tools/gate/GATE-RESULT.json` inside `runs_add3.tgz` |
| Extended Data Figs 6, 7 | IBL: all rows, region counts (134 regions with at least three sessions), positive control | `step3-ibl/runs/SUMMARY.md` |
| Extended Data Fig. 8a, b | reanalyses of Jahn et al. (2024) and Klee et al. (2026) | `step6-reanalysis-cell/vm-out-a2/` (`a2-out.tgz`, `summary.md`), `step6b-reanalysis-sciadv/out/` (`tests.json`, `SUMMARY.md`) |
| Extended Data Fig. 9 | fixed block orders | `step2-comparison/results/sim_summary.md`, `add3_summary.md`; `step2b-eeg/results/summary_2b.md` |
| Extended Data Fig. 10 | power and size-adjusted power (EEG graded control post hoc) | `step2-comparison/results/sim_summary.json` (`power`: power), `step2-comparison/results/size_adjusted_exact.json` (size-adjusted power), `step2b-eeg/results/summary_2b.json` (`size_adjusted_power_pos_graded`) |
| Supplementary Note 1 | the earlier mouse analysis (outputs only) | `trackA-std/results/results.json` (rerun), `trackA-std/first-run/results/results.json` (first run) |
| Supplementary Note 2, Table 2 | practice survey | `practice-survey/` (`SUMMARY.md`, `coding_final.csv`, `random-assignment-coding.csv` (random assignment of the decoded condition; post hoc), `AUDIT-AUTO-EXCLUSIONS.md`) |
| Supplementary Note 3 | alpha-power slope over the EEG session (post hoc) | `step2b-eeg/results/alpha_slope.json` |
| Supplementary Note 4, Table 3 | runs with one class; the two platforms | `step2-comparison/results/sim_summary.json` (cell c000), `step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md`, `step2b-eeg/results/summary_2b.json`, `step2-comparison/equiv/EQUIV-PLATFORM.txt`; `foldmap/` |
| Supplementary Note 5, Table 4 | predicted false-positive rate of the binomial test | `step1-decomposition/results/results.md` (block-number sweep) |
| Supplementary Note 6, Table 5 | the tests against established methods | the cells above |
| Supplementary Note 7, Table 6 | block-design fMRI and wearable sensors (post hoc) | `step4-fmri-haxby/results/summary.md`, `step5-pamap2/results/summary.md` |
| Supplementary Table 1 | changes made during the analyses, with dates | run logs inside the run archives; `trackA-std/RERUN.md`; `step6-reanalysis-cell/gate-run1.log`; `step6b-reanalysis-sciadv/out/gate-fixes/` |

### Names used in the files

| Name | Meaning in the paper |
|---|---|
| P1, P2, P3, P4, P5 | binomial test; trial-level permutation with refit (scikit-learn); trial-level permutation within runs (CoSMoMVPA tutorial); training labels permuted, refit (PyMVPA tutorial); the block permutation test |
| `S-main` / `main`, `S-tool` / `tool`, `S-block` / `block` | shuffled five-fold cross-validation; scikit-learn's default unshuffled stratified five-fold; group k-fold by block (whole blocks held out: five folds, four in EEG and in simulations with four blocks; in fMRI and the sensor data, fold = block index modulo 5 or 4) |
| `shared24`, `half24`, `paired24`, `iid`, `segment` (step 1) | labels on 24 blocks shared by training and test trials; the same with calibration trials from the first half of each block and held-out trials from the second half; separate blocks whose held-out labels copy calibration labels; labels varying trial by trial; first half of the session against the second (12 blocks) |
| `sep24` | step 1: calibration and held-out trials from separate blocks with independent labels; in step 2 the Allen scheme `sep24` is crossed with the splits, and only `sep24/pair` reproduces the step 1 separation |
| `nosel0`, `nosel`, `rank`, `sel`, `lr_topk`, `lr_all` (step 1 decoders) | two random pools without label use; the same pools with the class mapping; units ranked by d′ and cut at half; the cut chosen on calibration trials; logistic decoder on the 20 best units (Fig. 1a, row 2; Fig. 1b); logistic decoder on all units |
| `binom`, `trl_rerun`, `trl_fixed`, `blk_fixed`, `blk_rerun`, `trn_trl`, `trn_blk`, `circ_rerun` (step 1 tests) | binomial test; trial-level permutation with refit or with the decoder fixed; block permutation with the decoder fixed (Fig. 1a, row 2); block permutation with refit (the block permutation test); training labels permuted, trial or block form (Extended Data Fig. 1b); circular shift |
| `L1`–`L4` (toolboxes) | random 12-block design in runs of three; fixed AABB order; labels varying trial by trial without drift; runs of two blocks, one per class (Fig. 2a) |
| `PS-refit`, `PS-fixed`, `SEL-repeat`, `SEL-fixed`, `IID-*`, `*-block` (step 3) | the pseudosession test; pseudosessions with the decoder fixed; units reselected or kept fixed in every pseudosession; labels varying trial by trial; whole blocks held out |
| region-session | one brain region analyzed in one session (1,359 in all) |
| `detrended`, `raw`; `windows2s` (steps 4, 5) | fMRI with linear detrending and z-scoring within runs, or without preprocessing; 2-s windows of the sensor recordings |
| `run` split (step 4) | leave one run out, the split of the PyMVPA and CoSMoMVPA tutorials |
| `pos_face_house`, `pos_delta0.5`, `pos_delta1.0` (steps 4, 5) | positive controls: faces against houses; a signal of 0.5 or 1.0 standard deviations added to six features |
| `C1`–`C5` (survey) | coded items: split, test, decoder in the null, unit selection, code availability |
| `E4`, `E5`; `F`, `V`, `S`; `M`, `R` | primary contrasts of steps 4–5; of step 3 (fake labels, real labels, unit selection); of step 2 (simulation, mouse) |
| `balanced`, `fixed_half`, `fixed_aabb`, `fixed_abba`, `cleaned_s5`, `pos_graded`, `balanced_graded`, `N5`, `rerun49` (step 2b) | EEG arms: random balanced labels; fixed orders (halves, AABB in runs of four blocks, ABBA); the main preprocessing; the post hoc graded control and its noise rule; the rerun of worker 49 |
| `new` (Allen summaries) | the 30 mice other than the two on which the earlier analysis was developed |
| `dg_*`, `shared`, `sep` (step 1) | drifting-grating trials; shared or separate blocks without the 24-block suffix |
| `G1`–`G4` (step 2), `G1`–`G11` (step 6) | the toolbox agreement gates; the items of the step 6 reproduction check (gate) (`vm-out-a2/summary.md`; G10 and G11 in `out-a2/gate.json`, key `extra`, inside `vm-out-a2/a2-out.tgz`) |
| `arm`, `prep`, `fake` (steps 4, 5) | summary columns: fake labels or a positive control; preprocessing |
| `add3`, `trackA` | the further simulation and toolbox cells of step 2; the earlier mouse analysis (`trackA-std/`) |
| `Q1`, `Q2`, `Q3` (steps 2, 3) | step 3: fake labels, real block side, unit selection; step 2: Q3 is the negative control with labels varying trial by trial |
| `8t2`, `16t4`; `cond_pass`, `pred_ho`, `pred_xfit`; `spec`; `E`; `ec_only`, `eo_only`, `long120`, `pos_full` | step 1: four blocks per epoch shortened to 35 s or 17 s; exact rate, formula, formula from training blocks (Supplementary Note 5); specificity null of the earlier mouse analysis; step 2b primary contrast; EEG labels within one eye state, 120-s blocks, eyes closed against open |
| `c000`, `a000`–`a063` | primary simulation cell; the further simulation cells (`add3_summary.md`) |
| `gate/` (step 2), `runs_add3/tools/gate/` | the pipeline gate (the F-test decoder against the top-20 decoder, Methods); the toolbox agreement gates G1–G4 (inside `runs_add3.tgz`) |
| `P1`, `P2`, `P3`, `C` (keys of `trackA-std/results/results.json` and `first-run/results/results.json`) | the earlier mouse analysis (Supplementary Note 1; not the rule names P1–P5): best split of preference-ranked units against random splits selected the same way; logistic decoder on the top-ranked units against the same search on random orderings; label shuffle within halves with the selection rerun; labels with no information on blocks (`random_blocks`: `q2_p` held-out binomial test, `block_p` block shuffle) |
| `P1`–`P7`, `secondary (c)`, `(d)`, `(f)`, `as_written` (step 6, `vm-out-a2/summary.md`) | the expected outcomes of the step 6 analysis, each marked held or not held with the quantity that decides it (not the rule names P1–P5); the secondary tests (trial-level permutation, the estimated template, the adjacent-pair restriction); the port variant that follows the authors' code as written |
| `std6` (step 1) | the six standard visual areas (VISp, VISl, VISal, VISrl, VISam, VISpm) |
| `pos_dg24`, `pair` (step 2 mouse cells) | positive control on real drifting gratings (0 against 90 degrees); the step 1 pair split (training on the calibration blocks of each pair, testing on the held-out blocks) |
| `main`, `kall`, `lda`, `nogamma`; `cleaned_s2`, `minimal_s5` (step 2b) | decoders: the F-test pipeline with 20 features; the same with all features; linear discriminant analysis without selection; the main pipeline without the 30–45 Hz features; two further preprocessing variants of the sensitivity arm |
| `rate A`, `rate B`, `minus P5 survivors`, `minus P5 all`, `minus L3`, `P3 port`, `P4 port`, `zscore`, `chunks`, `p_mc`, `(headline)` (`SUMMARY-TOOLS.md`) | rate over the replicates where the tool ran; rate over all replicates with errors counted as non-rejections; difference from the block permutation test on the same replicates, over those where the tool ran or over all; difference from the same row in layout L3; our re-implementations of the CoSMoMVPA and PyMVPA rules; features z-scored within runs; PyMVPA's option that permutes whole blocks; p from the tool's null as (1 + count at or above) / (draws + 1); the rows of Fig. 2a |
| `Pipeline A`, `Pipeline B` (`step2-comparison/gate/GATE-RESULT.md`) | the step 2 pipeline with selection by |d′|; with selection by an F test (the one used) |
| `P1−base`, `P4−base` (`sim_summary.md`) | the rate minus the rate of the same block number and split with labels varying trial by trial and no drift |
| `S1_ITI`, `S1_PERI`, `S2` (step 6b, `out/SUMMARY.md`) | training on two of the three cued and self-paced pairs and testing on the third, in the intertrial and peri-movement windows; the intertrial window restricted to trials whose previous hit was at least 5 s earlier |

## How to reproduce

Install the quick-path environment first (`pip install -r requirements/quick-path.txt`, Python 3.12). Then rebuild every summary and figure from the shipped files and compare them with the shipped ones (`REPRODUCE.md` §2, 10 to 25 minutes depending on the machine). Full runs need the public data; the simulation grid, the toolboxes, the EEG analysis and the IBL analysis each ran on one cloud machine for 5 to 14 hours (`REPRODUCE.md` §3). Versions and machines are in `ENVIRONMENT.md`.

## Repository layout

| Path | What |
|---|---|
| `blockperm/` | The block permutation test as a function, with tests, an example, a tutorial (`docs/`) and a MATLAB and Octave port with its checks (`matlab/`). |
| `figures/` | Scripts that draw every figure from `analyses/`, the plotted values and the PDFs. |
| `requirements/` | Pinned package versions of each environment, from the `pip freeze` recorded with each run. |
| `analyses/step1-decomposition/` | Mouse recordings with labels assigned to blocks: trial-level tests, fixed and refitted decoders, training-label permutation (Fig. 1a, row 2; Fig. 1b). |
| `analyses/step2-comparison/` | Simulation grid, mouse cells and the toolboxes as shipped (Fig. 1 for the mouse and the simulation; Fig. 2a). The toolbox excerpts are in `toolbox-src/` (`THIRD-PARTY.md`); the toolbox machine set-up in `gcp/`. |
| `analyses/step2b-eeg/` | The same tests on MPI LEMON resting EEG (Fig. 1, EEG); cloud set-up in `gcp/`. |
| `analyses/step3-ibl/` | The IBL brain-wide map (Fig. 2b). |
| `analyses/trackA-std/` | The earlier mouse analysis that step 1 builds on: session list, the outputs of its first run (`first-run/`) and of the rerun (`results/`, `RERUN.md`). |
| `analyses/foldmap/` | Platform check of scikit-learn's `GroupKFold` fold map. |
| `analyses/practice-survey/` | Search, screening and coding of the survey (full texts not redistributed). |
| `analyses/step4-fmri-haxby/` | Post hoc: the same tests on block-design fMRI (Haxby et al. 2001, the PyMVPA tutorial data); code, rows and summary (Supplementary Note 7). |
| `analyses/step5-pamap2/` | Post hoc: the same tests on wearable-sensor recordings (PAMAP2); code, rows and summary; shares the step 4 engine, summary script and synthetic checks (Supplementary Note 7). |
| `analyses/step6-reanalysis-cell/` | Reanalysis of template decoding in Jahn et al. (2024): code, gate, outputs. The authors' code is not copied (`REPRODUCE.md` §3). `vm-out/`: the first run, stopped at the reproduction check (gate); `vm-out-a2/`: the reported run; `vm-out-a3/`: the run that added two descriptive quantities (post hoc): sessions and neurons per labeling, and the true-template z-test. |
| `analyses/step6b-reanalysis-sciadv/` | Reanalysis of context decoding in Klee et al. (2026): code, gate, outputs. The authors' code is not copied. |
| `REPRODUCE.md`, `ENVIRONMENT.md`, `NUMBERS.md`, `PROVENANCE.md` | Steps with expected outputs and runtimes; versions and machines; the source of every number; the origin of the files and the path placeholders. |
| `THIRD-PARTY.md`, `LICENSES/` | Origin and licenses of the toolbox excerpts. |

The folders `step1-decomposition` to `step3-ibl` each hold code (`code/`) and outputs (`results/` or `runs/`). The run rows of steps 2, 2b and 3 are shipped as archives (`*.tgz` with a hash file). `runs_pilot.tgz` and `runs_prep.tgz` in step 3 hold the timing pilot and the preparation records. Other files:

| Path (in `analyses/`) | What |
|---|---|
| `step1-decomposition/runs/` | run start records, logs and rows |
| `step2-comparison/calib/`, `calib_v2/`, `calib_run.log`, `calib_v2_run.log` | calibration of the simulator on the mouse spontaneous activity; the simulations use v2 (`calib_v2/CALIBRATION_v2-NOTE.md`) |
| `step2-comparison/pilot/`, `validate/`, `validate_run.log`, `gate/`, `equiv/` | timing pilot of the grid; validation of the grid runner before the main run; the pipeline gate (the F-test decoder against the top-20 decoder); the comparison of the laptop and cloud runs (Supplementary Note 4) |
| `step2-comparison/runs/CELLS.json`, `runs_add3/CELLS-ADD3.json` | the lists of simulation cells |
| `step2b-eeg/eligibility/` | participant eligibility and the seeded draw (`SUBJECTS.txt`, replacement orders, pilot and equivalence subjects, `lemon_eligibility.json`, BrainVision marker files, data-terms check, download and run logs) |
| `step2b-eeg/runs/` | preprocessing records and feature manifest, the graded-control pilots, and the laptop-cloud equivalence check (`EQUIV-2b.txt`) |
| `step3-ibl/budget/`, `pilot-attempt-2/runs/BUDGET-META.json` | the price and exchange-rate records and the timing-pilot input behind the cost limit of the IBL run (Supplementary Table 1) |
| `step3-ibl/meta/region_info.csv` | pinned copy of the brain-wide map region table, with its SHA-256 |
| `step6-reanalysis-cell/` (files outside `code/` and `vm-out*/`) | checks of the shared files and of the fetch script (`a2-gatefile-check.out`, `fetch-refusal-check.out`); the gate log (`gate-run1.log`); the output of `code/test_run_cell_a3.py` (`test_run_cell_a3.out`); Zenodo member lists (`*.tsv`); `authors-code/FETCHED.txt`; `note_tables.py`, which prints `vm-out-a2/note_tables.out` and `vm-out-a3/note_tables.out` |
| `step6b-reanalysis-sciadv/out/gate-fixes/` | the two fixes of the port (Supplementary Table 1) |
| `step6b-reanalysis-sciadv/out/gate-runs/`, `out/fields.txt`, `out/tests.partial.json` | a copy of every gate run; the fields found in the data members; the resume file of the test stage |
| `step6-reanalysis-cell/code/run_data_a2.sh`, `run_data_a3.sh`, `run_data_a3b.sh` | the scripts that ran `run_cell_a2.py` and `run_cell_a3.py` on the cloud machine |
| `step2-comparison/gcp/requirements-step2.txt`, `step2b-eeg/gcp/requirements-2b.txt` | the packages installed on the cloud machines (the same as `requirements/step2-cloud.txt` and `step2b-cloud.txt`) |
| `foldmap/replicate_x86_rows/` | the rows of the x86 rerun of the replicate check, as an archive (`rows.tgz`) and unpacked (`rows/`), with its log and package versions |
| `foldmap/replicate_laptop_x86map_rows/` | the rows of the laptop rerun of the replicate check with the x86 fold map passed as explicit folds |

## Data

No recordings are redistributed. Allen Brain Observatory Visual Coding Neuropixels (32 sessions; registry.opendata.aws/allen-brain-observatory) and MPI LEMON (resting EEG; fcon_1000.projects.nitrc.org/indi/retro/MPI_LEMON.html) are downloaded by the scripts in `analyses/trackA-std/code/` and `analyses/step2b-eeg/code/`; the data of the two reanalyses are on Zenodo (Jahn et al. 2024, 10.5281/zenodo.10529801, 0.8 GB of listed members; Klee et al. 2026, 10.5281/zenodo.16333867, a 3.57 GB archive); `REPRODUCE.md` §3 gives the commands that compare the downloaded files with the shipped manifests. The International Brain Laboratory data are read through the ONE API from the public server, Brain-Wide Map release `2023_12_bwm_release`, with the session list in `analyses/step3-ibl/runs/ORDER.json`. The fMRI data of Haxby et al. (2001), as distributed with PyMVPA (http://data.pymvpa.org/datasets/haxby2001), and PAMAP2 (UCI Machine Learning Repository, 10.24432/C5NW2H, CC BY 4.0) are downloaded by `analyses/step4-fmri-haxby/code/fetch_haxby.py` (checked against the server's MD5 sums) and `analyses/step5-pamap2/code/fetch_pamap2.py`; their manifests are in each step's `runs/`. The three main datasets take about 80 GB (Allen), 13 GB (LEMON) and 96 GB (IBL); the two post hoc datasets take 1.8 GB (Haxby et al.) and 0.7 GB (PAMAP2) as archives.

## Licenses

Our code is released under the MIT license (`LICENSE`). The toolbox excerpts keep their own licenses (`THIRD-PARTY.md`, texts in `LICENSES/`). Data remain under the terms of their providers.
