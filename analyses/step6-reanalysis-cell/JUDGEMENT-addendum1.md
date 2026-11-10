# Judgement of `review-addendum1.txt` (Claude, 2026-11-08 17:3x KST)

| Item | Verdict | Check |
|---|---|---|
| MUST 1 VM hashes before the stamp | valid | Without it the pilot run is not bound to the stamped file. Applied: VM restarted only to hash the run folder (no data), `vm-hashes2.txt`. |
| MUST 2 count of checks | valid | `test_synthetic-vm.out`: 54 PASS lines, the FAIL at line 81, one PASS after it. Applied as written. |
| SHOULD 1 RUNNOTE entry | valid | Applied. |
| SHOULD 2 placeholder branch | valid | Applied as written. |
| SHOULD 3 dated-addendum path not tested | valid | Applied as one sentence. |
| A-D | agree | Hash d06b5a82... confirmed locally (shasum at 17:29; the reviewer's hashlib check agrees; project rule is hashlib). |
Scope: documents and records only; no analysis, test or runner code changed by these items.

## 1b. Judgement of `review-addendum1b.txt` (Claude, 2026-11-08 17:3x KST)
| Item | Verdict | Applied |
|---|---|---|
| Addendum 1 MUST 1-2 resolved | agree | |
| 1b MUST 1 save the refusal check output | valid | `fetch-refusal-check.out` (17:38, exit 0), listed in `ADDENDUM-1b.sha256` |
| 1b SHOULD 1 refusal check as an assertion | valid | `fetch_data.py` raises if no unlisted member or if the refusal fails; rerun passed |
| 1b SHOULD 2 order before the download | valid | sentence added to Addendum 1b |
| 1b SHOULD 3 `python -I` | valid | docstring and run command |
| 1b SHOULD 4 author go for 1b | valid | recorded as not put to the author separately; reported on return |
| 1b SHOULD 5 RUNNOTE line | valid | added |
| RUNNOTE chronology slip | noted | not edited (running log); order stated here |
