# How to reproduce

Commands run from the repository root unless a `cd` is shown. Environment in `ENVIRONMENT.md` (quick path: Python 3.12 with `pip install -r requirements/quick-path.txt`, or `requirements/quick-path-lock.txt` with every package pinned; the proofs need network access). The command blocks are bash. Runtimes are for the laptop in `ENVIRONMENT.md`.

Rule names used in the outputs: P1 binomial test of held-out accuracy; P2 trial-level permutation with refit (scikit-learn `permutation_test_score`); P3 trial-level permutation within runs (CoSMoMVPA tutorial rule); P4 training labels permuted, refit (PyMVPA tutorial); P5 the block permutation test (all labels permuted by block, refit).

## Overview

| Step | Section | What it shows | Time |
|---|---|---|---|
| Check the files | §1 | every hash list matches the files here; the 17 timestamp proofs | about 1 min |
| Rebuild every summary from the shipped rows | §2 | the tables behind every number of the paper, byte for byte | about 5 min |
| Recompute one simulation replicate | §2 | the same p values as the cloud row | about 20 s |
| Test the function; recount the survey; synthetic checks of steps 4 and 5 | §2 | `blockperm` tests and example; the survey's counts; ALL OK | about 3 min |
| Redraw the figures | §2 | Figs 1–2 and Extended Data Figs 1–10 from the shipped outputs, byte for byte | about 1 min |
| Full runs | §3 | every row from the raw data or the simulator | hours to days per step |

Quick path (about 10 minutes): §1 and §2. `NUMBERS.md` gives the source of every number.

## 1. Check the files

```bash
python prereg/check_hash_lists.py                                  # 29 hash lists; must end with "ALL OK"
python prereg/ots_verify_public.py $(find analyses -name '*.ots')  # 17 proofs; earliest Bitcoin block of each; must end with "ALL OK"
```

`check_hash_lists.py` reports nine data manifests separately (recordings and EEG features that are not redistributed); §3 checks them after the download. `prereg/README.md` lists each proof against the start of its run and the first time a result was read.

## 2. Rebuild the summaries (quick path)

The run rows are shipped as archives, each unpacking into the folder name it had on the machine that wrote it. `-k` keeps the files already shipped (for example the public copies of the machine records). On Linux, GNU tar stops at those files with `-k`; write `tar xzf <archive> --skip-old-files` for each archive.

```bash
(cd analyses/step2-comparison && tar xzkf runs_cloud.tgz && tar xzkf runs_allen.tgz && tar xzkf runs_add3.tgz)   # into runs/, runs_allen/, runs_add3/
(cd analyses/step2b-eeg && tar xzkf runs_cloud_2b_rerun49.tgz)                                                 # into runs/
(cd analyses/step3-ibl && tar xzkf runs_ibl.tgz)                                                                # into runs/
```

Rebuild each summary into a scratch folder and compare it with the shipped one; every `cmp` must print nothing.

```bash
OUT=$(mktemp -d)
cd analyses/step1-decomposition/code                                         # step 1, a few seconds
python summarize.py --rows ../runs/rows.jsonl --out $OUT && cmp $OUT/results.md ../results/results.md
python summarize_within_train.py --rows ../runs/within_train_rows.jsonl --out $OUT && cmp $OUT/within_train.md ../results/within_train.md
cd ../../step2-comparison/code                                               # step 2, about 1 min
python summarize_sim.py --runs ../runs --out $OUT && cmp $OUT/sim_summary.json ../results/sim_summary.json
python summarize_allen.py --rows ../runs_allen --out $OUT && cmp $OUT/allen_summary.json ../results/allen_summary.json
python summarize_add3.py --runs ../runs_add3 --main-runs ../runs --out $OUT && cmp $OUT/add3_summary.json ../results/add3_summary.json
python add3_summarize_tools.py --tools ../runs_add3/tools > $OUT/SUMMARY-TOOLS.md && cmp $OUT/SUMMARY-TOOLS.md ../runs_add3/tools/SUMMARY-TOOLS.md
cd ../../step2b-eeg/code                                                     # step 2b, about 10 s
python summarize_2b.py --rows ../runs --out $OUT && cmp $OUT/summary_2b.json ../results/summary_2b.json
cd ../../step3-ibl/code                                                      # step 3, about 3 min
python summarize_ibl.py --rows ../runs --order ../runs/ORDER.json --stim ../runs/STIM-REGIONS.json \
    --realism ../runs/REALISM.json --region-info ../meta/region_info.csv > $OUT/SUMMARY.md && cmp $OUT/SUMMARY.md ../runs/SUMMARY.md
cd ../../step4-fmri-haxby/code                                               # steps 4 and 5 (post hoc), a few seconds each
python summarize.py --step 4 --rows ../runs --features ../runs --out $OUT/s4 && cmp $OUT/s4/summary.json ../results/summary.json
python summarize.py --step 5 --rows ../../step5-pamap2/runs --features ../../step5-pamap2/runs --out $OUT/s5 && cmp $OUT/s5/summary.json ../../step5-pamap2/results/summary.json
cd ../../..
```

