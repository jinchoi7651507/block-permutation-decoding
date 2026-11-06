# blockperm: a block permutation test for cross-validated decoding

`block_permutation_test_score` tests a cross-validated decoding score when the labels follow recording blocks (for example conditions presented in blocks of consecutive trials) and training and test trials may come from the same blocks. It has the call pattern of scikit-learn's `permutation_test_score`:

```python
from blockperm import block_permutation_test_score

score, null_scores, p = block_permutation_test_score(
    pipeline, X, y, blocks=block_id, cv=KFold(5, shuffle=True, random_state=0), n_permutations=1000, random_state=0)
```

## What it does
- Each permutation permutes the labels of whole blocks between blocks, so the labels of training and test trials move together and every block keeps its trials.
- The whole cross-validation is rerun for every permutation, including every step fitted to the labels. Put scaling, feature or neuron selection and the model in one scikit-learn `Pipeline`.
- `strata` restricts the permutation to blocks within the same stratum (for example within a run or a session).
- `draw` replaces the permutation with a user-given generator of block-label vectors, for example pseudosessions drawn from the task's own block generator.
- With few blocks the function enumerates every distinct arrangement (`exact="auto"`) and warns about the smallest attainable p value. With two blocks per class there are six arrangements, but for a two-class decoder an arrangement and its class swap give the same score, so p cannot fall below about one in three.

## When it is valid
- The enumerated null is exact, and the sampled p value valid, when the observed assignment was drawn uniformly from the set the function permutes over: all arrangements of the block labels, or all arrangements within `strata` if the design randomized within strata (for example within runs). Permuting across a unit the design did not randomize over can reject too often. For a constrained randomization (counterbalancing, limits per run), pass the design's own generator as `draw`.
- With a fixed block order, the test assumes that blocks are exchangeable under the null. Slow drift that follows the order can break this assumption, and then the test can reject or be conservative. A design with random block order, or several blocks per condition in random order, avoids the problem.
- With `GroupKFold` and blocks of equal size, the block-to-fold map depends on the tie order of `numpy.argsort`, which differs between platforms (arm64 and x86 gave different maps for 24 blocks with the same versions). For a result that reruns identically elsewhere, pass explicit folds (a list of train/test index pairs) or a shuffled `GroupKFold` with a seed (scikit-learn 1.6 or later), and record the folds.

## Why not the defaults
In the analyses this function accompanies, three rules that toolboxes run were tested on labels with no information, assigned to recording blocks, with training and test trials sharing blocks:
- trial-level permutation with the cross-validation rerun (scikit-learn `permutation_test_score`, MVPA-Light);
- trial-level permutation within runs (the CoSMoMVPA tutorial rule);
- permutation of training labels only, with test labels kept (the PyMVPA tutorial rule).

All three rejected far more often than 5%. Permuting block labels and rerunning the whole cross-validation stayed near 5% in random block designs. With a fixed block order the result depends on the data. In the simulated fixed orders the test was conservative (0–2.4% with shuffled 5-fold). In resting EEG with fixed orders aligned with slow drift it rejected often (first half against second half in most recordings, a pairs-of-blocks order in 29%), and it stayed near 5% for an order orthogonal to a linear trend. There the blocks were not exchangeable (label = time; see "When it is valid"). With labels that vary trial by trial, the first two rules stayed near 5%, and the training-label rule was somewhat above it (up to about 11–12%); the large excess arises when labels follow blocks. `examples/fake_block_labels.py` shows the effect on a synthetic drifting recording.

## One-line changes per tool
- **scikit-learn:** call `block_permutation_test_score` with `blocks=`. Passing `groups=` to `permutation_test_score` restricts the shuffle to within groups; with labels constant within blocks, every permutation then returns the observed labels.
- **CoSMoMVPA / PyMVPA:** permute chunk-level labels across chunks (one label per chunk, all trials of a chunk together) within the unit the design randomized over (within runs if blocks were randomized within runs; `strata=` here), and rerun the cross-validation.
- **PyMVPA training-label permutation:** permute the labels of all trials, training and test, block by block.

## Install and test
Python 3.12 with numpy, scipy and scikit-learn (tested with numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2):

```sh
pip install .                   # from this folder (the module and its dependencies); or copy blockperm.py into a project
python -m pytest tests          # about 45 s on one core
python examples/fake_block_labels.py
```

The test `test_equivalence_with_reference` checks that, with `exact=False`, the same `random_state` Generator and the same folds, this function returns the same observed score, null scores and p value (except that it returns no null when the observed score is undefined) as the reference implementation used in the analyses (`analyses/step2-comparison/code/sim.py` in the paper's repository; another location can be given with `REFERENCE_SIM_DIR`), for shuffled 5-fold, re-split stratified 5-fold, GroupKFold by block and a user `draw`; it is skipped when that file is not present. With the default `exact="auto"`, designs with no more arrangements than `n_permutations` are enumerated instead (the null then has one score per arrangement).

## Not included
No `n_jobs` and no fit parameters (unlike `permutation_test_score`); the permutations run one after another. License: MIT (`LICENSE`).
