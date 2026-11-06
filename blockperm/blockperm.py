"""Block permutation test for cross-validated decoding when labels follow recording blocks.

`block_permutation_test_score` has the call pattern of scikit-learn's `permutation_test_score`. It differs in what
it permutes: the labels of whole blocks are permuted between blocks (training and held-out trials together), and
the whole cross-validation, including every step fitted to the labels, is rerun for every permutation. A label
vector can instead be drawn from a user-given generator (for example pseudosessions drawn from the task's own
block generator).

This is the block permutation rule of the accompanying analyses. The enumerated null is exact, and the sampled p
value valid, when the observed assignment was drawn uniformly from the set the function permutes over: all
arrangements of the block labels, or all arrangements within strata if the design randomised within strata. For a
constrained randomisation (counterbalancing, limits per run), pass the design's own generator as `draw`. For a
fixed block order the test rests on an exchangeability model, not on the randomisation.
"""
from __future__ import annotations

import math
import numbers
import warnings
from collections import Counter

import numpy as np
from sklearn.base import clone, is_classifier
from sklearn.metrics import check_scoring
from sklearn.model_selection import check_cv

__all__ = ["block_permutation_test_score", "block_labels_of", "n_distinct_arrangements"]


def block_labels_of(y, blocks):
    """Per-block labels (in the order of np.unique(blocks)) and the position of each trial's block.

    Raises ValueError if a block holds more than one label."""
    y = np.asarray(y)
    blocks = np.asarray(blocks)
    if y.shape[0] != blocks.shape[0]:
        raise ValueError("y and blocks must have the same length")
    ub = np.unique(blocks)
    pos = np.searchsorted(ub, blocks)
    lab = []
    for i in range(len(ub)):
        v = np.unique(y[pos == i])
        if len(v) != 1:
            raise ValueError("labels must be constant within blocks (block %r holds %d labels)" % (ub[i], len(v)))
        lab.append(v[0])
    return np.array(lab), pos


def n_distinct_arrangements(block_labels, strata=None):
    """Number of distinct block-label vectors reachable by permuting labels between blocks (within strata).
    Both arguments are per block (one value per block, in the order of np.unique(blocks))."""
    block_labels = np.asarray(block_labels)
    strata = None if strata is None else np.asarray(strata)
    groups = [np.arange(len(block_labels))] if strata is None else [np.where(strata == s)[0] for s in np.unique(strata)]
    n = 1
    for g in groups:
        c = Counter(block_labels[g].tolist())
        k = math.factorial(len(g))
        for v in c.values():
            k //= math.factorial(v)
        n *= k
    return n


def _cv_score(estimator, X, y, splits, scorer, error_score):
    scores = []
    for tr, te in splits:
        if is_classifier(estimator) and len(np.unique(y[tr])) < 2:
            return error_score
        m = clone(estimator).fit(X[tr], y[tr])
        scores.append(scorer(m, X[te], y[te]))
    return float(np.mean(scores))


def _splits(cv, X, y, groups):
    with warnings.catch_warnings():            # splitters that ignore groups (KFold, StratifiedKFold) warn
        warnings.filterwarnings("ignore", message="The groups parameter is ignored")
        return list(cv.split(X, y, groups))