Each summary prints its tables; the `.md` files hold the same numbers as the `.json` files. On 2026-10-28 every `cmp` above found the files identical, in a clean copy with a fresh environment, and again on 2026-11-02 with `requirements/quick-path.txt` (with the Extended Data Fig. 3 summary and the figures below).

Recompute one simulation replicate from scratch (cell `c000`, replicate 0; about 20 s):

```bash
(cd analyses/step2-comparison/code && python run_grid.py --design random --B 12 --L 20 --tau-s 20 --drift 1 --split main \
    --reps 1 --n-perm 200 --seed 2026000 --out $OUT/c000.jsonl)
```

Compare it with replicate 0 of the shipped cloud rows (from the repository root):

```bash
python -c "import json,glob;n=json.loads(open('$OUT/c000.jsonl').readline());o=[r for f in glob.glob('analyses/step2-comparison/runs/c000_random_B12_tau20_d1_t0_main.w*.jsonl') for r in map(json.loads,open(f)) if r['rep']==0][0];[print(k,n[k],o[k],'same' if n[k]==o[k] else 'differs') for k in ('P1','P2','P3','P4','P5')]"
```

P2, P3 (undefined in this replicate), P4 and P5 print "same"; the binomial p value (P1, about 1e-27) differs only in the last floating-point digit.

Redraw the figures (Figs 1, 2a, 2b and Extended Data Figs 1–10) from the shipped outputs and compare them with the shipped PDFs (copied first into the scratch folder):

```bash
mkdir $OUT/pdf && cp figures/*.pdf $OUT/pdf/
(cd figures && python make_bc_figures.py > $OUT/values_bc.txt && python make_ed_figures.py > $OUT/values_ed.txt)
for f in $OUT/pdf/*.pdf; do cmp $f figures/$(basename $f); done
cat $OUT/values_bc.txt $OUT/values_ed.txt | cmp - figures/figures_values.txt
```

Both checks must print nothing (checked on 2026-11-02). The scripts overwrite the PDFs in `figures/` and also write PNG previews there. `figures/figures_values.txt` lists every plotted value with its source file and key.

The function, the fold-map check and the survey counts:

```bash
(cd blockperm && python -m pytest -q tests && python examples/fake_block_labels.py)
python analyses/foldmap/foldmap_check.py
(cd analyses/yaron-panel/code && python fixed_vs_repeated.py --from-csv ../results/null_draws.csv --out $OUT && cmp $OUT/fixed_vs_repeated.json ../results/fixed_vs_repeated.json)
python -c "import csv;r=[x for x in csv.DictReader(open('analyses/practice-survey/coding_final.csv')) if x['item']=='C2'];print(sum(x['final'] in ('trial-label permutation','binomial or parametric') for x in r),'of',len(r))"
python analyses/step4-fmri-haxby/code/test_synthetic.py
```

