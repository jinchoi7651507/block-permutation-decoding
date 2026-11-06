#!/usr/bin/env python3
"""Block-to-fold map of scikit-learn GroupKFold for the step 2 S-block layouts (B = 12 and 24 blocks of 20 trials).

GroupKFold sorts the group sizes with np.argsort (default kind), whose tie order for equal sizes may depend on the
platform. This script prints the map, its hash, numpy's CPU dispatch and the map a stable sort would give, so that
two platforms can be compared with the same versions (numpy 2.5.4, scikit-learn 1.7.2). It reads no study data.
"""
import hashlib
import json
import platform
import sys

import numpy as np
import sklearn
from sklearn.model_selection import GroupKFold

out = {"platform": platform.platform(), "machine": platform.machine(), "python": sys.version.split()[0],
       "numpy": np.__version__, "sklearn": sklearn.__version__, "maps": {}}
for B in (4, 12, 24):
    blocks = np.repeat(np.arange(B), 20)
    X = np.zeros((len(blocks), 1))
    fold_of_block = [-1] * B
    for k, (_, te) in enumerate(GroupKFold(min(5, B)).split(X, groups=blocks)):
        for b in np.unique(blocks[te]):
            fold_of_block[int(b)] = k
    out["maps"][str(B)] = fold_of_block
    out["argsort_ties_%d" % B] = np.argsort(np.full(B, 20)).tolist()
    out["argsort_stable_%d" % B] = np.argsort(np.full(B, 20), kind="stable").tolist()
try:
    feats = np._core._multiarray_umath.__cpu_features__
    out["numpy_cpu_features_enabled"] = sorted(k for k, v in feats.items() if v)
except AttributeError:
    out["numpy_cpu_features_enabled"] = None
s = json.dumps(out["maps"], sort_keys=True)
out["maps_sha256"] = hashlib.sha256(s.encode()).hexdigest()
print(json.dumps(out, indent=1))
