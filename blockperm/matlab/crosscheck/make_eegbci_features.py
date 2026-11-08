#!/usr/bin/env python3
"""Features from real EEG for the Python/MATLAB cross-check of the block permutation test.

PhysioNet EEG Motor Movement/Imagery data (EEGBCI), subject 1, runs 3-14 (MNE downloads them). Each run is one
block: runs 4, 6, 8, 10, 12 and 14 are motor imagery and runs 3, 5, 7, 9, 11 and 13 are executed movement, so the
label "imagery" is constant within each run. Features per 4-s epoch (cue onset 0 to 4 s): log variance of each
channel after an 8-30 Hz band-pass. Folds are fixed (five folds over shuffled epochs, seed 0), so training and
test epochs share runs. Writes features.csv (one row per epoch), labels.csv (label, run, fold, fake label) to the
output folder.

    python make_eegbci_features.py OUTDIR [MNE_DATA_DIR]
"""
import sys
from pathlib import Path

import mne
import numpy as np


def main(out, data_dir=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    runs = list(range(3, 15))
    files = mne.datasets.eegbci.load_data(1, runs, path=data_dir, update_path=False, verbose="error")
    X, run_of, imagery = [], [], []
    for run, f in zip(runs, files):
        raw = mne.io.read_raw_edf(f, preload=True, verbose="error")
        raw.filter(8.0, 30.0, verbose="error")
        events, _ = mne.events_from_annotations(raw, event_id=dict(T1=1, T2=2), verbose="error")
        epochs = mne.Epochs(raw, events, tmin=0.0, tmax=4.0, baseline=None, preload=True, verbose="error")
        X.append(np.log(epochs.get_data(copy=False).var(axis=2)))
        run_of += [run] * len(epochs)
        imagery += [int(run % 2 == 0)] * len(epochs)
    assert [r for r in runs if r % 2 == 0] == [4, 6, 8, 10, 12, 14]   # imagery runs of the EEGBCI protocol
    X = np.vstack(X)
    run_of = np.array(run_of)
    rng = np.random.default_rng(0)
    folds = np.empty(len(X), int)
    folds[rng.permutation(len(X))] = np.arange(len(X)) % 5 + 1
    fake_by_run = dict(zip(runs, rng.permutation([0] * 6 + [1] * 6)))   # labels with no information, by run
    fake = np.array([fake_by_run[r] for r in run_of])
    np.savetxt(out / "features.csv", X, delimiter=",", fmt="%.17g")
    np.savetxt(out / "labels.csv", np.column_stack([imagery, run_of, folds, fake]), delimiter=",", fmt="%d",
               header="imagery,run,fold,fake", comments="")
    print("epochs %d, features %d, runs %d" % (X.shape[0], X.shape[1], len(runs)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
