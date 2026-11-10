# Where each number of the paper comes from

Paths are relative to `analyses/`. Some rows give numbers of the results notes that the manuscript no longer quotes; they are kept for the record. "Note §n" is the results note of that step. Rule names: P1 binomial test of held-out accuracy; P2 trial-level permutation with refit (scikit-learn `permutation_test_score`); P3 trial-level permutation within runs (CoSMoMVPA tutorial rule); P4 training labels permuted, refit (PyMVPA tutorial); P5 the block permutation test (all labels permuted by block, refit). Rates are shares of tests with p < 0.05 on labels that carry no information. The "Value in the source" column quotes the source files, including their cell and layout labels (for example `shared24`: 24 blocks shared by training and test trials; `sep24`: calibration and held-out trials from separate blocks with independent labels; `S-main`, `S-tool`: shuffled five-fold and the scikit-learn default folds; `L1`–`L4`: block layouts of the toolbox runs; `PS-refit`: the pseudosession test); each results note defines them.

## Practice survey
| Number | Value in the source | Source |
|---|---|---|
| 14 studies, all with shared-block splits | C1 shared, 14 of 14 | `practice-survey/SUMMARY.md` (final values) |
| 11 of 14 used a trial-level test | "At-risk: 10 of 14" with one code recoded on 2026-11-04 (C2 of PMC12873149) | `practice-survey/SUMMARY.md` (primary outcome and its correction line); `practice-survey/coding_final.csv`; `practice-survey/final-check-2026-11-04/RESULT.md` |

## Data
| Number | Value | Source |
|---|---|---|
| 30 mice | 30 new mice (32 sessions in all, with the 2 mice of the original study; estimates use the 30) | `step2-comparison/RESULTS-NOTE.md` §3; `step1-decomposition/DESIGN.md` |
| 38 participants | 38 | `step2b-eeg/RESULTS-NOTE.md` §1 |
| IBL: 1,359 brain regions analyzed in single sessions (region-sessions in the notes), 325 sessions, 118 mice | 459 sessions in the order, 335 finished (106 skipped by the 250-trial rule, 18 errors); 1,359 region-sessions from 325 sessions of 118 mice | `step3-ibl/RESULTS-NOTE.md` §1 |

## Fig. 1 and the main text
| Number | Value | Source |
|---|---|---|
| trial-level permutation 98% (mouse), 92% (EEG) | P2 97.7 (shared24, S-main); EEG P2 92.2 (balanced, S-main) | `step2-comparison/results/allen_summary.md`, note §3; `step2b-eeg/results/summary_2b.md`, note §1 |
| cover letter: trial-level permutation 92–98% | the two values of the row above | as above |
| binomial test "did the same" | P1 99.2 (mouse); 93.6 (EEG) | same files |
| default unshuffled folds 38% (mouse), 39% (EEG) | P2 38.0 (shared24, S-tool); EEG P2 38.9 (S-tool) | same files |
| default folds, binomial test and trial-level permutation 38–39% | P1 37.9, P2 38.0 (shared24, S-tool); EEG P1 39.3, P2 38.9 (balanced, S-tool) | `step2-comparison/results/allen_summary.md`; `step2b-eeg/results/summary_2b.md` |
| labels varying trial by trial 2.8–6.0% | interleaved P2 2.8–6.0 | `step2-comparison/RESULTS-NOTE.md` §1 ("Interleaved labels") |
| real drifting-grating trials 98% | dg_shared24 P2 98.3 (P5 7.5) | `step2-comparison/RESULTS-NOTE.md` §3 |
| fixed decoder 84% (top-20 logistic); 43–95% across decoders | blk_fixed lr_topk 83.7; rank 42.7, sel 62.7, lr_all 95.3 | `step1-decomposition/results/results.md` (shared24) |
| training labels only 99% (mouse), 94% (EEG) | P4 99.2; EEG P4 93.9 | `step2-comparison/results/allen_summary.md`; `step2b-eeg/results/summary_2b.md` |
| training labels permuted between blocks 68–93% | trn_blk shared24 68.2–92.8 | `step1-decomposition/results/within_train.md` |
| block permutation test 5% | P5 5.2 (mouse), 4.9 (EEG), 5.7 (simulation, primary cell) | the three summaries above; `step2-comparison/results/sim_summary.md` |
| simulated fixed orders 0–2.4% | P5, fixed-order cells | `step2-comparison/RESULTS-NOTE.md` §1 |
| EEG fixed orders 95% (first half against second half), 29% (runs of four blocks) | fixed_half 94.7; fixed_aabb 28.9 (S-main) | `step2b-eeg/RESULTS-NOTE.md` §2 |
| separate training and test blocks: fixed decoder 3–6% (Supplementary Note 6) | sep24 blk_fixed 2.6–5.9 | `step1-decomposition/results/results.md` (sep24) |
| separate training and test blocks: trial-level tests about a quarter (Extended Data Fig. 2; Supplementary Note 6) | sep24 binom 19.3–30.3, trl_rerun/trl_fixed 20.0–31.1 | `step1-decomposition/results/results.md` (sep24) |
| circular-shift null 5% and 15% (random blocks), 35% (half-session split) (Supplementary Notes 2 and 6, Extended Data Fig. 2c; iid 2.8 is not a block scheme) | circ_rerun sel: iid 2.8, shared24 5.1, shared 15.1, segment 35.1 | `step1-decomposition/results/results.md` |
| whole blocks held out: trial-level training-label permutation 7–14% | sep24 trn_trl 7.0–14.3 | `step1-decomposition/results/within_train.md` |
| smallest p about one in three with two blocks per condition | 6 arrangements, 3 distinct scores (class swap) | `step2-comparison/DESIGN-v2-ADDENDUM.md` §3; note §1 (B = 4: smallest p seen 0.22–0.27) |
| power 7% and 66%; size-adjusted invalid tests 5–7% | P5 7.1 (δ 0.2), 65.6 (δ 0.5); P1, P2, P4 size-adjusted 5.0–7.2 | `step2-comparison/RESULTS-NOTE.md` §2 |
| EEG power about the same or less, 88–93% against 85%, training-label permutation 57% (post hoc) | size-adjusted P1–P3 87.8–92.5; P4 56.9; P5 84.6 | `step2b-eeg/RESULTS-NOTE.md` §4 |