- The tests end with "12 passed"; one of them checks that the function gives the same scores and p values as the simulator used in the analyses (`analyses/step2-comparison/code/sim.py`). The example prints 14 (35%) for trial-level permutation and 1 (2%) for the block permutation test, out of 40 recordings with labels that carry no information.
- `foldmap_check.py` prints `maps_sha256` a2f34e49… on arm64 (as `foldmap_arm64_laptop.json`) and 2b94cd2f… on x86 (as `foldmap_x86_c2d.json`). The replicate-level comparison (800 of 800) is in `analyses/foldmap/replicate_*_compare.txt`, with its protocol in `REPLICATE-CHECK.md`; its scripts expect the working repository's layout (`PROVENANCE.md`).
- The Extended Data Fig. 3 summary is rebuilt from the shipped permutation scores (null means 0.0014 fixed, 0.1149 repeated); the full rerun from the raw data is in `analyses/yaron-panel/RESULTS-NOTE.md`.
- The survey recount prints "11 of 14" (trial-level tests; one code recoded on 2026-11-04, `practice-survey/final-check-2026-11-04/RESULT.md`); with `item=='C1'` and `x['final']=='shared'` it prints "14 of 14".
- `test_synthetic.py` runs the synthetic checks of steps 4 and 5 (about 1 min) and ends with "ALL OK", as in `analyses/step4-fmri-haxby/test_synthetic.out`; scikit-learn's warning that KFold ignores `groups` is expected.

## 3. Full runs

Raw data are not redistributed. The blocks below use bash and start from the set-up line, and each stops at once if the set-up line has not been run, so that no block touches the shipped tree. To rerun a step without touching the shipped files, work in a copy of its folder with the shipped rows removed, then rebuild the summary as in §2 and compare it with the shipped one. These runs were not repeated for this repository; the commands are those of the reported runs.

```bash
REPO=$(pwd); RERUN=$(mktemp -d); cp -R analyses $RERUN/; cd $RERUN/analyses
```

