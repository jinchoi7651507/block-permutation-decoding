"""Loader for the Zenodo 10.5281/zenodo.10529801 files. STRUCTURE INFERRED from the authors' MATLAB code
(prepare_pseudopop_*_restricted_FEF.m); NOT YET CHECKED ON THE REAL FILES ("to verify on the real files").

Expected: Data/FR_around_event/FR_<event>_300_window_from_<a>_to_<b>/ID_<n>.mat, each with `Conditions` (struct with
block_nb, trial_in_block, rule [radians], belief [100 x trials], stim, belief_precision) and the ROI variables LIP, FEF,
PFC (neurons x trials). `read_mat` reads both MATLAB formats: older files (v5/v7, scipy) and v7.3 (HDF5, h5py; arrays
come back transposed and are transposed here). The loader stops and lists what it found if a field is missing, so that
a dated addendum can map names before any accuracy is computed.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import cell_env  # noqa: F401
import numpy as np

from cellport import (Session, WINDOWS, assemble_columns, color_bin, mean_windows, peak_belief_angle,
                      progression_in_block)

SESSION_IDS = [3, 8, 12, 14, 18, 20, 22, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44]
EXCLUDE = {"LIP": {30, 34}, "FEF": {14}}
ROI_VAR = {"LIP": "LIP", "FEF": "FEF", "LPFC": "PFC"}
REWARD_STARTS = list(range(0, 301, 50))       # 7 windows
TARGET_STARTS = list(range(-600, 351, 50))    # 20 windows


def window_dir(root, i):
    if i < 7:
        return Path(root) / ("FR_reward_end_300_window_from_%d_to_%d" % (REWARD_STARTS[i], REWARD_STARTS[i] + 300))
    s = TARGET_STARTS[i - 7]
    return Path(root) / ("FR_target_300_window_from_%d_to_%d" % (s, s + 300))


def _h5_value(node):
    import h5py
    if isinstance(node, h5py.Dataset):
        a = np.array(node)
        if a.dtype == object or a.dtype.kind == "O":
            raise SystemExit("HDF5 dataset %s holds object references (a struct array or cell); add a mapping in a dated addendum" % node.name)
        return np.squeeze(a.T) if a.ndim > 1 else a
    ns = SimpleNamespace()
    ns._fieldnames = list(node.keys())
    for k in node.keys():
        setattr(ns, k, _h5_value(node[k]))
    return ns


def read_mat(path):
    """Dict name -> value for a .mat file of either format. Structs are namespaces with attributes (scipy
    squeeze_me/struct_as_record=False style); v7.3 matrices are transposed back to MATLAB orientation."""
    from scipy.io import loadmat
    import h5py
    try:
        return loadmat(str(path), squeeze_me=True, struct_as_record=False)
    except (NotImplementedError, ValueError):
        if not h5py.is_hdf5(str(path)):
            raise
        out = {}
        with h5py.File(str(path), "r") as f:
            for k in f.keys():
                if k.startswith("#"):
                    continue
                out[k] = _h5_value(f[k])
        return out


def mat_format(path):
    """'v7.3 (HDF5)' or 'v5/v7' for a .mat file."""
    import h5py
    return "v7.3 (HDF5)" if h5py.is_hdf5(str(path)) else "v5/v7"


def _fields(cond):
    return list(getattr(cond, "_fieldnames", []) or [k for k in vars(cond) if not k.startswith("_")])


def load_session(root, sid, log=None):
    """Returns Session with feat (900 ms, active) and feat_by_window ('900', '600') for LIP, FEF, LPFC (kept neurons).
    `root` is the folder holding the window folders. Each window file is read once."""
    first = read_mat(window_dir(root, 0) / ("ID_%d.mat" % sid))
    if "Conditions" not in first:
        raise SystemExit("Conditions missing in ID_%d.mat of the first window; variables found: %s" % (sid, [k for k in first if not k.startswith("_")]))
    cond = first["Conditions"]
    need = ["block_nb", "trial_in_block", "rule", "belief"]
    miss = [f for f in need if not hasattr(cond, f)]
    if miss:
        raise SystemExit("Conditions lacks %s; fields found: %s" % (miss, _fields(cond)))
    block_all = np.atleast_1d(np.asarray(cond.block_nb))
    tib = np.atleast_1d(np.asarray(cond.trial_in_block))
    prog_all = progression_in_block(block_all, tib)
    true_bin = color_bin(np.atleast_1d(np.asarray(cond.rule, float)))[1:]
    belief_bin = color_bin(peak_belief_angle(np.asarray(cond.belief, float)))[1:]
    sess = Session(sid, block_all[1:], prog_all[1:], true_bin, belief_bin)
    rois = [r for r in ROI_VAR if sid not in EXCLUDE.get(r, set())]
    wins = {r: [] for r in rois}
    for w in range(27):
        m = first if w == 0 else read_mat(window_dir(root, w) / ("ID_%d.mat" % sid))
        for r in rois:
            var = ROI_VAR[r]
            if var not in m:
                raise SystemExit("variable %s missing in %s; found %s" % (var, window_dir(root, w), [k for k in m if not k.startswith("_")]))
            a = np.asarray(m[var], float)
            wins[r].append(a if a.ndim == 2 else a.reshape(1, -1))
    sess.feat_by_window = {k: {} for k in WINDOWS}
    for r in rois:
        raw, kept = assemble_columns(wins[r])
        for k, idx in WINDOWS.items():
            sess.feat_by_window[k][r] = mean_windows(raw, kept, idx)
    sess.feat = dict(sess.feat_by_window["900"])
    return sess


def load_all(root):
    sessions = [load_session(root, s) for s in SESSION_IDS]
    roi_sessions = {r: [i for i, s in enumerate(sessions) if r in s.feat] for r in ROI_VAR}
    return sessions, roi_sessions
