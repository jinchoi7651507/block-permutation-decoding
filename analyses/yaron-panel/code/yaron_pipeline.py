"""Selection and held-out scoring of Yaron et al. (2025, PLoS Biol 23: e3003242), ported to Python from the
authors' MATLAB code (Zenodo 10.5281/zenodo.15531880, v1.0.0), as needed for the fixed-versus-repeated comparison (Extended Data Fig. 3 of the paper).

Per session: active units (spike sum > 200); per condition and trial, the omission response = mean of bins
306:420 minus mean of bins 276:305 (MATLAB, 1-based); trials subsampled to 50 per condition as in allmats.m.
Pooled over sessions as in FindPEONS.m, including its row offset between the response list and the depth list
(reproduced so that the selection gives the published 123 neurons). Selection on odd trials: (1) Spearman of the
200 training points against condition labels 1..8, p < 0.05; (2) align by the sign of that correlation;
(3) two-sided sign-rank test of the 100 aligned values of conditions 5-8 against 0, p < 0.05; selected = (1) and (3).
Held-out score: Spearman of the aligned per-condition means on even trials, pooled over the selected units,
against the probabilities 0, 5, 10, 20, 75, 85, 90, 95. MATLAB conventions (signrank, corr) are reproduced.
"""
from __future__ import annotations

import functools
import math
from pathlib import Path

import h5py
import numpy as np
from scipy.stats import norm, rankdata, spearmanr, t as tdist

PROB_VALUES = np.array([0, 5, 10, 20, 75, 85, 90, 95], float)
# batchall.m:42, in tables order
SUR = 10 * np.array([260, 220, 305, 222, 284, 246, 300, 270, 170, 210, 260, 280, 280, 280,
                     340, 220, 240, 384 + 40], float) - 520
RESP = slice(305, 420)   # MATLAB 306:420
BASE = slice(275, 305)   # MATLAB 276:305
N_REPS = 50


def matlab_round(x: float) -> int:
    return int(math.floor(abs(x) + 0.5)) * (1 if x >= 0 else -1)


