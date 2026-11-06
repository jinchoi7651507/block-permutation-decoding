#!/usr/bin/env python3
"""Synthetic test of the step 3 runner (no IBL data): a fake trials table, its pseudosession pool from the pinned
generator, Poisson counts with a slow drift, one region-session, all rows of run_ibl.region_rows with reduced draws.
Checks that every row returns a p in (0, 1] or NaN, the P2 sequential rule equals scikit-learn's
permutation_test_score decisions at full draws, and times one region-session.

  python test_synthetic.py [--draws 20] [--pool 40]
"""
import argparse
import time

import numpy as np
import pandas as pd

import ibl_core as C
import run_ibl as R


def fake_trials(n, seed):
    from brainbox.task.closed_loop import generate_pseudo_session
    base = pd.DataFrame({"contrastLeft": np.r_[np.full(n // 2, 0.25), np.full(n - n // 2, np.nan)],
                         "contrastRight": np.r_[np.full(n // 2, np.nan), np.full(n - n // 2, 0.25)],
                         "probabilityLeft": np.full(n, 0.5), "choice": np.ones(n)})
    base.loc[0, "contrastLeft"], base.loc[1, "contrastLeft"] = 0.0, 1.0
    np.random.seed(seed)
    return generate_pseudo_session(base, generate_choices=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=20)
    ap.add_argument("--pool", type=int, default=40)
    ap.add_argument("--p2-only", action="store_true")
    args = ap.parse_args()
    C.N_DRAWS = args.draws
    trials = fake_trials(500, 1)
    mask = trials["probabilityLeft"].to_numpy() != 0.5
    pool, stim = R.pseudo_pool(trials, mask, 999, n=args.pool)
    while len(pool) < 220:                                           # pad the pool by reuse for the test only
        pool += pool[: 220 - len(pool)]
        stim += stim[: 220 - len(stim)]
    rng = np.random.default_rng(5)
    n = int(mask.sum())
    drift = np.cumsum(rng.normal(0, 0.05, n))
    X = rng.poisson(np.exp(1.0 + drift[:, None] * rng.normal(0, 1, 12)[None, :])).astype(float)
    Xs = rng.poisson(3.0, (n, 12)).astype(float)
    y_real = R.side_labels(trials["probabilityLeft"].to_numpy())[mask]
    right = ~np.isnan(trials["contrastRight"].to_numpy())
    con = np.where(right, trials["contrastRight"].to_numpy(), trials["contrastLeft"].to_numpy())
    stim_real = np.where(con > 0, right.astype(float), np.nan)[mask]
    t = time.time()
    rows = [] if args.p2_only else R.region_rows(X, y_real, pool, stim_real, stim, Xs, 999, 0, pilot=False)
    dt = time.time() - t
    bad = [] if args.p2_only else [(r["label"], k, v) for r in rows for k, v in r.items()
           if k != "label" and v is not None and not (np.isnan(v) or 0 < v <= 1)]
    print("rows", len(rows), "keys real", sorted(k for k in rows[-2] if k != "label") if rows else "-")
    print("bad p values:", bad)
    print(f"one region-session, {args.draws} draws: {dt:.1f} s")
    # P2 sequential vs scikit-learn permutation_test_score at full draws (decision at 0.05)
    from sklearn.model_selection import permutation_test_score
    keep = ~np.isnan(y_real)
    y, Xl = y_real[keep].astype(int), X[keep]
    folds = C.smain_folds(len(y), 999)
    est = C.decoder(Xl.shape[1])
    C.H_STOP = 10 ** 9                                                # no early stop: full draws
    p_ours, _ = C.p2(est, Xl, y, folds, "main", np.random.RandomState(7))
    _, _, p_sk = permutation_test_score(est, Xl, y, cv=folds, n_permutations=args.draws,
                                        random_state=np.random.RandomState(7), scoring="balanced_accuracy")
    print("P2 ours", p_ours, "sklearn", p_sk, "equal", abs(p_ours - p_sk) < 1e-12)
    # null-regime case (labels unrelated to activity, p away from the floor), 60 draws
    yn = np.random.default_rng(11).permutation(y)
    C.N_DRAWS = 60
    p_o, _ = C.p2(est, Xl, yn, folds, "main", np.random.RandomState(8))
    _, _, p_s = permutation_test_score(est, Xl, yn, cv=folds, n_permutations=60, random_state=np.random.RandomState(8),
                                       scoring="balanced_accuracy")
    print("P2 null regime ours", p_o, "sklearn", p_s, "equal", abs(p_o - p_s) < 1e-12)


if __name__ == "__main__":
    main()
