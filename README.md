*First timestamp: Bitcoin block 971261 (2026-10-13 15:18 UTC), for `analyses/trackA-std/PREREG-trackA.md`, before any new mouse session was downloaded. Check all 17 proofs with `python prereg/ots_verify_public.py $(find analyses -name '*.ots')`. Copied on 2026-11-06 from the authors' working repository. Archived at https://doi.org/10.5281/zenodo.24008938. Timestamped files are byte-identical, and `PROVENANCE.md` lists the changes to other files.*

# Block permutation tests for decoders when training and test trials share recording blocks

This repository holds the code, the timestamped designs and the outputs behind the preprint "Common decoding tests fail when training and test trials share recording blocks" (preprint to be posted within days). Nothing here has been peer reviewed yet.

**In short.** When training and test trials come from the same recording blocks, the permutation rules that decoding toolboxes ship and teach call labels that carry no information decodable in most tests, and the toolboxes run as shipped call about one in five decodable in balanced runs. Permuting the labels of all trials together, block by block, and refitting the decoder keeps the nominal 5% when conditions are assigned to blocks at random. The test is provided as a function in `blockperm/`.

## What the paper shows

Decoding studies often present conditions in blocks of consecutive trials and draw training and test trials from the same blocks. In a survey of 14 recent open-access studies that decoded block-structured variables from neuronal recordings, all 14 used such a split and 11 assessed significance with a test that treats trials as independent.

We assigned labels that carry no information to the recording blocks of mouse Neuropixels recordings (30 mice), human resting EEG (38 participants) and simulations calibrated on the mouse data, and ran the significance tests that decoding toolboxes provide. The expected rate is 5%.

- Trial-level permutation (the scikit-learn rule), with shuffled five-fold cross-validation, called 98% of these labels decodable in the mouse recordings and 92% in EEG.
- Permuting labels between whole blocks with the trained decoder held fixed called 84% decodable (top-20 logistic decoder).
- Permuting only the training labels and refitting, the rule in the PyMVPA tutorial, called 99% (mouse) and 94% (EEG) decodable.
- CoSMoMVPA and PyMVPA, run as shipped on simulated recordings, called 18–21% decodable.
- Permuting the labels of all trials together, block by block, and refitting the decoder called 5% decodable. Here this is exact, because the labels were assigned to blocks at random.
- In two post hoc analyses, block-design fMRI (Haxby et al. 2001, 6 participants) and body-worn sensor recordings (PAMAP2, 8 participants) gave the same pattern. With shared blocks, the trial-level and training-label rules called 90–100% of the labels decodable (detrended fMRI and sensors), and the block permutation test 8% and 5%.

In the International Brain Laboratory brain-wide recordings (1,359 brain regions analyzed in single sessions, 118 mice), we decoded which side the task's block structure favored. On the real block structure, the scikit-learn rule called 75% of the regions decodable and the pseudosession test (decoders refit on block sequences drawn from the task's own generator) 10%. For 884 regions (65%), only the scikit-learn rule called the block side decodable.

What to do: assign conditions to blocks at random, with several blocks per condition, and test with the block permutation test.

## Using the test

```python
from blockperm import block_permutation_test_score
score, null_scores, p = block_permutation_test_score(pipeline, X, y, blocks=block_id, cv=cv)
```

Install with `pip install ./blockperm` (Python 3.12), or copy `blockperm/blockperm.py` into a project. Put every step that is fitted to the labels (scaling, feature selection, the decoder) in one scikit-learn `Pipeline` and give one block identity per trial. The function permutes the labels of whole blocks, reruns the cross-validation for every permutation and returns the observed score, the null scores and the p value. `blockperm/README.md` explains the arguments, when the test is valid, the smallest attainable p value for few blocks, and the change for each toolbox.

## Results and where they are reproduced

