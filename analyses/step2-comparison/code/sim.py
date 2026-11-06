#!/usr/bin/env python3
"""Step 2 simulation and permutation rules (design ../DESIGN.md v1; POST HOC with respect to step 1).

Generator (§5a): k latent Ornstein-Uhlenbeck factors on trials (time constant tau, in trials) plus a slow
linear trend, unit loadings from a Gaussian, Poisson spike counts. Labels follow recording blocks
(random block assignment, fixed-order ABAB/ABBA/AABB, one block per condition) or vary trial by
trial (interleaved). Signal (delta > 0) adds a rate change on label-1 trials to a fraction f of units.

Rules (rows, §3), each refits the same scikit-learn pipeline (§2):
  P1  binomial test of the pooled held-out correct count
  P2  sklearn permutation_test_score (all labels permuted at trial level, whole CV rerun)
  P3  CoSMoMVPA cosmo_randomize_targets rule: labels permuted within each run (chunk), error if a run lacks a class
  P4  training-partition labels permuted per fold, refit, test labels kept (PyMVPA tutorial, ADAM)
  P5  block labels permuted between blocks, training and held-out together, whole CV rerun
      (block_permutation_test_score, the deliverable of §9)
Splits (§4): 'main' shuffled KFold(5); 'tool' unshuffled StratifiedKFold(5) (sklearn/MNE cv=None);
'block' GroupKFold(5) by block.
"""
from __future__ import annotations

import numpy as np
from scipy import stats
from sklearn.base import clone
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold, permutation_test_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def pipeline(k=20):
    return Pipeline([("scale", StandardScaler()), ("sel", SelectKBest(f_classif, k=k)),
                     ("lr", LogisticRegression(C=1.0, max_iter=1000))])


# ------------------------------------------------------------------ generator
def ou(n, tau, rng):
    """Unit-variance OU process sampled once per trial; tau in trials."""
    a = np.exp(-1.0 / tau)
    x = np.empty(n)
    x[0] = rng.standard_normal()
    e = rng.standard_normal(n) * np.sqrt(1 - a * a)
    for t in range(1, n):
        x[t] = a * x[t - 1] + e[t]
    return x


def simulate(n_trials, tau, drift, rng, n_units=100, k=3, base_rate=5.0, trend=0.5, labels=None, delta=0.0, f=0.1):
    """Counts (trials x units). drift scales the latent log-rate fluctuation (0 = none)."""
    latent = np.stack([ou(n_trials, tau, rng) for _ in range(k)], axis=1)          # trials x k
    lin = np.linspace(-1, 1, n_trials)[:, None] * trend
    load = rng.standard_normal((k + 1, n_units)) / np.sqrt(k + 1)
    eta = np.log(base_rate) + drift * np.hstack([latent, lin]) @ load
    if delta > 0 and labels is not None:
        sig = rng.choice(n_units, max(1, int(round(f * n_units))), replace=False)
        eta[:, sig] += delta * labels[:, None]
    return rng.poisson(np.exp(eta)).astype(float)


def block_index(n_blocks, block_len):
    return np.repeat(np.arange(n_blocks), block_len)


