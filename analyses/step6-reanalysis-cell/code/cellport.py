"""Python port of the pseudo-population decoder of Jahn et al., Cell 2024 (PMC11574977), Figure 2D and Fig. S3G.

Follows the authors' MATLAB code in authors-code/Figure_2/code (file and line references in DESIGN.md section 4).
Approximations (marked APPROX): the hyperparameter search (grid instead of bayesopt), fitPosterior (Platt scaling on
10-fold cross-validated scores) and fitcnet (sklearn MLP with the defaults recalled for fitcnet). To verify on the
real files: the holdout size (assumed round(0.2 * N)), the fitcnet defaults, the fitPosterior details.

Everything fitted to labels (qualifying neurons, trials per cell, hyperparameters, calibration, combiner) is inside
`run_decoder`, so a permutation test that calls it with permuted labels refits every step.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import warnings

import cell_env  # noqa: F401  (sets the thread variables to 1 before numpy is imported)
import numpy as np
from scipy.optimize import minimize
from sklearn.model_selection import KFold
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

warnings.filterwarnings("ignore", message="Solver terminated early")
N_PROG = 3
N_BINS = 3
import os
MIN_TRIALS = int(os.environ.get("CELL_MIN_TRIALS", "60"))   # a neuron qualifies with at least this many trials in each of the 9 cells (60; the synthetic suite lowers it through the variable so that worker processes agree)
HOLDOUT = 0.2


def n_val(n, rule=None):
    """Validation trials per cell for n trials: round(0.2 n) for rule 'round', ceil(0.2 n) for rule 'ceil'. The rule is
    fixed from the published gate values at gate time (cell_gate.val_rule_from_gate) and passed to the worker
    processes through the environment variable CELL_VAL_RULE (default 'round')."""
    import math
    rule = rule or os.environ.get("CELL_VAL_RULE", "round")
    if rule == "round":
        return int(round(HOLDOUT * n))
    if rule == "ceil":
        return int(math.ceil(HOLDOUT * n - 1e-9))
    raise ValueError("unknown validation size rule %r" % rule)
# APPROX: grid replacing bayesopt over BoxConstraint and KernelScale (the two hyperparameters the paper names; the
# MATLAB default Standardize is false, so standardisation is not searched: DESIGN.md section 0, D6). For a linear
# kernel, dividing the predictors by KernelScale s is the same as multiplying C by 1/s^2, so one effective C is searched.
# Upper end capped at 10^1: C >= 10^1.5 can need seconds per fit.
GRIDS = {"coarse": (-6.0, -4.5, -3.0, -2.0, -1.0, 0.0, 1.0),                         # default, 7 settings
         "fine": tuple(float(x) for x in np.round(np.arange(-6.0, 1.0 + 1e-9, 1.0 / 3.0), 4))}   # V2, 22 settings
LOG10_C_GRID = GRIDS["coarse"]
GRID_TOP = 1.0       # the upper edge, for the report of how often the chosen C sits at the edge
HIDDEN = 10                # fitcnet default, recalled, to verify


# ----------------------------------------------------------------------------- labels and cells
def color_bin(angle):
    """Third of the circle, 1..3, as the authors' comparisons (>= lower, < upper); 0 for NaN."""
    a = np.asarray(angle, float)
    out = np.zeros(a.shape, int)
    ok = ~np.isnan(a)
    m = np.mod(a, 2 * np.pi)
    for c in range(1, N_BINS + 1):
        sel = ok & (m >= (c - 1) * 2 * np.pi / N_BINS) & (m < c * 2 * np.pi / N_BINS)
        out[sel] = c
    return out


def peak_belief_angle(belief):
    """belief: (100, n_trials). argmax (first maximum) as angle 0..2pi*(99/100); NaN if the column is all zero."""
    b = np.asarray(belief, float)
    ang = np.argmax(b, axis=0) * (2 * np.pi / b.shape[0])
    ang = ang.astype(float)
    ang[np.all(b == 0, axis=0)] = np.nan
    return ang


def progression_in_block(block_nb, trial_in_block):
    block_nb = np.asarray(block_nb)
    size = {b: np.sum(block_nb == b) for b in np.unique(block_nb)}
    return np.array([t / size[b] for b, t in zip(block_nb, trial_in_block)], float)


