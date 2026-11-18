# Pre-submission recheck of the practice survey: result (2026-11-04; protocol `PROTOCOL.md`, written before the runs)

Eleven fresh `claude -p --model opus --tools "Read"` runs, three at a time, each inside its own folder; all returned, none with `is_error`, all JSON parsed (`raw/`, prompts in `prompts/`). Record and study texts are not redistributed; `../final-check-2026-11-02/scripts/extract.py` builds the record texts.

## Part 1: the 40 sampled automatic exclusions
40 of 40 excluded; no record judged include or unclear. No disagreement with the original audit, the 2026-11-02 check or the author's hand check.

## Part 2: the 70 codes of the 14 included studies
61 supported, 9 not (1 contradicted on C4, 1 unclear on C1, 1 contradicted on C2, 6 unclear on C5).

| Study | Item | Code | Checker | Second reading | Outcome |
|---|---|---|---|---|---|
| six studies (PMC12443960, PMC12660755, PMC12872450, PMC13418543, PMC13433320, PMC13633270) | C5 | yes | unclear: the code statement "is not in the full text body" | **Input artifact.** The checker received the `<body>` only; code statements sit in back matter (checked for PMC12443960: the statement is in `<back>`; all 140 quotes, the C5 quotes included, were found in the full XML by the 2026-11-02 quote check) | kept "yes" |
| PMC10783789 | C4 | none | contradicted: one secondary analysis decodes baseline against TS from neurons chosen by a TS-selectivity score computed on all frames ("Similar results were obtained for models trained on selective neurons only") | **Valid as stated** (quotes found in the full text). The main decoders use all neurons. C4 is not part of the at-risk definition, so no count changes. | kept "none" (main analysis), with a note in the resolution column and in Supplementary Table 2 |
| PMC12873149 | C1 | shared | unclear: the fold assignment is not stated | **Kept:** the third pass of 2026-10-20 resolved "shared" from the design (each class occupies its own session or epoch, so held-out frames share it with training frames; a whole-block hold-out would leave a class untrained). The checker did not weigh the design. | kept "shared" |
| PMC12873149 | C2 | unclear | contradicted: the Fig. 4D legend gives the test, "Decoding accuracy from data was compared with those that came from null models of shuffled data … paired Student's t-test" | **Valid** (passage read in the full text). The 2026-10-20 resolution said "shuffle form not stated; protocol forbids inference", but the test of significance itself is stated in the legend: a parametric test against shuffled-data accuracy, which is the scheme's "binomial or parametric vs chance". The coders quoted only the Methods sentence. | recoded to "binomial or parametric" |

## Outcome (2026-11-04)
- PMC12873149 C2: unclear → binomial or parametric in `../coding_final.csv` (the resolution column records the recode and its reason). At-risk studies (C1 shared and C2 in {binomial or parametric, trial-label permutation}): 10 of 14 → 11 of 14 (Wilson 95% 45–88% → 52–92%), the protocol's upper bound "11 of 14 counting unclear" (`../SUMMARY.md`). The REPRODUCE recount prints 11 of 14.
- PMC10783789 C4: kept "none" (main analysis); one secondary analysis selected units on all trials, noted in the resolution column.
- PMC12873149 C1 and the six C5 codes: kept, as judged above.
