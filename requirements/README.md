# Pinned environments

| File | Environment | Source of the versions |
|---|---|---|
| `quick-path.txt` | Python 3.12: hash and proof checks, every summary of `REPRODUCE.md` §2, the figures, `blockperm` tests | checked in a fresh environment on 2026-11-02 |
| `quick-path-lock.txt` | the same, with every package pinned | `pip freeze` of the fresh environment in which §1–§2 passed byte for byte on 2026-11-03 |
| `../analyses/trackA-std/requirements.txt` | Python 3.12: Track A and step 1 (Allen download and runs) | written with the Track A run |
| `step2-cloud.txt` | Python 3.12: step 2 simulation grid (cloud) | `pip freeze` in `runs/MACHINE.txt` inside `analyses/step2-comparison/runs_cloud.tgz` |
| `step2-add3-py312.txt`, `pymvpa-py39.txt` | addendum 3: the cells (Python 3.12) and PyMVPA 2.6.5 (Python 3.9); Octave 8.4 and CoSMoMVPA fe5acaf are installed by `analyses/step2-comparison/gcp/vm_add3_setup.sh` | `pip freeze` in `runs_add3/MACHINE.txt` inside `runs_add3.tgz` |
| `step2b-cloud.txt` | Python 3.12 with MNE 1.13.2: step 2b arms (cloud); set-up `analyses/step2b-eeg/gcp/vm_setup.sh` | `pip freeze` in `runs/MACHINE.txt` inside `runs_cloud_2b_rerun49.tgz` |
| `step3-ibl.txt` | Python 3.12 with ONE-api 3.6.1, ibllib 4.1.0, scikit-learn 1.9.1, `brainwidemap` at 118fc36; set-up `analyses/step3-ibl/gcp/vm_ibl_setup.sh` | `pip freeze` in `analyses/step3-ibl/runs/MACHINE.txt` |
| `step4-5-laptop.txt` | Python 3.12 with nibabel 5.3.2: steps 4 and 5 (post hoc fMRI and body-worn sensors) on the laptop | the step folders' `requirements.txt`, asserted by the runners |

The step 2 mouse cells and the step 2b preprocessing ran on the laptop of `ENVIRONMENT.md` with the step 2 and step 2b versions.