def progression_membership(prog):
    """(n, 3) boolean, as written: level 1 if p <= 1/3; level 2 if 1/3 < p <= 2/3; level 3 if p >= 2/3
    (a trial at exactly 2/3 is in levels 2 and 3, as in the authors' code)."""
    p = np.asarray(prog, float)
    ok = ~np.isnan(p)
    m = np.zeros((len(p), N_PROG), bool)
    m[:, 0] = ok & (p <= 1 / N_PROG)
    for j in range(2, N_PROG):
        m[:, j - 1] = ok & (p > (j - 1) / N_PROG) & (p <= j / N_PROG)
    m[:, N_PROG - 1] = ok & (p >= (N_PROG - 1) / N_PROG)
    return m


@dataclass
class Session:
    """One recording session after the column shift of the authors' prepare_pseudopop step.
    Column j holds the target-window rates of trial j+1 and the labels of trial j+1."""
    sid: int
    block: np.ndarray                 # (n_cols,) block number of each column
    prog: np.ndarray                  # (n_cols,) progression in block
    true_bin: np.ndarray              # (n_cols,) 1..3, 0 = no label
    belief_bin: np.ndarray            # (n_cols,) 1..3, 0 = no label
    feat: dict = field(default_factory=dict)   # roi -> (n_neurons, n_cols) active window (default 900 ms)
    feat_by_window: dict = field(default_factory=dict)   # "900" / "600" -> roi -> (n_neurons, n_cols)
    prog_member: np.ndarray = None

    def __post_init__(self):
        if self.prog_member is None:
            self.prog_member = progression_membership(self.prog)


def assemble_columns(fr_windows, n_reward_windows=7):
    """fr_windows: list of 27 arrays (neurons, n_trials): windows 1..7 reward_end, 8..27 target. Returns
    (raw (neurons, n_trials-1, 27) after the authors' fill, kept (neurons,) bool).
    Reward_end windows use trials 1..n-1, target windows trials 2..n (so column j pairs reward end of trial j with
    the targets of trial j+1). NaNs in a column are set to 0 when any of the 27 windows is not NaN; a neuron is
    dropped if window 1 is still NaN in any column."""
    n_tr = fr_windows[0].shape[1]
    nn = fr_windows[0].shape[0]
    raw = np.full((nn, n_tr - 1, len(fr_windows)), np.nan)
    for w, fr in enumerate(fr_windows):
        fr = np.asarray(fr, float)
        raw[:, :, w] = fr[:, : n_tr - 1] if w < n_reward_windows else fr[:, 1:]
    anyval = np.any(~np.isnan(raw), axis=2)
    for w in range(raw.shape[2]):
        sel = anyval & np.isnan(raw[:, :, w])
        raw[:, :, w][sel] = 0.0
    kept = ~np.any(np.isnan(raw[:, :, 0]), axis=1)
    return raw, kept


WINDOWS = {"900": (7, 13, 19), "600": (7, 13)}   # 0-based window indices of the code (windows 8, 14, 20; 8, 14)


def mean_windows(raw, kept, idx=(7, 13, 19)):
    """Mean of windows 8, 14, 20 (0-based 7, 13, 19) = the 900 ms combination of the authors (this_combination 2):
    the 300 ms windows -600 to -300, -300 to 0 and 0 to 300 ms around target onset, so the 900 ms window includes
    the first 300 ms after the targets. WINDOWS['600'] (windows 8 and 14, -600 to 0 ms) is the pre-target secondary."""
    return raw[kept][:, :, list(idx)].mean(axis=2)


def with_window(sessions, key):
    """Shallow copies of the sessions whose active features are the window `key` ('900' or '600')."""
    import copy
    out = []
    for s in sessions:
        c = copy.copy(s)
        c.feat = {r: a for r, a in s.feat_by_window[key].items()}
        out.append(c)
    return out


# ----------------------------------------------------------------------------- design from labels
def cell_columns(sess, bins):
    """dict (k, c) -> column indices, k = 0..2 progression level, c = 0..2 colour bin, for the label vector."""
    out = {}
    for k in range(N_PROG):
        for c in range(N_BINS):
            out[(k, c)] = np.where(sess.prog_member[:, k] & (bins == c + 1))[0]
    return out


