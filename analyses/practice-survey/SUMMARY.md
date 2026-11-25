# Practice survey summary (2026-10-20, with the recode of 2026-11-04)

Included papers: 14 (Europe PMC 2,370 hits, all screened). Coders A and B coded independently; Claude resolved 3 genuine disagreements from the quotes (`coding_final.csv`).

## Agreement (after normalising equivalent wording)
| item | agreement | Cohen's κ |
|---|---|---|
| C1 | 0.93 | 0.00 |
| C2 | 0.93 | 0.86 |
| C3 | 1.00 | 1.00 |
| C4 | 0.93 | 0.64 |
| C5 | 1.00 | 1.00 |

κ is undefined or low where nearly all papers share one value (C1: 13–14 of 14 'shared'), so raw agreement is the more informative number there.

## Final values
- C1: shared 14
- C2: binomial or parametric 2, other 1, pseudosession or circular/linear shift 2, trial-label permutation 9
- C3: refit 9, unclear 5
- C4: none 13, yes, on all trials 1
- C5: no 3, yes 11

## Primary outcome
- **At-risk: 11 of 14 (79%, Wilson 95% 52–92%)**: PMC11156468, PMC11574977, PMC11666460, PMC12443960, PMC12660755, PMC12872450, PMC12873149, PMC13065759, PMC13418543, PMC13433320, PMC7618349.
- Secondary (blocked split with a trial-level test): 0 of 14.
- Fixed-decoder nulls (C3 = fixed): 0 of 14; refit 9, unclear 5. Every at-risk paper is at risk because of a trial-level test (binomial or trial-label permutation) on a shared-block split, not because the decoder was held fixed.

## What this means (reading)
1. In this sample, shared-block splits were universal (14/14) and most significance tests were trial-level (binomial or trial-label permutation). Step 1 found these pass about 85–99% of fake labels with label-fitted decoders in shared-block schemes (`shared24`: binom 93–98%, trl_rerun 94–99% across ranked-unit and logistic decoders; `half24` 82–90%; real grating trials `dg_shared24` 88–95%), even when the decoder is refit (a label-free decoder passes far less: 13.9%).
2. Fixed-decoder block permutations were not observed here. The practice-relevant message is therefore: with shared-block splits, the common tests (binomial, trial-label permutation even with refitting) fail; a block-level permutation with the decoder refit keeps the nominal rate. With held-out blocks that have their own labels, a decoder held fixed is valid, but trial-level tests still called about a quarter of the labels decodable (step 1, `sep24`). The fixed-decoder result of step 1 remains the explanation of why block preservation alone is not enough.
3. The main text does not judge the surveyed papers' conclusions, apart from one decoding analysis in each of the two studies reanalyzed in steps 6 and 6b.

## Limitations and deviations
- Small sample (14 of 2,370); open-access full texts with these keywords only; one screener (agent); 1,698 records excluded by an automatic keyword screen; an audit of 40 of them found none wrongly excluded (Wilson 95% 0–8.8%; `AUDIT-AUTO-EXCLUSIONS.md`). Beyond the audit sample, these were not checked: reason-1 records whose XML has no `<body>` (order 517, in the sample, was one), all 67 reason-2 keyword exclusions, the animal-plus-recording-term subset, and the two possibly relevant records without full text (893, 1820).
- Coder A could see the screening `reason` column (one-line summary of the decoded variable), not the evidence quotes.
- 'At-risk' means the test is of a type that step 1 found invalid under shared blocks; it does not mean the paper's conclusion is wrong.
