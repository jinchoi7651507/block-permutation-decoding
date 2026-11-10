"""Synthetic session generator shared by test_synthetic.py and the determinism stage of run_cell.py."""
from __future__ import annotations

import cell_env  # noqa: F401
import numpy as np

import cellport as cp

ROIS = ["A", "B", "C"]


def make_sessions(seed, n_sess=6, n_blocks=9, block_len=(60, 100), n_neur=5, signal=0.0, block_sd=0.5, drift=0.02,
                  walk=0.02, rois=ROIS, n_levels_noise=1.0):
    """Sessions with blocks whose colour bin is drawn at random (counts balanced as far as possible), per-neuron
    block offsets (SD block_sd), a slow random walk over trials plus a linear drift, and an optional template signal
    (signal x neuron tuning to the true bin). No information about the bin otherwise."""
    rng = np.random.default_rng(seed)
    sessions = []
    for s in range(n_sess):
        lens = rng.integers(block_len[0], block_len[1] + 1, n_blocks)
        bins_b = np.resize(np.array([1, 2, 3]), n_blocks)
        rng.shuffle(bins_b)
        block, tib, bins = [], [], []
        for b, (L, c) in enumerate(zip(lens, bins_b)):
            block += [b + 1] * L
            tib += list(range(1, L + 1))
            bins += [c] * L
        block, tib, bins = np.array(block), np.array(tib), np.array(bins)
        n = len(block)
        prog = cp.progression_in_block(block, tib)
        sess = cp.Session(s, block, prog, bins.astype(int), bins.astype(int))
        for r in rois:
            off = rng.normal(0, block_sd, (n_neur, n_blocks))
            wk = np.cumsum(rng.normal(0, walk, (n_neur, n)), axis=1)
            lin = drift * rng.normal(0, 1, (n_neur, 1)) * np.linspace(-1, 1, n)[None]
            tune = rng.normal(0, 1, (n_neur, 3))
            f = rng.normal(0, n_levels_noise, (n_neur, n)) + off[:, block - 1] + wk + lin + signal * tune[:, bins - 1]
            sess.feat[r] = 5.0 + f
        sess.feat_by_window = {"900": dict(sess.feat), "600": {r: v.copy() for r, v in sess.feat.items()}}
        sessions.append(sess)
    roi_sessions = {r: list(range(n_sess)) for r in rois}
    return sessions, roi_sessions


