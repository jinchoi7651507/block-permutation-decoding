# Judgement of `review-addendum2.txt` (Claude, 2026-11-08 22:0x KST)
| Item | Verdict | Applied |
|---|---|---|
| MUST 1 section 2 sentence | valid; checked in the authors' code: `plot_Fig2_cross_temporal_decoding.m` l.1540 stores `Classification_net_correct` from the `..._900ms_NN_<n>` files as `Classification_net_correct_comb`, l.1609-1611 nanmean; `plot_Fig2_ET_pseudo_pop.m` l.60-71 loads the same files, l.173-175 mean | replaced, with the field name added |
| MUST 2 no --addendum | valid | stated; the wrapper refuses it |
| SHOULD 1 save test output, hash list | valid | `test_run_cell_a2.out`; list below |
| SHOULD 2 fallback to Figure_2_PCA.mat | valid (fixed before any value is read) | coded and tested |
| SHOULD 3 descriptive _net vs _combined; RUNNOTE line | valid | `compare-names`; run note |
| SHOULD 4 test through the entry point, positive case | valid | 8 checks |
| SHOULD 5 fresh out folder | valid | `out-a2/` |
| SHOULD 6 python -I | valid | docstring |
| Re-check MUST: other spellings of --addendum | valid (argparse accepts `--addendum=` and abbreviations; no other runner option starts with --a) | refused; test added |
| Re-check SHOULD 1: shape guard in compare-names | valid | applied |
| Re-check SHOULD 2: hash list contents | valid | applied |
