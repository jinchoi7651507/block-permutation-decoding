#!/usr/bin/env python3
"""Step 2b runner (DESIGN.md v2 §4-§6; addendum DESIGN-v2-ADDENDUM.md). Uses the step 2 rules and pipeline
(../../step2-comparison/code/sim.py, unchanged).

Per subject (features from preprocess.py) and arm, every label assignment of that arm is tested under three splits
(S-main shuffled KFold 5; S-tool unshuffled StratifiedKFold 5 re-split per permuted label vector; S-block
GroupKFold(4) by block, deterministic) with the rules P1-P5 (200 permutation draws; P3 runs = runs of 4 consecutive
blocks of the arm, DESIGN §5: 4 runs with 16 blocks, 2 runs with 8). One JSON line per (subject, arm, assignment, split, readout, variant) with every p, the observed
accuracy and the P5 null accuracies.

Before any arm: subjects with fewer than 20 epochs in any block are dropped (reported); every block is then
subsampled (seeded) to the smallest per-block epoch count of that subject, so that both classes always have the
same number of epochs and accuracy equals balanced accuracy (§6, S9).

Arms (block = one 60-s condition segment; 8 EC + 8 EO blocks):
  balanced    class 1 = 4 EC + 4 EO blocks; 50 assignments per subject from the 4,900, without replacement and
              without the A/B swap of an assignment already drawn; draw d uses default_rng([2026, 2, s, d]).
              P5 null set: the 4,900.
  ec_only, eo_only  epochs of one state only; its 8 blocks split 4 + 4; all 35 assignments distinct up to the swap.
              P5 null set: the 70.
  fixed_half, fixed_aabb, fixed_abba  blocks 1-8 vs 9-16; block pairs AABB AABB; block pairs ABBA ABBA (each class
              4 EC + 4 EO by construction). P5 null set: the 4,900.
  long120     pairs of consecutive blocks as 8 blocks of 120 s; all 35 assignments distinct up to the swap.
              P5 null set: the 70.
  pos_full    EC vs EO labels (pipeline check, at ceiling). P5 null set: all 8 + 8 assignments of the 16 blocks.
  pos_graded  EC vs EO with the weakening rule fixed on the pilot subjects (--graded-rule); 50 seeded weakenings
              (one if the rule has no epoch subsampling).
  balanced_graded  the balanced arm's 50 fake assignments on data weakened by the same rule (seeds [2026, 7, s, d]);
              calibrates size-adjusted power of pos_graded (S-main).
Readouts: main = sim.pipeline() (k = 20); sensitivity kall = sim.pipeline(k = "all"), lda = scaler + LDA (no
selection), nogamma = main without the 30-45 Hz features, for the balanced arm under S-main. Variants: cleaned_s5 (primary); cleaned_s2, minimal_s5 for the
balanced arm under S-main.

  python run_2b.py --features <dir> --subjects ../eligibility/SUBJECTS.txt --arms balanced --out ../runs/rows.w0.jsonl
"""
import argparse
import itertools
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "step2-comparison" / "code"))
import sim  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
N_PERM = 200
MIN_EPOCHS = 20
# Weakening rules for the graded positive control (fixed before the pilot; chosen by graded_pilot.py):
# (channels, epochs per block): R1 frontal 16 channels, all epochs; R2 all channels, 4 epochs; R3 all, 2 epochs;
# R4 frontal, 4 epochs; R5 frontal, 2 epochs.
GRADED_RULES = {"R1": ("frontal", None, 0.0), "R2": ("all", 4, 0.0), "R3": ("all", 2, 0.0), "R4": ("frontal", 4, 0.0),
                "R5": ("frontal", 2, 0.0),
                # mixing ladder (EEG review M4): a fraction q of each block's epochs exchanged with epochs of the paired
                # opposite-state block (blocks 2j and 2j+1), all channels, all epochs; labels unchanged
                "Q30": ("all", None, 0.30), "Q35": ("all", None, 0.35), "Q40": ("all", None, 0.40), "Q45": ("all", None, 0.45),
                "Q48": ("all", None, 0.48)}                                  # last step (EEG re-review COULD)