def matlab_signrank(x: np.ndarray, tail: str = "both") -> float:
    """MATLAB signrank(x, 0, 'tail', tail): zeros dropped; exact over the actual midranks for n <= 15,
    else normal approximation with tie and continuity correction. tail 'right' = median > 0."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    x = x[x != 0]
    n = len(x)
    if n == 0:
        return np.nan
    r = rankdata(np.abs(x))
    w = r[x > 0].sum()
    if n <= 15:
        masks = (np.arange(2 ** n)[:, None] >> np.arange(n)) & 1
        sums = masks @ r
        if tail == "right":
            return float(np.mean(sums >= w - 1e-9))
        wm = min(w, r.sum() - w)
        return float(min(1.0, 2 * np.mean(sums <= wm + 1e-9)))
    _, tc = np.unique(np.abs(x), return_counts=True)
    sd = np.sqrt((n * (n + 1) * (2 * n + 1) - (tc ** 3 - tc).sum() / 2) / 24)
    d = w - n * (n + 1) / 4
    if tail == "right":
        return float(norm.sf((d - 0.5) / sd))
    return float(2 * norm.sf(abs((d - 0.5 * np.sign(d)) / sd)))


def spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    ok = ~(np.isnan(x) | np.isnan(y))
    if ok.sum() < 3:
        return np.nan, np.nan
    res = spearmanr(x[ok], y[ok])
    return float(res.statistic), float(res.pvalue)


# ---------------------------------------------------------------- loading (reads neural data)

def _cls(d) -> str:
    c = d.attrs.get("MATLAB_class", b"")
    return c.decode() if isinstance(c, (bytes, np.bytes_)) else str(c)


def _mat_index(f: h5py.File, name: str) -> np.ndarray:
    """MATLAB 1-based row numbers. v7.3 stores an empty array as its dims with MATLAB_empty=1."""
    d = f[name]
    if d.attrs.get("MATLAB_empty", 0):
        return np.array([], int)
    assert _cls(d) == "double", (name, _cls(d))
    return np.asarray(d, float).ravel().astype(int)


def condition_rows(f: h5py.File) -> list[np.ndarray]:
    """inddss from maketests:170 (1-based MATLAB row numbers into res)."""
    g = lambda k: _mat_index(f, k)
    return [g("indd5") + 1000, g("indd55") + 2000, g("indd105") + 4000, g("indo205A") - 4000,
            g("indo205B") - 4000, g("indd105") + 5000, g("indd55") + 3000, g("indd5")]


def load_session(path: Path, sur: float) -> dict:
    """Per-session quantities the pipeline needs. res in HDF5 is stored (units, time, items)."""
    with h5py.File(path, "r") as f:
        res = f["res"]
        assert res.ndim == 3 and res.shape[1] == 600, res.shape
        assert _cls(res) == "double", _cls(res)
        n_units, _, n_items = res.shape
        rows = condition_rows(f)
        # res is chunked (all units, few bins, one item): stream over items once for the totals
        total = np.zeros(n_units)
        for a in range(0, n_items, 250):
            total += np.asarray(res[:, :, a:a + 250], float).sum(axis=(1, 2))
        nu = np.where(total > 200)[0]                       # 0-based unit indices
        cl_ids = np.asarray(f["cluster_ids"], float).ravel()
        cl_depth = np.asarray(f["cluster_depths"], float).ravel()
        uni = np.asarray(f["uni"], float).ravel()
        assert nu.max(initial=-1) < len(uni), (len(uni), nu.max())   # MATLAB uni(nu(i)) would error
        # read only the rows and bins the pipeline uses, in one pass
        used = np.unique(np.concatenate(rows)) - 1
        pos = {r: i for i, r in enumerate(used)}
        W = np.asarray(res[:, 275:420, used], float)        # (units, bins 276:420, used rows)
        resp_sl, base_sl = slice(30, 145), slice(0, 30)     # 306:420 and 276:305 within W
        allom, meanom, depth = [], [], []
        for u in nu:
            X = W[u]                                        # (bins, used rows)
            per_cond, means = [], []
            for idx in rows:
                cols = np.array([pos[r] for r in idx - 1])
                resp = X[resp_sl][:, cols].mean(0) - X[base_sl][:, cols].mean(0)   # per trial (:205)
                per_cond.append(resp)
                # :204 order: time mean per trial, then trial mean; baseline trial mean per bin, then bin mean
                means.append(X[resp_sl][:, cols].mean(0).mean() - X[base_sl][:, cols].mean(1).mean())
            allom.append(per_cond)
            meanom.append(means)
            hit = cl_depth[cl_ids == uni[u]]
            assert len(hit) == 1, (u, len(hit))
            depth.append(hit[0])
    meanom = np.array(meanom)
    m = np.array([functools.reduce(lambda a, b: a + b, row) / 8 for row in meanom])  # sequential sum
    sel = np.where(~np.isinf(m) & ~np.isnan(m) & (m != 0))[0]
    near_zero = np.where((m != 0) & (np.abs(m) < 1e-9))[0]    # logged: exact-zero test is order-sensitive
    return {"allom": allom, "sel": sel, "depth_post": sur - np.array(depth)[sel],
            "n_active": len(nu), "rows_len": [len(r) for r in rows], "near_zero": near_zero}


def session_ids(tables_path: Path) -> list[str]:
    """tables{1,1..18} in order (the order batchall.m iterates and SUR is paired with)."""
    import scipy.io as sio                                   # tables.mat is a small v5 file (510 B)
    t = sio.loadmat(tables_path)["tables"]                   # 6 x 18 cell; row 1 = session ids
    assert t.shape == (6, 18), t.shape
    return [str(np.asarray(t[0, j]).ravel()[0]) for j in range(18)]


def load_all(raw_dir: Path) -> list[dict]:
    ids = session_ids(raw_dir / "tables.mat")
    assert len(ids) == 18, ids
    return [dict(load_session(raw_dir / f"res{sid}.mat", SUR[tt]), sid=sid) for tt, sid in enumerate(ids)]


# ---------------------------------------------------------------- pooling (sel bug reproduced)

def pooled_rows(sessions: list[dict]) -> tuple[list, np.ndarray, np.ndarray]:
    """allom rows (pre-sel, all sessions), depth list (post-sel), session of each allom row."""
    allom = [row for s in sessions for row in s["allom"]]
    depth = np.concatenate([s["depth_post"] for s in sessions])
    session_of_row = np.concatenate([np.full(s["n_active"], i) for i, s in enumerate(sessions)])
    return allom, depth, session_of_row


def subsample(A: np.ndarray) -> np.ndarray:
    step = matlab_round((len(A) - 1) / 51)
    s = A[::step]
    if len(s) < N_REPS:
        raise ValueError(f"only {len(s)} samples after subsampling (L={len(A)}, step={step})")
    return 30000 * s[:N_REPS]


def session_of_data_rows(session_of_row: np.ndarray, omind: np.ndarray) -> np.ndarray:
    """Session membership of the rows of data, by allom row."""
    return session_of_row[omind]


def pooled_rows_fixed(sessions: list[dict]) -> tuple[list, np.ndarray, np.ndarray]:
    """Pooling without the row offset: allom rows restricted to each session's sel (not used here)."""
    allom = [s["allom"][i] for s in sessions for i in s["sel"]]
    depth = np.concatenate([s["depth_post"] for s in sessions])
    session_of_row = np.concatenate([np.full(len(s["sel"]), i) for i, s in enumerate(sessions)])
    return allom, depth, session_of_row


