#!/usr/bin/env python3
"""Step 5 (DESIGN.md §2-§3): from one PAMAP2 protocol file (subject10x.dat, 54 columns, 100 Hz) to a feature file.
Non-overlapping windows of 200 consecutive rows; a window is dropped if its timestamps contain a step larger than
0.015 s (a gap in the recording), if any of the 27 IMU channels (hand, chest, ankle: 3D acceleration +-16 g, 3D
gyroscope, 3D magnetometer) has fewer than 100 valid rows, or if heart rate has no valid value. Features per window:
mean and SD of each IMU channel over its valid rows, and mean heart rate (55). The retained windows are cut into 24
consecutive blocks of equal count (remainder at the end dropped); runs = 4 runs of 6 blocks. A subject is included if
at least 480 windows are retained and every feature varies. Writes <out>/<subject>.npz (X, block, run, block_run,
block_t0, block_t1) and <out>/<subject>.json (counts; included or not, with the reason).

  python prepare_pamap2.py --file <data>/Protocol/subject101.dat --subject subject101 --out <features dir>
"""
import argparse
import json
from pathlib import Path

import numpy as np

WIN, MIN_VALID, MAX_STEP, N_BLOCKS, BLOCKS_PER_RUN, MIN_WINDOWS = 200, 100, 0.015, 24, 6, 480


def imu_columns():
    """0-based column indices of the 27 IMU channels: IMU i (hand, chest, ankle) starts at column 3 + 17 i with
    temperature at +0, acc16 at +1..+3, acc6 at +4..+6, gyro at +7..+9, magnetometer at +10..+12, orientation +13..+16."""
    cols = []
    for i in range(3):
        base = 3 + 17 * i
        cols += [base + 1, base + 2, base + 3, base + 7, base + 8, base + 9, base + 10, base + 11, base + 12]
    return cols


def windows(data):
    assert data.shape[1] == 54, data.shape
    ts = data[:, 0]
    assert np.all(np.diff(ts) > 0), "timestamps not increasing"
    cols = imu_columns()
    n = data.shape[0] // WIN
    feats, t0, t1 = [], [], []
    dropped = {"gap": 0, "imu": 0, "hr": 0}
    for w in range(n):
        seg = data[w * WIN:(w + 1) * WIN]
        if np.diff(seg[:, 0]).max() > MAX_STEP:
            dropped["gap"] += 1
            continue
        imu, hr = seg[:, cols], seg[:, 2]
        if np.isfinite(imu).sum(axis=0).min() < MIN_VALID:
            dropped["imu"] += 1
            continue
        if not np.isfinite(hr).any():
            dropped["hr"] += 1
            continue
        feats.append(np.concatenate([np.nanmean(imu, axis=0), np.nanstd(imu, axis=0), [np.nanmean(hr)]]))
        t0.append(seg[0, 0])
        t1.append(seg[-1, 0])
    return np.array(feats), np.array(t0), np.array(t1), n, dropped


def build(data):
    X, t0, t1, n_win, dropped = windows(data)
    info = {"windows_total": int(n_win), "windows_kept": int(len(X)), "windows_dropped": dropped}
    if len(X) < MIN_WINDOWS:
        info.update({"included": False, "reason": f"{len(X)} windows retained, fewer than {MIN_WINDOWS}"})
        return None, info
    per = len(X) // N_BLOCKS
    X, t0, t1 = X[:per * N_BLOCKS], t0[:per * N_BLOCKS], t1[:per * N_BLOCKS]
    if np.any(X.std(axis=0) == 0):
        info.update({"included": False, "reason": "a feature is constant"})
        return None, info
    block = np.repeat(np.arange(N_BLOCKS), per)
    info.update({"included": True, "windows_per_block": int(per), "n_features": int(X.shape[1])})
    return {"X": X, "block": block, "run": block // BLOCKS_PER_RUN, "block_run": np.arange(N_BLOCKS) // BLOCKS_PER_RUN,
            "block_t0": np.array([t0[block == b][0] for b in range(N_BLOCKS)]),
            "block_t1": np.array([t1[block == b][-1] for b in range(N_BLOCKS)])}, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--subject", required=True, choices=[f"subject{i}" for i in range(101, 110)])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        feat, info = build(np.loadtxt(a.file))
    except Exception as e:                                  # any failure excludes the subject, with its reason
        feat, info = None, {"included": False, "reason": f"exception {type(e).__name__}: {e}"}
    info["subject"] = a.subject
    if feat is not None:
        np.savez_compressed(out / f"{a.subject}.npz", **feat)
    (out / f"{a.subject}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


if __name__ == "__main__":
    main()