def block_permutation_test_score(estimator, X, y, *, blocks, cv=None, n_permutations=1000, scoring=None,
                                 random_state=None, strata=None, draw=None, groups="blocks", exact="auto",
                                 error_score=np.nan):
    """Evaluate the significance of a cross-validated score by permuting labels between blocks.

    Parameters
    ----------
    estimator : scikit-learn estimator (a Pipeline with every label-fitted step: scaling, selection, model)
    X : array (n_trials, n_features)
    y : array (n_trials,), constant within each block
    blocks : array (n_trials,), block identity of each trial (a recording block of consecutive trials)
    cv : as in scikit-learn (int, splitter or iterable); default 5-fold. A splitter is re-applied to every
        permuted label vector (as scikit-learn does), so label-stratified folds follow the permuted labels.
    n_permutations : number of permutations (ignored when the exact enumeration is used)
    scoring : as in scikit-learn; default the estimator's score (accuracy for classifiers). The score is the mean
        over folds, as in `permutation_test_score`.
    random_state : int, numpy Generator, RandomState or None (passed to numpy.random.default_rng unless a
        Generator); the permutations use this stream only, so the same Generator and folds reproduce the same null
    strata : optional array (n_trials,), constant within blocks: labels are permuted only between blocks of the
        same stratum. Use the unit the design randomised over (for example within runs if blocks were randomised
        within runs); permuting across that unit can reject too often.
    draw : optional callable(rng) -> per-block label vector (order of np.unique(blocks)); replaces the
        permutation, for example to draw pseudosessions from the task's generator. `strata` and `exact` are
        ignored when `draw` is given.
    groups : "blocks" (default) passes the block identity to `cv.split` as `groups`, so GroupKFold-type splitters
        hold out whole blocks; None passes nothing; an array is passed as given.
    exact : "auto" enumerates all distinct block-label arrangements when there are no more of them than
        `n_permutations` (the null then has one score per arrangement, the observed one included, and its length
        is the number of arrangements, not `n_permutations`); True forces the enumeration (at most 100,000
        arrangements); False always samples with replacement.
    error_score : number used as the score of a cross-validation with a one-class training fold (classifiers).
        Other fit errors are raised. NaN null scores count as exceedances (conservative); an undefined observed
        score returns p = NaN with a warning.

    Returns
    -------
    score : float, observed cross-validated score
    permutation_scores : array, scores under the null (empty when the observed score is undefined; the
        reference implementation returned its full null in that case, with p NaN as here)
    pvalue : float, (1 + #{null >= score} + #{null NaN}) / (n_null + 1) when sampling; when enumerating,
        (1 + #{other arrangements with score >= observed or NaN}) / (number of arrangements), the observed
        arrangement counted once with its observed score (also when the cross-validation is not deterministic).
    """
    X = np.asarray(X)
    y = np.asarray(y)
    blocks = np.asarray(blocks)
    if X.shape[0] != y.shape[0] or blocks.shape[0] != y.shape[0]:
        raise ValueError("X, y and blocks must have the same number of trials")
    if not (isinstance(exact, (bool, np.bool_)) or (isinstance(exact, str) and exact == "auto")):
        raise ValueError('exact must be "auto", True or False')
    exact = exact if isinstance(exact, str) else bool(exact)
    if not isinstance(n_permutations, numbers.Integral) or isinstance(n_permutations, bool) or n_permutations < 1:
        raise ValueError("n_permutations must be an integer of at least 1")
    if isinstance(groups, str) and groups != "blocks":
        raise ValueError('groups must be "blocks", None or an array with one value per trial')
    if not isinstance(error_score, numbers.Real) or isinstance(error_score, (bool, np.bool_)):
        raise ValueError("error_score must be a number (NaN by default)")
    lab, pos = block_labels_of(y, blocks)
    rng = random_state if isinstance(random_state, np.random.Generator) else np.random.default_rng(random_state)
    cv = check_cv(cv, y, classifier=is_classifier(estimator))
    scorer = check_scoring(estimator, scoring=scoring)
    g = blocks if isinstance(groups, str) else groups
    if strata is not None:
        if np.asarray(strata).shape[0] != y.shape[0]:
            raise ValueError("strata must have one value per trial")
        st_lab, _ = block_labels_of(np.asarray(strata), blocks)
    else:
        st_lab = None

    score = _cv_score(estimator, X, y, _splits(cv, X, y, g), scorer, error_score)
    if not np.isfinite(score):
        warnings.warn("the observed score is undefined (a training fold with one class, or a scorer that returned "
                      "NaN); p is NaN and no null was computed", stacklevel=2)
        return score, np.array([], float), float("nan")

    n_arr = n_distinct_arrangements(lab, st_lab) if draw is None else None
    use_exact = draw is None and (exact is True or (exact == "auto" and n_arr <= n_permutations))
    if draw is None and n_arr < 20:
        warnings.warn("only %d distinct block-label arrangements: with exact enumeration p cannot fall below %.3g, "
                      "and not below %.3g when swapping the two classes leaves the score unchanged (a refit two-class "
                      "classifier with balanced blocks)%s"
                      % (n_arr, 1.0 / n_arr, 2.0 / n_arr, "" if use_exact else "; consider exact=True"), stacklevel=2)

    if use_exact:
        if n_arr > 100_000:
            raise ValueError("too many arrangements to enumerate (%d)" % n_arr)
        arrangements = _enumerate(lab, st_lab)
        obs = next(i for i, a in enumerate(arrangements) if np.array_equal(a, lab))
        null = np.array([score if i == obs else
                         _cv_score(estimator, X, a[pos], _splits(cv, X, a[pos], g), scorer, error_score)
                         for i, a in enumerate(arrangements)])
        others = np.delete(null, obs)
        ge = 1 + np.sum(others[~np.isnan(others)] >= score - 1e-12) + np.isnan(others).sum()
        return score, null, float(ge / len(null))

    null = []
    for _ in range(n_permutations):
        if draw is not None:
            lp = np.asarray(draw(rng))
            if lp.shape != lab.shape:
                raise ValueError("draw must return one label per block")
        elif st_lab is None:
            lp = rng.permutation(lab)
        else:
            lp = lab.copy()
            for s in np.unique(st_lab):
                i = np.where(st_lab == s)[0]
                lp[i] = lab[rng.permutation(i)]
        yp = lp[pos]
        null.append(_cv_score(estimator, X, yp, _splits(cv, X, yp, g), scorer, error_score))
    null = np.array(null, float)
    p = (1 + np.sum(null[~np.isnan(null)] >= score - 1e-12) + np.isnan(null).sum()) / (len(null) + 1)
    return score, null, float(p)


def _multiset_permutations(items):
    """Distinct orderings of a list with repeated values, each once (no n! intermediate list)."""
    counts = Counter(items)
    keys = sorted(counts)
    n = len(items)
    cur = []

    def rec():
        if len(cur) == n:
            yield tuple(cur)
            return
        for k in keys:
            if counts[k]:
                counts[k] -= 1
                cur.append(k)
                yield from rec()
                cur.pop()
                counts[k] += 1
    yield from rec()


def _enumerate(lab, st_lab):
    """All distinct block-label vectors reachable by permuting within strata (observed one included)."""
    idx_groups = [np.arange(len(lab))] if st_lab is None else [np.where(st_lab == s)[0] for s in np.unique(st_lab)]
    per_group = [list(_multiset_permutations(lab[i].tolist())) for i in idx_groups]
    out = []
    def rec(k, cur):
        if k == len(idx_groups):
            out.append(cur.copy())
            return
        for arr in per_group[k]:
            cur[idx_groups[k]] = arr
            rec(k + 1, cur)
    rec(0, lab.copy())
    return out
