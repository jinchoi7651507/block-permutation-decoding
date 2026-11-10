# Judgement of `review-results.txt` (analysis note, 2026-11-09 00:1x KST)
Checked by Claude: hashlib over DESIGN-v2.sha256 (3 differ: NOTES.md, code/matlab_port.py, code/run_reanalysis.py); gate.json behaviour p (0.03125, 0.6875, 0.84375, 0.6875 against 0.03, 0.69, 0.84, 0.68), Figure 4 cells and artefacts; untracked outputs (5 files).
| Item | Verdict |
|---|---|
| Q1 numbers | agree (no mismatch) |
| Q1 SHOULD 1.2 bullet, trial-shuffle minimum | valid |
| Q2 marks; SHOULD wording | agree; valid |
| Q3 code | agree |
| Q4 MUST section 1.7 replacement | valid in substance (the omitted limit and scope are required by DESIGN 2 item 5 and 6); text to be applied after the author's go |
| Q4 SHOULD known-difference sentence | valid |
| Q5 MUST 1-7 (section 1.8) | valid; checked items above; outputs committed now for provenance |
| Q5 SHOULD | valid |
Applied now: outputs committed (record only). Text changes to RESULTS.md: waiting for the author.

## Re-check (`review-results-recheck.txt`, 2026-11-09 00:5x KST)
| Item | Verdict | Applied |
|---|---|---|
| 1 scope "verdict for this study" | valid (only context decoding was tested) | replaced |
| 2 "did not touch the data of the tests" | valid (the gate records outputs only) | replaced |
| 3 "10 distinct arrangements" | valid (DESIGN 2 item 1) | replaced |
| 4 deviation dates | valid (RUNNOTE 03:08, 11:33, 03:07) | added |
| 5 /Users/ path in out/tests.log | valid (1 line; checked) | not changed (committed record); for the public step: leave out or note in PROVENANCE |
