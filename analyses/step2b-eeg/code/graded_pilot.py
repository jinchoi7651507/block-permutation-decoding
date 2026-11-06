#!/usr/bin/env python3
"""Step 2b graded positive control, pilot (DESIGN.md v2 §4; addendum §5). Run on the 5 pilot subjects only
(eligibility/PILOT-SUBJECTS.txt, not in the main table) before the main run.

For each weakening rule in run_2b.GRADED_ORDER (R1, R2, R4, R3, R5, then the mixing ladder Q30-Q48) and pilot subject:
20 seeded weakenings (1 for R1, which has no random part)
(default_rng([2026, 6, subject, draw])) of the EC vs EO labels, S-main split, P5 only (200 draws). Power = share of
p < 0.05 over the tests, also per subject. Chosen rule: the first rule in that order with pooled power in [0.20, 0.90]
and per-subject power strictly between 0.05 and 0.95 in at least 3 of the 5 subjects; if none, "not achieved" (the
graded control is then reported as not achieved and pos_graded / balanced_graded are not run). The main-run power is
targeted by the pilot, not guaranteed. Writes graded_pilot.json with every p and the chosen rule.

  python graded_pilot.py --features <dir> --subjects ../eligibility/PILOT-SUBJECTS.txt --out ../runs/graded_pilot.json
"""
import argparse
import json
from pathlib import Path

import numpy as np

import run_2b as r
import sim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    subs = [s.strip() for s in Path(args.subjects).read_text().splitlines() if s.strip()]
    res = {"rules": {}, "subjects": subs}
    for rule in r.GRADED_ORDER:
        ps = []
        for si, s in enumerate(subs):
            data, info = r.load(args.features, s, "cleaned_s5", 1000 + si)
            if data is None:
                continue
            X, blk, bcond, chs = data
            _, null, _ = r.arm_assignments("pos_full", bcond, si)
            deterministic = r.GRADED_RULES[rule][1] is None and r.GRADED_RULES[rule][2] == 0
            for d in range(1 if deterministic else 20):                          # R1 has no randomness: one test
                rng = np.random.default_rng([2026, 6, si, d])
                Xw, bw = r.weaken(X, blk, chs, rule, rng)
                y = bcond.astype(int)[bw]
                fl = r.folds_for("main", Xw, y, bw, int(rng.integers(2**31 - 1)))
                _, _, p = sim.block_permutation_test_score(sim.pipeline(), Xw, y, bw, fl, r.N_PERM, rng, draw=r.draw_from(null))
                ps.append((s, p))
        power = float(np.mean([p < 0.05 for _, p in ps])) if ps else None
        per = {s: float(np.mean([p < 0.05 for ss, p in ps if ss == s])) for s in {ss for ss, _ in ps}}
        res["rules"][rule] = {"p": ps, "power": power, "per_subject_power": per}
    chosen = None
    for rule in r.GRADED_ORDER:
        v = res["rules"][rule]
        if v["power"] is None:
            continue
        mid = sum(1 for x in v["per_subject_power"].values() if 0.05 < x < 0.95)
        if 0.20 <= v["power"] <= 0.90 and mid >= 3:
            chosen = rule
            break
    res["chosen"] = chosen if chosen else "not achieved"
    Path(args.out).write_text(json.dumps(res, indent=1))
    print({k: v["power"] for k, v in res["rules"].items()}, "chosen", res["chosen"])


if __name__ == "__main__":
    main()