| Result in the paper | Value | Status | Output | `REPRODUCE.md` |
|---|---|---|---|---|
| Survey: shared-block splits; trial-level tests | 14 of 14; 11 of 14 | protocol committed before the search | `analyses/practice-survey/SUMMARY.md` | §2 (recount) |
| Fig. 1, row 1: trial-level permutation | 98% mouse, 92% EEG | specified in advance | `analyses/step2-comparison/results/allen_summary.md`, `analyses/step2b-eeg/results/summary_2b.md` | §2 |
| Fig. 1, row 2: block permutation, decoder held fixed | 84%; 43–95% across decoders fitted to the labels | post hoc (designed after the Track A results); run started 9 min before its block, no result read before it | `analyses/step1-decomposition/results/results.md` | §2 |
| Extended Data Fig. 3: published rat data, block permutation with the unit selection fixed or repeated | null mean 0.001 (fixed) against 0.115 (repeated); observed 0.337 | post hoc | `analyses/yaron-panel/RESULTS-NOTE.md` | §2 |
| Fig. 1, row 3: training labels only, refit | 99% mouse, 94% EEG | specified in advance | as row 1 | §2 |
| Fig. 1, row 4: block permutation test | 5% (mouse, EEG, simulation) | specified in advance | as row 1; `analyses/step2-comparison/results/sim_summary.md` | §2 |
| Block permutation test with a fixed block order | 0–2.4% in simulation; 95% and 29% in EEG | specified in advance | `analyses/step2-comparison/RESULTS-NOTE.md` §1, `analyses/step2b-eeg/RESULTS-NOTE.md` §2 | §2 |
| Fig. 2a: CoSMoMVPA and PyMVPA as shipped (simulation) | 18–21%, against 4% | added after the main design (addendum 3, post hoc); one replicate of one cell was seen before it was stamped | `analyses/step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md` | §2 |
| Group-level tests on shared-block splits | t-test 100%; null built from the block permutation test 4–7% (shared-block splits) | specified in advance | `analyses/step2b-eeg/RESULTS-NOTE.md` §3, `analyses/step2-comparison/RESULTS-NOTE.md` §3 | §2 |
| Power of the block permutation test; size-adjusted power of the other tests | 7% and 66% (simulation); EEG 88–93% for the trial-level tests and 57% for training-label permutation, against 85% | specified in advance; EEG post hoc | `analyses/step2-comparison/RESULTS-NOTE.md` §2, `analyses/step2b-eeg/RESULTS-NOTE.md` §4 | §2 |
| Fig. 2b: IBL, fake block sequences | 70% against 5% | specified in advance | `analyses/step3-ibl/runs/SUMMARY.md` | §2 |
| Fig. 2b: IBL, real block structure | 884 of 1,359 verdicts differ (65%) | specified in advance | as above | §2 |
| Post hoc: block-design fMRI (Haxby et al. 2001) | shared blocks: trial-level permutation 90%, training-label permutation 91%, block permutation test 8% (detrended) | post hoc; design timestamped before the download | `analyses/step4-fmri-haxby/RESULTS-NOTE.md`, `results/summary.md` | §2 |
| Post hoc: body-worn sensors (PAMAP2) | shared blocks: 100%, 100%, 5% | post hoc; design timestamped before the download | `analyses/step5-pamap2/RESULTS-NOTE.md`, `results/summary.md` | §2 |
| GroupKFold fold map differs between platforms | 800 of 800 p values match with the x86 map | post hoc check | `analyses/foldmap/REPLICATE-CHECK.md` | §2 |

Every number in the paper is traced to a file and key in `NUMBERS.md`.

### Extended Data, Supplementary Information and figures

