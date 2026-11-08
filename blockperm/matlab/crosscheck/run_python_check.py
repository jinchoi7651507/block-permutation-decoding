#!/usr/bin/env python3
"""Python side of the cross-check: exact block permutation null of a nearest-centroid decoder on the EEGBCI
features, for the real labels (imagery vs executed) and for the labels with no information. Writes
null_python_<labels>.csv (scores sorted) and p_python.csv (one row per label set: imagery, fake).

    python run_python_check.py DIR
"""
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import PredefinedSplit
from sklearn.neighbors import NearestCentroid

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from blockperm import block_permutation_test_score  # noqa: E402


def main(d):
    d = Path(d)
    X = np.loadtxt(d / "features.csv", delimiter=",")
    tab = np.loadtxt(d / "labels.csv", delimiter=",", skiprows=1, dtype=int)
    runs, cv = tab[:, 1], PredefinedSplit(tab[:, 2])
    rows = []
    for name, y in (("imagery", tab[:, 0]), ("fake", tab[:, 3])):
        score, null, p = block_permutation_test_score(NearestCentroid(), X, y, blocks=runs, cv=cv, exact=True,
                                                      groups=None)
        np.savetxt(d / ("null_python_%s.csv" % name), np.sort(null), fmt="%.17g")
        rows.append("%.17g,%d,%.17g" % (score, len(null), p))
        print("%s: score %.4f, %d arrangements, p %.4f" % (name, score, len(null), p))
    (d / "p_python.csv").write_text("score,n_null,p\n" + "\n".join(rows) + "\n")   # rows: imagery, fake


if __name__ == "__main__":
    main(sys.argv[1])