def build_design(sessions, bins_by_session, rois, roi_sessions):
    """Qualifying neurons, N_progression and N_neurons for a labelling.
    roi_sessions: roi -> list of session indices that contribute to the ROI.
    Returns dict with 'cells' (per session), 'qual' (roi -> list of (session index, neuron index)), 'n_prog',
    'n_neurons', 'n_qual' (roi -> count); n_prog is None if no neuron qualifies in some ROI."""
    cells = [cell_columns(s, b) for s, b in zip(sessions, bins_by_session)]
    qual, mins = {}, []
    for roi in rois:
        q = []
        for si in roi_sessions[roi]:
            m = min(len(v) for v in cells[si].values())
            if m >= MIN_TRIALS:
                nn = sessions[si].feat[roi].shape[0]
                q += [(si, n) for n in range(nn)]
                mins.append(m)
        qual[roi] = q
    n_qual = {r: len(qual[r]) for r in rois}
    if min(n_qual.values()) == 0:
        return {"cells": cells, "qual": qual, "n_prog": None, "n_neurons": 0, "n_qual": n_qual}
    return {"cells": cells, "qual": qual, "n_prog": int(min(mins)), "n_neurons": int(min(n_qual.values())),
            "n_qual": n_qual}


def draw_pseudopop(rng, sessions, design, roi):
    """One bootstrap draw (authors' prepare_bootstrap): neurons with replacement among qualifying ones, per neuron
    and cell n_prog trials without replacement from its own session, 80/20 holdout per neuron and cell.
    Returns Xtt (neurons, n_tt, 3, 3), Xva (neurons, n_va, 3, 3) with axes (neuron, trial, level, bin)."""
    npg, nn = design["n_prog"], design["n_neurons"]
    n_va = n_val(npg)
    n_tt = npg - n_va
    q = design["qual"][roi]
    pick = rng.integers(0, len(q), size=nn)
    Xtt = np.empty((nn, n_tt, N_PROG, N_BINS))
    Xva = np.empty((nn, n_va, N_PROG, N_BINS))
    for i, pi in enumerate(pick):
        si, n = q[pi]
        f = sessions[si].feat[roi][n]
        cl = design["cells"][si]
        for k in range(N_PROG):
            for c in range(N_BINS):
                cols = rng.choice(cl[(k, c)], size=npg, replace=False)
                perm = rng.permutation(npg)
                Xva[i, :, k, c] = f[cols[np.sort(perm[:n_va])]]
                Xtt[i, :, k, c] = f[cols[np.sort(perm[n_va:])]]
    return Xtt, Xva


# ----------------------------------------------------------------------------- classifiers
def _fit_svc(X, y, log10c):
    return SVC(kernel="linear", C=10.0 ** log10c, max_iter=200000).fit(X, y)


def _decision(model, X):
    return model.decision_function(X)


def _platt(f, y):
    """Platt scaling with smoothed targets; P(y=1) = 1 / (1 + exp(A f + B)). APPROX of fitPosterior."""
    npos, nneg = int(np.sum(y == 1)), int(np.sum(y == 0))
    t = np.where(y == 1, (npos + 1.0) / (npos + 2.0), 1.0 / (nneg + 2.0))

    def nll(ab):
        z = ab[0] * f + ab[1]
        return float(np.sum(t * z + np.logaddexp(0, -z)))   # = -sum t log p - (1-t) log(1-p), p = sigmoid(-z)

    res = minimize(nll, np.array([0.0, np.log((nneg + 1.0) / (npos + 1.0))]), method="BFGS")
    return float(res.x[0]), float(res.x[1])