## Fig. 2a and the toolboxes
| Number | Value | Source |
|---|---|---|
| CoSMoMVPA and PyMVPA as shipped 18–21%, against 4% | L4: CoSMoMVPA 20.2 / 20.8, PyMVPA 18.4 / 21.4; P5 4.4 | `step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md`; note §5 |
| fixed block order 31–70% | L2: CoSMoMVPA 30.6 / 58.6, PyMVPA 48.6 / 70.2 | same |
| PyMVPA chunk-level permutation 4–5% in L1–L3, 11.8% in L4 (Methods, per-toolbox change) | 5.4 / 4.0 / 5.0 (L1–L3); 11.8 (L4) | same |
| `groups` permutes within blocks | scikit-learn `_shuffle` | `step2-comparison/TOOLBOX-DEFAULTS.md`; `toolbox-src/sk_validation.py` |
| group level: t-test 100%; group null 4–7% | EEG t 100%, group null 4%; mouse t 100% (S-main, S-tool), group null 4–7% | `step2b-eeg/RESULTS-NOTE.md` §3; `step2-comparison/RESULTS-NOTE.md` §3 |

## Extended Data Fig. 3a (rat auditory cortex, post hoc)
| Number | Value in the source | Source |
|---|---|---|
| 123 units selected, observed 0.337 | observed 0.3368, selected 123 | `yaron-panel/results/fixed_vs_repeated.json` |
| null mean with the selection fixed 0.001, repeated 0.115 | arms.fixed.null_mean 0.0014; arms.repeated.null_mean 0.1149 | same |

## Fig. 2b and the IBL
| Number | Value | Source |
|---|---|---|
| fake block sequences: scikit-learn rule 70%, pseudosession test 5% | P2 70.4, PS-refit 4.9 | `step3-ibl/runs/SUMMARY.md`; note §2 |
| real block side: different verdicts in 884 of 1,359 (65%), all P2 only | P2 only 884, PS-refit only 0; both 146, neither 329 | `step3-ibl/runs/SUMMARY.md`; note §3 |
| real block side: scikit-learn rule 75%, pseudosession test 10% | P2 74.6, PS-refit 9.8 (mouse-weighted) | `step3-ibl/runs/SUMMARY.md`; note §3 |
| the difference is about the size of the excess on labels with no information | V 64.8 against F 65.6 points | note §2, §3 |
| fixed units in the pseudosession null 6% against 5% | SEL-fixed 6.1, SEL-repeat 4.9 | note §4 |