def build_data(allom: list, depth: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """FindPEONS:19-21 + allmats.m: omind indexes allom rows by position in the depth list."""
    omind = np.where((depth < 1800) & (depth > 0))[0]
    data = np.stack([np.stack([subsample(np.asarray(allom[i][j])) for j in range(8)], axis=1)
                     for i in omind])                   # (neurons, 50, 8)
    return data, omind


# ---------------------------------------------------------------- selection and scoring

def permute_blocks(data: np.ndarray, session_of_neuron: np.ndarray, perms: np.ndarray) -> np.ndarray:
    """Block-label permutation: in session s, condition column c takes the data of block perms[s][c].
    The same permutation applies to odd and even trials."""
    out = np.empty_like(data)
    for s in np.unique(session_of_neuron):
        m = session_of_neuron == s
        out[m] = data[m][:, :, perms[s]]
    return out


def heldout_rho(data: np.ndarray, test: np.ndarray, peon: np.ndarray, sign: np.ndarray):
    """FindPEONS section 8: pooled Spearman of aligned per-condition test means."""
    idx = np.where(peon)[0]
    if len(idx) == 0:
        return 0.0, np.nan, 0
    te = data[idx][:, test, :].mean(1)                  # (k, 8)
    te = np.where(sign[idx, None] == -1, te[:, ::-1], te)
    y = te.reshape(-1, order="F")                       # condition-major, as mean(:) in :376
    x = np.repeat(PROB_VALUES, len(idx))
    r, p = spearman(x, y)
    return r, p, len(idx)


ODD = np.arange(0, N_REPS, 2)    # MATLAB 1:2:50
EVEN = np.arange(1, N_REPS, 2)   # MATLAB 2:2:50


# ---------------------------------------------------------------- fast selection

def spearman_rows(Y: np.ndarray, x: np.ndarray):
    """Row-wise Spearman of Y (n, m) against x (m,), average ranks, Student-t p (as scipy/MATLAB large n)."""
    ry = rankdata(Y, axis=1)
    rx = rankdata(x)
    ry = ry - ry.mean(1, keepdims=True)
    rx = rx - rx.mean()
    den = np.sqrt((ry ** 2).sum(1) * (rx ** 2).sum())
    with np.errstate(invalid="ignore", divide="ignore"):
        r = (ry @ rx) / den
        m = Y.shape[1]
        tt = r * np.sqrt((m - 2) / np.maximum(1 - r ** 2, 1e-300))
        p = 2 * tdist.sf(np.abs(tt), m - 2)
    p = np.where(np.abs(r) >= 1, 0.0, p)
    bad = np.isnan(Y).any(1)
    for i in np.where(bad)[0]:                            # 'Rows','complete' path
        r[i], p[i] = spearman(x.astype(float), Y[i])
    return r, p


def select_fast(data: np.ndarray, train: np.ndarray, tail: str = "both"):
    tr = data[:, train, :]
    lab = np.tile(np.arange(1, 9), len(train)).astype(float)
    rho, pc = spearman_rows(tr.reshape(len(tr), -1), lab)
    sign = np.sign(rho)
    sign[np.isnan(sign) | (sign == 0)] = 1
    al = np.where(sign[:, None, None] == -1, tr[:, :, ::-1], tr)
    hp = al[:, :, 4:8].reshape(len(tr), -1)
    sig = np.zeros(len(tr), bool)
    for i in range(len(tr)):
        h = hp[i][~np.isnan(hp[i])]
        if len(h) and np.any(h != 0):
            sig[i] = matlab_signrank(h, tail) < 0.05
    return (pc < 0.05) & sig, sign, pc


def score(data, train, test, tail="both"):
    peon, sign, pc = select_fast(data, train, tail)
    rho, _, k = heldout_rho(data, test, peon, sign)
    return (0.0 if not np.isfinite(rho) else rho), int(peon.sum()), peon, sign, pc


def draw_perms_full(draw: int, n_sess: int) -> np.ndarray:
    """One uniform permutation of the eight condition blocks per session, seeds default_rng([11, 1, session, draw])
    (the seeds of the earlier run of this analysis, 2026-10-06)."""
    out = np.empty((n_sess, 8), int)
    for s in range(n_sess):
        out[s] = np.random.default_rng([11, 1, s, draw]).permutation(8)
    return out
