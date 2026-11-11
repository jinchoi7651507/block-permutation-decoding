# blockperm

A block permutation test for cross-validated decoding. Use it when the labels follow recording blocks (for example, conditions presented in blocks of consecutive trials) and training and test trials can come from the same blocks.

`block_permutation_test_score` has the same call as scikit-learn's `permutation_test_score`, plus `blocks=`:

```python
from blockperm import block_permutation_test_score

score, null_scores, p = block_permutation_test_score(
    pipeline, X, y, blocks=block_id,
    cv=KFold(5, shuffle=True, random_state=0), n_permutations=1000, random_state=0)
```

You can try it in the browser without installing anything: [demo in Colab](https://colab.research.google.com/github/jinchoi7651507/block-permutation-decoding/blob/main/blockperm/examples/blockperm_demo.ipynb) (about two minutes).

## Why

Slow drift makes recording blocks distinguishable. When training and test trials share blocks, tests that permute single trials, or only the training labels, call labels with no information decodable far more often than 5%. Permuting the labels of whole blocks and refitting the whole pipeline in every permutation keeps the rate near 5% when conditions were assigned to blocks at random. The preprint has the measurements: https://doi.org/10.5281/zenodo.24012190

## What it does

- Each permutation moves the labels of whole blocks, so training and test labels move together.
- The whole cross-validation is rerun in every permutation. Put every step fitted to the labels (scaling, feature or neuron selection, the model) in one scikit-learn `Pipeline`.
- `strata=` permutes only within a run or a session.
- `draw=` takes your own generator of block labels, for example pseudosessions from the task's block generator.
- With few blocks, every distinct arrangement is enumerated, and a warning gives the smallest p value you can get.
- `permutation_test_score(..., groups=blocks)` does not do this: it shuffles within groups, and with one label per block nothing moves.

## When it is valid

- The p value is exact when conditions were assigned to blocks at random, from the set the function permutes over (all blocks, or within `strata`).
- With a fixed block order, the test assumes that blocks are exchangeable. Drift that follows the order can break that.

## Install

```sh
pip install blockperm
```

Python 3.12 or later, with numpy and scikit-learn. One CPU core is enough. The permutations run one after another (no `n_jobs`).

## Documentation and citation

The tutorial, a MATLAB and Octave port, and the analyses behind the preprint are at https://github.com/jinchoi7651507/block-permutation-decoding.

If you use blockperm, please cite:
Choi, D. (2026). Common decoding tests fail when training and test trials share recording blocks. Zenodo. https://doi.org/10.5281/zenodo.24012190

License: MIT.
