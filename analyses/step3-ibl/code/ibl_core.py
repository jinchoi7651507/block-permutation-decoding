#!/usr/bin/env python3
"""Step 3 (IBL) core computations, DESIGN.md v1 §3-§7 (stamped). Pure functions on arrays; no IBL I/O, so they can be
tested on synthetic sessions. Statistic = balanced accuracy (§4). Every p = (1 + #{null >= obs}) / (n + 1) except the
sequential Besag-Clifford p of P2 and P4 (§5); an undefined observed statistic gives NaN (an error, never a small p).

Label vectors are given on the kept trials of a session (0/1, NaN = trial dropped in this draw). Blocks of a label
vector = runs of equal values in trial order over the session's kept trials (a masked trial does not break a block).
"""
from __future__ import annotations

import numpy as np
from scipy import stats
from sklearn.base import clone
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

N_DRAWS = 200
H_STOP = 10


def decoder(n_units, select=True):
    steps = [("scale", StandardScaler())]
    if select:
        steps.append(("sel", SelectKBest(f_classif, k=min(20, n_units))))
    steps.append(("lr", LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced")))
    return Pipeline(steps)


def int_seed(parts):
    return int(np.random.default_rng(list(parts)).integers(2 ** 31 - 1))


def blocks_of(y):
    """Block index of each trial of a 0/1 vector (NaN-free): a new block starts when the value changes."""
    y = np.asarray(y)
    return np.concatenate([[0], np.cumsum(y[1:] != y[:-1])])


def p_mc(null, obs):
    if not np.isfinite(obs):
        return float("nan")
    null = np.asarray(null, float)
    return float((1 + np.sum(null[~np.isnan(null)] >= obs - 1e-12) + np.isnan(null).sum()) / (len(null) + 1))


# ------------------------------------------------------------------ splits and scoring
def smain_folds(n, session_index):
    """S-main: shuffled KFold(5), seed [2026, 31, session_index]; independent of labels."""
    return list(KFold(5, shuffle=True, random_state=int_seed([2026, 31, session_index])).split(np.zeros(n)))


def sblock_folds(y):
    """S-block: GroupKFold(5) by the blocks of the label vector being scored."""
    g = blocks_of(y)
    k = min(5, len(np.unique(g)))
    return list(GroupKFold(k).split(np.zeros(len(y)), y, groups=g))


def _bacc(y, p):
    return balanced_accuracy_score(y, p) if len(np.unique(y)) == 2 else np.nan


def cv_score(est, X, y, folds, kind):
    """kind 'main': mean over folds of per-fold balanced accuracy (scikit-learn permutation_test_score with
    scoring='balanced_accuracy'); 'pooled': balanced accuracy of the pooled held-out predictions (S-block, P1).
    A training fold with one class gives NaN. Returns (score, pooled predictions)."""
    pred = np.full(len(y), -1)
    per = []
    for tr, te in folds:
        if len(np.unique(y[tr])) < 2:
            return np.nan, None
        m = clone(est).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
        per.append(_bacc(y[te], pred[te]) if kind == "main" else np.nan)
    if kind == "main":
        per = np.asarray(per, float)
        return (float(np.mean(per)) if np.all(np.isfinite(per)) else np.nan), pred
    return float(_bacc(y, pred)), pred


# ------------------------------------------------------------------ rows
def p1_z(y, pred):
    """One-sided z test of pooled held-out balanced accuracy against 0.5, var = (1/n1 + 1/n2) / 16 (§5)."""
    if pred is None:
        return float("nan")
    n1, n0 = int(np.sum(y == 1)), int(np.sum(y == 0))
    if n1 == 0 or n0 == 0:
        return float("nan")
    ba = _bacc(y, pred)
    return float(stats.norm.sf((ba - 0.5) / np.sqrt((1 / n1 + 1 / n0) / 16)))


def sequential_p(stat_null, obs, rs, n_max=None, h=None):
    """Besag-Clifford: draw until h exceedances (p = h / k) or n_max draws (usual p). stat_null(rs) -> one null
    statistic. Exceedance = null >= obs; NaN null counts as an exceedance."""
    n_max = N_DRAWS if n_max is None else n_max                  # read at call time (module setting)
    h = H_STOP if h is None else h
    if not np.isfinite(obs):
        return float("nan"), 0
    ex = 0
    for k in range(1, n_max + 1):
        v = stat_null(rs)
        if not np.isfinite(v) or v >= obs - 1e-12:
            ex += 1
            if ex >= h:
                return h / k, k
    return (1 + ex) / (n_max + 1), n_max


def p2(est, X, y, folds, kind, rs):
    """scikit-learn permutation_test_score rule (all labels permuted at trial level, CV rerun) with fixed folds,
    sequential; rs = numpy RandomState (as scikit-learn's _shuffle)."""
    obs, _ = cv_score(est, X, y, folds, kind)
    return sequential_p(lambda r: cv_score(est, X, y[r.permutation(len(y))], folds, kind)[0], obs, rs)


def p4(est, X, y, folds, kind, rs):
    """Training labels permuted per fold, refit, test labels kept (PyMVPA / ADAM), sequential."""
    obs, _ = cv_score(est, X, y, folds, kind)

    def one(r):
        pred = np.full(len(y), -1)
        per = []
        for tr, te in folds:
            ytr = y[tr][r.permutation(len(tr))]
            if len(np.unique(ytr)) < 2:
                return np.nan
            pred[te] = clone(est).fit(X[tr], ytr).predict(X[te])
            per.append(_bacc(y[te], pred[te]))
        return float(np.mean(per)) if kind == "main" else float(_bacc(y, pred))
    return sequential_p(one, obs, rs)


def subset_folds(folds, keep):
    """Session folds restricted to the trials in `keep` (bool over the session's kept trials), re-indexed."""
    idx = np.cumsum(keep) - 1
    w = np.where(keep)[0]
    return [(idx[np.intersect1d(tr, w)], idx[np.intersect1d(te, w)]) for tr, te in folds]


def null_refit(est, X, lab, kind, fm):
    """Null statistic of one pseudosession label vector (NaN = dropped): pipeline rerun on its own trials, S-main
    folds = session folds restricted to those trials, S-block folds from its own blocks. Does not depend on the
    scored labels, so it is computed once per pool member and region-session (cache in run_ibl)."""
    keep = ~np.isnan(lab)
    yl = lab[keep].astype(int)
    fl = subset_folds(fm, keep) if kind == "main" else sblock_folds(yl)
    return cv_score(est, X[keep], yl, fl, kind)[0]


def ps_rows(est, X, y, nulls_refit, pool, kind, fm, fixed=True):
    """PS-refit and PS-fixed. y: scored labels on the session's kept trials (NaN = not in this label's trial set);
    nulls_refit: precomputed null_refit values of the pool members used; pool: their label vectors (for PS-fixed).
    Observed on y's own trials. PS-fixed: the predictions of the decoder fitted on y, scored against each null
    label vector on the trials both define. Returns (p_refit, p_fixed or None)."""
    ko = ~np.isnan(y)
    yo = y[ko].astype(int)
    folds = subset_folds(fm, ko) if kind == "main" else sblock_folds(yo)
    obs, pred = cv_score(est, X[ko], yo, folds, kind)
    p_fix = None
    if fixed:
        null_f = []
        pfull = np.full(len(y), -1)
        if pred is not None:
            pfull[ko] = pred
        for lab in pool:
            both = ko & ~np.isnan(lab)
            yl, pk = lab[both].astype(int), pfull[both]
            if pred is None:
                null_f.append(np.nan)
            elif kind == "main":
                fb = subset_folds(fm, both)
                per = [_bacc(yl[te], pk[te]) for _, te in fb]
                null_f.append(float(np.mean(per)) if np.all(np.isfinite(per)) else np.nan)
            else:
                null_f.append(float(_bacc(yl, pk)))
        p_fix = p_mc(null_f, obs)
    return p_mc(nulls_refit, obs), p_fix


# ------------------------------------------------------------------ selection pipeline (Q3)
def calib_split(y):
    """Calibration = first half of each block (time order), held-out = second half (§4)."""
    g = blocks_of(y)
    cal = np.zeros(len(y), bool)
    for b in np.unique(g):
        idx = np.where(g == b)[0]
        cal[idx[: len(idx) // 2]] = True
    return cal, ~cal


def select_units(X, y, cal):
    """Units with two-sample KS p < 0.05 between sides on calibration trials; fewer than 2 -> the 2 smallest p."""
    a, b = X[cal & (y == 1)], X[cal & (y == 0)]
    if len(a) == 0 or len(b) == 0:
        return None
    p = np.array([stats.ks_2samp(a[:, u], b[:, u]).pvalue for u in range(X.shape[1])])
    sel = np.where(p < 0.05)[0]
    return sel if len(sel) >= 2 else np.argsort(p, kind="stable")[:2]


def sel_score(X, y, units=None, split=None):
    """Fit the decoder (without SelectKBest) on calibration trials of the selected units, balanced accuracy on
    held-out. units=None: select on this label vector; split=None: split from this label vector."""
    cal, ho = calib_split(y) if split is None else split
    if units is None:
        units = select_units(X, y, cal)
    if units is None or len(np.unique(y[cal])) < 2 or len(np.unique(y[ho])) < 2:
        return np.nan, units
    m = decoder(len(units), select=False).fit(X[cal][:, units], y[cal])
    return float(_bacc(y[ho], m.predict(X[ho][:, units]))), units


def null_sel_repeat(X, lab):
    """SEL-repeat null statistic of one pseudosession (selection and fit rerun on its own trials); label-independent
    of the scored vector, cached per pool member and region-session."""
    keep = ~np.isnan(lab)
    return sel_score(X[keep], lab[keep].astype(int))[0]


def sel_rows(X, y, nulls_repeat, pool):
    """SEL-repeat (precomputed nulls) and SEL-fixed (the units selected on y kept; split and fit rerun on each
    pseudosession's own trials). y with NaN = not in this label's trial set."""
    ko = ~np.isnan(y)
    obs, units = sel_score(X[ko], y[ko].astype(int))
    fix = []
    for lab in pool:
        keep = ~np.isnan(lab)
        fix.append(sel_score(X[keep], lab[keep].astype(int), units=units)[0] if units is not None else np.nan)
    return p_mc(nulls_repeat, obs), p_mc(fix, obs)


def sel_iid_rows(X, y_iid, split, rs, n=None):
    """i.i.d. control for the selection pipeline: draw j's split, labels = trial permutation of draw j's labels;
    null = trial-level permutations with (a) selection repeated, (b) the selected units of y_iid kept."""
    n = N_DRAWS if n is None else n
    obs, units = sel_score(X, y_iid, split=split)
    a, b = [], []
    for _ in range(n):
        yp = y_iid[rs.permutation(len(y_iid))]
        a.append(sel_score(X, yp, split=split)[0])
        b.append(sel_score(X, yp, units=units, split=split)[0] if units is not None else np.nan)
    return p_mc(a, obs), p_mc(b, obs)
