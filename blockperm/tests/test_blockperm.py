"""Tests of block_permutation_test_score (no study data; synthetic recordings only)."""
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, StratifiedKFold, GroupKFold, permutation_test_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blockperm import block_permutation_test_score, block_labels_of, n_distinct_arrangements  # noqa: E402

_HERE = Path(__file__).resolve()
_CANDIDATES = [_HERE.parents[2] / "analyses" / "step2-comparison" / "code",      # public repository layout
               _HERE.parents[3] / "results" / "step2-comparison" / "code"]       # working-repository layout
REFERENCE = Path(os.environ.get("REFERENCE_SIM_DIR", next((c for c in _CANDIDATES if (c / "sim.py").exists()), _CANDIDATES[0])))


def reference_sim():
    """The reference implementation used in the analyses (read only; no bytecode written next to it)."""
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(REFERENCE))
    try:
        import sim
    finally:
        sys.dont_write_bytecode = old
    return sim


def lr():
    return Pipeline([("scale", StandardScaler()), ("lr", LogisticRegression(C=1.0, max_iter=1000))])


def drifting_counts(n_trials, n_units, rng, tau=20.0, sd=0.6):
    """Poisson counts with one slow shared AR(1) factor (no label signal)."""
    a = np.exp(-1.0 / tau)
    z = np.empty(n_trials)
    z[0] = rng.standard_normal()
    e = rng.standard_normal(n_trials) * np.sqrt(1 - a * a)
    for t in range(1, n_trials):
        z[t] = a * z[t - 1] + e[t]
    load = rng.standard_normal(n_units)
    return rng.poisson(np.exp(np.log(5.0) + sd * z[:, None] * load[None, :])).astype(float)


