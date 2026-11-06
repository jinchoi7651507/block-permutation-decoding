#!/usr/bin/env python3
"""Step 2 addendum 3 §2b/§2c: PyMVPA 2.6.5 as shipped (Python 3.9 environment) on the replicate files of
add3_tools_data.py. Variants:
  main   : the tutorial's permutation test (pymvpa_tut.rst l. 256-330): LinearCSVMC(), NFoldPartitioner on chunks,
           AttributePermutator('targets', limit={'partitions': 1}, count=1) chained after the partitioner,
           MCNullDist(Repeater(count=n_perm), tail='left', enable_ca=['dist_samples']) on the mean error.
  zscore : as main after mvpa2 zscore(ds, chunks_attr='chunks') (per-run z-scoring, the mvpa2 default).
  chunks : the tutorial's whole-dataset form (l. 162) with AttributePermutator('targets', strategy='chunks',
           chunk_attr='blocks', count=n_perm) as the MCNullDist generator: one permutation of whole blocks per draw,
           shared by all folds (training and testing together; pymvpa_permutation.py l. 64-71, 238-258).
p_tool = the tool's null_prob = #{null error <= observed error} / n (Nonparametric cdf, `<=`, no +1; stats.py
l. 106-110); also k = #{null <= observed} and p_mc = (1 + k) / (n + 1) from dist_samples.
mvpa2.seed(1000 * rep + 7) before each replicate. CSV line: layout, rep, variant, p_tool, p_mc, k, observed error,
error flag, n_perm, seconds, error message. The data file is loaded outside the error capture. Resumable.

  python add3_pymvpa.py --data DIR --out pymvpa.w<k>.csv --variant main [--worker k --of n] [--n-perm 200]
  python add3_pymvpa.py --data DIR --gate GATE_DIR [--n-perm 200] [--gate-reps 50] [--exact-reps 10]
"""
import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
from scipy.io import loadmat

import mvpa2
from mvpa2.base.node import ChainNode
from mvpa2.clfs.svm import LinearCSVMC
from mvpa2.clfs.stats import MCNullDist
from mvpa2.datasets.base import dataset_wizard
from mvpa2.generators.base import Repeater
from mvpa2.generators.partition import NFoldPartitioner
from mvpa2.generators.permutation import AttributePermutator
from mvpa2.mappers.fx import mean_sample
from mvpa2.mappers.zscore import zscore
from mvpa2.measures.base import CrossValidation


def load(f):
    m = loadmat(str(f))
    ds = dataset_wizard(samples=m["X"].astype(float), targets=m["targets"].ravel().astype(int),
                        chunks=m["chunks"].ravel().astype(int))
    ds.sa["blocks"] = m["blocks"].ravel().astype(int)
    return ds


def permutator(variant):
    if variant == "chunks":
        return AttributePermutator("targets", strategy="chunks", chunk_attr="blocks", count=1)
    return AttributePermutator("targets", limit={"partitions": 1}, count=1)


def tool_p(ds, n_perm, variant, clf=None):
    clf = clf if clf is not None else LinearCSVMC()
    partitioner = NFoldPartitioner(attr="chunks")
    if variant == "chunks":
        # whole-dataset form of the tutorial (l. 162): one block permutation per draw, shared by all folds
        distr = MCNullDist(AttributePermutator("targets", strategy="chunks", chunk_attr="blocks", count=n_perm),
                           tail="left", enable_ca=["dist_samples"])
    else:
        null_cv = CrossValidation(clf, ChainNode([partitioner, permutator(variant)], space=partitioner.get_space()),
                                  postproc=mean_sample())
        distr = MCNullDist(Repeater(count=n_perm), tail="left", measure=null_cv, enable_ca=["dist_samples"])
    cv = CrossValidation(clf, partitioner, postproc=mean_sample(), null_dist=distr, enable_ca=["stats"])
    err = float(np.asarray(cv(ds)).ravel()[0])
    null = np.asarray(distr.ca.dist_samples).ravel()
    k = int(np.sum(null <= err + 1e-12))
    return float(np.asarray(cv.ca.null_prob).ravel()[0]), (1 + k) / (len(null) + 1), k, err, null


def name_parts(f):
    return tuple(map(int, re.match(r"L(\d)_r(\d+)\.mat", f.name).groups()))


def run(args):
    out = Path(args.out)
    done = set()
    if out.exists():
        done = {(int(a), int(b), c) for a, b, c in (l.split(",")[:3] for l in out.read_text().splitlines() if l)}
    files = sorted(Path(args.data).glob("L*_r*.mat"))
    for i, f in enumerate(files):
        if i % args.of != args.worker:
            continue
        j, rep = name_parts(f)
        if (j, rep, args.variant) in done:
            continue
        ds = load(f)
        if args.variant == "zscore":
            zscore(ds, chunks_attr="chunks")
        t = time.time()
        mvpa2.seed(1000 * rep + 7)
        flag, pt, pm, k, e, msg = 0, float("nan"), float("nan"), -1, float("nan"), ""
        try:
            pt, pm, k, e, _ = tool_p(ds, args.n_perm, args.variant)
        except Exception as ex:
            flag, msg = 1, re.sub(r"[,\n\r]", " ", str(ex))[:160]
        with out.open("a") as fh:
            fh.write("%d,%d,%s,%.10g,%.10g,%d,%.10g,%d,%d,%.1f,%s\n"
                     % (j, rep, args.variant, pt, pm, k, e, flag, args.n_perm, time.time() - t, msg))


