#!/usr/bin/env python3
"""Step 2 pipeline gate against step 1 lr_topk on Allen shared24 (design ../gate/GATE-DESIGN.md).

Rebuilds step 1's shared24 counts, labels, split and null draws exactly (step 1 decompose.py functions,
same RNG streams and order of consumption), recomputes step 1's lr_topk as an integrity check, and
evaluates two scikit-learn pipelines on the same draws:
  A  StandardScaler -> SelectKBest(|d'| as step 1, k=20) -> LogisticRegression(C=1)
  B  StandardScaler -> SelectKBest(f_classif, k=20)      -> LogisticRegression(C=1)

  python gate_pipeline.py --dir <allen nwb folder> --out ../gate/gate_rows.jsonl [--worker i --of n]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
S1 = HERE.parents[1] / "step1-decomposition"
_spec = importlib.util.spec_from_file_location("dec", S1 / "code" / "decompose.py")
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)
tax, emn = dec.tax, dec.emn
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def abs_dprime(X, y):
    a, b = X[y == 0], X[y == 1]
    va, vb = a.var(axis=0, ddof=1), b.var(axis=0, ddof=1)
    pooled = np.sqrt(0.5 * (va + vb))
    d = np.where(pooled > 0, (a.mean(axis=0) - b.mean(axis=0)) / np.where(pooled > 0, pooled, 1), 0.0)
    return np.abs(d)


def make(kind, tight=False):
    sel = SelectKBest(abs_dprime if kind == "A" else f_classif, k=dec.LR_K)
    lr = LogisticRegression(C=1.0, tol=1e-10, max_iter=10000) if tight else LogisticRegression(C=1.0)
    return Pipeline([("scale", StandardScaler()), ("sel", sel), ("lr", lr)])


def pipe_fit(kind, X, labels, cal, test, tight=False):
    """Held-out % and predictions on all trials. k = min(20, n units) as step 1."""
    p = make(kind, tight)
    p.set_params(sel__k=min(dec.LR_K, X.shape[1]))
    if len(np.unique(labels[cal])) < 2:
        return float("nan"), None
    p.fit(X[cal], labels[cal])
    pred = p.predict(X)
    return dec.acc(pred, labels, test), pred


def gate_area(c24, blk24, sid, a):
    n = c24.shape[1]
    rng = tax.rng_for(sid, a, dec.STREAMS["shared24"])
    S = dec.Scheme("shared24", blk24, rng, n)
    labels, cal, test = S.labels, S.cal, S.test
    ro24 = tax.rng_for(sid, a, 33)
    o24, s24 = ro24.permutation(c24.shape[0]), bool(ro24.integers(2))
    R = dec.Readouts(c24, cal, test, o24, s24)
    s1_acc, s1_pred = R.fit("lr_topk", labels)
    perms = [rng.permutation(labels) for _ in range(dec.N_TRL)]
    blk, is_exact = S.block_null(dec.N_BLK_MC)
    idx = np.arange(len(blk)) if len(blk) <= dec.N_BLK_MC_LR else rng.choice(len(blk), dec.N_BLK_MC_LR, replace=False)
    X = c24.T.astype(float)
    out = {"session": sid, "area": a, "n_units": int(c24.shape[0]), "s1_acc_recomputed": s1_acc}
    for kind in ("A", "B"):
        sc, pred = pipe_fit(kind, X, labels, cal, test)
        o = {"acc": sc, "same_pred_as_s1": bool(np.array_equal(pred, s1_pred))}
        o["acc_tight"] = pipe_fit(kind, X, labels, cal, test, tight=True)[0]
        o["trl_rerun"], o["trl_rerun_nan"] = dec.mc_p([pipe_fit(kind, X, lp, cal, test)[0] for lp in perms], sc)
        o["blk_fixed"], _ = dec.mc_p([dec.acc(pred, lb, test) for lb in blk], sc)
        o["blk_rerun"], o["blk_rerun_nan"] = dec.mc_p([pipe_fit(kind, X, blk[i], cal, test)[0] for i in idx], sc)
        out[kind] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    args = ap.parse_args()
    rows = [json.loads(l) for l in (S1 / "runs" / "rows.jsonl").read_text().splitlines()]
    want = {}
    for r in rows:
        if "shared24" in r:
            want.setdefault(r["session"], {})[r["area"]] = r["shared24"]["lr_topk"]["acc"]
    out = Path(args.out)
    done = {(json.loads(l)["session"], json.loads(l)["area"]) for l in out.read_text().splitlines()} if out.exists() else set()
    for si, sid in enumerate(sorted(want)):
        if si % args.of != args.worker:
            continue
        t0 = time.time()
        path = Path(args.dir) / f"session_{sid}.nwb"
        ids, spikes, area, onset, ori = emn.load_session(path)
        good, _ = tax.unit_table(path)
        area = np.where(good, area, "excluded-quality")
        on24, blk24 = dec.spont_onsets(path, 8)
        for a in sorted(want[sid]):
            if (sid, a) in done:
                continue
            sel = np.where(area == a)[0]
            c24, _ = tax.area_counts(spikes, sel, on24)
            row = gate_area(c24, blk24, sid, a)
            row["s1_acc_rows"] = want[sid][a]
            row["integrity"] = abs(row["s1_acc_recomputed"] - want[sid][a]) < 1e-9
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"  {sid} {a}: integrity {row['integrity']} A {row['A']['acc']:.2f} s1 {want[sid][a]:.2f}", flush=True)
            if not row["integrity"]:
                raise SystemExit("integrity check failed: step 1 lr_topk not reproduced; stop")
        print(f"SESSION {sid}: {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
