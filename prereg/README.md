# Pre-specification and timestamps

Every analysis except Extended Data Fig. 3a (post hoc, `analyses/yaron-panel/`, not timestamped) and the practice survey (protocol committed, not timestamped) was specified in a design document that was reviewed, committed and timestamped with OpenTimestamps. Only a digest derived from the SHA-256 of a hash list (or of the document) is sent to the calendar servers. The Bitcoin block that later includes it is third-party evidence that the file existed by the block time. A proof can carry several attestations, one per calendar server; the earliest block is the one that counts and the one listed below.

The designs and their proofs stay next to the files they cover, in `analyses/<step>/`, because each hash list names its files by paths relative to that folder. This folder holds the index below and two check scripts.

```sh
python prereg/check_hash_lists.py                                  # every hash list against the files here: ALL OK
pip install opentimestamps
python prereg/ots_verify_public.py $(find analyses -name '*.ots')  # 23 proofs; earliest block of each; ALL OK (needs network access)
```

Times are UTC. "Run start" is the start of the analysis the proof covers; "first read" is the first time any result of that analysis was opened; pilot outputs seen earlier are listed in each results note §0.

| Proof (in `analyses/`) | What it fixes | Committed | Earliest block | Run start | First read | Order |
|---|---|---|---|---|---|---|
| `trackA-std/PREREG-trackA.md` | earlier mouse analysis and the first benchmark with labels that carry no information (30 mice) | 2026-10-13 14:53 (9428c78, under an earlier folder name) | 971261, 10-13 15:18 | 10-16 15:06; rerun 10-18 14:33 (see notes) | 10-16 15:36 | block before run |
| `step1-decomposition/DESIGN.sha256` | step 1 design v2 (post hoc: designed after the Track A results): why those labels pass, fixed and refitted decoders | 10-19 18:15 | 972191, 10-19 18:25 | 10-19 18:16 | after 20:45 | run started 9 min before the block; no result read before it |
| `step1-decomposition/DESIGN-ADDENDUM.sha256` | addendum (post hoc): permutation of training labels only | 10-20 05:55 | 972271, 10-20 05:59 | 10-20 05:55 | about 06:30 | run started 4 min before the block; no result read before it |
| `step2-comparison/DESIGN-v2.sha256` | simulation grid and the permutation rules of common toolboxes | 10-21 02:51 | 972410, 10-21 03:37 | 10-21 13:07 (laptop); 10-22 14:40 (cloud, the reported run) | 10-23 (see notes); main results 10-26 | block before run |
| `step2-comparison/DESIGN-v2-ADDENDUM.sha256` | addendum 1: mouse cells, power, group-level test | 10-21 13:44 | 972486, 10-21 13:52 | 10-22 | 10-23 (see notes); main results 10-26 | block before run |
| `step2-comparison/RUN-PLATFORM.sha256` | the cloud run is the result; the laptop run serves only an equivalence check | 10-22 14:38 (decision, c5d1d41); 14:43–14:44 (reviewed text and hash list) | 972625, 10-22 15:00 | 10-22 14:40 | 10-23 | decision committed before the cloud start; final text and proof a few minutes after it; no result read before the block |
| `step2-comparison/DESIGN-v2-ADDENDUM-3.sha256` | addendum 3 (post hoc; one replicate of cell a063 seen before it was stamped): fixed orders, toolbox splits, CoSMoMVPA and PyMVPA as shipped | 10-26 04:12 | 973186, 10-26 04:33 | about 05:20 | about 11:30 | block before run |
| `step2b-eeg/DESIGN-v2.sha256` | step 2b: the same rules on MPI LEMON resting EEG | 10-21 03:18 | 972412, 10-21 03:40 | after the block (download) | 10-26 | block before run |
| `step2b-eeg/eligibility/SUBJECTS.sha256` | the participants drawn for step 2b | 10-21 04:23 | 972419, 10-21 04:34 | download 10-21 13:25 (`eligibility/download.log`, written in KST) | no result (participant list) | block before download |
| `step2b-eeg/DESIGN-v2-ADDENDUM.sha256` | addendum 1: preprocessing and arms | 10-22 02:43 | 972558, 10-22 03:03 | after the block | 10-26 | block before run |
| `step2b-eeg/DESIGN-v2-ADDENDUM-2.sha256` | addendum 2 (post hoc): second graded control and cloud run | 10-22 13:54 | 972621, 10-22 14:21 | 10-23 14:27 | 10-26 | block before run |
| `step3-ibl/DESIGN-v1.sha256` | step 3: the IBL brain-wide map | 10-22 03:08 | 972561, 10-22 03:31 | 10-26 | 10-27 | block before run |
| `step3-ibl/DESIGN-v1-CODE-ADDENDUM.sha256` | code addendum 1: runner, preparation, machine and budget rule | 10-26 05:15 | 973195, 10-26 05:49 | 10-26 06:32 | 10-27 | block before run |
| `step3-ibl/DESIGN-v1-CODE-ADDENDUM-2.sha256` | code addendum 2: the summary script | 10-26 06:03 | 973197, 10-26 06:04 | 10-27 (after the main run) | 10-27 | block before run |
| `step3-ibl/BUDGET-OUTCOME.sha256` | sessions, workers and time cap of the main run | 10-26 15:32 | 973255, 10-26 16:21 | 10-26 17:05 | 10-27 | block before run |
| `step4-fmri-haxby/DESIGN-v2.sha256` | step 4 (post hoc): the same rules on block-design fMRI (Haxby et al. 2001) | 11-02 09:49 | 974245, 11-02 10:42 | 11-02 11:32 (download) | 11-02 16:32 | block before download |
| `step5-pamap2/DESIGN-v2.sha256` | step 5 (post hoc): the same rules on body-worn sensors (PAMAP2) | 11-02 09:49 | 974245, 11-02 10:42 | 11-02 16:31 (download) | 11-02 21:46 | block before download |
| `step6-reanalysis-cell/DESIGN-v2.sha256` | step 6: reanalysis of Jahn et al. (2024) | 11-07 18:15 | 974962, 11-07 18:28 | 11-08 11:18 (download) | 11-09 03:17 | block before download |
| `step6-reanalysis-cell/ADDENDUM-1.sha256` | addendum 1: test-suite fixes only | 11-08 08:33 | 975049, 11-08 10:18 | suite pilot 07:58 (no data); download 11:18 | 11-09 03:17 | pilot before the stamp, data after the block |
| `step6-reanalysis-cell/ADDENDUM-1b.sha256` | addendum 1b: data-fetch wrapper | 11-08 08:39 | 975049, 11-08 10:18 | 11-08 11:18 | 11-09 03:17 | block before run |
| `step6-reanalysis-cell/ADDENDUM-2.sha256` | addendum 2: gate file | 11-08 13:20 | 975069, 11-08 13:37 | 11-08 17:16 | 11-09 03:17 | block before run |
| `step6-reanalysis-cell/ADDENDUM-3.sha256` | addendum 3 (written after the results were read): design replay and the true-template z-test promised by the design | 11-09 03:39 | 975126, 11-09 03:44 | 11-09 04:33 | 11-09 06:25 | block before run |
| `step6b-reanalysis-sciadv/DESIGN-v2.sha256` | step 6b: reanalysis of Klee et al. (2026) | 11-07 15:09 | 974945, 11-07 15:17 | download 11-07 16:52; tests 11-08 07:44 | 11-08 15:04 | block before download |