def block_labels(design, n_blocks, rng):
    """Per-block label vector."""
    if design == "random":
        a = np.zeros(n_blocks, int)
        a[rng.choice(n_blocks, n_blocks // 2, replace=False)] = 1
        return a
    pat = {"ABAB": [0, 1], "ABBA": [0, 1, 1, 0], "AABB": [0, 0, 1, 1]}[design]
    return np.array([pat[i % len(pat)] for i in range(n_blocks)])


# ------------------------------------------------------------------ splits
def splitter(kind, seed, n_block_folds=5):
    if kind == "main":
        return KFold(5, shuffle=True, random_state=seed)
    if kind == "tool":
        return StratifiedKFold(5)
    if kind == "block":
        return GroupKFold(n_block_folds)          # deterministic: the same block-to-fold map in every replicate
    raise ValueError(kind)


def folds(kind, X, y, blocks, seed, n_block_folds=5):
    return list(splitter(kind, seed, n_block_folds).split(X, y, groups=blocks))


class Resplit:
    """A splitter that is re-applied to each (permuted) label vector, as scikit-learn does when
    permutation_test_score gets a splitter object (StratifiedKFold folds depend on y). Review 2b S3(a)."""

    def __init__(self, cv, groups):
        self.cv, self.groups = cv, groups

    def get(self, X, y):
        return list(self.cv.split(X, y, groups=self.groups))


def _folds_for(fl, X, y):
    return fl.get(X, y) if isinstance(fl, Resplit) else fl


def cv_correct(est, X, y, fl):
    """Total held-out correct (for P1) and the MEAN OF FOLD ACCURACIES (the statistic of scikit-learn's
    permutation_test_score, used by every permutation rule so P2-P5 compare the same statistic; v2 review must 7).
    Each fold refit. fl: list of folds or Resplit. A training fold with one class gives (nan, nan)."""
    fl = _folds_for(fl, X, y)
    c = 0
    accs = []
    for tr, te in fl:
        if len(np.unique(y[tr])) < 2:
            return np.nan, np.nan
        m = clone(est).fit(X[tr], y[tr])
        k = int((m.predict(X[te]) == y[te]).sum())
        c += k
        accs.append(k / len(te))
    return c, float(np.mean(accs))


def p_mc(null, obs):
    """(1 + #{null >= obs} + #NaN null) / (N + 1). An undefined observed statistic gives NaN (counted as an
    error by the caller, never as a small p; v2 review must 6)."""
    if not np.isfinite(obs):
        return float("nan")
    null = np.asarray(null, float)
    return float((1 + np.sum(null[~np.isnan(null)] >= obs - 1e-12) + np.isnan(null).sum()) / (len(null) + 1))


# ------------------------------------------------------------------ rules
def p1_binomial(est, X, y, fl):
    c, _ = cv_correct(est, X, y, fl)
    if not np.isfinite(c):
        return float("nan")
    return float(stats.binom.sf(c - 1, len(y), 0.5))


def p2_sklearn(est, X, y, fl, n_perm, seed):
    # A y-dependent splitter (StratifiedKFold) is passed as an object so sklearn re-splits on every permuted y.
    # GroupKFold does not depend on y: its folds are passed as a list, so `groups` never reaches sklearn's
    # _shuffle (which would permute within blocks and give p = 1; DESIGN.md §3 footnote, a separate sanity cell).
    if isinstance(fl, Resplit):
        cv = fl.get(X, y) if isinstance(fl.cv, GroupKFold) else fl.cv
    else:
        cv = fl
    _, _, p = permutation_test_score(est, X, y, cv=cv, n_permutations=n_perm, random_state=seed, scoring="accuracy")
    return float(p)


def p3_within_run(est, X, y, fl, runs, n_perm, rng):
    """CoSMoMVPA rule: error (None) if a run lacks a class; else permute labels within each run, rerun CV."""
    for r in np.unique(runs):
        if len(np.unique(y[runs == r])) < 2:
            return None
    _, obs = cv_correct(est, X, y, fl)
    null = []
    for _ in range(n_perm):
        yp = y.copy()
        for r in np.unique(runs):
            idx = np.where(runs == r)[0]
            yp[idx] = y[rng.permutation(idx)]
        null.append(cv_correct(est, X, yp, fl)[1])
    return p_mc(null, obs)


def p4_train_only(est, X, y, fl, n_perm, rng):
    fl = _folds_for(fl, X, y)                               # folds fixed by the observed labels (PyMVPA/ADAM)
    _, obs = cv_correct(est, X, y, fl)
    null = []
    for _ in range(n_perm):
        c, accs = 0, []
        for tr, te in fl:
            ytr = y[tr][rng.permutation(len(tr))]
            if len(np.unique(ytr)) < 2:
                c = np.nan
                break
            m = clone(est).fit(X[tr], ytr)
            accs.append(int((m.predict(X[te]) == y[te]).sum()) / len(te))
        null.append(float(np.mean(accs)) if np.isfinite(c) else np.nan)
    return p_mc(null, obs)


def block_permutation_test_score(est, X, y, blocks, fl, n_perm, rng, draw=None):
    """P5 and the deliverable (§9): permute the per-block label vector between blocks (training and
    held-out together) or draw it from `draw(rng)` (e.g. pseudosessions), map to trials, rerun the whole CV.
    Returns (observed accuracy, null accuracies, p)."""
    ub = np.unique(blocks)
    lab = np.array([y[blocks == b][0] for b in ub])
    if any(len(np.unique(y[blocks == b])) > 1 for b in ub):
        raise ValueError("labels must be constant within blocks")
    _, obs = cv_correct(est, X, y, fl)
    pos = np.searchsorted(ub, blocks)
    null = []
    for _ in range(n_perm):
        lp = draw(rng) if draw is not None else rng.permutation(lab)
        null.append(cv_correct(est, X, lp[pos], fl)[1])
    return obs, np.array(null), p_mc(null, obs)


# ------------------------------------------------------------------ generator v2 (DESIGN.md §13-§14)
def ou_matrix(n, tau, m, rng):
    """m independent unit-variance OU series of length n (tau in trials), vectorised over series."""
    a = np.exp(-1.0 / tau)
    x = np.empty((n, m))
    x[0] = rng.standard_normal(m)
    e = rng.standard_normal((n, m)) * np.sqrt(1 - a * a)
    for t in range(1, n):
        x[t] = a * x[t - 1] + e[t]
    return x


def simulate2(n_trials, rng, n_units=89, tau_f=2.0, sigma_f=0.4, tau_s=20.0, sigma_s=0.4, sigma_u=0.2,
              base_rate=5.7, k_f=3, k_s=1, trend=0.0, labels=None, delta=0.0, f=0.1, keep=None):
    """Counts (trials x units). Log rate = log(base) + sigma_f * fast shared OU (k_f factors, tau_f)
    + sigma_s * slow shared OU (k_s factors, tau_s) + sigma_u * unit-specific slow OU (tau_s)
    + trend * (random sign) * linear ramp on random loadings. Loadings ~ N(0, 1/k). `keep`: indices of the
    simulated time points to return (for epoch layouts with gaps; the process runs through the gaps)."""
    n = n_trials if keep is None else int(np.max(keep)) + 1
    ff = ou_matrix(n, tau_f, k_f, rng) @ (rng.standard_normal((k_f, n_units)) / np.sqrt(k_f))
    fs = ou_matrix(n, tau_s, k_s, rng) @ (rng.standard_normal((k_s, n_units)) / np.sqrt(k_s))
    fu = ou_matrix(n, tau_s, n_units, rng) if sigma_u > 0 else 0.0
    ramp = (np.linspace(-1, 1, n)[:, None] * rng.standard_normal(n_units)[None, :]) * trend * rng.choice([-1, 1])
    eta = np.log(base_rate) + sigma_f * ff + sigma_s * fs + sigma_u * fu + ramp
    if keep is not None:
        eta = eta[keep]
    if delta > 0 and labels is not None:
        sig = rng.choice(n_units, max(1, int(round(f * n_units))), replace=False)
        eta[:, sig] += delta * labels[:, None]
    return rng.poisson(np.exp(eta)).astype(float)
