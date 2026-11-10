# Environment

All analyses are Python except the two toolboxes run as shipped (CoSMoMVPA in Octave, PyMVPA 2.6.5). The cloud runs record one thread per process (`OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`; `MACHINE.txt`), and the cloud drivers set it; the laptop runs of the mouse cells set `OMP_NUM_THREADS=1`, and step 1 and `trackA-std` did not record it. The step 2b record shows `vCPU: 1` because of this setting; the machine had 56 vCPUs. Parallelism came from separate worker processes with seeds fixed per task, so the number of workers does not change any result.

## Where each analysis ran

| Analysis | Machine | Versions recorded with the run |
|---|---|---|
| `trackA-std` (earlier mouse analysis; first benchmark with labels that carry no information) | laptop: MacBook, Apple A18 Pro, 8 GB RAM, macOS 26.6.2 | Python 3.12.3, numpy 2.4.6, scipy 1.18.1, h5py 3.16.0 (`trackA-std/requirements.txt`) |
| `step1-decomposition` | the same laptop | Python 3.12.3; package versions not written into the run logs; the logs show the `trackA-std` environment of the row above (the summaries reproduce byte for byte with the quick-path environment below) |
| `step2-comparison`, simulation grid (the reported run) | Google Compute Engine c2d-highcpu-56 (AMD EPYC 7B13, 56 vCPU), Ubuntu 24.04.5 | Python 3.12, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2 (full `pip freeze` in `runs/MACHINE.txt` inside `runs_cloud.tgz`) |
| `step2-comparison`, mouse cells and the laptop equivalence run | the laptop | as above (`RUN-PLATFORM.md`) |
| `step2-comparison`, addendum 3 and the toolboxes | c2d-highcpu-56 (AMD EPYC 7B13), Ubuntu 24.04.5 | Python 3.12 with numpy 2.5.4 for the cells; GNU Octave 8.4.0 with CoSMoMVPA fe5acaf; PyMVPA 2.6.5 in Python 3.9 with numpy 1.21.6, scipy 1.7.3, scikit-learn 1.0.2 and its bundled libsvm (`runs_add3/MACHINE.txt` inside `runs_add3.tgz`) |
| `step2b-eeg`, preprocessing | the laptop (`runs/prep.out`, `runs/prep.log`) | Python 3.12.3, MNE 1.13.2, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2 (`DESIGN-v2-ADDENDUM.md`) |
| `step2b-eeg`, arms and controls | c2d-highcpu-56 (AMD EPYC 7B13), Ubuntu 24.04.5 | MNE 1.13.2, numpy 2.5.4, scikit-learn 1.7.2 (`runs/MACHINE.txt` inside the archive) |
| `step3-ibl`, main run | c2d-highmem-56 (AMD EPYC 7B13, 56 vCPU, 440 GB), Ubuntu 24.04.5 | ONE-api 3.6.1, ibllib 4.1.0, scikit-learn 1.9.1, numpy 2.5.4, scipy 1.18.1, `brainwidemap` at commit 118fc36 (`runs/MACHINE.txt`, with `pip freeze`) |
| `step3-ibl`, summary | the laptop | Python 3.12.3, numpy 2.5.4, scipy 1.18.1, pandas 2.3.3 |
| `yaron-panel` (Extended Data Fig. 3) | the laptop | Python 3.12.3, numpy 2.4.6, scipy 1.18.1, h5py 3.16.0, matplotlib 3.10.9 (`yaron-panel/RESULTS-NOTE.md`) |
| `step4-fmri-haxby`, `step5-pamap2` (post hoc) | the laptop (`chain_45.sh`; one process per subject, `OMP_NUM_THREADS=1`) | Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2, nibabel 5.3.2 (step 4; `requirements.txt` of each step); the runners stop with other numpy or scikit-learn versions |
| `step6-reanalysis-cell` | Google Compute Engine c2d-highcpu-56 (AMD EPYC 7B13, 56 vCPU), Ubuntu 24.04 | Python 3.12.3, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, h5py 3.14.0; threads and platform recorded in the outputs |
| `step6b-reanalysis-sciadv` | the laptop, macOS arm64, 6 workers | Python 3.12, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2, mat-io 1.0.2, h5py 3.16.0, pandas 3.1.1 |

## Quick-path environment

```sh
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements/quick-path.txt   # numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2, pandas 2.3.3, h5py 3.16.0, matplotlib 3.10.9, pytest, opentimestamps
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

With this environment every summary in `REPRODUCE.md` §2 and every figure is rebuilt byte for byte from the shipped files (checked on 2026-10-28 and, with h5py and matplotlib added, on 2026-11-02 on the laptop above). Pinned versions for the full runs, from the `pip freeze` recorded with each run, are in `requirements/` (`requirements/README.md`).

## Platform differences

- scikit-learn's `GroupKFold` with blocks of equal size assigns blocks to folds by the tie order of `numpy.argsort`, which differs between arm64 and x86 with the same versions. For 24 equal blocks this gives different folds on the laptop and on the cloud machine; for 4 and 12 blocks the maps are the same. The reported cells are the cloud (x86) run. `analyses/foldmap/` shows the two maps and a replicate-level check: on an x86 machine, and on the laptop with the x86 map passed as explicit folds, every p value of the affected cells equals the cloud value (800 of 800).
- The IBL data are read through the ONE API from the public server (`openalyx.internationalbrainlab.org`) with the Brain-Wide Map freeze `2023_12_bwm_release`.