def random_block_design(n_blocks, block_len, rng):
    blocks = np.repeat(np.arange(n_blocks), block_len)
    lab = np.zeros(n_blocks, int)
    lab[rng.choice(n_blocks, n_blocks // 2, replace=False)] = 1
    return blocks, lab[blocks]


@pytest.mark.skipif(not (REFERENCE / "sim.py").exists(), reason="reference sim.py not found")
@pytest.mark.parametrize("split", ["main", "tool", "block", "draw"])
def test_equivalence_with_reference(split):
    """Same data, folds and random stream (exact=False): identical observed score, null scores and p as the
    reference implementation, for shuffled 5-fold, re-split stratified 5-fold, GroupKFold by block and a user draw."""
    sim = reference_sim()
    rng = np.random.default_rng(11)
    blocks, y = random_block_design(12, 20, rng)
    X = sim.simulate2(240, rng, n_units=40, tau_s=20.0)
    est = sim.pipeline(k=20)
    draw = None
    if split in ("main", "draw"):
        fl = sim.folds("main", X, y, blocks, seed=5)
        cv_new, groups = fl, None
        if split == "draw":
            draw = lambda g: g.permutation(np.array([0, 1] * 6))
    elif split == "tool":
        fl = sim.Resplit(StratifiedKFold(5), blocks)
        cv_new, groups = StratifiedKFold(5), "blocks"
    else:
        fl = sim.folds("block", X, y, blocks, seed=5)
        cv_new, groups = GroupKFold(5), "blocks"
    obs, null, p = sim.block_permutation_test_score(est, X, y, blocks, fl, 40, np.random.default_rng(3), draw=draw)
    s2, null2, p2 = block_permutation_test_score(est, X, y, blocks=blocks, cv=cv_new, n_permutations=40,
                                                 random_state=np.random.default_rng(3), groups=groups, exact=False,
                                                 draw=draw)
    assert s2 == pytest.approx(obs, abs=1e-12)
    np.testing.assert_allclose(null2, null, atol=1e-12)
    assert p2 == pytest.approx(p, abs=1e-12)


def test_exact_p_is_valid_over_all_arrangements():
    """6 blocks, 3 per label: 20 arrangements. Taking each in turn as the observed one, the share with p <= alpha
    is at most alpha (the exact randomisation property), at alpha 0.05, 0.10 and 0.25."""
    rng = np.random.default_rng(8)
    blocks = np.repeat(np.arange(6), 20)
    X = drifting_counts(120, 8, rng)
    cv = KFold(5, shuffle=True, random_state=0)
    from blockperm import _enumerate
    arrs = _enumerate(np.array([0, 0, 0, 1, 1, 1]), None)
    assert len(arrs) == 20
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ps = np.array([block_permutation_test_score(lr(), X, a[blocks], blocks=blocks, cv=cv, groups=None,
                                                    exact=True)[2] for a in arrs])
    assert np.all(ps >= 1 / 20 - 1e-12)
    for alpha in (0.05, 0.10, 0.25):
        assert np.mean(ps <= alpha + 1e-12) <= alpha + 1e-12


def test_exact_p_not_below_one_over_n_with_random_folds():
    """Shuffled folds without a seed differ between calls; the observed arrangement still counts once."""
    rng = np.random.default_rng(9)
    blocks = np.repeat(np.arange(6), 20)
    y = np.array([0, 1, 0, 1, 0, 1])[blocks]
    X = drifting_counts(120, 8, rng)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(3):
            _, null, p = block_permutation_test_score(lr(), X, y, blocks=blocks, cv=KFold(5, shuffle=True),
                                                      groups=None, exact=True)
            assert len(null) == 20 and p >= 1 / 20 - 1e-12


def test_size_under_drift_and_contrast_with_trial_permutation():
    """Random block assignment with slow drift, no signal: the block test stays near 5%; scikit-learn's
    trial-level permutation_test_score with shuffled 5-fold rejects far more often (the failure it replaces)."""
    reps, n_perm = 60, 49
    rej_block, rej_trial = 0, 0
    for r in range(reps):
        rng = np.random.default_rng(1000 + r)
        blocks, y = random_block_design(12, 20, rng)
        X = drifting_counts(240, 20, rng)
        cv = KFold(5, shuffle=True, random_state=r)
        _, _, p = block_permutation_test_score(lr(), X, y, blocks=blocks, cv=cv, n_permutations=n_perm,
                                               random_state=r, groups=None, exact=False)
        _, _, pt = permutation_test_score(lr(), X, y, cv=cv, n_permutations=n_perm, random_state=r)
        rej_block += p < 0.05
        rej_trial += pt < 0.05
    assert rej_block / reps <= 0.14          # 99% binomial upper limit for 5% at n = 60 is about 0.13
    assert rej_trial / reps >= 0.30


def test_exact_enumeration_small_design():
    rng = np.random.default_rng(2)
    blocks, y = random_block_design(4, 30, rng)
    X = drifting_counts(120, 10, rng)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        s, null, p = block_permutation_test_score(lr(), X, y, blocks=blocks, cv=GroupKFold(4), n_permutations=1000,
                                                  random_state=0)
    assert any("distinct block-label arrangements" in str(x.message) for x in w)
    assert len(null) == 6                     # 4 blocks, 2 per label: 4!/(2!2!) arrangements
    assert p >= 1 / 6 - 1e-12
    assert np.any(np.isclose(null, s))        # the observed arrangement is one of them


def test_strata_restrict_permutations():
    rng = np.random.default_rng(4)
    blocks = np.repeat(np.arange(8), 15)
    lab = np.array([0, 1, 0, 1, 1, 0, 1, 0])
    y = lab[blocks]
    strata = (blocks >= 4).astype(int)        # two halves, 2 + 2 blocks per label in each
    assert n_distinct_arrangements(lab, None) == 70
    assert n_distinct_arrangements(lab, np.array([0, 0, 0, 0, 1, 1, 1, 1])) == 36
    X = drifting_counts(120, 10, rng)
    _, null, _ = block_permutation_test_score(lr(), X, y, blocks=blocks, cv=KFold(5, shuffle=True, random_state=0),
                                              n_permutations=36, random_state=0, strata=strata, groups=None,
                                              exact=True)
    assert len(null) == 36


def test_draw_generator_is_used():
    rng = np.random.default_rng(5)
    blocks, y = random_block_design(10, 20, rng)
    X = drifting_counts(200, 10, rng)
    fixed = np.array([0, 1] * 5)
    cv = KFold(5, shuffle=True, random_state=0)
    _, null, _ = block_permutation_test_score(lr(), X, y, blocks=blocks, cv=cv, n_permutations=5,
                                              random_state=0, draw=lambda g: fixed, groups=None)
    ref, _, _ = block_permutation_test_score(lr(), X, fixed[blocks], blocks=blocks, cv=cv, n_permutations=1,
                                             random_state=0, groups=None, exact=False)
    np.testing.assert_allclose(null, ref)


def test_input_errors():
    blocks = np.repeat(np.arange(6), 10)
    y = np.repeat([0, 1, 0, 1, 0, 1], 10)
    y_bad = y.copy()
    y_bad[3] = 1 - y_bad[3]
    X = np.random.default_rng(0).standard_normal((60, 4))
    with pytest.raises(ValueError, match="constant within blocks"):
        block_permutation_test_score(lr(), X, y_bad, blocks=blocks)
    with pytest.raises(ValueError, match="one label per block"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, draw=lambda g: np.zeros(3), n_permutations=2)
    with pytest.raises(ValueError, match="groups must be"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, groups="block")
    with pytest.raises(ValueError, match="exact must be"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, exact="yes")
    with pytest.raises(ValueError, match="at least 1"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, n_permutations=1.5)
    with pytest.raises(ValueError, match="one value per trial"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, strata=np.zeros(5))
    with pytest.raises(ValueError, match="at least 1"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, n_permutations=0)
    with pytest.raises(ValueError, match="error_score"):
        block_permutation_test_score(lr(), X, y, blocks=blocks, error_score="raise")
    with pytest.raises(ValueError, match="same number of trials"):
        block_permutation_test_score(lr(), X[:50], y, blocks=blocks)


def test_single_class_training_fold_counts_as_exceedance():
    """Folds hold out blocks {2, 3} and {0, 1}. Observed labels 0101 give two classes in every training fold;
    the arrangements 0011 and 1100 leave one class in training, score NaN and count as exceedances. An observed
    arrangement with a one-class training fold gives p = NaN."""
    blocks = np.repeat(np.arange(4), 10)
    lab, _ = block_labels_of(np.repeat([0, 0, 1, 1], 10), blocks)
    assert list(lab) == [0, 0, 1, 1]
    i01, i23 = np.where(blocks < 2)[0], np.where(blocks >= 2)[0]
    folds = [(i01, i23), (i23, i01)]
    X = np.random.default_rng(1).standard_normal((40, 3))
    y = np.repeat([0, 1, 0, 1], 10)
    s, null, p = block_permutation_test_score(lr(), X, y, blocks=blocks, cv=folds, groups=None, random_state=0)
    assert np.isfinite(s) and np.isnan(null).sum() == 2 and len(null) == 6
    ge = np.sum(null[~np.isnan(null)] >= s - 1e-12) + np.isnan(null).sum()
    assert p == pytest.approx(ge / len(null))
    _, _, p_bad = block_permutation_test_score(lr(), X, np.repeat([0, 0, 1, 1], 10), blocks=blocks, cv=folds,
                                               groups=None, random_state=0)
    assert np.isnan(p_bad)