def fit_binary_svm(X, y, rng, grid="coarse"):
    """Hyperparameter search (10-fold CV misclassification over the grid), final fit, Platt calibration from
    10-fold CV scores. X (m, neurons), y in {0, 1}. Returns (model, A, B, chosen log10 C). Ties go to the first
    setting in grid order (the smallest C)."""
    kf = list(KFold(10, shuffle=True, random_state=int(rng.integers(2**31 - 1))).split(X))
    best, bestloss = None, np.inf
    for lc in GRIDS[grid]:
        err = 0
        for tr, te in kf:
            if len(np.unique(y[tr])) < 2:
                err += len(te) * 0.5
                continue
            m = _fit_svc(X[tr], y[tr], lc)
            err += np.sum((_decision(m, X[te]) > 0).astype(int) != y[te])
        if err < bestloss - 1e-12:
            best, bestloss = lc, err
    lc = best
    final = _fit_svc(X, y, lc)
    kf2 = list(KFold(10, shuffle=True, random_state=int(rng.integers(2**31 - 1))).split(X))
    cv_f = np.empty(len(y))
    for tr, te in kf2:
        cv_f[te] = _decision(_fit_svc(X[tr], y[tr], lc), X[te])
    A, B = _platt(cv_f, y)
    return final, A, B, lc


def posterior(model, A, B, X):
    return 1.0 / (1.0 + np.exp(A * _decision(model, X) + B))


def _svm_training_set(Xtt, k, n_data, other_idx, as_written, levels):
    """Training matrix for the classifier of bin k (authors' loops). levels: list of progression levels pooled.
    as_written=True reproduces the `increment=1` placement: in each level group the first n_data/2 'other' columns
    hold the first other bin for neuron 1 only (other neurons zero), the next n_data/2 hold the second other bin
    for all neurons. as_written=False places both other bins for all neurons."""
    nn = Xtt.shape[0]
    others = [l for l in range(N_BINS) if l != k]
    half = n_data // 2
    this = np.concatenate([Xtt[:, :n_data, p, k] for p in levels], axis=1)
    cols = []
    for p in levels:
        blk = np.zeros((nn, n_data))
        if as_written:
            blk[0, :half] = Xtt[0, other_idx, p, others[0]]
            blk[:, half:] = Xtt[:, other_idx, p, others[1]]
        else:
            blk[:, :half] = Xtt[:, other_idx, p, others[0]]
            blk[:, half:] = Xtt[:, other_idx, p, others[1]]
        cols.append(blk)
    other = np.concatenate(cols, axis=1)
    X = np.concatenate([this.T, other.T], axis=0)
    y = np.concatenate([np.ones(this.shape[1], int), np.zeros(other.shape[1], int)])
    return X, y


def _mlp(P, g, rng):
    """APPROX of fitcnet defaults: one hidden layer of 10 ReLU units, no regularisation, L-BFGS."""
    return MLPClassifier(hidden_layer_sizes=(HIDDEN,), activation="relu", solver="lbfgs", alpha=0.0, max_iter=1000,
                         tol=1e-6, random_state=int(rng.integers(2**31 - 1))).fit(P, g)


def _val_matrix(Xva, p):
    """Validation observations of level p, bins stacked: (3 * n_va, neurons) and bin labels 0..2."""
    nva = Xva.shape[1]
    X = np.concatenate([Xva[:, :, p, c].T for c in range(N_BINS)], axis=0)
    g = np.repeat(np.arange(N_BINS), nva)
    return X, g