| Item | Content | Source (in `analyses/` unless stated) |
|---|---|---|
| Figs 1, 2a, 2b; Extended Data Figs 1–10 | the plotted values and the scripts that draw them | `figures/` (`figures_values.txt`; `REPRODUCE.md` §2) |
| Extended Data Fig. 1 | real drifting-grating trials | `step1-decomposition/results/results.md` (`dg_*`), `step2-comparison/results/allen_summary.md` (`dg_shared24`) |
| Extended Data Fig. 2 | decoders and splits in the mouse recordings | `step1-decomposition/results/results.md`, `within_train.md` |
| Extended Data Fig. 3 | rat recordings, unit selection fixed or repeated (post hoc) | `yaron-panel/results/fixed_vs_repeated.json`, `yaron-panel/RESULTS-NOTE.md` |
| Extended Data Fig. 4 | simulation grid | `step2-comparison/results/sim_summary.md` |
| Extended Data Fig. 5 | fixed block orders | `step2-comparison/results/sim_summary.md`, `add3_summary.md`; `step2b-eeg/results/summary_2b.md` |
| Extended Data Fig. 6 | toolboxes in all layouts; agreement gate | `step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md`; gate result `runs_add3/tools/gate/GATE-RESULT.json` inside `runs_add3.tgz`; `step2-comparison/RESULTS-NOTE.md` §5 |
| Extended Data Fig. 7 | group-level tests | `step2b-eeg/RESULTS-NOTE.md` §3, `step2-comparison/RESULTS-NOTE.md` §3 |
| Extended Data Figs 8, 9 | IBL: all rows, region counts (134 regions with at least three sessions), positive control | `step3-ibl/runs/SUMMARY.md`, `step3-ibl/RESULTS-NOTE.md` |
| Extended Data Fig. 10 | power and size-adjusted power (EEG graded control post hoc; the pre-specified first graded control did not reach its target range) | `step2-comparison/RESULTS-NOTE.md` §2, `step2b-eeg/RESULTS-NOTE.md` §4 |
| Supplementary Note 1 | the earlier pre-registered mouse analysis (outputs only) | `trackA-std/results/results.md`, `trackA-std/prereg-run/results/` |
| Supplementary Note 2, Table 2 | practice survey | `practice-survey/` (`SUMMARY.md`, `coding_final.csv`, `AUDIT-AUTO-EXCLUSIONS.md`, `final-check-2026-11-02/`, `final-check-2026-11-04/`) |
| Supplementary Note 3 | alpha-power slope over the EEG session (post hoc) | `step2b-eeg/RESULTS-NOTE.md` §6, `step2b-eeg/results/alpha_slope.json` |
| Supplementary Note 4, Table 3 | runs with one class; the two platforms | `step2-comparison/RESULTS-NOTE.md` §1, §5, §6; `foldmap/` |
| Supplementary Note 5, Table 4 | predicted false-positive rate of the binomial test | `step1-decomposition/results/results.md` (block-number sweep), `step1-decomposition/RESULTS-NOTE.md` (P-D) |
| Supplementary Note 6, Table 5 | the tests against established methods | the cells above |
| Supplementary Note 7, Table 6 | block-design fMRI and body-worn sensors (post hoc) | `step4-fmri-haxby/`, `step5-pamap2/` (`RESULTS-NOTE.md`, `results/summary.md`) |
| Supplementary Table 1 | timestamp proofs, run starts, deviations | `prereg/README.md` |

### Names used in the files