| Data | Size | Download | Run |
|---|---|---|---|
| Allen Visual Coding Neuropixels, 32 sessions | about 80 GB (74.5 GB for the 30 new mice) | depends on the connection | step 1: 8.6 + 2.5 core-hours |
| MPI LEMON, 40 participants | 12.8 GB | 1.5 h on the authors' connection (`eligibility/download.log`) | step 2b main arms: 8.5 h on one 56-vCPU machine (`runs/vm.log` in the archive) |
| IBL Brain-Wide Map, 459 sessions | about 96 GB in all, at most 1.2 GB per session; each worker deletes a session's spike files after counting, so the disk holds about 1.3 GB per worker | during the run, one session at a time | 6 h 8 min with 47 workers |
| Yaron et al. (2025), 19 files | 1.3 GB | depends on the connection | about 5 min to load, 2 min for 1,000 permutations |
| Haxby et al. (2001), PyMVPA distribution, 6 subjects (step 4) | 1.8 GB of archives | about 5 min (the run's `fetch.log`) | about 5 h for six subjects in parallel on the laptop of `ENVIRONMENT.md` (part of it in sleep cycles; `chain.log`) |
| PAMAP2, UCI archive (step 5) | 0.7 GB archive | about 3 min | about 2 h for eight subjects, six at a time, on the same laptop |

The simulation grid needs no data. It ran for about 13 h on one 56-vCPU machine (below).

### trackA-std and step 1 (Allen Brain Observatory Visual Coding Neuropixels; 32 sessions)

Needs h5py (`trackA-std/requirements.txt`). `<nwb folder>` is an absolute path. The download writes `MANIFEST.sha256` into the target folder; compare it with the shipped one.

```bash
: "${RERUN:?run the set-up line of section 3 first}"
cd "$RERUN/analyses"
python trackA-std/code/download_sessions.py --dir <nwb folder> --only all
diff <(sort <nwb folder>/MANIFEST.sha256) <(sort trackA-std/MANIFEST.sha256) && echo "data as in the manifest"
cd step1-decomposition && rm -f runs/rows*.jsonl runs/within_train_rows*.jsonl && cd code
IDS=$(python -c "import csv;print(','.join(r['session_id'] for r in csv.DictReader(open('../../trackA-std/sessions_trackA.csv'))))")
for k in 0 1 2 3; do python decompose.py --dir <nwb folder> --sessions $IDS --out ../runs/rows_$k.jsonl --worker $k --of 4 & done; wait
cat ../runs/rows_[0-9].jsonl > ../runs/rows.jsonl
for k in 0 1 2 3 4; do python within_train.py --dir <nwb folder> --sessions $IDS --out ../runs/within_train_rows_$k.jsonl --worker $k --of 5 & done; wait
cat ../runs/within_train_rows_[0-9].jsonl > ../runs/within_train_rows.jsonl
```

The Track A analysis itself (Supplementary Note 1) is shipped as its code, its pre-registration and its outputs (`trackA-std/results/`, `trackA-std/prereg-run/results/`); its run rows are not shipped except `runs/extra.jsonl`, so its tables are not rebuilt in §2.

Then §2 (step 1). The summaries report the compute used: 8.6 core-hours for `decompose.py` and 2.5 for `within_train.py`. `summarize.py` also compares the trial-level rows with `trackA-std/runs/extra.jsonl`.

### step 2 (simulation grid, mouse cells, toolboxes)

```bash
: "${RERUN:?run the set-up line of section 3 first}"
cd "$RERUN/analyses"
cd step2-comparison && find runs -name '*.jsonl' -delete && rm -rf runs_allen runs_add3/*.jsonl runs_add3/tools
PY=$(which python) WORKERS=<n> bash code/cloud_chain.sh       # Linux (sha256sum); the driver of the reported grid: every cell, the power pilot, the δ choice, the power cells
cd code && python allen_cells.py --dir <nwb folder> --out ../runs_allen/rows.w0.jsonl --worker 0 --of 1   # <nwb folder>: the Allen download of the step 1 block
PY312=<python 3.12> PY39=<python 3.9 with PyMVPA 2.6.5> COSMO=<CoSMoMVPA checkout at fe5acaf> W=<n> bash add3_run.sh   # addendum 3; Linux with GNU Octave
```

The reported grid ran on one 56-vCPU cloud machine from 2026-10-22 14:40 to 10-23 03:58 UTC (`runs/run.log` in `runs_cloud.tgz`), with the versions of `requirements/step2-cloud.txt`. Addendum 3 took about 5 h on a second machine, set up by `gcp/vm_add3_setup.sh` (Octave 8.4, CoSMoMVPA fe5acaf, PyMVPA 2.6.5 under Python 3.9; versions in `requirements/step2-add3-py312.txt` and `requirements/pymvpa-py39.txt`) and run by `gcp/vm_add3_go.sh`. The mouse cells (`allen_cells.py`) ran on the arm64 laptop. Cells with 24 equal blocks held out by `GroupKFold` give the same folds only on the same processor family. Rerun them on x86 to match the cloud rows, and the mouse cells on arm64 to match the shipped mouse rows, or pass the recorded folds explicitly (`analyses/foldmap/`, `ENVIRONMENT.md`). `RUN-PLATFORM.md` explains why the cloud rows are the result and the laptop rows serve only an equivalence check.

### step 2b (MPI LEMON resting EEG)

Needs MNE 1.13.2 (`pip install -r requirements/step2b-cloud.txt`). The download script rewrites `eligibility/EEG-MANIFEST.sha256` in the copy; compare it with the shipped one.

```bash
: "${RERUN:?run the set-up line of section 3 first}"; : "${REPO:?run the set-up line of section 3 first}"
cd "$RERUN/analyses/step2b-eeg/code"
rm -f ../runs/rows*.jsonl                                       # the shipped rows unpacked in §2; the runner skips jobs already in its output file
LEMON_DIR=<raw folder> bash download_eeg.sh                     # participants of ../eligibility/SUBJECTS.txt
cmp ../eligibility/EEG-MANIFEST.sha256 $REPO/analyses/step2b-eeg/eligibility/EEG-MANIFEST.sha256 && echo "data as in the manifest"
for k in $(seq 0 <n-1>); do LEMON_DIR=<raw folder> python preprocess.py --subjects ../eligibility/SUBJECTS.txt --out <features dir> --worker $k --of <n> & done; wait
mkdir -p ../runs-example && python run_2b.py --features <features dir> --subjects ../eligibility/SUBJECTS.txt --arms balanced --out ../runs-example/rows.w0.jsonl   # a small example, kept apart from ../runs
```

The last command above runs the balanced arm only, into its own folder. The reported cloud run (56 workers on one machine set up by `gcp/vm_setup.sh` with `requirements/step2b-cloud.txt`; machine record by `gcp/vm_machine.sh`) ran:

```bash
: "${RERUN:?run the set-up line of section 3 first}"
cd "$RERUN/analyses/step2b-eeg/code"
for k in $(seq 0 55); do python run_2b.py --features <features dir> --subjects ../eligibility/SUBJECTS.txt --out ../runs/rows.w$k.jsonl --worker $k --of 56 & done; wait   # all arms of DESIGN-v2-ADDENDUM.md §4, splits main, tool, block
for k in $(seq 0 55); do python run_2b.py --features <features dir> --subjects ../eligibility/SUBJECTS.txt --sensitivity --out ../runs/rows_sens.w$k.jsonl --worker $k --of 56 & done; wait
python graded_pilot2.py --features <features dir> --subjects ../eligibility/PILOT2-SUBJECTS.txt --out ../runs/graded_pilot2.json   # addendum 2 §4 (post hoc); chose rule N5
for k in $(seq 0 55); do python run_graded2.py --features <features dir> --subjects ../eligibility/SUBJECTS.txt --arms pos_graded,balanced_graded --splits main --graded-rule N5 --out ../runs/rows_graded2.w$k.jsonl --worker $k --of 56 & done; wait
python posthoc_alpha_slope.py --features <features dir> --rows ../runs --out <scratch>/alpha_slope.json   # Supplementary Note 3 (post hoc)
```

Then rebuild the step 2b summary as in §2.

The arms are defined in `DESIGN-v2-ADDENDUM.md` §4 and the graded control in `DESIGN-v2-ADDENDUM-2.md` (post hoc); `runs/vm.log` (in the archive) and `runs/COMPLETION-2b.txt` record each phase, the reviewed rerun of sensitivity worker 49 and the stopped unreviewed first rerun. The preprocessing order on the laptop is in `gcp/chain2b.sh` and `gcp/chain2b_add2.sh`. The first graded control (addendum 1 §5) did not reach its target power range, and its arms were not run (results note §4). `download_eeg.sh` uses the BSD form `stat -f %z`; on Linux use `stat -c %s`.

### step 3 (IBL Brain-Wide Map, 459 sessions)

Needs ONE-api 3.6.1, ibllib 4.1.0, scikit-learn 1.9.1 and the `brainwidemap` package at commit 118fc36 (github.com/int-brain-lab/paper-brain-wide-map; all pinned in `requirements/step3-ibl.txt`). The cloud machine was set up by `gcp/vm_ibl_setup.sh`.

```bash
: "${RERUN:?run the set-up line of section 3 first}"; : "${REPO:?run the set-up line of section 3 first}"
cd "$RERUN/analyses/step3-ibl/code"
rm -rf ../runs/rows.w*.jsonl ../runs/claims ../runs/SUMMARY.md           # the shipped rows unpacked in §2
python -c "from one.api import ONE; ONE(base_url='https://openalyx.internationalbrainlab.org', username='intbrainlab', password='international', silent=True)"   # the public IBL login, as in the scripts
python prep_ibl.py order --out ../runs/ORDER.json && cmp ../runs/ORDER.json $REPO/analyses/step3-ibl/runs/ORDER.json
python prep_ibl.py regions --region-info ../meta/region_info.csv --out ../runs/STIM-REGIONS.json
python prep_ibl.py budget-meta --order ../runs/ORDER.json --out ../runs/BUDGET-META.json
python prep_ibl.py realism --order ../runs/ORDER.json --out ../runs/REALISM.json
for k in $(seq 0 46); do python run_ibl.py --order ../runs/ORDER.json --n-sessions 459 --out ../runs/rows.w$k.jsonl --cache <cache folder>/$k --claims ../runs/claims & done; wait   # 47 workers, one ONE cache each
python summarize_ibl.py --rows ../runs --order ../runs/ORDER.json --stim ../runs/STIM-REGIONS.json --realism ../runs/REALISM.json --region-info ../meta/region_info.csv > ../runs/SUMMARY.md
cmp ../runs/SUMMARY.md $REPO/analyses/step3-ibl/runs/SUMMARY.md   # identical only if the public server returns the same data
```

`meta/region_info.csv` is the pinned copy of the `brainwidemap` file (step 3 results note §0). `gcp/vm_ibl_run.sh` is the driver of the main run, which used 47 workers on one 56-vCPU machine for 6 h 8 min (`RUNNOTE-2.md`). Download sizes per session are in `runs/DISK-SIZES.json`.

### steps 4 and 5 (post hoc; block-design fMRI and body-worn sensors)

Use the quick-path environment with nibabel 5.3.2 added (`pip install -r requirements/step4-5-laptop.txt`; nibabel is needed only by `prepare_haxby.py`). The runners stop if numpy or scikit-learn has another version. `code/chain_45.sh` is the orchestration that ran both steps after the timestamp proofs were attested (it waits for the attestations, checks the hash lists, then runs the commands below).

```bash
export OMP_NUM_THREADS=1
: "${RERUN:?run the set-up line of section 3 first}"
cd "$RERUN/analyses/step4-fmri-haxby/code"
python fetch_haxby.py --dir <data>/haxby                                   # MD5 against the server's MD5SUMS; writes MANIFEST.sha256
diff <data>/haxby/MANIFEST.sha256 ../runs/MANIFEST-haxby.sha256 && echo "data as in the manifest"
for i in 1 2 3 4 5 6; do python prepare_haxby.py --subject-dir <data>/haxby/subj$i --subject subj$i --out <data>/haxby/features; done
for i in 1 2 3 4 5 6; do python run_haxby.py --features <data>/haxby/features --subject subj$i --out-dir <rows> & done; wait
python summarize.py --step 4 --rows <rows> --features <data>/haxby/features --out <out>
cd ../../step5-pamap2/code
python fetch_pamap2.py --dir <data>/pamap2
diff <(grep Protocol <data>/pamap2/MANIFEST.sha256) <(grep Protocol ../runs/MANIFEST-pamap2.sha256) && echo "data as in the manifest"   # the archive hash can change if UCI repackages it
for i in $(seq 101 109); do python prepare_pamap2.py --file <data>/pamap2/Protocol/subject$i.dat --subject subject$i --out <data>/pamap2/features; done
for i in $(seq 101 108); do python run_pamap2.py --features <data>/pamap2/features --subject subject$i --out-dir <rows5> & done; wait   # subject109 is excluded by the preparation (the reported chain also started it, and it stopped at its exclusion check)
python ../../step4-fmri-haxby/code/summarize.py --step 5 --rows <rows5> --features <data>/pamap2/features --out <out5>
```

`code/chain_45.sh` is the run record and keeps the working-repository layout (`results/step4-fmri-haxby/`); the commands above are the same steps for this layout. The synthetic checks of both steps are in §2.

### practice survey: quote check

```bash
: "${RERUN:?run the set-up line of section 3 first}"
cd "$RERUN/analyses/practice-survey"
python fetch_fulltext.py        # the 14 full texts from Europe PMC into fulltext/; compared with fulltext-MANIFEST.sha256 (records can be updated)
python check_quotes.py          # strict pass: 107 of 140 quotes found (the others differ only in formatting); rewrites quote_check.md and quote_check.csv
python check_quotes_alnum.py    # second pass, spaces and punctuation ignored: 140 of 140; rewrites its line in quote_check.md
```

### yaron-panel (Extended Data Fig. 3; Zenodo 10.5281/zenodo.15531781, 19 files)

Needs h5py (`ENVIRONMENT.md`). The download checks each file against the Zenodo md5 and writes `MANIFEST.local.sha256`; compare it with the shipped manifest.

```bash
: "${RERUN:?run the set-up line of section 3 first}"
cd "$RERUN/analyses/yaron-panel/data"
python fetch_yaron.py                                           # into raw/; files already present and matching are skipped
diff MANIFEST.sha256 MANIFEST.local.sha256 && echo "data as in the manifest"
cd ../code
python fixed_vs_repeated.py --raw ../data/raw --cache <file.npz> --worker 0 --of 1 --parts <dir>
python fixed_vs_repeated.py --raw ../data/raw --cache <file.npz> --collect --parts <dir> --out <dir>
cmp <dir>/fixed_vs_repeated.json ../results/fixed_vs_repeated.json && cmp <dir>/null_draws.csv ../results/null_draws.csv
```
