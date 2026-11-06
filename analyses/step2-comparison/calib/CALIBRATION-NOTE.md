# Allen calibration: result and a design problem it exposed (analysis note, 2026-10-21 11:15 KST)

Run 2026-10-21 01:40–01:57 KST (`code/calibrate.py`, committed before running: 2bc887e and the timestamp fix after it). 154 areas, 32 sessions.

## Result
- τ̂ (single exponential on PC1 autocorrelation, lags 1–5): median over mice **1.9 trials** (≈ 4 s; IQR over mice 1.4–3.2).
- Slow excess variance of 10-trial window means: median **0.31** (IQR 0.25–0.38).
- Matching drift: with τ = 1.9 the generator reaches only 0.24 at the largest grid value (drift 1.0) → **best at the grid edge; no match.**

## What this means
The single-time-scale generator of DESIGN.md v1 §5a cannot reproduce Allen spontaneous activity: the short τ̂ describes fast fluctuations of PC1 (lag 1–5), but Allen also has much more slow variance (over 10–20 s windows and beyond) than an OU process with τ ≈ 2 trials can produce. The step 1 results themselves show the slow part matters (fake block labels pass block-shared tests at 85–99%). The L/τ grid {0.3, 1, 3} defined on this τ̂ would put every realistic block length at L/τ ≫ 3.

## Proposed revision for DESIGN.md v2 (to be persona-reviewed before any stamping; not applied)
- Two latent components: fast OU (τ_f, from PC1 lags 1–5, ≈ 2 trials) and slow OU (τ_s, from the autocorrelation of 10-trial window means of PC1, or from a two-exponential fit over lags 1–60), plus the linear trend; their variances matched to two statistics (lag-1 autocorrelation of PC1 and the slow excess variance above).
- Define the grid on τ_s: L/τ_s ∈ {0.3, 1, 3} with "Allen-level" = the matched slow variance, 0 and 2× as before.
- Re-run the calibration with the revised generator (script written and committed before running) and report both fits.
- Pilot timing is unaffected (generation cost is negligible).

This is a change to the generator after seeing a calibration statistic (not a test result). It is recorded here and goes to review with the 2b design.
