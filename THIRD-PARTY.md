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

The toolboxes were run, not modified: CoSMoMVPA in GNU Octave 8.4.0 and PyMVPA 2.6.5 in Python 3.9 (`ENVIRONMENT.md`).