def gate(args):
    """G2: per fold and draw, targets equal the observed ones on the testing partition and are a permutation of them
    on the training partition (L2 replicates 0..gate_reps-1, draws regenerated from the replicate's seed). The draws
    and each fold's test chunk are saved for add3_gate.py. G3: PyMVPA CrossValidation with the stamped pipeline in
    SKLLearnerAdapter equals a plain scikit-learn leave-one-run-out loop (same environment). G4 (exact rule check):
    on replicates 0..exact_reps-1, PyMVPA's full MCNullDist with SKLLearnerAdapter(pipeline) gives the null errors;
    add3_gate.py recomputes them from the regenerated draws (equality expected)."""
    from sklearn.base import clone
    from sklearn.feature_selection import SelectKBest, f_classif
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from mvpa2.clfs.skl.base import SKLLearnerAdapter
    pipe = Pipeline([("scale", StandardScaler()), ("sel", SelectKBest(f_classif, k=20)),
                     ("lr", LogisticRegression(C=1.0, max_iter=1000))])
    gdir = Path(args.gate)
    gdir.mkdir(parents=True, exist_ok=True)
    res = {"G2_checked": 0, "G2_fail": 0, "G3_checked": 0, "G3_maxdiff": 0.0, "G4_exact_reps": args.exact_reps}
    for rep in range(args.gate_reps):
        ds = load(Path(args.data) / ("L2_r%03d.mat" % rep))
        y0 = np.array(ds.sa.targets)
        mvpa2.seed(1000 * rep + 7)
        partitioner = NFoldPartitioner(attr="chunks")
        chain = ChainNode([partitioner, permutator("main")], space=partitioner.get_space())
        perms, test_chunks = [], []
        for _ in range(args.n_perm):
            draw, tc = [], []
            for d in chain.generate(ds):
                part = np.array(d.sa.partitions)
                tr, te = part == 1, part == 2
                tg = np.array(d.sa.targets)
                ok = np.array_equal(tg[te], y0[te]) and np.array_equal(np.sort(tg[tr]), np.sort(y0[tr]))
                res["G2_checked"] += 1
                res["G2_fail"] += int(not ok)
                draw.append(tg)
                tc.append(int(np.unique(np.array(d.sa.chunks)[te])[0]))
            perms.append(draw)
            test_chunks.append(tc)
        np.save(gdir / ("L2_r%03d_pymvpa_perm.npy" % rep), np.array(perms, dtype=np.int8))
        np.save(gdir / ("L2_r%03d_pymvpa_testchunk.npy" % rep), np.array(test_chunks, dtype=np.int8))
        cv = CrossValidation(SKLLearnerAdapter(clone(pipe)), NFoldPartitioner(attr="chunks"), postproc=mean_sample())
        acc_tool = 1.0 - float(np.asarray(cv(ds)).ravel()[0])
        X, ch = np.array(ds.samples), np.array(ds.sa.chunks)
        accs = [float(np.mean(clone(pipe).fit(X[ch != r], y0[ch != r]).predict(X[ch == r]) == y0[ch == r]))
                for r in np.unique(ch)]
        res["G3_checked"] += 1
        res["G3_maxdiff"] = max(res["G3_maxdiff"], abs(acc_tool - float(np.mean(accs))))
        if rep < args.exact_reps:
            mvpa2.seed(1000 * rep + 7)
            _, _, _, err, null = tool_p(ds, args.n_perm, "main", clf=SKLLearnerAdapter(clone(pipe)))
            mine = []                                         # same draws, plain scikit-learn, same environment
            for draw, tc in zip(perms, test_chunks):
                errs = []
                for tg, c in zip(draw, tc):
                    tr, te = ch != c, ch == c
                    errs.append(float(np.mean(clone(pipe).fit(X[tr], tg[tr]).predict(X[te]) != y0[te])))
                mine.append(float(np.mean(errs)))
            res["G4_exact_maxdiff"] = max(res.get("G4_exact_maxdiff", 0.0), float(np.max(np.abs(null - np.array(mine)))))
            res["G4_exact_obsdiff"] = max(res.get("G4_exact_obsdiff", 0.0), abs(err - (1.0 - float(np.mean(accs)))))
    (gdir / "pymvpa_gate.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out")
    ap.add_argument("--gate")
    ap.add_argument("--variant", default="main", choices=("main", "zscore", "chunks"))
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--gate-reps", type=int, default=50, help="synthetic tests only; the study gate uses 50")
    ap.add_argument("--exact-reps", type=int, default=10)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    args = ap.parse_args()
    gate(args) if args.gate else run(args)


if __name__ == "__main__":
    main()
