# Track A results (filled in by code/trackA_summarize.py)

All proportions are means over mice of each mouse's proportion of recorded areas (session-area pairs); intervals are 95% cluster-bootstrap intervals over mice (B = 20,000, seed 20261015).

Pre-registration: PREREG-trackA.md (commit ____, sha256 ____, OpenTimestamps block ____ at ____ UTC).
Download finished: ____ UTC (from MANIFEST.sha256 mtime). Analysis run: ____ UTC. Machine: ____.
Deviations from the pre-registration (write "none" if none): ____

## Gates
- The two original sessions reproduce the committed seed-1 outputs exactly. Good-only: True. Every cluster: True. If either is False the summary script stops; report and do not fix and rerun.
- Checks (missing sessions, P1/extra correspondence, non-converged fits, skipped C, invalid-time overlaps): {"sessions_missing_or_unread": [], "p1_vs_extra_area_mismatch": [], "p1_free_vs_p3_obs_mismatch": [], "logistic_nonconverged": 0, "c_skipped_sessions": [], "dg_trials_overlapping_invalid": 86, "excluded_under_section_6": []}

## P1 (primary): planned best-split readout, Allen quality == good, 30 new mice, six standard areas
Animal-level means (95% cluster-bootstrap interval over animals; B = 20,000).
- Best split minus specificity null (g_null; co-primary): 16.5 (14.8 to 18.0; animals 30, area units 143)
- Specificity null minus always guessing (d; co-primary): 12.5 (10.8 to 14.2; animals 30, area units 143)
- Best split minus always guessing (g_const): 28.9 (26.0 to 31.8; animals 30, area units 143)
- Ratio R = mean d / mean g_const: 0.431 (0.403 to 0.459; conditional on positive denominators, undefined resamples 0); single share in interval: None
- Branch for summary sentence M3 (PREREG section 7): ('ratio', 0.43)
- Mice included / in set: 30 / 30
- Area units: g_null > 0 in 138/143; p_spec < 0.05 in 76/143
- Verdicts: g_null replicated (lower bound > 0): True; d replicated (lower bound > 0): True

## P2 (co-primary): standard decoder (L2 logistic, top-k by |d'|, k by calibration CV)
- Held-out accuracy minus its specificity null (same k search on random orderings): 6.3 (5.5 to 7.3; animals 30, area units 143)
- Held-out accuracy minus always guessing: 44.3 (42.8 to 45.6; animals 30, area units 143)
- Proportion of area units with p < 0.05 (animal-level mean): 0.082 (0.036 to 0.133; animals 30, area units 143)
- k chosen: observed k chosen (5/10/20/40): [81, 31, 22, 9]; null k: [1248, 2724, 7743, 16885]
- Verdict: delta interval above 0: True

## P3: information null (labels shuffled within half x temporal frequency x stimulus block, selection rerun) for the planned readout
- Best split minus shuffle mean: 31.7 (29.1 to 34.4; animals 30, area units 143)
- Proportion of area units with p < 0.05: 0.956 (0.917 to 0.992; animals 30, area units 143)

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
{"mean_running_speed_calibration_half": 8.796618748238052, "mean_running_speed_heldout_half": 8.386715708056478, "units_presence_below_0_9_in_std6_new": 614, "pseudo_trials_overlapping_invalid": 494, "null_nan_counts": 0}

## Sensitivity (P1; key = units/animals/areas)
| run | g_null | d | R |
|---|---|---|---|
| good/new/std6 | 16.5 (14.8 to 18.0; animals 30, area units 143) | 12.5 (10.8 to 14.2; animals 30, area units 143) | 0.431 |
| good/new/allvis | 16.5 (15.0 to 17.9; animals 30, area units 157) | 12.1 (10.4 to 13.9; animals 30, area units 157) | 0.423 |
| good/original/std6 | 15.3 (13.2 to 17.4; animals 2, area units 11) | 11.3 (10.7 to 11.9; animals 2, area units 11) | 0.425 |
| good/original/allvis | 15.3 (13.2 to 17.4; animals 2, area units 11) | 11.3 (10.7 to 11.9; animals 2, area units 11) | 0.425 |
| good/all32/std6 | 16.4 (14.9 to 17.9; animals 32, area units 154) | 12.4 (10.8 to 14.0; animals 32, area units 154) | 0.431 |
| good/all32/allvis | 16.4 (15.1 to 17.8; animals 32, area units 168) | 12.1 (10.5 to 13.7; animals 32, area units 168) | 0.423 |
| all/new/std6 | 15.4 (13.5 to 17.3; animals 30, area units 143) | 9.7 (8.1 to 11.3; animals 30, area units 143) | 0.386 |
| all/new/allvis | 15.6 (13.9 to 17.2; animals 30, area units 157) | 9.5 (7.8 to 11.1; animals 30, area units 157) | 0.379 |
| all/original/std6 | 18.0 (15.3 to 20.6; animals 2, area units 11) | 9.7 (9.1 to 10.3; animals 2, area units 11) | 0.350 |
| all/original/allvis | 18.0 (15.3 to 20.6; animals 2, area units 11) | 9.7 (9.1 to 10.3; animals 2, area units 11) | 0.350 |
| all/all32/std6 | 15.6 (13.8 to 17.4; animals 32, area units 154) | 9.7 (8.2 to 11.2; animals 32, area units 154) | 0.383 |
| all/all32/allvis | 15.7 (14.1 to 17.3; animals 32, area units 168) | 9.5 (8.0 to 11.1; animals 32, area units 168) | 0.377 |
| sdk/new/std6 | 17.0 (15.0 to 18.6; animals 30, area units 135) | 17.3 (15.6 to 19.0; animals 30, area units 135) | 0.505 |
| sdk/new/allvis | 17.2 (15.5 to 18.6; animals 30, area units 147) | 17.0 (15.2 to 18.8; animals 30, area units 147) | 0.498 |
| sdk/original/std6 | 14.6 (11.3 to 17.9; animals 2, area units 8) | 20.0 (17.7 to 22.3; animals 2, area units 8) | 0.578 |
| sdk/original/allvis | 14.6 (11.3 to 17.9; animals 2, area units 8) | 20.0 (17.7 to 22.3; animals 2, area units 8) | 0.578 |
| sdk/all32/std6 | 16.8 (15.0 to 18.4; animals 32, area units 143) | 17.5 (15.9 to 19.1; animals 32, area units 143) | 0.510 |
| sdk/all32/allvis | 17.0 (15.4 to 18.4; animals 32, area units 155) | 17.2 (15.5 to 18.9; animals 32, area units 155) | 0.503 |

## Genotype (descriptive only, no test; good/new/std6)
| genotype | g_null | d |
|---|---|---|
| Cre | 17.4 (15.4 to 19.2; animals 14, area units 69) | 13.3 (11.1 to 15.6; animals 14, area units 69) |
| wt | 15.6 (13.2 to 18.0; animals 16, area units 74) | 11.7 (9.4 to 14.3; animals 16, area units 74) |

## Notes for the abstract (fill by hand, following PREREG-trackA.md section 7)
- Which pre-written sentence applies: ____
- Anything unexpected (reported, not acted on): ____
