#!/usr/bin/env python3
"""Shared engine of steps 4 and 5 (DESIGN.md §4-§8 of each step): fake labels assigned within runs, the splits,
and the rules P1-P5 of step 2 (../../step2-comparison/code/sim.py, unchanged). P5 permutes the per-block labels
within runs, the unit of randomization of the fake labels, so it is exact by construction.
Whole-block splits use a fixed block-to-fold map (block index modulo the number of folds, PredefinedSplit), so the
folds do not depend on GroupKFold's tie order (which differs between platforms; step 2, Supplementary Note 4).
"""
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import LeaveOneGroupOut, PredefinedSplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "step2-comparison" / "code"))
import sim  # noqa: E402

N_PERM = 200
VERSIONS = {"numpy": np.__version__, "scikit-learn": sklearn.__version__}


def within_run_assignments(block_run, n_assign, stream, s_index):
    """n_assign per-block 0/1 vectors with half of each run's blocks in class 1, drawn with
    default_rng([2026, stream, s_index, d]); redrawn while equal to an earlier vector or its class swap."""
    block_run = np.asarray(block_run)
    runs = np.unique(block_run)
    chosen, keys = [], set()
    for d in range(n_assign):
        rng = np.random.default_rng([2026, stream, s_index, d])
        for _ in range(100000):
            v = np.zeros(len(block_run), int)
            for r in runs:
                idx = np.where(block_run == r)[0]
                v[rng.choice(idx, len(idx) // 2, replace=False)] = 1
            if tuple(v) not in keys and tuple(1 - v) not in keys:
                break
        else:
            raise RuntimeError("no new assignment found")
        keys.add(tuple(v))
        chosen.append(v)
    return chosen


def within_run_draw(lab, block_run):
    """P5 draw: the observed per-block labels permuted within each run."""
    lab, block_run = np.asarray(lab), np.asarray(block_run)
    groups = [np.where(block_run == r)[0] for r in np.unique(block_run)]

    def draw(rng):
        out = lab.copy()
        for idx in groups:
            out[idx] = lab[rng.permutation(idx)]
        return out
    return draw


def block_fold_map(blk, n_folds):
    """Fold of each sample under the whole-block split: block index modulo n_folds."""
    return np.asarray(blk) % n_folds


def folds_for(split, X, y, blk, run, seed, n_block_folds):
    if split == "main":
        return sim.folds("main", X, y, blk, seed)                       # shuffled KFold(5), random_state = seed
    if split == "tool":
        return sim.Resplit(sim.splitter("tool", seed), blk)             # unshuffled StratifiedKFold(5), re-split per y
    if split == "run":
        return list(LeaveOneGroupOut().split(X, y, groups=run))
    if split == "block":
        return list(PredefinedSplit(block_fold_map(blk, n_block_folds)).split())
    raise ValueError(split)


def run_rules(est, X, y, blk, run, fl, block_run, rng, seed):
    """Every rule on one labelled dataset. blk: block id per sample (0..K-1, contiguous); run: run id per sample;
    block_run: run id of each block 0..K-1. Returns p values, the observed accuracy, P5's null accuracies and the
    number of convergence warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", ConvergenceWarning)
        out = {"acc": sim.cv_correct(est, X, y, fl)[1]}
        out["P1"] = sim.p1_binomial(est, X, y, fl)
        out["P2"] = sim.p2_sklearn(est, X, y, fl, N_PERM, seed)
        p3 = sim.p3_within_run(est, X, y, fl, run, N_PERM, rng)
        out["P3"], out["P3_error"] = (None, True) if p3 is None else (p3, False)
        out["P4"] = sim.p4_train_only(est, X, y, fl, N_PERM, rng)
        K = int(blk.max()) + 1
        assert sorted(np.unique(blk)) == list(range(K)), "block ids must be 0..K-1"
        lab = np.array([y[blk == b][0] for b in range(K)])
        _, null5, out["P5"] = sim.block_permutation_test_score(est, X, y, blk, fl, N_PERM, rng,
                                                               draw=within_run_draw(lab, block_run))
    out["P5_null_acc"] = [None if not np.isfinite(v) else round(float(v), 6) for v in null5]
    out["convergence_warnings"] = sum(issubclass(x.category, ConvergenceWarning) for x in w)
    out["n_perm"] = N_PERM
    out["versions"] = VERSIONS
    return out


def read_rows(path):
    """Rows of a JSON-lines file; a truncated last line (crash during a write) is dropped and reported."""
    rows = []
    if not Path(path).exists():
        return rows
    text = Path(path).read_text()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if i != len(lines) - 1:
                raise
            print(f"dropping a truncated last line of {path}", file=sys.stderr)
            Path(path).write_text("".join(l + "\n" for l in lines[:-1]))
            return rows
    if text and not text.endswith("\n"):                   # a complete last line without its newline
        with Path(path).open("a") as fh:
            fh.write("\n")
    return rows


def write_row(out, row, t0):
    row["seconds"] = round(time.time() - t0, 1)
    with Path(out).open("a") as fh:
        fh.write(json.dumps(row) + "\n")
        fh.flush()
