# Practice survey protocol: block-structured decoding and its significance tests (fixed before screening, 2026-10-20)

Purpose: estimate how often published decoding analyses of block-structured variables use a significance test that step 1 (`../step1-decomposition/RESULTS-NOTE.md`) found to pass fake labels: a trial-level test (binomial, t-test, trial-label permutation) or a block permutation with the fitted decoder held fixed, when calibration and held-out trials share blocks. This replaces the non-systematic 12-paper reading. Committed before any paper is screened; deviations will be reported.

## 1. Search
- Database: Europe PMC REST API (full-text search of open-access articles), publication date 2024-01-01 to 2026-10-19, research articles, English.
- Query (exact, run once, results saved with the retrieval date):
  `(decoding OR decoder OR classifier) AND (permutation OR shuffled OR shuffle) AND (block OR blocks OR context) AND (neurons OR "single units" OR "calcium imaging" OR Neuropixels OR electrophysiology) AND OPEN_ACCESS:y AND PUB_YEAR:[2024 TO 2026]`
- Order the hits by Europe PMC id, shuffle with numpy `default_rng(20261020)`, and screen in that order until **40 included papers** or the list ends.

## 2. Inclusion (all required)
1. Primary research with recordings of neural activity in animals (spikes or calcium imaging; fMRI/EEG/MEG excluded here).
2. A decoder or classifier predicts a task variable from population activity, with accuracy evaluated on held-out trials (cross-validation or train/test split).
3. The decoded variable is constant within blocks of consecutive trials (block design, task context or rule blocks, prior blocks, sessions or epochs as conditions), stated in Methods.
4. Statistical significance of decoding is reported.
Exclusion reasons are recorded per screened paper (first failing criterion).

## 3. Coding (per included paper; quote the Methods sentence for every item)
| Item | Values |
|---|---|
| C1 split | blocked (whole blocks held out) / shared (random trial-level k-fold, odd–even, or train/test inside blocks) / unclear |
| C2 test | binomial or parametric vs chance / trial-label permutation / block or session permutation / pseudosession or circular/linear shift / other / unclear |
| C3 refit in null | decoder refit in every null draw / decoder fixed, only held-out labels permuted / unclear |
| C4 label-based unit selection before decoding | none / yes, inside training folds / yes, on all trials / unclear |
| C5 code available | yes / no |
- **At-risk (primary outcome):** C1 = shared AND (C2 ∈ {binomial or parametric, trial-label permutation} OR (C2 = block permutation AND C3 = fixed)). Also reported: C1 = blocked with C2 ∈ {binomial or parametric, trial-label permutation} (known Harris-type risk, step 1 `sep`: 26–28%).
- Unclear items are not counted as at-risk; the proportion is reported with unclear cases as a separate column (lower and upper bound).

## 4. Coders
Two coders (independent agents) code the same included list without seeing each other's codes; a third pass (Claude) resolves disagreements from the quoted text. Agreement (Cohen's κ for C1–C3) is reported.

## 5. Output
`search.json` (raw hits with retrieval date), `screening.csv` (id, DOI, decision, reason), `coding_A.csv`, `coding_B.csv`, `coding_final.csv`, `SUMMARY.md` (proportion at-risk with Wilson 95% interval, by item). Papers are named in the supplementary list; the main text reports only counts and does not single out individual studies as wrong.