| Name | Meaning in the paper |
|---|---|
| P1, P2, P3, P4, P5 | binomial test; trial-level permutation with refit (scikit-learn); trial-level permutation within runs (CoSMoMVPA tutorial); training labels permuted, refit (PyMVPA tutorial); the block permutation test |
| `S-main` / `main`, `S-tool` / `tool`, `S-block` / `block` | shuffled five-fold cross-validation; scikit-learn's default unshuffled stratified five-fold; group five-fold by block (whole blocks held out) |
| `shared24`, `half24`, `paired24`, `iid`, `segment` (step 1) | labels on 24 blocks shared by training and test trials; the same with calibration trials from the first half of each block and held-out trials from the second half; separate blocks whose held-out labels copy calibration labels; labels varying trial by trial; first half of the session against the second (12 blocks) |
| `sep24` | step 1: calibration and held-out trials from separate blocks with independent labels; in step 2 the Allen scheme `sep24` is crossed with the splits, and only `sep24/pair` reproduces the step 1 separation |
| `nosel0`, `nosel`, `rank`, `sel`, `lr_topk`, `lr_all` (step 1 decoders) | two random pools without label use; the same pools with the class mapping; units ranked by d′ and cut at half; the cut chosen on calibration trials; logistic decoder on the 20 best units (Fig. 1, row 2); logistic decoder on all units |
| `binom`, `trl_rerun`, `trl_fixed`, `blk_fixed`, `blk_rerun`, `trn_trl`, `trn_blk`, `circ_rerun` (step 1 tests) | binomial test; trial-level permutation with refit or with the decoder fixed; block permutation with the decoder fixed (Fig. 1, row 2); block permutation with refit (the block permutation test); training labels permuted, trial or block form (Fig. 1, row 3); circular shift |
| `L1`–`L4` (toolboxes) | random 12-block design in runs of three; fixed AABB order; labels varying trial by trial without drift; runs of two blocks, one per class (Fig. 2a) |
| `PS-refit`, `PS-fixed`, `SEL-repeat`, `SEL-fixed`, `IID-*`, `*-block` (step 3) | the pseudosession test; pseudosessions with the decoder fixed; units reselected or kept fixed in every pseudosession; labels varying trial by trial; whole blocks held out |
| region-session | one brain region analyzed in one session (1,359 in all) |
| `detrended`, `raw`; `windows2s` (steps 4, 5) | fMRI with linear detrending and z-scoring within runs, or without preprocessing; 2-s windows of the sensor recordings |
| `run` split (step 4) | leave one run out, the split of the PyMVPA and CoSMoMVPA tutorials |
| `pos_face_house`, `pos_delta0.5`, `pos_delta1.0` (steps 4, 5) | positive controls: faces against houses; a signal of 0.5 or 1.0 standard deviations added to six features |
| `C1`–`C5` (survey) | coded items: split, test, decoder in the null, unit selection, code availability |
| `E4`, `E5`; `F`, `V`, `S`; `M`, `R` | primary contrasts of steps 4–5; of step 3 (fake labels, real labels, unit selection); of step 2 (simulation, mouse) |
| `balanced`, `fixed_half`, `fixed_aabb`, `fixed_abba`, `cleaned_s5`, `pos_graded`, `balanced_graded`, `N5`, `rerun49` (step 2b) | EEG arms: random balanced labels; fixed orders (halves, AABB in runs of four blocks, ABBA); the main preprocessing; the post hoc graded control and its noise rule; the reviewed rerun of worker 49 |
| `new` (Allen summaries) | the 30 mice other than the two of the original study |
| `dg_*`, `shared`, `sep` (step 1) | drifting-grating trials; shared or separate blocks without the 24-block suffix |
| `G1`–`G4`, `P-D` | toolbox agreement gates; the step 1 prediction tested in Supplementary Note 5 |
| `arm`, `prep`, `fake` (steps 4, 5) | summary columns: fake labels or a positive control; preprocessing |
| `add3`, Track A | addendum 3 of step 2; the earlier pre-registered mouse analysis (`trackA-std/`) |
| `Q1`, `Q2`, `Q3` (steps 2, 3) | step 3: fake labels, real block side, unit selection; step 2: Q3 is the negative control with labels varying trial by trial |
| `8t2`, `16t4`; `cond_pass`, `pred_ho`, `pred_xfit`; `spec`; `E`; `ec_only`, `eo_only`, `long120`, `pos_full` | step 1: four blocks per epoch shortened to 35 s or 17 s; exact rate, formula, formula from training blocks (Supplementary Note 5); Track A specificity null; step 2b primary contrast; EEG labels within one eye state, 120-s blocks, eyes closed against open |
| `c000`, `a063` | primary simulation cell; an addendum 3 cell (one replicate seen before the addendum was stamped) |
| `gate/` (step 2), `runs_add3/tools/gate/` | the pipeline gate (the F-test decoder against the top-20 decoder, Methods); the toolbox agreement gates G1–G4 (inside `runs_add3.tgz`) |

## How to reproduce

```sh
python prereg/check_hash_lists.py                                  # every hash list against the files: ALL OK
python prereg/ots_verify_public.py $(find analyses -name '*.ots')  # the 17 timestamp proofs: ALL OK
```

Then rebuild every summary and figure from the shipped files and compare them with the shipped ones (`REPRODUCE.md` §2, about 10 minutes on a laptop, with `pip install -r requirements/quick-path.txt`). Full runs need the public data; the simulation grid, the toolboxes, the EEG analysis and the IBL analysis each ran on one cloud machine for 5 to 14 hours (`REPRODUCE.md` §3). Versions and machines are in `ENVIRONMENT.md`.

## Repository layout