## Supplementary Note 7 and the main text: steps 4 and 5 (post hoc)
| Number | Value in the source | Source |
|---|---|---|
| fMRI, shared blocks: trial-level 90%, training-label 91%, block permutation test 8% (95% 4–10%) | P2 90.0, P4 91.1, P5 7.8 (4.4–10.0) | `step4-fmri-haxby/results/summary.md`, fake / detrended / split main |
| SN 7: block permutation test 2.9–7.8% in every split of both datasets (labels with no information) | fMRI P5 3.3–7.8 (detrended and raw, splits block, main, run, tool); sensors P5 2.9–5.0 (splits block, main, tool) | `step4-fmri-haxby/results/summary.md`, `step5-pamap2/results/summary.md`, fake rows |
| sensors, shared blocks: 100%, 100%, 5% | P2 100.0, P4 100.0, P5 5.0 (2.1–8.8) | `step5-pamap2/results/summary.md`, fake / windows2s / split main |
| primary contrasts 82.2 (73.9–90.0) and 95.0 (91.2–97.9) points; 6 of 6 and 8 of 8 subjects | E4, E5 | each step's `results/summary.md`, primary contrast |
| leave one run out: tutorial rules 10.6–17.8% | P3, P4 under split run, detrended and raw | `step4-fmri-haxby/results/summary.md` |
| whole blocks held out: 17–23% (detrended fMRI), 0.6–1.7% (raw fMRI), training-label 34% (sensors) | split block cells | both summaries |
| Supplementary Table 6 | every cell with labels with no information | both summaries |
| 6 and 8 participants; 307–675 voxels; 1,264–2,235 windows | inclusion records | `step4-fmri-haxby/runs/prepare.log`, `step5-pamap2/runs/prepare.log` |

## Supplementary Note 2 (survey) and figure legends: further numbers
| Number | Value in the source | Source |
|---|---|---|
| 2,370 hits; 1,539 automatic, 159 without full text (1,698); 672 read; 14 included | screening counts | `practice-survey/SCREENING-NOTE.md`, `SUMMARY.md` |
| 179 flagged by a broader keyword screen; 11 read; 7 reasons corrected | deviation 2 | `practice-survey/SCREENING-NOTE.md` |
| κ 0.86 (test), 1.00 (refit), 0.64 (unit selection); raw agreement 0.93–1.00 | agreement table | `practice-survey/SUMMARY.md` |
| 14 of 14 shared splits, Clopper–Pearson 95% 77–100%; 11 of 14 at risk, Wilson 52–92% | C1, at-risk outcome; intervals computed from the counts | `practice-survey/SUMMARY.md` |
| 0 of 40 wrongly excluded; Wilson upper bound 8.8%, about 150 of 1,698 | audit | `practice-survey/AUDIT-AUTO-EXCLUSIONS.md` |
| 140 of 140 quotes found (first, strict pass 107 of 140) | quote check | `practice-survey/quote_check.md` |
| SN 7: 12 runs (11 for one participant), 30 assignments per participant, 55 features, one sensor participant excluded (42 windows, fewer than 480) | designs and inclusion records | `step4-fmri-haxby/DESIGN.md`, `step5-pamap2/DESIGN.md`, `step5-pamap2/runs/prepare.log` |
| SN 7 positive controls: faces against houses 6 of 6; added signal 99.6–100% | control cells | both summaries |
| Fig. 1: 1,000 simulation replicates; Fig. 2a: 500 replicates per layout | primary cell; layout L4 | `step2-comparison/results/sim_summary.md`; `runs_add3/tools/SUMMARY-TOOLS.md` |
| ED 2: binomial test 26.5% with separate blocks | `sep`, binom, sel | `step1-decomposition/results/results.md` |
| ED 3: p = 0.001 for both nulls | `p` | `yaron-panel/results/fixed_vs_repeated.json` |
| ED 7: 200 sets of labels with no information (mouse), 50 label assignments (EEG) | group-level columns | `step2-comparison/RESULTS-NOTE.md` §3, `step2b-eeg/RESULTS-NOTE.md` §3 |
| ED 9: 134 regions recorded in at least three sessions | region counts | `step3-ibl/runs/SUMMARY.md` |

