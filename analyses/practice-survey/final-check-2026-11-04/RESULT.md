# Pre-submission recheck of the practice survey: result (2026-11-04 12:5x KST; protocol `PROTOCOL.md`, committed bbea383 before the runs)

Eleven fresh `claude -p --model opus --tools "Read"` runs, three at a time, each inside its own folder; all returned, none with `is_error`, all JSON parsed (`raw/`, prompts in `prompts/`). Record and study texts stay in the session scratchpad (not redistributed).

## Part 1: the 40 sampled automatic exclusions
40 of 40 excluded; no record judged include or unclear. No disagreement with the original audit, the 2026-11-02 check or the author's hand check.

## Part 2: the 70 codes of the 14 included studies
61 supported, 9 not (1 contradicted on C4, 1 unclear on C1, 1 contradicted on C2, 6 unclear on C5).

| Study | Item | Code | Checker | Claude's check | Proposed |
|---|---|---|---|---|---|
| six studies (PMC12443960, PMC12660755, PMC12872450, PMC13418543, PMC13433320, PMC13633270) | C5 | yes | unclear: the code statement "is not in the full text body" | **Input artifact.** The checker received the `<body>` only; code statements sit in back matter (checked for PMC12443960: the statement is in `<back>`; all 140 quotes, the C5 quotes included, were found in the full XML by the 2026-11-02 quote check) | Keep "yes". |
| PMC10783789 | C4 | none | contradicted: one secondary analysis decodes baseline against TS from neurons chosen by a TS-selectivity score computed on all frames ("Similar results were obtained for models trained on selective neurons only") | **Valid as stated** (quotes found in the full text). The main decoders use all neurons. C4 is not part of the at-risk definition, so no count changes. | Author: recode to "yes, on all trials (secondary analysis)" in `coding_final.csv` (dated) and Supplementary Table 2, or keep "none" (main analysis) with a table note. |
| PMC12873149 | C1 | shared | unclear: the fold assignment is not stated | **Kept by Claude:** the third pass of 2026-10-20 resolved "shared" from the design (each class occupies its own session or epoch, so held-out frames share it with training frames; a whole-block hold-out would leave a class untrained). The checker did not weigh the design. | Keep "shared". |
| PMC12873149 | C2 | unclear | contradicted: the Fig. 4D legend gives the test, "Decoding accuracy from data was compared with those that came from null models of shuffled data … paired Student's t-test" | **Valid** (passage read in the full text by Claude). The 2026-10-20 resolution said "shuffle form not stated; protocol forbids inference", but the test of significance itself is stated in the legend: a parametric test against shuffled-data accuracy, which is the scheme's "binomial or parametric vs chance". The coders quoted only the Methods sentence. | Author decision; see below. |

## What a recode of PMC12873149 C2 would change
- At-risk (C1 shared and C2 in {binomial or parametric, trial-label permutation}): 10 of 14 → **11 of 14** (Wilson 95% 45–88% → 52–92%). It was the protocol's upper bound "11 of 14 counting unclear" (SUMMARY.md).
- Text: abstract "10 treated trials as independent" → 11; main text first paragraph "10 assessed significance …" → 11; SN 2 Result ("Ten of them … nine permuted trial labels and one used a binomial or parametric test" → eleven, nine, two; "Of the other four … in one the test could not be determined" → three, none undetermined) and Supplementary Table 2 row; NUMBERS and README; `coding_final.csv` with a dated correction (the REPRODUCE recount would then print 11 of 14); SUMMARY.md correction line. The cover letter ("most used one of these tests") is unchanged.
- Whether the abstract change needs a blind is the author's call (one digit, same sentence).

Nothing has been changed.

## Applied (author 2026-11-04 15:4x: "apply your recommendation" (translated from Korean); f92dd43)
- PMC12873149 C2: unclear → binomial or parametric in `../coding_final.csv` (resolution column records the recode and its reason); at-risk 11 of 14 (Wilson 52–92%) in the abstract, main text, SN 2 (with one sentence on the recode) and Supplementary Table 2, README, NUMBERS, REPRODUCE; correction line in `../SUMMARY.md`.
- PMC10783789 C4: code kept "none"; Supplementary Table 2 cell "none (main analysis; one secondary analysis selected units on all trials)"; note in the resolution column.
- C1 of PMC12873149 and the six C5 codes kept, as judged above.
