# Grid-runner validation before stamping (DESIGN.md §14 must 8; run 2026-10-21 11:31–11:46 KST, follow-up 11:46–11:50)

Script `code/validate_runner.sh` (written 11:31, committed 07f8bd2 before running), 200 replicates per cell, seed 9, 3 workers; follow-up `code/validate_iid.py` (seed 77). Monte Carlo 99% band for 5% at n = 200: 1.0–9.0%.

| Cell | Rule | Rate p < 0.05 | Verdict |
|---|---|---|---|
| A: interleaved labels, drift 0 (fast component still on), B 12, S-main | P1 binomial | 10.0% | above band |
| | P2 sklearn permutation_test_score | 6.0% | OK |
| | P3 within-run permutation (0 errors) | 6.5% | OK |
| | P4 training labels only | 10.5% | above band |
| B: random block design, Allen drift, B 12, S-main, **P5 only** (P1–P4 of this primary layout not computed) | P5 block permutation, rerun | 4.5% | OK (exact by randomisation) |
| Follow-up: fully independent Poisson counts (no latent factors), interleaved labels, 240 trials × 89 units, S-main | P1 | 8.3% (n = 1,000; MC 99% band 4.4–5.6% at this n) | above nominal |
| | P4 | 10.3% (n = 300; band 2.0–8.0%) | above nominal |

## Reading
- The runner and the valid rules behave as intended: P2 and P3 are near 5% on independent labels, and P5 is near 5% under random block assignment.
- **P1 and P4 exceed 5% even on fully independent data.** These are properties of the rules, not runner bugs:
  - P1 treats the pooled cross-validated correct count as binomial; k-fold estimates share training data across folds, so their variance exceeds the binomial variance (known: no unbiased variance estimator for k-fold CV, Bengio & Grandvalet 2004), giving about 8% here.
  - P4 (training labels only, folds fixed) inflates under cross-validation with independent data, as Valente et al. (2021) showed for "Within(Train)"; about 10% here.
- Consequence for the design (to add in v2 §11 predictions, which did not state this): P1 and P4 are expected above 5% already without drift; their block-design inflation should be read against this iid baseline (report both: rate and rate minus the iid baseline). The sanity cells in §8 ("P2 with interleaved labels and no drift") stay; add P1 and P4 there as "known above nominal".
- No study cell was opened: cell B computed only P5.

## Correction (2026-10-21, addendum 1 review C-a)
The Monte Carlo 99% band of a 5% rate at n = 1,000 is 3.3–6.9%, not 4.4–5.6% as written in the table above; at n = 300 it is 2.0–8.3%. The reading (P1 8.3% and P4 10.3% above nominal on independent data) is unchanged.