## Supplementary Notes 1, 3, 4 and 5
| Number | Value in the source | Source |
|---|---|---|
| SN 1: 16.5 (14.8–18.0), 12.5 (10.8–14.2), 43%, 28.9, 6.3 (5.5–7.3), 96%, 26.5% (20.6–32.7), 3.8% (0.8–7.2) | the rerun of the pre-registered analysis | `trackA-std/results/results.md` |
| SN 1: pre-registered run 15.7 and 6.0 | split and logistic results | `trackA-std/prereg-run/results/results.md` |
| SN 3: slope median +0.0045 (range −0.059 to +0.084; 14 of 38 negative), −0.0016 and +0.0101 within states, Spearman 0.10 (−0.23 to 0.41) and −0.07 (−0.39 to 0.26) | `summary` | `step2b-eeg/results/alpha_slope.json`; note §6 |
| SN 4: 47% of balanced assignments leave a run with one class | 438 of 924 (47.4%) | `step2-comparison/DESIGN-v2-ADDENDUM-3.md` |
| SN 4: 461 of 1,000 failed; 97% of the other 539; 52% counting failures; 0.6% for the block permutation test on the same 539 | P3 error share 46.1, 97.2, 52.4; P5 0.6 | `step2-comparison/RESULTS-NOTE.md` §1 |
| SN 4: CoSMoMVPA stopped in 238 of 500; 16–18% over the 262 others | L1 | `step2-comparison/RESULTS-NOTE.md` §5; `runs_add3/tools/SUMMARY-TOOLS.md` |
| SN 4: EEG runs lacking a class 28%; 70%; 50% counting failures | P3 error share 28.3, 70.4, 50.2 | `step2b-eeg/RESULTS-NOTE.md` §1 |
| SN 4: 38,431 simulations in 76 cells; identical p 58–93%; rates within 2.6 points | equivalence check | `step2-comparison/RESULTS-NOTE.md` §6 |
| SN 4: 800 of 800 (x86 and laptop with the x86 map) against 116 of 800; Supplementary Table 3 | replicate check; fold maps | `foldmap/REPLICATE-CHECK.md`, `foldmap/RESULT.md` |
| SN 5 and the Discussion (a calculation fixed before the run predicted the rate with separate blocks): Supplementary Table 4 (all rows); ρ 0.77 against 0.48 | block-number sweep; prediction P-D | `step1-decomposition/results/results.md`; `step1-decomposition/RESULTS-NOTE.md` |

## Numbers stated only in the Methods
| Number | Value in the source | Source |
|---|---|---|
| 143 recorded areas (30 mice); 154 in all 32 | "Areas: 143 in the 30 new mice, 154 in all 32" | `step2-comparison/RESULTS-NOTE.md` §3 |
| 24 blocks of about 35 s (spontaneous activity) | measured block length 35 s (8 blocks per epoch) | `step1-decomposition/results/results.md` (block-number sweep) |
| gate: 149 of 154 areas identical; F-test version within 0.6 points | pipeline gate | `step2-comparison/gate/GATE-RESULT.md` |
| 40 participants drawn, 38 kept | `SUBJECTS.txt`; two dropped by the epoch rule | `step2b-eeg/eligibility/`, `step2b-eeg/QC-NOTE.md`, results note §1 |
| EEG block permutations in the main and fixed-order arms drawn from the 4,900 balanced assignments (200 draws) | P5 null set = the 4,900; `N_PERM` 200 in `step2b-eeg/code/run_2b.py` | `step2b-eeg/RESULTS-NOTE.md` §2 |
| IBL: 459 sessions of 139 mice; 335 finished, 106 skipped, 18 errors; 325 sessions with regions; 47 workers | completed prefix and denominators | `step3-ibl/RESULTS-NOTE.md` §1, `step3-ibl/RUNNOTE-2.md` |
| IBL: 20 fake block sequences per session; one pool of 220 pseudosessions | design §3 | `step3-ibl/DESIGN.md` |
| IBL realism check: KS 0.06, permutation p 0.14 | ks 0.0602, ks_perm_p 0.1409 | `step3-ibl/runs/REALISM.json` |
| 40 automatic exclusions checked, none wrongly excluded (Wilson 0–8.8%) | 0 of 40 (agent audit); 40 of 40 excluded (independent check, 2026-11-02); author's hand check: none wrongly excluded (`practice-survey/AUTHOR-CHECK.md`) | `practice-survey/AUDIT-AUTO-EXCLUSIONS.md`, `practice-survey/final-check-2026-11-02/RESULT.md` |

