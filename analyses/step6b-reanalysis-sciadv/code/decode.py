"""Decoders and tests for the pre-specified reanalysis (DESIGN.md sections 4-6).

Window statistic: the authors' per-bin linear SVM (fitcsvm defaults: linear kernel, box constraint 1, no
standardisation), balanced subsampling of the larger class, unstratified random 20-fold cross-validation over
trials, accuracy averaged over folds; here averaged over the bins of a pre-specified window and over R repeats
of (subsample, folds). Every step that depends on the labels (the subsample, the folds) is redone for every
label vector, real or permuted.
"""
from __future__ import annotations

import hashlib
import itertools
import math
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.model_selection import KFold
from sklearn.svm import SVC

BLOCKPERM_DIR = Path(__file__).resolve().parents[3] / "code-package" / "blockperm"
if str(BLOCKPERM_DIR) not in sys.path:
    sys.path.insert(0, str(BLOCKPERM_DIR))
import blockperm  # noqa: E402  (used for n_distinct_arrangements and the equivalence test)

BLOCKPERM_SHA256 = "4a5f8009e1d49d5bf1e30cb47a08f25f745e712bcc99b690456dd1c2081f4a08"      # pinned at the stamp (review S8)
PINNED_VERSIONS = {"numpy": "2.5.4", "scipy": "1.18.1", "scikit-learn": "1.7.2"}


def check_environment(strict=True):
    """blockperm.py hash and package versions; the stage-2 driver stops on a mismatch (DESIGN.md section 5)."""
    import scipy
    import sklearn
    got = {"numpy": np.__version__, "scipy": scipy.__version__, "scikit-learn": sklearn.__version__}
    hb = hashlib.sha256((BLOCKPERM_DIR / "blockperm.py").read_bytes()).hexdigest()
    if strict and (hb != BLOCKPERM_SHA256 or got != PINNED_VERSIONS):
        raise SystemExit("environment differs from the stamp: blockperm %s, versions %s" % (hb, got))
    return {"blockperm_sha256": hb, "versions": got}

MASTER_SEED = 20261104

# 0-based bin indices (MATLAB bin k is index k-1); centres from matlab_port.bin_centre_s
WINDOWS = {
    "ITI": list(range(15, 44)),    # MATLAB bins 16-44, centres -3.95 to -2.08 s before the reward threshold crossing
    "PERI": list(range(72, 81)),   # MATLAB bins 73-81, centres -0.15 to +0.38 s
}
BASELINE_BIN = 44                  # MATLAB bin 45 (-2.02 s), the authors' movement-decoder baseline


def rng_for(*keys) -> np.random.Generator:
    h = hashlib.sha256(("%d|" % MASTER_SEED + "|".join(map(str, keys))).encode()).digest()
    return np.random.default_rng([int.from_bytes(h[i:i + 4], "little") for i in range(0, 16, 4)])


def svm_factory():
    return SVC(kernel="linear", C=1.0)


def balanced_subsample(y, rng):
    """MATLAB datasample(Idx_large, n_small, 'Replace', false): all trials of the smaller class plus a random
    subset of the larger one. Returns sorted indices."""
    cls = np.unique(y)
    if len(cls) != 2:
        raise ValueError("two classes needed")
    i0, i1 = np.where(y == cls[0])[0], np.where(y == cls[1])[0]
    if len(i0) > len(i1):
        i0 = rng.choice(i0, len(i1), replace=False)
    elif len(i1) > len(i0):
        i1 = rng.choice(i1, len(i0), replace=False)
    return np.sort(np.concatenate([i0, i1]))


def cv_accuracy_bins(X, y, bins, folds, clf_factory=svm_factory):
    """Mean over bins of the fold-averaged accuracy (percent). X: trials x cells x bins. NaN if a training fold
    holds one class."""
    accs = []
    for b in bins:
        Xb = X[:, :, b]
        fa = []
        for tr, te in folds:
            if len(np.unique(y[tr])) < 2:
                return float("nan")
            m = clf_factory().fit(Xb[tr], y[tr])
            fa.append(np.mean(m.predict(Xb[te]) == y[te]))
        accs.append(np.mean(fa))
    return 100.0 * float(np.mean(accs))