GRADED_ORDER = ("R1", "R2", "R4", "R3", "R5", "Q30", "Q35", "Q40", "Q45", "Q48")
FRONTAL = ("Fp1", "Fp2", "AF7", "AF3", "AFz", "AF4", "AF8", "F7", "F5", "F3", "F1", "Fz", "F2", "F4", "F6", "F8")


def readout(name):
    if name == "main":
        return sim.pipeline()
    if name == "kall":
        return sim.pipeline(k="all")
    if name == "nogamma":                                   # main pipeline without the 30-45 Hz band (EEG review S6)
        from sklearn.compose import ColumnTransformer
        return Pipeline([("drop_gamma", ColumnTransformer([("keep", "passthrough", list(range(244)))])),
                         *sim.pipeline().steps])
    if name == "lda":
        return Pipeline([("scale", StandardScaler()), ("lda", LinearDiscriminantAnalysis())])
    raise ValueError(name)


def load(features, subject, variant, si):
    """The analysis set is fixed on cleaned_s5 (a subject dropped there is dropped in every variant and readout);
    other variants use their own smallest per-block count (reported)."""
    z = np.load(Path(features) / f"{subject}.npz")
    prim = np.bincount(z["cleaned_s5_block"], minlength=16)
    X, blk, cond = z[f"{variant}_X"].astype(float), z[f"{variant}_block"], z[f"{variant}_cond"]
    counts = np.bincount(blk, minlength=16)
    if len(prim) != 16 or prim.min() < MIN_EPOCHS or len(counts) != 16 or counts.min() < 1:
        return None, {"dropped": True, "epochs_per_block": counts.tolist(), "epochs_per_block_cleaned_s5": prim.tolist()}
    m = int(counts.min())
    rng = np.random.default_rng([2026, 1, si])
    keep = np.sort(np.concatenate([rng.choice(np.where(blk == b)[0], m, replace=False) for b in range(16)]))
    bcond = np.array([cond[blk == b][0] for b in range(16)])
    return (X[keep], blk[keep], bcond, list(z["channels"])), {"dropped": False, "epochs_per_block": counts.tolist(), "kept_per_block": m}