## Reanalyses of published studies (added 2026-11-09; not in the preprint text)
| Number | Value in the source | Source |
|---|---|---|
| Jahn et al. (2024) primary, Holm-adjusted p LIP, FEF, LPFC 0.64, 0.48, 0.64 | 0.6434, 0.4795, 0.6434 | `step6-reanalysis-cell/vm-out-a2/summary.md` |
| trial shuffle null mean 0.33, p at its minimum in all regions | 0.3335, 0.3335, 0.3333; 0.000999 | `step6-reanalysis-cell/vm-out-a2/note_tables.out` |
| block permutation null means 0.75, 0.70, 0.72; observed 0.76, 0.75, 0.74 | 0.7537, 0.6975, 0.7181; 0.7570, 0.7526, 0.7393 | as above |
| qualifying sessions and true-template z-test, gate items | Addendum 3 | `step6-reanalysis-cell/vm-out-a3/note_tables.out`, `RESULTS.md` section 1.8 |
| Klee et al. (2026) group block test p, ITI and PERI, 1.5e-05 and 6e-06; drift accuracy 51.4% | as stated | `step6b-reanalysis-sciadv/out/SUMMARY.md` |
| Jahn et al. (2024) corrected p 0.48–0.64 (main text) | Holm 0.4795, 0.6434, 0.6434 | `step6-reanalysis-cell/vm-out-a2/summary.md` |
| 3 of 14 surveyed studies stated random assignment of the decoded condition (two with a constraint) | random 1, pseudorandom-constrained 2 | `practice-survey/random-assignment-coding.csv` |
| raw fMRI, whole blocks held out: accuracy on labels with no information 40% (mean) | 0.3997 over 180 rows | `step4-fmri-haxby/runs/rows.step4.*.jsonl` (arm fake, prep raw, split block) |
| Jahn et al. (2024): 17 sessions, 171 blocks | as stated | `step6-reanalysis-cell/RESULTS.md` section 1.1 |
| Klee et al. (2026): intertrial window 3.95 to 2.08 s before the reward threshold crossing | as stated | `step6b-reanalysis-sciadv/DESIGN.md` section 0, item 2 |
| Klee et al. (2026): smallest per-mouse block p 0.1 | 0.1 | `step6b-reanalysis-sciadv/out/SUMMARY.md` |
| Extended Data Fig. 3c: 100,000 random combinations of the per-mouse trial-level nulls | as stated | `figures/make_ed_figures.py`, `ed3()` |
| Klee et al. (2026): 20 arrangements per mouse, 10 distinct scores, smallest group p 10^-6 (Methods) | C(6,3) = 20, class swap gives 10; (2/20)^6 | `step6b-reanalysis-sciadv/RESULTS.md`, `DESIGN.md` |
| Klee et al. (2026): self-paced drift decoding above chance in 3 of 6 mice; first Go trials of three mice (Methods) | as stated | `step6b-reanalysis-sciadv/out/SUMMARY.md`, `RESULTS.md` |
| Extended Data Fig. 3a: 18 sessions | 18 | `yaron-panel/RESULTS-NOTE.md` |
| Methods, Supplementary Table 1: 8 of 30 sessions (stated rerun) | as stated | `trackA-std/RERUN.md` |
| SN 2: random assignment, 1 random, 2 constrained, 9 fixed, 1 animal-determined, 1 not stated | counts of the coding | `practice-survey/random-assignment-coding.csv` |
| SN 5: 9 of 10 rows inside the interval, about 3 points, formula 0.3–5.4 points | recomputed from the table | `step1-decomposition/results/results.md` |
| SN 6: EEG, labels assigned within one eye state 93%, labels on 120-s blocks 96% | as stated | `step2b-eeg/results/summary_2b.md` |
| Methods: labels varying trial by trial without slow drift, CoSMoMVPA 6.2%, PyMVPA training-label rule 10–12% | as stated | `step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md` |
| Jahn et al. (2024): a mean of three to four blocks per color bin (Discussion; Extended Data Fig. 3b) | G10: LIP 3.42, FEF 3.40, LPFC 3.35 | `step6-reanalysis-cell/RESULTS.md` (G10) |
| SN 6: 100% of runs with random folds, 54% with contiguous folds (simulated block variable) | a value of the cited paper, not an output of this repository | Harris (2020), Fig. 8 and its text |
