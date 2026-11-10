"""Python port of the preprocessing in the authors' MATLAB code (Zenodo 16333867).

Sources (extracted to ../authors-code/, see NOTES.md):
  Support Functions/MATLAB/dF_Anya_test.m     -> df_anya()
  Figure Functions/Figure4.m, Panel D         -> fig4_cell_filter(), build_trials()
  Figure Functions/Figure2.m, Panel F/G       -> fig2_cells(), fig2_clusters()

MATLAB conventions reproduced here (each checked in test_synthetic.py):
  prctile      = linear interpolation with plotting position (i - 0.5)/n  (numpy method="hazen")
  movmean(x,5) = centred window of 5, shrinking at the ends
  zscore       = (x - mean) / std with N - 1
  EventTS      = 1-based frame indices
"""
from __future__ import annotations

import warnings

import numpy as np
from scipy.interpolate import interp1d

FS = 30            # imaging frames per second
PRE = 5            # s before the event
POST = 5           # s after the event
BIN = 2            # frames per bin (66 ms)
N_FRAMES = (PRE + POST) * FS          # 300
N_BINS = N_FRAMES // BIN              # 150


def bin_centre_s(k1: int) -> float:
    """Centre time (s, relative to the event frame) of 1-based bin k1 (MATLAB index)."""
    return (2 * k1 - 0.5 - PRE * FS) / FS


def matlab_prctile(x, p):
    x = np.asarray(x, float)
    return float(np.percentile(x, p, method="hazen"))


def matlab_movmean(x, k=5):
    x = np.asarray(x, float)
    n = len(x)
    h = k // 2
    c = np.concatenate([[0.0], np.cumsum(x)])
    lo = np.clip(np.arange(n) - h, 0, n)
    hi = np.clip(np.arange(n) + h + 1, 0, n)
    return (c[hi] - c[lo]) / (hi - lo)


