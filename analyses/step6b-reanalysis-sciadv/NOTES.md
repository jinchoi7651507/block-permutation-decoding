# Notes for the reviewer (stage 1, 2026-11-04 KST)

Stage 1 only: no data member was downloaded, opened or read. Nothing in this folder is committed. The main session commits.

## 1. What was read
- Full text: `<scratchpad>/impact1104/PMC13418543.txt` (plain-text conversion of PMC13418543).
- Our scout note: `revised-manu/practice-survey/impact-scout-2026-11-04/RESULT.md`.
- Our implementation: `code-package/blockperm/blockperm.py` and its `README.md`.
- Zenodo API record 16333867 (metadata only): one file, `Klee_ScienceAdv_data_code.zip`, 3,572,288,274 bytes, md5 18c4429be98ed9595009292caf478ded, created 2026-07-21. The record description says it holds 2 files (an article PDF and the zip); the API lists only the zip.

## 2. Zip central directory and extracted members
HTTP range requests worked (HTTP 206). The central directory (47 members) was read with about 5 kB of range requests and written to `manifest-zenodo-16333867.tsv` (name, uncompressed size, compressed size, CRC-32, date) by `code/fetch_members.py list`.

Extracted to `authors-code/` (code and documentation only; CRC-32 checked by zipfile; about 200 kB fetched in total). The same list is in `authors-code/EXTRACTED.tsv`.

| Member | Bytes |
|---|---|
| readme_Data Structure Contents.docx | 27,316 |
| Figure Functions/Figure1.m | 15,948 |
| Figure Functions/Figure2.m | 18,101 |
| Figure Functions/Figure3.m | 20,774 |
| Figure Functions/Figure4.m | 91,243 |
| Figure Functions/FigureS1.m | 38,013 |
| Figure Functions/FigureS2.m | 37,503 |
| Figure Functions/FigureS3.m | 21,836 |
| Figure Functions/FigureS4.m | 16,092 |
| Figure Functions/FigureS5.m | 15,018 |
| Figure Functions/FigureS6.m | 39,013 |
| Figure Functions/FigureS7.m | 85,252 |
| Figure Functions/FigureS8.m | 86,987 |
| Support Functions/Bonsai/GetBonsai_AllGoNoGo2p.m | 2,814 |
| Support Functions/Bonsai/GetBonsai_HitRate.m | 226 |
| Support Functions/Bonsai/GetBonsai_Joystick.m | 1,339 |
| Support Functions/Bonsai/GetBonsai_JoystickPsth.m | 2,399 |
| Support Functions/Bonsai/GetBonsai_LickTrace.m | 1,365 |
| Support Functions/Bonsai/GetBonsai_Optopara.m | 1,611 |
| Support Functions/Bonsai/GetBonsai_Sounds.m | 1,333 |
| Support Functions/Bonsai/GetBonsai_VideoTimestamps.m | 1,369 |
| Support Functions/Bonsai/GetBonsai_Weight.m | 1,525 |
| Support Functions/Bonsai/GetBrukerVoltage.m | 709 |
| Support Functions/Bonsai/Get_2P_Frames_At_BonsaiEvents.m | 2,903 |
| Support Functions/Bonsai/Get_DLC.m | 2,117 |
| Support Functions/Bonsai/Get_DLC2p.m | 2,184 |
| Support Functions/Bonsai/Get_TextFile.m | 1,382 |
| Support Functions/MATLAB/dF_Anya_test.m | 2,162 |
| Support Functions/MATLAB/GoToneHitRate.m | 2,755 |
| Support Functions/MATLAB/GoToneHitRate2.m | 2,448 |
| Support Functions/MATLAB/roiMatchPub.m | 24,490 |
| Support Functions/MATLAB/shadePlot2.m | 1,330 |
| Support Functions/MATLAB/slanCM.m | 3,612 |

