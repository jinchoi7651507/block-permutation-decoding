"""Loader for the deposited MATLAB structures. TO BE CHECKED against the real files in stage 2.

The structure is inferred from the authors' code and readme (NOTES.md), not from the data:
  Switching_2p_Struc_Main(s), s = 1..6 (one element per mouse, one imaging session each), fields
    cells_raw_neurophil_corrected  cells x frames
    EventID                        per event; compared with 'Hit' / 'Go' in MATLAB (categorical or string)
    EventTS                        per event, 1-based frame index
    BlockType                      per event, 1 self-paced, 2 cued
    Joystick, D1D2class, AnimalID, SwitchSessionCounter, ...
  Switching_Behav_Struc(k), one element per block, fields AnimalID, SwitchSessionType (1 self, 2 cued),
    SwitchSessionCounter (1..3), SessionDay, ReactionTimeFromTrialStart, PressRate, RewardRate, HitToPressRate
  clusters_fig2.mat: clusterMeta (or top-level) clusterIDs, AnimalCellID

scipy.io.loadmat reads v5/v7 files but not MATLAB categorical/string objects or v7.3 (HDF5) files; for those
the mat-io package (import name matio) is used.
"""
from __future__ import annotations

import numpy as np

FIELDS_2P = ("cells_raw_neurophil_corrected", "EventID", "EventTS", "BlockType")


def _load_any(path, variable_names=None):
    try:
        import scipy.io as sio
        d = sio.loadmat(path, squeeze_me=True, struct_as_record=False, variable_names=variable_names)
        return d, "scipy"
    except NotImplementedError:          # v7.3
        pass
    import matio
    return matio.load_from_mat(path, variable_names=variable_names), "matio"


def _get(el, name):
    if isinstance(el, dict):
        return el[name]
    if hasattr(el, name):
        return getattr(el, name)
    if hasattr(el, "dtype") and el.dtype.names and name in el.dtype.names:
        return el[name]
    raise KeyError(name)


def _as_str_array(v):
    v = np.asarray(v, dtype=object).ravel()
    out = []
    for x in v:
        if isinstance(x, bytes):
            x = x.decode()
        out.append(str(x).strip())
    arr = np.array(out)
    if any(s.startswith("<") and "Opaque" in s for s in arr[:5]):
        raise TypeError("EventID came back as an opaque MATLAB object; use mat-io (matio)")
    return arr


def _elements(struct):
    s = struct
    if hasattr(s, "ravel") and getattr(s, "dtype", None) is not None and s.dtype == object:
        return list(s.ravel())
    if isinstance(s, (list, tuple)):
        return list(s)
    if hasattr(s, "dtype") and s.dtype.names:            # numpy structured array (matio / record form)
        return [s[i] for i in np.ndindex(s.shape)]
    return [s]


def load_2p(path):
    """List of per-mouse dicts with the four fields used, as numpy arrays."""
    d, how = _load_any(path, ["Switching_2p_Struc_Main"])
    els = _elements(d["Switching_2p_Struc_Main"])
    mice = []
    for i, el in enumerate(els):
        m = dict(index=i, reader=how)
        m["cells"] = np.asarray(_get(el, "cells_raw_neurophil_corrected"), float)
        m["event_id"] = _as_str_array(_get(el, "EventID"))
        m["event_ts"] = np.asarray(_get(el, "EventTS"), float).ravel().astype(np.int64)
        m["block_type"] = np.asarray(_get(el, "BlockType"), float).ravel().astype(int)
        for opt in ("AnimalID", "SwitchSessionCounter", "D1D2class"):
            try:
                m[opt] = np.asarray(_get(el, opt))
            except KeyError:
                pass
        if not (len(m["event_id"]) == len(m["event_ts"]) == len(m["block_type"])):
            raise ValueError("mouse %d: EventID, EventTS and BlockType differ in length" % i)
        mice.append(m)
    return mice


def load_behav(path):
    d, _ = _load_any(path, ["Switching_Behav_Struc"])
    rows = []
    for el in _elements(d["Switching_Behav_Struc"]):
        r = {}
        for f in ("AnimalID", "SwitchSessionType", "SwitchSessionCounter", "SessionDay",
                  "ReactionTimeFromTrialStart", "PressRate", "RewardRate", "HitToPressRate"):
            v = np.asarray(_get(el, f), float).ravel()
            r[f] = float(v[0]) if v.size == 1 else (np.nan if v.size == 0 else v)
        rows.append(r)
    return rows


def load_clusters(path):
    d, _ = _load_any(path)
    src = d.get("clusterMeta", d)
    ids = np.asarray(_get(src, "clusterIDs")).ravel().astype(int)
    try:
        animal = np.asarray(_get(src, "AnimalCellID")).ravel()
    except KeyError:
        animal = None
    return ids, animal
