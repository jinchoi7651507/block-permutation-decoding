# Judgement of `review-results.txt` (analysis note, 2026-11-09 12:2x KST; author's overnight instruction: decide and act within reach, report in the morning)
Checked by Claude: `note_tables.py` reproduces the 1.3 and 1.4 values and the Q4 slopes, fitted nulls, adjusted p and 98.3rd percentiles independently of the reviewer's scripts; `cell_tests.py` l.179 returns only n_prog and n_neurons (n_qual computed in `cellport.py` l.180 and returned by `run_decoder`; dropped at `cell_tests.py` l.179); `run_cell.py` l.230 stores G11 means only, `cell_gate.py` l.170 z-test on the estimated-template port only; hp 300,0 in the gate run file.
| Item | Verdict | Applied |
|---|---|---|
| Q1-Q3 | agree | |
| MUST 1 | valid (FEF observed exceeds the null mean by about 1 SD) | yes |
| MUST 2 | valid | yes |
| MUST 3 | valid (Q4 reproduced; wording "null mean") | yes |
| MUST 4 | valid (DESIGN 8) | yes |
| MUST 5 | valid (DESIGN 5d) | yes |
| MUST 6 | valid (checked in code); cannot be recovered without a rerun | reported, section 1.7 item 6 |
| MUST 7 | valid (DESIGN 5) | yes |
| SHOULD 1 | valid | yes |
| SHOULD 2 | valid (cut) | yes |
| SHOULD 3-7 | valid | yes (S4 `note_tables.py`, 1.7 item 7; S6 dated line; S7 `a2-gatefile-check.out`) |
| P7 margin | noted, mark unchanged (rule applied as stamped) | no |

## Re-check (`review-results-recheck.txt`, 2026-11-09 12:2x KST)
| Item | Verdict | Applied |
|---|---|---|
| 1 Holm threshold applies to the first rejection only | valid (Holm: later steps need 1/30, 1/20) | replaced |
| 2 n_qual location | valid (checked in `cellport.py`) | replaced above |
| 3 source of the gate-run C counts | valid | added |

## Addendum 3 results (`review-addendum3-results.txt`, 2026-11-09 15:2x KST)
All four MUST valid (retry log checked: one HTTP 500 and one IncompleteRead; largest p 2.008e-06); applied.