def window_stat(X, y, bins, key, R=4, n_folds=20, clf_factory=svm_factory, subsample=True, fixed_folds=None,
                group_folds=None):
    """Mean over R repeats of the window accuracy; repeat r uses rng_for(*key, r) for the subsample and folds.
    group_folds: optional per-trial group array; folds then hold out one group at a time (secondary S1)."""
    out = []
    for r in range(R):
        rng = rng_for(*key, r)
        idx = balanced_subsample(y, rng) if subsample else np.arange(len(y))
        if fixed_folds is not None:
            folds = fixed_folds
        elif group_folds is not None:
            g = np.asarray(group_folds)[idx]
            folds = [(np.where(g != v)[0], np.where(g == v)[0]) for v in np.unique(g)]
        else:
            kf = KFold(n_folds, shuffle=True, random_state=int(rng.integers(2**31 - 1)))
            folds = list(kf.split(idx))
        out.append(cv_accuracy_bins(X[idx], y[idx], bins, folds, clf_factory))
    return float(np.mean(out))


# ---------------------------------------------------------------- block arrangements
def canonical_partitions(block_labels):
    """All distinct arrangements of the per-block labels (as many blocks of each class as observed).
    Returns (arrangements, canon) where arrangements is a list of per-block label vectors and canon[i] is the
    index of the class-swap-invariant partition (the set of blocks sharing block 0's label) of arrangement i.
    Swapping the two classes leaves a refit two-class decoder's accuracy unchanged, so each partition is
    scored once."""
    lab = np.asarray(block_labels)
    cls = np.unique(lab)
    n, k = len(lab), int(np.sum(lab == cls[1]))
    arrs, keys = [], []
    for comb in itertools.combinations(range(n), k):
        a = np.full(n, cls[0])
        a[list(comb)] = cls[1]
        arrs.append(a)
        keys.append(tuple(int(i) for i in np.where(a == a[0])[0]))
    uniq = sorted(set(keys))
    canon = [uniq.index(kk) for kk in keys]
    assert len(arrs) == blockperm.n_distinct_arrangements(lab)
    return arrs, canon, uniq


def block_test(X, trial_block, block_labels, bins, key, R=4, n_folds=20, n_jobs=1, **kw):
    """Exact block permutation test over all arrangements (training and test trials permuted together, the
    whole pipeline refit). Returns dict(observed, null (one score per arrangement), p, n_arrangements,
    p_min)."""
    from joblib import Parallel, delayed
    arrs, canon, uniq = canonical_partitions(block_labels)
    trial_block = np.asarray(trial_block)
    obs_i = next(i for i, a in enumerate(arrs) if np.array_equal(a, block_labels))
    first = {}
    for i, c in enumerate(canon):
        first.setdefault(c, i)
    jobs = [(c, arrs[i]) for c, i in sorted(first.items())]
    scores = Parallel(n_jobs=n_jobs)(
        delayed(window_stat)(X, a[trial_block], bins, key + ("part", uniq[c]), R, n_folds, **kw) for c, a in jobs)
    by_c = dict(zip([c for c, _ in jobs], scores))
    null = np.array([by_c[c] for c in canon])
    obs = null[obs_i]
    others = np.delete(null, obs_i)
    ge = 1 + np.sum(others[~np.isnan(others)] >= obs - 1e-9) + np.isnan(others).sum()
    p = float(ge / len(null))
    n_sw = len(null) / len(uniq)
    return dict(observed=float(obs), null=null.tolist(), p=p, n_arrangements=len(null),
                n_distinct=len(uniq), p_min=float(n_sw / len(null)), observed_index=int(obs_i))


def trial_shuffle_test(X, y, bins, key, D=1000, R=4, n_folds=20, n_jobs=1, observed=None, **kw):
    """The authors' rule made formal: permute the condition labels across all trials (class counts kept),
    redo the subsample, folds and fits, D times. p = (1 + #{null >= observed}) / (D + 1)."""
    from joblib import Parallel, delayed
    y = np.asarray(y)
    perms = [rng_for(*key, "perm", d).permutation(y) for d in range(D)]
    null = np.array(Parallel(n_jobs=n_jobs)(
        delayed(window_stat)(X, yp, bins, key + ("draw", d), R, n_folds, **kw) for d, yp in enumerate(perms)))
    if observed is None:
        observed = window_stat(X, y, bins, key + ("observed",), R, n_folds, **kw)
    ok = ~np.isnan(null)
    p = float((1 + np.sum(null[ok] >= observed - 1e-9) + np.sum(~ok)) / (D + 1))
    return dict(observed=float(observed), null=null.tolist(), p=p, D=D)