def decode_across(Xtt, Xva, rng, as_written=True, grid="coarse", log=None):
    """Authors' main decoder: three one-versus-rest SVMs trained on the three levels pooled, then a network on the
    three posteriors of all training trials. Returns validation accuracy per progression level (3,)."""
    n_tt = Xtt.shape[1]
    n_data = n_tt - (n_tt % 2)
    models = []
    for k in range(N_BINS):
        other_idx = np.sort(rng.choice(n_data, n_data // 2, replace=False))
        X, y = _svm_training_set(Xtt, k, n_data, other_idx, as_written, list(range(N_PROG)))
        m, A, B, hp = fit_binary_svm(X, y, rng, grid)
        if log is not None:
            log.append(hp)
        models.append((m, A, B))
    Xall = np.concatenate([Xtt[:, :, p, c].T for p in range(N_PROG) for c in range(N_BINS)], axis=0)
    gall = np.concatenate([np.full(n_tt, c) for p in range(N_PROG) for c in range(N_BINS)])
    P = np.column_stack([posterior(m, A, B, Xall) for m, A, B in models])
    net = _mlp(P, gall, rng)
    acc = np.empty(N_PROG)
    for p in range(N_PROG):
        Xv, gv = _val_matrix(Xva, p)
        Pv = np.column_stack([posterior(m, A, B, Xv) for m, A, B in models])
        acc[p] = np.mean(net.predict(Pv) == gv)
    return acc


def decode_within(Xtt, Xva, rng, as_written=True, grid="coarse", log=None):
    """Authors' 'within' decoder: SVMs and network trained separately for each progression level."""
    n_tt = Xtt.shape[1]
    n_data = n_tt - (n_tt % 2)
    acc = np.empty(N_PROG)
    for p in range(N_PROG):
        models = []
        for k in range(N_BINS):
            other_idx = np.sort(rng.choice(n_data, n_data // 2, replace=False))
            X, y = _svm_training_set(Xtt, k, n_data, other_idx, as_written, [p])
            m, A, B, hp = fit_binary_svm(X, y, rng, grid)
            if log is not None:
                log.append(hp)
            models.append((m, A, B))
        Xall = np.concatenate([Xtt[:, :, p, c].T for c in range(N_BINS)], axis=0)
        gall = np.repeat(np.arange(N_BINS), n_tt)
        P = np.column_stack([posterior(m, A, B, Xall) for m, A, B in models])
        net = _mlp(P, gall, rng)
        Xv, gv = _val_matrix(Xva, p)
        Pv = np.column_stack([posterior(m, A, B, Xv) for m, A, B in models])
        acc[p] = np.mean(net.predict(Pv) == gv)
    return acc


def decode_centroid(Xtt, Xva, rng, as_written=True, grid="coarse", log=None):
    """Cheap stand-in used only by the synthetic size studies (variant 'fast'): nearest class centroid on the
    pseudo-population, fitted on the training trials of the three levels pooled. Not part of the analysis."""
    cen = np.stack([np.concatenate([Xtt[:, :, p, c] for p in range(N_PROG)], axis=1).mean(1) for c in range(N_BINS)])
    acc = np.empty(N_PROG)
    for p in range(N_PROG):
        Xv, gv = _val_matrix(Xva, p)
        d = ((Xv[:, None, :] - cen[None]) ** 2).sum(2)
        acc[p] = np.mean(d.argmin(1) == gv)
    return acc


# ----------------------------------------------------------------------------- whole pipeline for one labelling
def decode_draw(sessions, design, roi, rng, variant="across", as_written=True, grid="coarse", log=None):
    """One pseudo-population draw for one ROI, fully refitted. Returns the validation accuracy per level (3,)."""
    fn = {"across": decode_across, "within": decode_within, "fast": decode_centroid}[variant]
    Xtt, Xva = draw_pseudopop(rng, sessions, design, roi)
    return fn(Xtt, Xva, rng, as_written=as_written, grid=grid, log=log)


def run_decoder(sessions, bins_by_session, rois, roi_sessions, n_draws, rng, variant="across", as_written=True,
                grid="coarse"):
    """The whole pipeline for one label vector: design (qualification, trials per cell, neurons), then n_draws
    pseudo-populations per ROI, each fully refitted. Returns dict roi -> (n_draws, 3) accuracies (or None when no
    design exists), the design counts and the chosen log10 C of every SVM fit per ROI ('hp')."""
    des = build_design(sessions, bins_by_session, rois, roi_sessions)
    if des["n_prog"] is None:
        return {"acc": {r: None for r in rois}, "n_prog": None, "n_neurons": des["n_neurons"], "n_qual": des["n_qual"],
                "hp": {r: [] for r in rois}}
    acc = {r: np.empty((n_draws, N_PROG)) for r in rois}
    hp = {r: [] for r in rois}
    for r in rois:
        for d in range(n_draws):
            acc[r][d] = decode_draw(sessions, des, r, rng, variant, as_written, grid, hp[r])
    return {"acc": acc, "n_prog": des["n_prog"], "n_neurons": des["n_neurons"], "n_qual": des["n_qual"], "hp": hp}


def z_test(dist, null=1 / 3):
    """The authors' test: z = (mean - null) / std over the draws (std with ddof=1, MATLAB default), p = 1 - normcdf(z)."""
    from scipy.stats import norm
    d = np.asarray(dist, float)
    return float(norm.sf((d.mean() - null) / d.std(ddof=1)))