Notes
- **Step 1.** Both proofs were submitted when the runs started; their attestations were fetched only later. For both, the run started a few minutes before the block and no result was opened before it. The designs were committed before the runs (63050a0, a7252cc).
- **Step 2, first read.** Before the main results were opened on 10-26, two things were seen on 10-23 and are stated in the step 2 results note (§0): the power-pilot rates printed by the equivalence check, and the p values of one replicate (replicate 0 of addendum-3 cell a063, before addendum 3 was written).
- **Track A.** The outputs shipped in `trackA-std/` come from a rerun on 2026-10-18 that selects the drifting-grating table by name (`trackA-std/RERUN.md`). It is a stated deviation from the pre-registration, decided after the pre-registered outputs had been seen; those outputs are in `trackA-std/prereg-run/results/`. Step 1 builds on the rerun.
- **Practice survey.** Its protocol (`practice-survey/PROTOCOL.md`) was committed before the search, but not timestamped.
- `step3-ibl/BUDGET-OUTCOME.sha256` names seven cloud scripts by their path in the working repository (`../../working-archive/2026-10-26/gcp/`); they are in `analyses/step3-ibl/gcp/`, and `check_hash_lists.py` reads them there.
- **Time zones.** Times in this table are UTC; the results notes, run notes and laptop logs give KST (UTC+9).
- **Where the run starts are recorded.** Track A: `trackA-std/RERUN.md` and its logs; step 1: `step1-decomposition/runs/START.txt`, `START-within-train.txt`; step 2: `runs/run.log` in `runs_cloud.tgz`, `runs_add3/run.log` in `runs_add3.tgz`; step 2b: `runs/prep.log` (laptop) and `runs/vm.log` in `runs_cloud_2b_rerun49.tgz`; step 3: `runs/run.log` in `runs_ibl.tgz` and `RUNNOTE-2.md`; steps 4 and 5: `step4-fmri-haxby/runs/chain.log` (KST). "First read" comes from the results notes (§0 of each).
- **Commits.** The commit identifiers in the table are those of the authors' working repository, whose history is not part of this repository; the proofs and the byte-identical files are the evidence.
- **Step 2b, worker 49.** Before the reviewed rerun of sensitivity worker 49, a first rerun was started before its wrapper had been reviewed; it was stopped and its partial output was set aside unopened (`runs/COMPLETION-2b.txt`).
- **Step 2b, first graded control.** The graded control of addendum 1 did not reach its target power range on the pilot subjects and its arms were not run (results note §4); addendum 2 (post hoc) replaced it.
- **Steps 4 and 5.** Both designs were committed together and stamped in one submission, so both proofs carry block 974245. A chain script, written after the stamp and not under it (`step4-fmri-haxby/code/chain_45.sh`), waited for the attestations, checked the hash lists and only then downloaded the data. The step 4 runs went on while the laptop cycled between sleep and dark wake on battery; this changed only the run time (`step4-fmri-haxby/RESULTS-NOTE.md` §0).
- **Steps 6 and 6b.** Both are reanalyses of published data, so the first read follows the block. For step 6, the first data run (11-08 11:18) stopped at the gate with no value read; the rerun is Addendum 2. For step 6b, gate run 1 failed and two port fixes followed; the gate outputs before and after are in `out/gate-runs/`.
- Deviations from each design are listed with their dates in the step's run note or results note and summarized in `PROVENANCE.md`.
