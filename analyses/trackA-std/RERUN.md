# Track A rerun on the standard drifting-grating table (2026-10-18 23:35 KST, written and committed before running)

**Why.** The independent reproduction of the post hoc conventional control found that in 8 of the 30 new sessions (761418226, 762120172, 762602078, 763673393, 791319847, 797828357, 798911424, 799864342) the planned loader took the first interval table whose name contains `drifting_gratings`, which there is `drifting_gratings_contrast_presentations` (2 Hz, nine contrasts). PREREG-trackA §3 specifies the drifting gratings with all five temporal frequencies pooled, i.e. `drifting_gratings_presentations`. The author asked to rerun everything on the correct table.

**Status.** A deviation from PREREG-trackA §4 ("script unchanged"), made after the pre-registered outputs were seen, to meet §3's definition. The pre-registered run (`results/trackA/`) stays as committed; both are reported.

**Change (only this).** `code/ephys-matched-null.py:87` and `code/trackA_extra.py:92` select `drifting_gratings_presentations` by name. Every other file is a copy of `results/trackA/` (diff against it). The 24 sessions with one table are unaffected in data, but the shared null generator makes later sessions' null draws change wherever an earlier session's area units change.

**Commands.** PREREG-trackA README §5 unchanged (P1 good/all/sdk with `--dump-draws`; `trackA_extra.py` 4 workers; `trackA_summarize.py --runs runs --out results`), same 32 NWB (hashes match MANIFEST), Python 3.12.3, numpy 2.4.6, scipy 1.18.1, h5py 3.16.0. Gate 2 (original rows equal `expected/`) applies unchanged. The conventional control is rerun with `--conventional-draws` in a separate P1 good run whose other outputs must be byte-identical to the main P1 good run.
