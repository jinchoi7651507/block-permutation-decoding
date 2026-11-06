# Track A results (filled in by code/trackA_summarize.py)

All proportions are means over mice of each mouse's proportion of recorded areas (session-area pairs); intervals are 95% cluster-bootstrap intervals over mice (B = 20,000, seed 20261015).

Pre-registration: PREREG-trackA.md (commit ____, sha256 0328e9a56fd503791fdf62bd35ce793a17cfc59281415ea7a7016e9e967de22e, OpenTimestamps block 971261 at 2026-10-13 15:18:51 UTC).
Download finished: 2026-10-15 11:16:17 UTC (from MANIFEST.sha256 mtime, folder-root copy; the download folder's copy was rewritten byte-identically on 2026-10-16 15:05 UTC when the download command was re-run to confirm all 32 sizes against the server). Analysis run: 2026-10-16 15:06–15:36 UTC (P1 x3, then trackA_extra.py 4 workers, then summary). Machine: Mac17,5 (Apple A18 Pro, 8 GB RAM), macOS 26.6.2, Python 3.12.3 (pyenv, no venv) with numpy 2.4.6, scipy 1.18.1, h5py 3.16.0.
Deviations from the pre-registration (write "none" if none): none in data, code, settings or commands. Run used the system pyenv Python 3.12.3 with the pinned package versions instead of a fresh .venv. Gate 0 environment changes (if any): ____ (gate 0 was run before this session).

## Gates
- The two original sessions reproduce the committed seed-1 outputs exactly. Good-only: True. Every cluster: True. If either is False the summary script stops; report and do not fix and rerun.
- Checks (missing sessions, P1/extra correspondence, non-converged fits, skipped C, invalid-time overlaps): {"sessions_missing_or_unread": [], "p1_vs_extra_area_mismatch": [], "p1_free_vs_p3_obs_mismatch": [], "logistic_nonconverged": 0, "c_skipped_sessions": [], "dg_trials_overlapping_invalid": 84, "excluded_under_section_6": []}

## P1 (primary): planned best-split readout, Allen quality == good, 30 new mice, six standard areas
Animal-level means (95% cluster-bootstrap interval over animals; B = 20,000).
- Best split minus specificity null (g_null; co-primary): 15.7 (14.1 to 17.3; animals 30, area units 143)
- Specificity null minus always guessing (d; co-primary): 11.2 (9.4 to 13.0; animals 30, area units 143)
- Best split minus always guessing (g_const): 26.8 (23.8 to 30.0; animals 30, area units 143)
- Ratio R = mean d / mean g_const: 0.416 (0.387 to 0.444; conditional on positive denominators, undefined resamples 0); single share in interval: None
- Branch for summary sentence M3 (PREREG section 7): ('ratio', 0.42)
- Mice included / in set: 30 / 30
- Area units: g_null > 0 in 138/143; p_spec < 0.05 in 81/143
- Verdicts: g_null replicated (lower bound > 0): True; d replicated (lower bound > 0): True

## P2 (co-primary): standard decoder (L2 logistic, top-k by |d'|, k by calibration CV)
- Held-out accuracy minus its specificity null (same k search on random orderings): 6.0 (5.3 to 6.7; animals 30, area units 143)
- Held-out accuracy minus always guessing: 38.0 (34.1 to 41.7; animals 30, area units 143)
- Proportion of area units with p < 0.05 (animal-level mean): 0.146 (0.082 to 0.221; animals 30, area units 143)
- k chosen: observed k chosen (5/10/20/40): [76, 32, 26, 9]; null k: [1635, 3296, 8224, 15445]
- Verdict: delta interval above 0: True

## P3: information null (labels shuffled within half x temporal frequency x stimulus block, selection rerun) for the planned readout
- Best split minus shuffle mean: 29.3 (26.3 to 32.4; animals 30, area units 143)
- Proportion of area units with p < 0.05: 0.947 (0.906 to 0.983; animals 30, area units 143)

## C: calibration on spontaneous activity (fake labels; proportion of recorded areas with p < 0.05)
| scheme | Q2 (held-out vs always guessing) | trial shuffle | block shuffle (exact) | specificity |
|---|---|---|---|---|
| iid labels, odd/even split (nothing to find) | 0.008 (0.000 to 0.025; animals 30, area units 143) | 0.029 (0.006 to 0.058; animals 30, area units 143) | n/a | 0.008 (0.000 to 0.025; animals 30, area units 143) |
| segment: one stretch of time per label, odd/even split | 1.000 (1.000 to 1.000; animals 30, area units 143) | 1.000 (1.000 to 1.000; animals 30, area units 143) | 0.817 (0.744 to 0.884; animals 30, area units 143) | 0.932 (0.873 to 0.978; animals 30, area units 143) |
| labels assigned to blocks at random, separate calibration and held-out blocks | 0.265 (0.206 to 0.327; animals 30, area units 143) | n/a | 0.038 (0.008 to 0.072; animals 30, area units 143) | 0.064 (0.031 to 0.101; animals 30, area units 143) |

## Original two mice (pre-specified analyses reported for completeness; six areas, good units)
- P2 delta: 9.1 (8.3 to 9.9; animals 2, area units 11)
- P3 excess: 29.0 (25.6 to 32.3; animals 2, area units 11)

## Descriptive
{"mean_running_speed_calibration_half": 11.622230694316482, "mean_running_speed_heldout_half": 10.51264225577491, "units_presence_below_0_9_in_std6_new": 628, "pseudo_trials_overlapping_invalid": 494, "null_nan_counts": 0}

## Sensitivity (P1; key = units/animals/areas)
| run | g_null | d | R |
|---|---|---|---|
| good/new/std6 | 15.7 (14.1 to 17.3; animals 30, area units 143) | 11.2 (9.4 to 13.0; animals 30, area units 143) | 0.416 |
| good/new/allvis | 15.6 (14.1 to 17.2; animals 30, area units 156) | 11.0 (9.3 to 12.8; animals 30, area units 156) | 0.413 |
| good/original/std6 | 15.3 (13.2 to 17.4; animals 2, area units 11) | 11.3 (10.7 to 11.9; animals 2, area units 11) | 0.425 |
| good/original/allvis | 15.3 (13.2 to 17.4; animals 2, area units 11) | 11.3 (10.7 to 11.9; animals 2, area units 11) | 0.425 |
| good/all32/std6 | 15.7 (14.2 to 17.2; animals 32, area units 154) | 11.2 (9.6 to 12.9; animals 32, area units 154) | 0.416 |
| good/all32/allvis | 15.6 (14.2 to 17.1; animals 32, area units 167) | 11.0 (9.4 to 12.7; animals 32, area units 167) | 0.414 |
| all/new/std6 | 14.8 (12.9 to 16.6; animals 30, area units 143) | 8.9 (7.3 to 10.6; animals 30, area units 143) | 0.377 |
| all/new/allvis | 14.7 (13.0 to 16.5; animals 30, area units 156) | 8.9 (7.4 to 10.5; animals 30, area units 156) | 0.377 |
| all/original/std6 | 18.0 (15.3 to 20.6; animals 2, area units 11) | 9.7 (9.1 to 10.3; animals 2, area units 11) | 0.350 |
| all/original/allvis | 18.0 (15.3 to 20.6; animals 2, area units 11) | 9.7 (9.1 to 10.3; animals 2, area units 11) | 0.350 |
| all/all32/std6 | 15.0 (13.2 to 16.7; animals 32, area units 154) | 9.0 (7.5 to 10.5; animals 32, area units 154) | 0.375 |
| all/all32/allvis | 14.9 (13.3 to 16.6; animals 32, area units 167) | 9.0 (7.5 to 10.5; animals 32, area units 167) | 0.375 |
| sdk/new/std6 | 15.4 (13.5 to 17.1; animals 30, area units 134) | 14.7 (12.6 to 16.9; animals 30, area units 134) | 0.490 |
| sdk/new/allvis | 15.4 (13.6 to 17.2; animals 30, area units 145) | 14.7 (12.5 to 16.9; animals 30, area units 145) | 0.487 |
| sdk/original/std6 | 14.6 (11.3 to 17.9; animals 2, area units 8) | 20.0 (17.7 to 22.3; animals 2, area units 8) | 0.578 |
| sdk/original/allvis | 14.6 (11.3 to 17.9; animals 2, area units 8) | 20.0 (17.7 to 22.3; animals 2, area units 8) | 0.578 |
| sdk/all32/std6 | 15.3 (13.6 to 17.0; animals 32, area units 142) | 15.1 (13.0 to 17.2; animals 32, area units 142) | 0.496 |
| sdk/all32/allvis | 15.4 (13.6 to 17.1; animals 32, area units 153) | 15.0 (12.9 to 17.1; animals 32, area units 153) | 0.494 |

## Genotype (descriptive only, no test; good/new/std6)
| genotype | g_null | d |
|---|---|---|
| Cre | 16.3 (14.0 to 18.6; animals 14, area units 69) | 12.1 (9.5 to 14.9; animals 14, area units 69) |
| wt | 15.1 (12.9 to 17.4; animals 16, area units 74) | 10.3 (8.2 to 12.6; animals 16, area units 74) |

## Notes for the abstract (fill by hand, following PREREG-trackA.md section 7)
- Which pre-written sentence applies: ____
- Anything unexpected (reported, not acted on): ____
