# block_permutation_test for MATLAB and Octave

`block_permutation_test.m` is a MATLAB port of `block_permutation_test_score` in `../blockperm.py`. The Python function is the reference implementation. The MATLAB port was not used for any result of the accompanying paper.

It works with any MATLAB decoding code that can be wrapped in a function of the label vector. You pass a function that takes a label vector and returns a cross-validated score. The test calls it once with the real labels and once for every permutation, so every step fitted to the labels is fitted again.

```matlab
% X: trials x features, y: one label per trial, run: block (run) of each trial
folds = mod(randperm(numel(y))', 5) + 1;               % fixed folds, shared by every call
score_fcn = @(labels) my_cv_accuracy(X, labels, folds);  % fits the whole pipeline on these labels
[score, null, p] = block_permutation_test(score_fcn, y, run, 'NPermutations', 1000, 'Seed', 0);
```

Options: `'Strata'` (permute only within, for example, sessions), `'Draw'` (a function handle called with no arguments that returns one label per block, for example a pseudosession; it should use MATLAB's global random stream so that `'Seed'` fixes its draws), `'Exact'` (`'auto'`, `true` or `false`), `'Seed'`. `help block_permutation_test` lists them.

## With MVPA-Light

Keep the folds fixed across calls and put the classifier inside the score function.

```matlab
% MVPA-Light: predefined folds so that every call uses the same split
cfg = struct('classifier', 'lda', 'metric', 'accuracy', 'cv', 'predefined', 'fold', folds, 'feedback', 0);
score_fcn = @(labels) mv_classify(cfg, X, labels);
[score, null, p] = block_permutation_test(score_fcn, y, run);
```

Run on the EEG features of `crosscheck/` with MVPA-Light 942ce39 in Octave 11.3.0 (which needs the Octave packages `statistics` and `datatypes` for MVPA-Light): the same labels gave the same score on repeated calls, and the test ran. Other toolboxes need the same two properties, fixed folds and the classifier fitted inside the function. Only the MVPA-Light call above was run.

## Checks

- `test_block_permutation_test.m`: unit checks (errors, exact p, strata, seeds, `Draw`, cell-array labels) and the rejection rate on labels with no information assigned to drifting blocks (4.0% of 200 datasets in Octave 11.3.0; `test_block_permutation_test.out`).
- `crosscheck/`: the same exact null in Python and in MATLAB on real EEG (PhysioNet EEG Motor Movement/Imagery, subject 1, runs 3–14, 12 runs, 924 arrangements; nearest-centroid decoder, fixed folds). The nulls agreed to 2.2e-16 and the p values were equal, for the real labels and for labels with no information (`crosscheck/crosscheck.out`). The exact enumeration uses no random numbers, so equal results are expected for any data. Sampled permutations use each language's random generator, so sampled nulls agree in distribution, not number by number.

Run the checks:

```
cd matlab
octave --no-gui --eval "test_block_permutation_test" > test_block_permutation_test.out
python crosscheck/make_eegbci_features.py OUT                          # needs mne; downloads the EEG data
python crosscheck/run_python_check.py OUT
octave --no-gui --eval "cd crosscheck; run_matlab_check('OUT')"
octave --no-gui --eval "cd crosscheck; run_mvpa_light_example('OUT', 'path/to/MVPA-Light')"
```

In MATLAB, run `test_block_permutation_test` from the `matlab` folder.

Tested with Octave 11.3.0. The code avoids features missing from Octave and should run in MATLAB R2016b or later; it has not been run in MATLAB.