# ---------------------------------------------------------------- group level
def _q(x):
    """Accuracies (percent) on an integer grid of 1e-6 percent, so that sums are exact (review M3)."""
    return np.round(np.asarray(x, float) * 1e6).astype(np.int64)


def exact_group_null(per_mouse_nulls):
    """Exact null distribution of the SUM over mice of the quantised accuracies when each mouse's arrangement
    is independently uniform over its arrangements. Returns (integer sums, probabilities)."""
    vals, probs = np.array([0], np.int64), np.array([1.0])
    for nl in per_mouse_nulls:
        v, c = np.unique(_q(nl), return_counts=True)
        vals, inv = np.unique(np.add.outer(vals, v).ravel(), return_inverse=True)
        probs = np.bincount(inv, weights=np.multiply.outer(probs, c / c.sum()).ravel())
    return vals, probs


def group_block_p(observed_per_mouse, per_mouse_nulls):
    T = float(np.mean(observed_per_mouse))
    S = int(_q(observed_per_mouse).sum())
    v, pr = exact_group_null(per_mouse_nulls)
    p = float(pr[v >= S].sum())
    p_min = float(np.prod([np.mean(_q(nl) == _q(nl).max()) for nl in per_mouse_nulls]))
    assert p >= p_min - 1e-15, "group p below its attainable minimum"
    return dict(T=T, p=p, p_min=p_min)


def group_top_count(per_mouse_p, p_min_per_mouse):
    """Secondary: number of mice whose observed arrangement scores at the top (p equals its minimum), against a
    binomial with success probability equal to that minimum (conservative with ties)."""
    from scipy.stats import binom
    k = int(sum(np.isclose(p, q) for p, q in zip(per_mouse_p, p_min_per_mouse)))
    q = float(np.max(p_min_per_mouse))
    return dict(k=k, n=len(per_mouse_p), p=float(binom.sf(k - 1, len(per_mouse_p), q)))


def group_trial_p(observed_per_mouse, per_mouse_nulls, n_combo=100_000, key=("group-trial",)):
    """Group version of the trial shuffle: null of the mean over mice from independent random draws of each
    mouse's trial-shuffle null."""
    rng = rng_for(*key)
    T = float(np.mean(observed_per_mouse))
    cols = [np.asarray(nl)[rng.integers(len(nl), size=n_combo)] for nl in per_mouse_nulls]
    null = np.mean(cols, axis=0)
    return dict(T=T, p=float((1 + np.sum(null >= T - 1e-9)) / (n_combo + 1)))


# ---------------------------------------------------------------- movement decoder (positive control)
def movement_stat(X, bins, base_bin, key, R=2, n_folds=20, swap=None):
    """Press bin w vs baseline bin of the same trials (authors' Panel F), averaged over the window bins.
    swap: optional boolean per trial; True exchanges the two labels of that trial (within-trial null)."""
    n = X.shape[0]
    accs = []
    for w in bins:
        A, B = X[:, :, w], X[:, :, base_bin]
        ya, yb = np.ones(n, int), np.full(n, 2)
        if swap is not None:
            ya = np.where(swap, 2, 1)
            yb = np.where(swap, 1, 2)
        Xw = np.concatenate([A, B])
        yw = np.concatenate([ya, yb])
        accs.append(window_stat(Xw[:, :, None], yw, [0], key + ("bin", w), R, n_folds, subsample=False))
    return float(np.mean(accs))


def movement_test(X, bins, base_bin, key, D=100, R=2, n_folds=20, n_jobs=1):
    from joblib import Parallel, delayed
    obs = movement_stat(X, bins, base_bin, key + ("obs",), R, n_folds)
    swaps = [rng_for(*key, "swap", d).random(X.shape[0]) < 0.5 for d in range(D)]
    null = np.array(Parallel(n_jobs=n_jobs)(
        delayed(movement_stat)(X, bins, base_bin, key + ("null", d), R, n_folds, s) for d, s in enumerate(swaps)))
    return dict(observed=obs, null=null.tolist(), p=float((1 + np.sum(null >= obs - 1e-9)) / (D + 1)), D=D)


def smallest_p_note(n_arr, n_distinct):
    return "%d arrangements, %d distinct scores: smallest per-mouse p = %.3g" % (n_arr, n_distinct, n_arr / n_distinct / n_arr)


if __name__ == "__main__":
    warnings.warn("library module; run run_reanalysis.py or test_synthetic.py")
