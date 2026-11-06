#!/usr/bin/env python3
"""Step 2b addendum 2: pilot of the noise ladder on the second-round pilot subjects (eligibility/PILOT2-SUBJECTS.txt).

As graded_pilot.py (addendum 1 §5): for each rule in graded2.NOISE_ORDER and pilot subject, 20 seeded weakenings
(default_rng([2026, 11, subject, draw])) of the EC vs EO labels, S-main split, P5 only (200 draws, null = all 8 + 8
assignments of the 16 blocks). Power = share of p < 0.05, pooled and per subject. Chosen rule: the first rule in the
ladder with pooled power in [0.20, 0.90] and per-subject power strictly between 0.05 and 0.95 in at least 3 of the 5
subjects; if none, "not achieved" (final for every graded-control variant of step 2b). The full ladder is always run in
the stated order (no subset option). The script stops if fewer than 5 subjects can be evaluated (addendum 2 §3:
replace a dropped subject first). Stored with every test: p, observed accuracy, median and 95th percentile of the null
accuracies, kept epochs per block. --workers runs the (rule, subject) tasks in parallel processes; every task has its
own seeds, so the result does not depend on the number of workers.

  python graded_pilot2.py --features <dir> --subjects ../eligibility/PILOT2-SUBJECTS.txt --out ../runs/graded_pilot2.json [--workers 56]
"""
import argparse
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import graded2 as g
import run_2b as r
import sim

def task(job):
    features, rule, si, s = job                     # everything the task needs is in the job (works with spawn and fork)
    data, info = r.load(features, s, "cleaned_s5", 2000 + si)
    if data is None:
        return rule, s, None
    X, blk, bcond, chs = data
    _, null, _ = r.arm_assignments("pos_full", bcond, si)
    rows = []
    for d in range(20):
        rng = np.random.default_rng([2026, 11, si, d])
        Xw, bw = g.weaken2(X, blk, chs, rule, rng)
        y = bcond.astype(int)[bw]
        fl = r.folds_for("main", Xw, y, bw, int(rng.integers(2**31 - 1)))
        obs, nul, p = sim.block_permutation_test_score(sim.pipeline(), Xw, y, bw, fl, r.N_PERM, rng, draw=r.draw_from(null))
        rows.append({"subject": s, "draw": d, "p": p, "obs": float(obs), "null_median": float(np.nanmedian(nul)),
                     "null_q95": float(np.nanpercentile(nul, 95)), "kept_per_block": info.get("kept_per_block")})
    return rule, s, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    subs = [s.strip() for s in Path(args.subjects).read_text().splitlines() if s.strip()]
    sha = Path(args.subjects).with_suffix(".sha256")              # hash of the committed list (re-check R1)
    if sha.exists():
        import hashlib
        want = sha.read_text().split()[0]
        if hashlib.sha256(Path(args.subjects).read_bytes()).hexdigest() != want:
            raise SystemExit(f"{args.subjects} does not match {sha}; stop")
    jobs = [(args.features, rule, si, s) for rule in g.NOISE_ORDER for si, s in enumerate(subs)]
    if args.workers > 1:
        with Pool(args.workers) as pool:
            out = pool.map(task, jobs, chunksize=1)
    else:
        out = [task(j) for j in jobs]
    dropped = sorted({s for _, s, rows in out if rows is None})
    evaluated = [s for s in subs if s not in dropped]
    if len(evaluated) != 5:                         # exactly 5 (re-check R2)
        raise SystemExit(f"{len(evaluated)} pilot subjects evaluable, 5 required (dropped {dropped}); replace them first (addendum 2 §3)")
    res = {"rules": {}, "subjects": subs, "evaluated_subjects": evaluated, "ladder": list(g.NOISE_ORDER)}
    for rule in g.NOISE_ORDER:
        rows = [x for rr, _, rws in out if rr == rule and rws for x in rws]
        power = float(np.mean([x["p"] < 0.05 for x in rows]))
        per = {s: float(np.mean([x["p"] < 0.05 for x in rows if x["subject"] == s])) for s in evaluated}
        res["rules"][rule] = {"rows": rows, "power": power, "per_subject_power": per}
    chosen = None
    for rule in g.NOISE_ORDER:
        v = res["rules"][rule]
        mid = sum(1 for x in v["per_subject_power"].values() if 0.05 < x < 0.95)
        if 0.20 <= v["power"] <= 0.90 and mid >= 3:
            chosen = rule
            break
    res["chosen"] = chosen if chosen else "not achieved"
    Path(args.out).write_text(json.dumps(res, indent=1))
    print({k: round(v["power"], 3) for k, v in res["rules"].items()}, "chosen", res["chosen"])


if __name__ == "__main__":
    main()
