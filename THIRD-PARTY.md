# Third-party files

`analyses/step2-comparison/toolbox-src/` holds excerpts of the toolboxes whose permutation rules the paper tests. They document the rules as shipped (`analyses/step2-comparison/TOOLBOX-DEFAULTS.md`). Files marked "timestamped" are named in `DESIGN-v2-ADDENDUM-3.sha256` and are kept byte for byte. Each file keeps the license of its project; the license texts are in `LICENSES/`.

| File | Project, commit | Copied | License (text in `LICENSES/`) | Timestamped |
|---|---|---|---|---|
| `sk_validation.py` | scikit-learn `sklearn/model_selection/_validation.py`, 106573971c | 2026-10-20 | BSD-3-Clause, © the scikit-learn developers (`scikit-learn-COPYING.txt`) | no |
| `mne_base.py` | MNE-Python, 0616647f51 | 2026-10-20 | BSD-3-Clause, © MNE-Python authors (`MNE-Python-LICENSE.txt`) | no |
| `mvl_stats.m` | MVPA-Light `statistics/mv_statistics.m`, 942ce39377 | 2026-10-20 | MIT, © Matthias Treder (`MVPA-Light-LICENSE.txt`) | no |
| `cosmo_rand.m` | CoSMoMVPA, fe5acaf303 | 2026-10-20 | MIT (Expat), © Nikolaas N. Oosterhof and CoSMoMVPA contributors (`CoSMoMVPA-COPYING.txt`) | yes |
| `cosmo_balance_partitions.m`, `cosmo_check_partitions.m`, `cosmo_classify_lda.m`, `cosmo_run_permutation_test.m`, `cosmo_faq_l580-600.rst`, `cosmo_faq_l1150-1200.rst` (line ranges of the FAQ) | CoSMoMVPA, fe5acaf303 | 2026-10-26 | as above | yes |
| `pymvpa_permutation.py`, `pymvpa_tut.rst` | PyMVPA, f699189b5b | 2026-10-20 | MIT, © Michael Hanke, Yaroslav Halchenko, Nikolaas N. Oosterhof (`PyMVPA-COPYING.txt`) | no |
| `pymvpa-2.6.5/pymvpa265_permutation.py`, `pymvpa265_stats.py`, `pymvpa265_libsvm_link.txt` | PyMVPA release 2.6.5 | 2026-10-26 | MIT, as above; `pymvpa265_stats.py` also contains code taken from SciPy, BSD, © Enthought, Inc. (`SciPy-LICENSE.txt`) | yes |
| `adam_first.SOURCE.txt` | pointer to ADAM `qsub/adam_MVPA_firstlevel.m`, 27fefb9e19; the file itself is not redistributed | 2026-10-20 | ADAM is GPL-3.0 | no |

Other third-party material: `analyses/step6-reanalysis-cell/code/cellport.py` and `analyses/step6b-reanalysis-sciadv/code/matlab_port.py` are Python ports of code deposited with the studies (Zenodo 10.5281/zenodo.10529801 and 10.5281/zenodo.16333867, CC BY 4.0; the headers name the sources, and the two files are hash-listed, so the license is stated here). `analyses/yaron-panel/code/yaron_pipeline.py` is a Python port of the code deposited with Yaron et al. (2025; Zenodo 10.5281/zenodo.15531880, MIT, © 2025 Amit Yaron, text in `LICENSES/PEON-LICENSE.txt`; the header names the source). `analyses/step3-ibl/meta/region_info.csv` comes from `paper-brain-wide-map` (MIT, `LICENSES/paper-brain-wide-map-LICENSE.txt`). `analyses/step6-reanalysis-cell/S3-legend.txt` quotes a legend of the supplement of Jahn et al. (2024; article CC BY 4.0), kept because the timestamped design relies on it. `analyses/step2b-eeg/eligibility/markers/` holds BrainVision header and marker files (`.vhdr`, `.vmrk`) of the public MPI LEMON release, which is shared under the Open Data Commons Public Domain Dedication and License (PDDL).

The toolboxes were run, not modified: CoSMoMVPA in GNU Octave 8.4.0 and PyMVPA 2.6.5 in Python 3.9 (`ENVIRONMENT.md`).