| Path | What |
|---|---|
| `blockperm/` | The block permutation test as a function, with tests and an example. |
| `figures/` | Scripts that draw every figure from `analyses/`, the plotted values and the PDFs. |
| `requirements/` | Pinned package versions of each environment, from the `pip freeze` recorded with each run. |
| `analyses/step1-decomposition/` | Mouse recordings with labels assigned to blocks: trial-level tests, fixed and refitted decoders, training-label permutation (Fig. 1, row 2). |
| `analyses/step2-comparison/` | Simulation grid, mouse cells and the toolboxes as shipped (Fig. 1 for the mouse and the simulation; Fig. 2a). The toolbox excerpts are in `toolbox-src/` (`THIRD-PARTY.md`); the toolbox machine set-up in `gcp/`. |
| `analyses/step2b-eeg/` | The same tests on MPI LEMON resting EEG (Fig. 1, EEG); cloud set-up and laptop chains in `gcp/`. |
| `analyses/step3-ibl/` | The IBL brain-wide map (Fig. 2b). |
| `analyses/trackA-std/` | The earlier mouse analysis that step 1 builds on: session list, reference outputs, its pre-registration and its stated rerun. |
| `analyses/foldmap/` | Platform check of scikit-learn's `GroupKFold` fold map. |
| `analyses/practice-survey/` | Protocol, search, screening and coding of the survey (full texts not redistributed). |
| `analyses/step4-fmri-haxby/` | Post hoc: the same tests on block-design fMRI (Haxby et al. 2001, the PyMVPA tutorial data); design, code, rows, summary, results note (Supplementary Note 7). |
| `analyses/step5-pamap2/` | Post hoc: the same tests on body-worn sensor recordings (PAMAP2); design, code, rows, summary, results note; shares the step 4 engine, summary script, synthetic checks and run note (Supplementary Note 7). |
| `analyses/yaron-panel/` | Extended Data Fig. 3: the block permutation with the unit selection held fixed or repeated, on the public data of Yaron et al. (2025). |
| `prereg/` | Index of the timestamp proofs against run times, and two check scripts. |
| `REPRODUCE.md`, `ENVIRONMENT.md`, `NUMBERS.md`, `PROVENANCE.md` | Steps with expected outputs and runtimes; versions and machines; the source of every number; what was copied and what changed. |
| `THIRD-PARTY.md`, `LICENSES/` | Origin and licenses of the toolbox excerpts. |

The folders `step1-decomposition` to `step3-ibl` each hold a design (`DESIGN*.md`, with its hash list and `.ots` proof), code (`code/`), outputs (`results/` or `runs/`) and a results note (`RESULTS-NOTE.md`). The run rows of steps 2, 2b and 3 are shipped as archives (`*.tgz` with a hash file). `runs_pilot.tgz` and `runs_prep.tgz` in step 3 hold the timing pilot and the preparation records. In each step, `DESIGN.md` is the version named by its hash list (`DESIGN-v2.sha256` for design v2, `DESIGN-v1.sha256` for v1), and the step 1 `DESIGN-ADDENDUM.sha256` covers `DESIGN-ADDENDUM-within-train.md`.

## Pre-specification and timestamps

Each analysis was specified in a design document that was reviewed, committed and timestamped with OpenTimestamps. `prereg/README.md` lists every proof with its earliest Bitcoin block against the start of the run and the first time any result was read, and it states the exceptions: the two step 1 runs started a few minutes before their blocks, the step 2 cloud run started 20 minutes before the block of its run-platform proof (the decision was committed before the run, its reviewed text a few minutes after), the Track A outputs come from a stated rerun, and the survey protocol was committed but not timestamped (its commit, 38 s before the search, is in the authors' working history, which is not part of this repository). Apart from one replicate of one addendum-3 cell, seen before that addendum was stamped, no result was opened before its block. Timestamped files are kept byte for byte (`PROVENANCE.md`).

## Data

No recordings are redistributed. Allen Brain Observatory Visual Coding Neuropixels (32 sessions) and MPI LEMON (resting EEG) are downloaded by the scripts in `analyses/trackA-std/code/` and `analyses/step2b-eeg/code/`; `REPRODUCE.md` §3 gives the commands that compare the downloaded files with the shipped manifests. The International Brain Laboratory data are read through the ONE API from the public server, Brain-Wide Map release `2023_12_bwm_release`, with the session list in `analyses/step3-ibl/runs/ORDER.json`. The rat auditory cortex recordings of Yaron et al. (2025; Zenodo 10.5281/zenodo.15531781, CC BY 4.0) are downloaded by `analyses/yaron-panel/data/fetch_yaron.py` and checked against its manifest (`REPRODUCE.md` §3). The fMRI data of Haxby et al. (2001), as distributed with PyMVPA (data.pymvpa.org/datasets/haxby2001), and PAMAP2 (UCI Machine Learning Repository, 10.24432/C5NW2H, CC BY 4.0) are downloaded by `analyses/step4-fmri-haxby/code/fetch_haxby.py` (checked against the server's MD5 sums) and `analyses/step5-pamap2/code/fetch_pamap2.py`; their manifests are in each step's `runs/`. The four main datasets take about 80 GB (Allen), 13 GB (LEMON), 96 GB (IBL) and 1.4 GB (Yaron et al.); the two post hoc datasets take 1.8 GB (Haxby et al.) and 0.7 GB (PAMAP2) as archives.

## Licenses

Our code is released under the MIT license (`LICENSE`). The toolbox excerpts keep their own licenses (`THIRD-PARTY.md`, texts in `LICENSES/`). Data remain under the terms of their providers.
