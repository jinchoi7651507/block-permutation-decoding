# Pre-submission recheck of the practice survey by a fresh Opus 5.5 (protocol written 2026-11-04 12:4x KST, before any run)

Plan entry (root plan, "제출 직전 할 일 추가", 2026-11-03): before submission, fresh Claude Opus 5.5 instances recheck (1) the 40 sampled automatic exclusions and (2) the 70 codes of the 14 included studies against the full texts. Author's go: 2026-11-04 12:4x.

**Part 1, the 40 exclusions.** Same records, criteria and input as `../final-check-2026-11-02/` (record texts built mechanically from the Europe PMC XML fetched on 2026-11-02 by `../final-check-2026-11-02/scripts/extract.py`; the Europe PMC core record for the two without full text). Four batches of 10, each a fresh `claude -p --model opus --tools "Read"` run inside a folder holding only the criteria and its ten record files (relative paths). The checker does not see the automatic reason, the earlier audits or the author's statement. Output per record as in 2026-11-02: include / exclude (first failing criterion) / unclear, with a verbatim quote.

**Part 2, the 70 codes.** For each included study, a text file with its five codes (`../coding_final.csv`: item, final value, the quote the code rests on) and the whole body of its full text (the XML in `../fulltext/`, checked against `../fulltext-MANIFEST.sha256`, all sections, whitespace collapsed). Seven batches of two studies, each a fresh Opus instance as above. The checker reads the coding scheme (`../PROTOCOL.md` items C1–C5, verbatim) and, for every code, answers: supported / contradicted / unclear, with every sentence of the full text that contradicts the code or bears on it outside its quote (for example a whole-block hold-out, a block or session permutation, a statement that the decoder was refit or fixed, or unit selection on the labels), quoted verbatim.

**Reading (fixed now).**
- Part 1: a record is a disagreement if the checker says include or unclear.
- Part 2: a code is a disagreement if the checker says contradicted or unclear. A changed code would change the survey counts only through C1 (shared vs blocked) or C2 (test type) of the at-risk definition, or C3 for fixed decoders.
- Every disagreement is listed with the quotes for the author, who decides. Nothing in the manuscript or SN 2 changes before that. If no disagreement is found, the result is recorded and the manuscript stays as it is.
- At most three runs at a time; runs with `is_error` or without parseable JSON are voided and rerun with the same prompt. Results in this folder (`raw/`, `RESULT.md`); full texts and record texts stay unshipped.
