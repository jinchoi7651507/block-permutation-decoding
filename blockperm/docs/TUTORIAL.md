# Using the block permutation test

This guide shows how to test a cross-validated decoding score when the labels follow recording blocks. Use it when conditions were presented in blocks of consecutive trials (or runs, or sessions) and the label of every trial in a block is the same.

## 1. Install

From a copy of the repository:

```
pip install ./blockperm
```

It needs Python 3.12, numpy and scikit-learn. A release on PyPI is planned.

## 2. The basic call

`block_permutation_test_score` takes the arguments of scikit-learn's `permutation_test_score`, plus the block of each trial.

```python
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from blockperm import block_permutation_test_score

pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
score, null_scores, p = block_permutation_test_score(
    pipeline, X, y, blocks=block_id,
    cv=KFold(5, shuffle=True, random_state=0), n_permutations=1000, random_state=0)
```

- `X` has one row per trial, `y` one label per trial, `block_id` the block of each trial.
- Each permutation moves the labels of whole blocks between blocks. Training and test trials keep the label of their block, so they move together.
- The whole pipeline is fitted again for every permutation. Put every step that uses the labels inside the pipeline: scaling, feature or neuron selection and the classifier. A step fitted once outside the pipeline is not refitted and can make the test reject too often.
- When permutations are sampled, `p` is `(1 + number of null scores >= score) / (n_permutations + 1)`, and a null score that is NaN counts as at least the observed score. When all arrangements are enumerated (section 6), `p` is `(1 + number of other arrangements with a score >= the observed score) / (number of arrangements)`.

## 3. Folds

- The folds may put trials of the same block in training and test sets (for example `KFold`), or hold out whole blocks (for example `GroupKFold`). Both kinds of folds are supported. The validity conditions in section 7 apply to both.
- `groups="blocks"` (the default) passes the blocks to the splitter, so `GroupKFold` holds out whole blocks. Splitters that ignore groups, such as `KFold`, work with the default too.
- To get the same folds on every computer, pass the folds as a list of `(train_index, test_index)` pairs, or use a splitter with a fixed `random_state`. With `GroupKFold` and blocks of equal size, the assignment of blocks to folds can differ between platforms.

## 4. Permute within the unit the design randomized over

If blocks were assigned to conditions at random within each run or session, permute only within that unit:

```python
cv = KFold(5, shuffle=True, random_state=0)   # as in section 2
score, null_scores, p = block_permutation_test_score(
    pipeline, X, y, blocks=block_id, strata=run_id, cv=cv, n_permutations=1000, random_state=0)
```

`strata` has one value per trial and must be constant within each block. Permuting across a unit that the design did not randomize over can reject too often.

## 5. Use the task's own block generator

If the block sequence came from a known random generator (for example a task that switches blocks with a given probability), pass a function that draws new block sequences from it. The test then compares the observed score with scores on fake sequences from the same generator (pseudosessions).

```python
from blockperm import block_labels_of
block_labels, _ = block_labels_of(y, block_id)   # observed label of each block, in the order of np.unique(block_id)

def draw(rng):
    # one label per block, in the same order; replace this line with the task's own generator
    return rng.permutation(block_labels)

score, null_scores, p = block_permutation_test_score(
    pipeline, X, y, blocks=block_id, draw=draw, cv=cv, n_permutations=1000, random_state=0)   # cv as in section 2
```

## 6. Few blocks

- With few blocks there are few distinct ways to arrange the block labels. When there are no more arrangements than `n_permutations`, the function scores every arrangement once (`exact="auto"`) and the p value is exact.
- The smallest possible p value is one over the number of arrangements. For two classes with two blocks each there are 6 arrangements. With balanced blocks, a refitted two-class classifier gives the same score to an arrangement and to its class swap, so p cannot fall below 2/6 here. The function warns when there are fewer than 20 arrangements.
- Plan several blocks per condition. With 6 blocks per class there are 924 arrangements.

## 7. Fixed block order

The p value is valid when the observed assignment of blocks to conditions was drawn uniformly at random from the arrangements being permuted, and exact when all arrangements are enumerated. For a constrained randomization such as counterbalancing, pass the design's generator as `draw` (section 5). With a fixed order (for example A B A B, the same in every session), the test assumes that the blocks are exchangeable under the null. Slow changes over the session that follow the order can break this assumption, and the test can then reject without any information about the condition. For a fixed order:

- report the correlation of the labels with time (block position) next to the result;
- check the analysis on fake labels that follow time, for example the first half of the session against the second half;
- prefer a random block order, or several blocks per condition in random order, when designing new experiments.

## 8. Check your own pipeline with labels that carry no information

`examples/fake_block_labels.py` assigns labels to whole blocks at random and runs both scikit-learn's `permutation_test_score` and the block permutation test. Because the labels carry no information, a valid test calls about 5% of them significant. Replace the synthetic recording in the example with your own data and pipeline to see how often each test calls your fake labels significant.

```
cd blockperm
python examples/fake_block_labels.py 40
```

It takes about 3 minutes and prints 14 (35%) for `permutation_test_score` and 1 (2%) for the block permutation test, out of 40 recordings.

## 9. Time-resolved decoding

The function returns one score. For a decoder fitted at each time point, call it once per time point with the same `random_state`, or write a score that averages over a time window, and correct for the number of time points or windows you test.

## 10. MATLAB and Octave

`matlab/block_permutation_test.m` is a port for MATLAB and Octave that takes a function returning the cross-validated score for a given label vector. See `matlab/README.md`.

## 11. What to report

- The number of blocks per condition and how blocks were assigned to conditions (random, counterbalanced or fixed order).
- The folds, the pipeline steps fitted inside each permutation, the number of permutations (or that all arrangements were enumerated) and the smallest attainable p value.
- For a fixed order, the correlation of the labels with time.
