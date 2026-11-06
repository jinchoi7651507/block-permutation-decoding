#!/usr/bin/env python3
"""Fake block labels on a drifting synthetic recording: scikit-learn's trial-level permutation test against the
block permutation test. Labels are assigned to whole blocks at random and carry no information, so a valid test
should reject in about 5% of recordings. Synthetic data only; runs in about a minute on one core.

    python examples/fake_block_labels.py [n_recordings]
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, permutation_test_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blockperm import block_permutation_test_score  # noqa: E402


def recording(rng, n_blocks=12, block_len=20, n_units=20, tau=20.0, sd=0.6):
    """Poisson counts with one slow shared factor, and labels constant within blocks (half the blocks each)."""
    n = n_blocks * block_len
    a = np.exp(-1.0 / tau)
    z = np.empty(n)
    z[0] = rng.standard_normal()
    e = rng.standard_normal(n) * np.sqrt(1 - a * a)
    for t in range(1, n):
        z[t] = a * z[t - 1] + e[t]
    X = rng.poisson(np.exp(np.log(5.0) + sd * z[:, None] * rng.standard_normal(n_units)[None, :])).astype(float)
    blocks = np.repeat(np.arange(n_blocks), block_len)
    lab = np.zeros(n_blocks, int)
    lab[rng.choice(n_blocks, n_blocks // 2, replace=False)] = 1
    return X, lab[blocks], blocks


def main(n_rec=40, n_perm=99):
    est = Pipeline([("scale", StandardScaler()), ("lr", LogisticRegression(max_iter=1000))])
    trial, block = 0, 0
    for r in range(n_rec):
        rng = np.random.default_rng(r)
        X, y, blocks = recording(rng)
        cv = KFold(5, shuffle=True, random_state=r)          # training and test trials share blocks
        _, _, p_trial = permutation_test_score(est, X, y, cv=cv, n_permutations=n_perm, random_state=r)
        _, _, p_block = block_permutation_test_score(est, X, y, blocks=blocks, cv=cv, n_permutations=n_perm,
                                                     random_state=r, groups=None)
        trial += p_trial < 0.05
        block += p_block < 0.05
    print("labels with no information, %d recordings, p < 0.05:" % n_rec)
    print("  permutation_test_score (trial labels permuted): %d (%.0f%%)" % (trial, 100 * trial / n_rec))
    print("  block_permutation_test_score (block labels permuted): %d (%.0f%%)" % (block, 100 * block / n_rec))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