Not extracted: all seven `.mat` members under `Data Structures/` (largest: the muscimol structure, 3.6 GB uncompressed; `Switching_2p_Struc_Main.mat` is 246.5 MB), `slanCM_Data.mat` (colormap data) and `slanCM.asv` (an editor autosave).

Authors' paths: five extracted files contain the authors' own absolute paths (example file paths on their machines and lab server): `Support Functions/Bonsai/GetBonsai_Joystick.m`, `GetBonsai_Weight.m`, `GetBonsai_Optopara.m`, `GetBonsai_VideoTimestamps.m`, `Get_DLC.m`. They are left byte-identical, are not used by our port, and should not be shipped without review. The figure scripts use `cd('/Structures')` before loading data.

## 3. Code paths used for the port
- `Figure Functions/Figure4.m`, Panel D (lines 832-1085): context decoder. Per mouse (`Switching_2p_Struc_Main(s)`, s = 1..6): dF/F by `dF_Anya_test`, Figure 4 cell filter (more than one upward crossing of 30 % in the 5-frame moving mean, none of 500 %), z-score; trials at `Hit` events of cued (`BlockType == 2`) then self-paced (`BlockType == 1`) blocks, -5 to +5 s, 2-frame bins (150 bins); artefact trials (mean over cells above 10) set to NaN; one balanced subsample (`datasample` without replacement); per bin `fitcsvm` linear, `cvpartition(n,'KFold',20)`; `numShuffles = 50` with `randperm` of all labels and a new partition; the plotted chance is the mean of the 50 shuffles, plotted from -1 to +1 s. No formal test is computed in Panel D.
- Panel F (lines 1352-1610): movement decoder, bin w vs bin 45 (-2.02 s) of the same trials, `numWorkers = 12`.
- `FigureS6.m` Panel B: decoder on the population mean (one feature), standardised, 10 folds, 100 shuffles, also stores the 95th shuffle percentile. In the plotting code the shuffle mean is shifted (`dShuff = dShuff(:,plotWindow)+6`); we do not know why. Panel C (neuron-dropping curve, "exceeded chance levels in all animals"): bins 74-76 averaged, standardised, 20 folds, 10 neuron subsets, 20 shuffles.
- `Figure2.m` Panels F-G: all cells with valid dF/F (filter commented out), trial averages; clustering on the self-paced press-aligned average (frames 91-210), Ward linkage on Euclidean distances, `maxclust` 3. The Methods describe clustering on cue-aligned activity of n = 1,271 neurons; the Results give 1,261 and the code clusters the self-paced press-aligned matrix.
- `Figure1.m` Panels F-J: per mouse, mean over the three blocks of each type (`mean`, not `nanmean`), then `signrank` across the 6 mice. Panel F uses `ReactionTimeFromTrialStart`.
- `dF_Anya_test.m`: the baseline is the 50th percentile of each 60-s window placed at the window start, linearly interpolated and extrapolated. The paper text also mentions Gaussian smoothing, which this function does not do. Because the window median is placed at the window start, a slow linear trend leaves a residual of half a window of the trend (synthetic ramp: about -9 %, test T2). We port this behaviour exactly.

## 4. Inferred, to be checked on the real files (stage 2)
- One element of `Switching_2p_Struc_Main` per mouse, one continuous imaging session per mouse covering all six blocks (the code loops `s = 1:6` and plots six curves).
- Block membership: block index = number of `BlockType` changes along the event list, assuming events are in recording order. To be checked: six blocks per mouse in the order 2,1,2,1,2,1.
- `EventID` is compared with `'Hit'` with `==` in MATLAB, so it is probably a categorical or string array. scipy cannot read those objects; `code/loader.py` falls back to the mat-io package (installed in `<venv>`, version 1.0.2). Not tested on the real file. If it fails, the fallback is to ask the reviewer for a MATLAB export of the four fields, or to parse the MCOS subsystem by hand.
- MATLAB `predict` on NaN rows: unknown whether these count as errors. We remove artefact trials before subsampling instead (DESIGN 3.4).
- Behaviour fields are scalars per block (the MATLAB assignment would fail otherwise).