def two_class_sets(ec, eo):
    """All assignments with half of the EC blocks and half of the EO blocks in class 1 (per-block vectors)."""
    out = []
    for a in itertools.combinations(ec, len(ec) // 2):
        for b in itertools.combinations(eo, len(eo) // 2):
            v = np.zeros(16, int)
            v[list(a) + list(b)] = 1
            out.append(v)
    return out


ARMS = ("balanced", "ec_only", "eo_only", "fixed_half", "fixed_aabb", "fixed_abba", "long120", "pos_full", "pos_graded",
        "balanced_graded")


def splits_of(blocks):
    """All 4 + 4 splits of a list of 8 blocks (70) and one per A/B swap pair (35), as 0/1 vectors over len(blocks)."""
    n = len(blocks)
    allv, distinct, seen = [], [], set()
    for a in itertools.combinations(range(n), n // 2):
        v = np.zeros(n, int)
        v[list(a)] = 1
        allv.append(v)
        if frozenset(range(n)) - frozenset(a) not in seen:
            seen.add(frozenset(a))
            distinct.append(v)
    return allv, distinct


def arm_assignments(arm, bcond, s_index):
    """Returns (assignments, P5 null vectors, block map). Vectors are indexed by the arm's own blocks 0..K-1;
    block map turns the 16 original block numbers into the arm's blocks (-1 = epochs not used)."""
    ec, eo = list(np.where(bcond == 1)[0]), list(np.where(bcond == 0)[0])
    ident = np.arange(16)
    if arm in ("balanced", "balanced_graded"):
        allv = two_class_sets(ec, eo)
        chosen, keys = [], set()
        for d in range(50):
            rng = np.random.default_rng([2026, 2, s_index, d])
            while True:
                v = allv[rng.integers(len(allv))]
                if tuple(v) not in keys and tuple(1 - v) not in keys:
                    break
            keys.add(tuple(v))
            chosen.append(v)
        return chosen, allv, ident
    if arm in ("ec_only", "eo_only"):
        bl = ec if arm == "ec_only" else eo
        bmap = np.full(16, -1)
        bmap[bl] = np.arange(8)
        allv, distinct = splits_of(bl)
        return distinct, allv, bmap
    if arm.startswith("fixed_"):
        pair = {"fixed_half": [1, 1, 1, 1, 0, 0, 0, 0], "fixed_aabb": [1, 1, 0, 0, 1, 1, 0, 0],
                "fixed_abba": [1, 0, 0, 1, 1, 0, 0, 1]}[arm]
        return [np.repeat(np.array(pair), 2)], two_class_sets(ec, eo), ident
    if arm == "long120":
        allv, distinct = splits_of(list(range(8)))
        return distinct, allv, ident // 2
    if arm in ("pos_full", "pos_graded"):
        null = []
        for a in itertools.combinations(range(16), 8):
            v = np.zeros(16, int)
            v[list(a)] = 1
            null.append(v)
        n = 1 if arm == "pos_full" else 50
        return [bcond.astype(int)] * n, null, ident
    raise ValueError(arm)


def draw_from(vectors):
    def draw(rng):
        return vectors[rng.integers(len(vectors))]
    return draw


def weaken(X, blk, chs, rule, rng):
    """Graded positive control: keep the rule's channels (all 5 bands of each) and, if set, m random epochs per block."""
    which, m, q = GRADED_RULES[rule]
    if which == "frontal":
        idx = [i for i, c in enumerate(chs) if c in FRONTAL]
        assert len(idx) == len(FRONTAL), "frontal channels missing"
        n_ch = len(chs)
        cols = np.concatenate([np.array(idx) + b * n_ch for b in range(5)])
        X = X[:, cols]
    if q > 0:                                             # exchange (not copy) epochs between paired blocks 2j, 2j+1
        X = X.copy()
        src = X.copy()
        for b in np.unique(blk):
            if b % 2:
                continue
            own, other = np.where(blk == b)[0], np.where(blk == b + 1)[0]
            n_ = min(len(own), len(other))
            k = min(int(round(q * n_)), (n_ - 1) // 2)       # never half or more of a block (final check: Q48 at 20 epochs)
            a, c = rng.choice(own, k, replace=False), rng.choice(other, k, replace=False)
            X[a], X[c] = src[c], src[a]
    if m is not None:
        keep = np.sort(np.concatenate([rng.choice(np.where(blk == b)[0], m, replace=False) for b in np.unique(blk)]))
        X, blk = X[keep], blk[keep]
    return X, blk


def folds_for(split, X, y, blk, seed):
    if split == "main":
        return sim.folds("main", X, y, blk, seed)
    if split == "tool":
        return sim.Resplit(sim.splitter("tool", seed), blk)
    if split == "block":
        return list(GroupKFold(4).split(X, y, groups=blk))
    raise ValueError(split)


def run_rules(est, X, y, blk, fl, null_vectors, rng, seed, runs):
    out = {"acc": sim.cv_correct(est, X, y, fl)[1]}
    out["P1"] = sim.p1_binomial(est, X, y, fl)
    out["P2"] = sim.p2_sklearn(est, X, y, fl, N_PERM, seed)
    p3 = sim.p3_within_run(est, X, y, fl, runs, N_PERM, rng)
    out["P3"], out["P3_error"] = (None, True) if p3 is None else (p3, False)
    out["P4"] = sim.p4_train_only(est, X, y, fl, N_PERM, rng)
    _, null5, out["P5"] = sim.block_permutation_test_score(est, X, y, blk, fl, N_PERM, rng, draw=draw_from(null_vectors))
    out["P5_null_acc"] = [None if not np.isfinite(v) else round(float(v), 6) for v in null5]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--arms", default="balanced,ec_only,eo_only,fixed_half,fixed_aabb,fixed_abba,long120,pos_full")
    ap.add_argument("--splits", default="main,tool,block")
    ap.add_argument("--sensitivity", action="store_true", help="balanced arm, S-main: kall, lda, nogamma, cleaned_s2, minimal_s5")
    ap.add_argument("--graded-rule", default=None, help="a rule of GRADED_ORDER, fixed by graded_pilot.py before the main run")
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    args = ap.parse_args()
    subs = [s.strip() for s in Path(args.subjects).read_text().splitlines() if s.strip()]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for l in out.read_text().splitlines():
            r = json.loads(l)
            done.add((r["subject"], r["arm"], r["assignment"], r["split"], r["readout"], r["variant"]))
    jobs = []
    for si, s in enumerate(subs):
        if args.sensitivity:
            for ro, var in (("kall", "cleaned_s5"), ("lda", "cleaned_s5"), ("nogamma", "cleaned_s5"), ("main", "cleaned_s2"),
                            ("main", "minimal_s5")):
                jobs.append((si, s, "balanced", "main", ro, var))
        else:
            for arm in args.arms.split(","):
                for sp in args.splits.split(","):
                    jobs.append((si, s, arm, sp, "main", "cleaned_s5"))
    for j, (si, s, arm, sp, ro, var) in enumerate(jobs):
        if j % args.of != args.worker:
            continue
        data, info = load(args.features, s, var, si)
        if data is None:
            with out.open("a") as fh:
                fh.write(json.dumps({"subject": s, "arm": arm, "assignment": -1, "split": sp, "readout": ro,
                                     "variant": var, **info}) + "\n")
            continue
        X, blk, bcond, chs = data
        assigns, null_vectors, bmap = arm_assignments(arm, bcond, si)
        graded = arm in ("pos_graded", "balanced_graded")
        if graded:
            if args.graded_rule is None:
                raise SystemExit(f"{arm} needs --graded-rule")
            if arm == "pos_graded" and GRADED_RULES[args.graded_rule][1] is None and GRADED_RULES[args.graded_rule][2] == 0:
                assigns = assigns[:1]                       # deterministic weakening (R1): one test per subject
        ab = bmap[blk]
        m = ab >= 0
        X, ab = X[m], ab[m]
        K = int(ab.max()) + 1
        for a_i, v in enumerate(assigns):
            if (s, arm, a_i, sp, ro, var) in done:
                continue
            t = time.time()
            Xa, aba = X, ab
            if graded:
                stream = 5 if arm == "pos_graded" else 7
                Xa, aba = weaken(X, ab, chs, args.graded_rule, np.random.default_rng([2026, stream, si, a_i]))
            y = v[aba]
            seed = int(np.random.default_rng([2026, 3, si, a_i, ARMS.index(arm)]).integers(2**31 - 1))
            rng = np.random.default_rng([2026, 4, si, a_i, ARMS.index(arm), ["main", "tool", "block"].index(sp)])
            fl = folds_for(sp, Xa, y, aba, seed)
            row = {"subject": s, "arm": arm, "assignment": a_i, "split": sp, "readout": ro, "variant": var,
                   "labels": v.tolist(), "n_epochs": int(len(y)), "graded_rule": args.graded_rule if graded else None,
                   "seed": seed, "subject_index": si, "arm_index": ARMS.index(arm), "split_index": ["main", "tool", "block"].index(sp),
                   "kept_per_block": info.get("kept_per_block"),
                   "label_block_corr": float(np.corrcoef(v, np.arange(K))[0, 1])}
            row.update(run_rules(readout(ro), Xa, y, aba, fl, null_vectors, rng, seed, aba // 4))   # runs of 4 consecutive blocks (DESIGN §5)
            row["seconds"] = round(time.time() - t, 1)
            with out.open("a") as fh:
                fh.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