def matlab_zscore(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    if s == 0:
        s = 1.0                      # MATLAB zscore: a zero standard deviation is replaced by 1
    return (x - x.mean()) / s


def df_anya(signal, fs=FS, win_s=60, base_prc=50):
    """dF_Anya_test.m: baseline = 50th percentile in non-overlapping 60-s windows (window I1..I1+winSize,
    inclusive, as in the MATLAB code), placed at positions 1:ceil(Ls/nPts):end and linearly
    interpolated/extrapolated; dF/F in percent; all-NaN if the baseline goes negative.
    (The paper text also mentions Gaussian smoothing; the deposited function has none.)"""
    FP = np.asarray(signal, float).ravel()
    Ls = len(FP)
    win = win_s * fs
    n_pts = Ls // win
    if n_pts < 2:
        raise ValueError("recording shorter than two baseline windows")
    step = int(np.ceil(Ls / n_pts))
    X = np.arange(1, Ls + 1)[::step]
    Y = np.empty(n_pts)
    for n in range(n_pts):
        i1 = n * win + 1
        i2 = min(i1 + win, Ls)
        Y[n] = matlab_prctile(FP[i1 - 1:i2], base_prc)
    if len(X) != n_pts:
        raise ValueError("MATLAB interp1 would fail here (len(X)=%d, nPts=%d)" % (len(X), n_pts))
    L = np.arange(1, Ls + 1)
    if np.ptp(Y) == 0:
        # MATLAB interp1 returns exactly Y(1) for equal knots; scipy's extrapolation adds ~1e-16 noise
        baseline = np.full(Ls, Y[0])
    else:
        baseline = interp1d(X, Y, kind="linear", fill_value="extrapolate")(L)
    if baseline.min() < 0:
        return np.full(Ls, np.nan), np.nan
    return (FP - baseline) / baseline * 100.0, float(baseline.mean())


def _upward_crossings(v, thresh):
    idxl = v >= thresh
    idxl[0] = False
    idx = np.where(idxl)[0]
    return idx[v[idx - 1] < thresh]


def fig4_keep_cell(df):
    """Figure4.m cell filter: more than one upward crossing of 30 % (movmean 5) and none of 500 % (raw)."""
    p1 = _upward_crossings(matlab_movmean(df, 5), 30)
    p2 = _upward_crossings(np.asarray(df, float), 500)
    return len(p2) == 0 and len(p1) > 1


def preprocess_cells(raw, mode):
    """raw: cells x frames (neuropil-corrected F). mode 'fig4' (Figure 4 filter) or 'fig2' (all cells).
    Returns z-scored dF/F (kept cells x frames) and the indices of kept cells in raw."""
    out, keep = [], []
    for i in range(raw.shape[0]):
        df, _ = df_anya(raw[i])
        if mode == "fig4":
            if not fig4_keep_cell(df):
                continue
        elif mode != "fig2":
            raise ValueError(mode)
        out.append(matlab_zscore(df))
        keep.append(i)
    return np.array(out), np.array(keep, int)


def block_ids(event_block_type):
    """Block index (0, 1, ...) of each event from the per-event BlockType sequence (in recording order)."""
    bt = np.asarray(event_block_type)
    return np.concatenate([[0], np.cumsum(bt[1:] != bt[:-1])]).astype(int)


def build_trials(cells, event_id, event_ts, block_type, include_go=False, binned=True, matlab_label_lag=False):
    """Figure4.m Panel D trial matrix.

    Trials are Hit events of cued blocks (type 2) then of self-paced blocks (type 1) (then Go events, type 3,
    if include_go), each cut from -5 s to +5 s around the event frame and kept only if the window lies in the
    recording (TS + 150 < n_frames and TS - 149 > 0). Returns a dict with
      X       trials x cells x bins (binned) or x frames, artefact trials set to NaN as in MATLAB
      ttype   1 self-paced, 2 cued, 3 go
      block   block index of the event; ts the event frame (1-based)
      artefact boolean (mean over cells > 10 z at any time point)
      keep_cells  cells without NaN in the trial average (MATLAB exclude_nan_cells), applied to X
    """
    event_id = np.asarray(event_id).astype(str)
    event_ts = np.asarray(event_ts).astype(np.int64).ravel()
    block_type = np.asarray(block_type).ravel()
    blk = block_ids(block_type)
    sel_g = (block_type == 2) & (event_id == "Hit")
    sel_s = (block_type == 1) & (event_id == "Hit")
    parts = [(np.where(sel_g)[0], 2), (np.where(sel_s)[0], 1)]
    if include_go:
        parts.append((np.where(event_id == "Go")[0], 3))
    nf = cells.shape[1]
    Xs, tt, bb, ts = [], [], [], []
    # Figure2.m line 197: TrialType1(CGlobal)=TStype(Clocal), with Clocal counting only the kept trials,
    # so every trial after a skipped one takes the label of an earlier event (list order: cued Hit, self Hit, Go)
    all_types = np.concatenate([np.full(len(idx), typ) for idx, typ in parts])
    n_kept = 0
    for idx, typ in parts:
        for e in idx:
            t = int(event_ts[e])
            if t + POST * FS < nf and t - PRE * FS + 1 > 0:
                seg = cells[:, t - PRE * FS:t + POST * FS]            # 1-based t-149 .. t+150
                if binned:
                    seg = seg.reshape(seg.shape[0], N_BINS, BIN).mean(axis=2)
                Xs.append(seg)
                tt.append(int(all_types[n_kept]) if matlab_label_lag else typ)
                n_kept += 1
                bb.append(blk[e])
                ts.append(t)
    X = np.stack(Xs).astype(float)                                   # trials x cells x time
    with np.errstate(invalid="ignore"):
        art = np.any(np.nanmean(X, axis=1) > 10, axis=1)
    X[art] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        tm = np.nanmean(X, axis=0)                                   # cells x time
    keep_cells = ~np.any(np.isnan(tm), axis=1)
    return dict(X=X[:, keep_cells, :], ttype=np.array(tt), block=np.array(bb), ts=np.array(ts),
                artefact=art, keep_cells=keep_cells)


def fig2_self_lever_matrix(trials_per_mouse):
    """Figure2.m: per cell, trial average (nanmean) of self-paced press-aligned frames 91:210 (-2 to +2 s);
    returns cells x 120 for all mice concatenated (unbinned trials required)."""
    rows = []
    for tr in trials_per_mouse:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            m = np.nanmean(tr["X"][tr["ttype"] == 1], axis=0)        # cells x 300
        rows.append(m[:, 90:210])
    return np.concatenate(rows, axis=0)


def fig2_clusters(self_lever_matrix, k=3):
    """Ward linkage on Euclidean distances, cut at k clusters (MATLAB linkage(pdist,'ward'), cluster maxclust)."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import pdist
    Z = linkage(pdist(self_lever_matrix, "euclidean"), "ward")
    return fcluster(Z, k, "maxclust")