## 5. Open questions for the reviewer
1. Fig. 4D gate: the paper gives no decoding numbers. Is digitising Fig. 4D (six time points, real and shuffle) from the published figure acceptable as the gate reference, with tolerance 3 points (real) and 2 points (shuffle)? If not, the gate can rest on the counts, clusters and behaviour only, and the decoding curve becomes descriptive.
2. ITI window: the paper's "intertrial periods" is not defined. We chose -3.95 to -2.08 s before the reward threshold crossing (before any possible cue). Is that an acceptable reading, or should the window be post-reward (for example +2 to +5 s)?
3. Power under drift: in simulation (T10), strong block-level drift removed most of the block test's power for a moderate event-locked signal. Should the drift check (DESIGN 4.6) be promoted to a pre-condition for interpreting a null block result, for example "a null result is called uninformative if the same-condition first-vs-last decoding exceeds a stated accuracy"?
4. Alpha: two windows, each at 0.05 without correction (separate claims). Keep, or use 0.025?
5. R = 4 repeats and D = 1,000 draws give about half a day on 6 cores. Acceptable, or reduce D to 500 for the ITI window?
6. The neuron count gate accepts 1,261 or 1,271 (Results vs Methods) as long as it equals the length of the saved cluster labels. Is that the right reading of the discrepancy?
7. Should the per-cluster decoders (Fig. 4J-L) or the cue-window decoder (Fig. 4E) be added? They are outside v1 to keep one primary contrast per window.

## 6. Files
- `DESIGN.md`: design v1, draft.
- `code/matlab_port.py` (preprocessing port), `code/decode.py` (statistic, tests, group nulls), `code/loader.py` (to be checked), `code/fetch_members.py` (range-request listing and extraction), `code/run_reanalysis.py` (stage 2 driver: `gate`, then `tests`, refuses tests unless the gate passed), `code/summarize.py` (tables and verdict sentences), `code/test_synthetic.py`.
- `test_synthetic.out`: output of the full synthetic run.
- `manifest-zenodo-16333867.tsv`, `authors-code/` (extracted code and readme), `authors-code/EXTRACTED.tsv`.
- Paths: the code finds `code-package/blockperm` relative to its own location; data folder, output folder and the zip URL are command-line arguments.

## 7. Added 2026-11-07 (after the v1 persona reviews)
- Correction to the stage-1 notes in the main session (copied from DESIGN.md section 0, review stat S10): the smallest group p (2/20)^6 = 10^-6 is right; a remark of 2026-11-04 that it should be 1/20^6 forgot the class swap.
- Open questions 1 to 7 of section 5 were decided in DESIGN.md section 0 and confirmed by the author on 2026-11-07 (11:5x KST); the item-3 clarification was confirmed at 16:3x KST and the Fig. 4D gate range (bins 60-90) at 17:2x KST. DESIGN.md section 9 lists the answers to the v1 reviews.
- MATLAB `signrank` p for n = 6 is a multiple of 1/32 only if it uses the exact distribution without ties; the published 0.68 (Fig. 1J) is not on that grid, so the gate treats a p value as fatal only if it falls on the other side of 0.05 (DESIGN.md 3.5).
- New stage: `run_reanalysis.py inspect` (writes `out/fields.txt`), required before `gate`. The `--fig-ref` argument no longer exists.

## Stamp record (2026-11-08 01:5x KST)
- `DESIGN-v2.sha256` committed 7b6092e (2026-11-08 00:09 KST), OTS submitted 00:09 KST (475fd8e).
- Earliest Bitcoin attestation: block 974945 at 2026-11-07 15:17:29 UTC (2026-11-08 00:17:29 KST), verified with `brief-communication/prereg/ots_verify_public.py` (ALL OK, file hash matches the proof).
- No data member was downloaded or opened before the attestation.
