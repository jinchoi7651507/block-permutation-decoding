# Allen calibration v2: result (analysis note, 2026-10-21 11:31 KST)

Run 11:26–11:30 KST (`code/calibrate_v2.py`, design in its header, committed before running: d016750). 154 areas, 32 mice; layout = median epochs 136/144/144 trials with gaps 1,247 and 1,157 trials; base rate 5.48 counts per trial.

| target | Allen (median over mice) | sd over mice | best simulated |
|---|---|---|---|
| PC1 autocorrelation lag 1 / 2 / 5 / 10 / 20 / 40 | 0.45 / 0.32 / 0.24 / 0.10 / 0.05 / −0.04 | 0.18 / 0.20 / 0.17 / 0.12 / 0.09 / 0.08 | 0.43 / 0.23 / 0.13 / 0.08 / 0.03 / −0.03 |
| slow excess variance (10-trial windows) | 0.31 | 0.11 | 0.27 |
| PC1 variance share | 0.151 | 0.018 | 0.157 |

- **Best point (Allen level): τ_f 1, σ_f 0.6, τ_s 40, σ_s 0.4, σ_u 0.4; distance 0.9** (sum of 8 squared standardised differences; every target within about 0.6 sd). v1's single-time-scale generator could not reach the slow variance at all; v2 can.
- **τ_s is not identified** (pre-stated rule): profile distance 1.18 / 1.29 / 0.90 / 2.73 / 1.37 for τ_s = 10 / 20 / 40 / 80 / 160; four values within 1 unit of the best. Per-mouse best τ_s IQR 20–160; split halves 10 and 40. → "Allen-level τ_s" is reported as a range (10–160 trials, i.e. 20–320 s), and the τ_s grid of §14 (τ_s = 7, 20, 67 with L = 20) is a sensitivity analysis, not anchored to one Allen value. Recommendation for v2: add τ_s = 160 (L/τ_s = 0.125) so the grid spans the identified range.
- **Grid edges:** τ_f (1, lower edge), σ_f (0.6, upper) and σ_u (0.4, upper) are at the edge of the pre-set grid. The fit is already within 1 sd per target, so the edge does not limit the match, but the parameter values themselves may lie beyond the grid. Not extended now (would be a new, post hoc grid); flagged for the review. The slow variance (0.27 vs 0.31) is slightly under-matched, consistent with σ_u at its edge.
- Labels were not used; no test result was computed.
