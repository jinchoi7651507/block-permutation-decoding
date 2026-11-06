#!/usr/bin/env python3
"""Summary of steps 4 and 5 (DESIGN.md §8 of each step).
- Reads ../runs/rows.step<N>.<subject>.jsonl (test rows are rejected) and the feature JSONs (inclusion).
- Checks: one row per key; every included subject complete (step 4: 30 x 2 x 4 fake + 2 control rows;
  step 5: 30 x 3 fake + 60 control rows); stops otherwise.
- Unit = subject. Per subject, the share of its assignments with p < 0.05 (strict); undefined p values and P3
  errors are left out of that subject's denominator and counted. Mean over subjects; subject percentile bootstrap
  95% interval (B = 20,000; a fresh numpy.random.default_rng(20261102) for every quantity). "Inflated" = lower
  bound above 10%.
- Primary contrast (fixed per step): E = 1[p_P2 < 0.05] - 1[p_P5 < 0.05] per (subject, assignment) on fake labels,
  main split, primary preprocessing (step 4 "detrended", step 5 "windows2s"); pairs with an undefined p are left
  out and counted; mean per subject, then over subjects; "positive" = bootstrap lower bound above 0. Also reported:
  per-subject E, the number of subjects with E > 0 (exact one-sided binomial test over all subjects with a defined E;
  subjects with E = 0 are kept and count as not positive, which is conservative), and for each rule the number of
  subjects whose count of rejections is at least 5 of 30 (above the 95% binomial bound under 5%). With fewer than
  5 included subjects no decision is made (descriptive only).

  python summarize.py --step 4 --rows ../runs --features <features dir> --out ../results
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

RULES = ("P1", "P2", "P3", "P4", "P5")
B, SEED, MIN_SUBJECTS = 20000, 20261102, 5
PRIMARY_PREP = {4: "detrended", 5: "windows2s"}
EXPECTED = {4: {"fake": 30 * 2 * 4, "control": 2}, 5: {"fake": 30 * 3, "control": 60}}
SUBJECTS = {4: [f"subj{i}" for i in range(1, 7)], 5: [f"subject{i}" for i in range(101, 110)]}


def expected_keys(st, s):
    if st == 4:
        k = {(s, "fake", p, d, sp) for p in ("detrended", "raw") for d in range(30) for sp in ("main", "tool", "run", "block")}
        return k | {(s, "pos_face_house", "detrended", 0, sp) for sp in ("main", "run")}
    k = {(s, "fake", d, sp) for d in range(30) for sp in ("main", "tool", "block")}
    return k | {(s, f"pos_delta{x}", d, "main") for x in (0.5, 1.0) for d in range(30)}
KEY = {4: ("subject", "arm", "prep", "assignment", "split"), 5: ("subject", "arm", "assignment", "split")}


def boot(per_subject):
    v = np.array(per_subject, float)
    if len(v) == 0:
        return float("nan"), [float("nan"), float("nan")]
    rng = np.random.default_rng(SEED)
    m = v[rng.integers(0, len(v), (B, len(v)))].mean(axis=1)
    return float(v.mean()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def finite(p):
    return p is not None and not (isinstance(p, float) and np.isnan(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int, required=True, choices=(4, 5))
    ap.add_argument("--rows", required=True)
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    st = a.step
    incl = {}
    for f in sorted(Path(a.features).glob("*.json")):
        j = json.loads(f.read_text())
        incl[j["subject"]] = (bool(j.get("included")), j.get("reason"))
    assert sorted(incl) == sorted(SUBJECTS[st]), f"feature JSONs present for {sorted(incl)}, expected {SUBJECTS[st]}"
    rows = []
    for f in sorted(Path(a.rows).glob(f"rows.step{st}.*.jsonl")):
        if f.name.endswith(".test.jsonl"):
            continue
        rows += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    assert not any(r.get("test") for r in rows), "test rows in the input"
    assert all(r["step"] == st for r in rows)
    keys = [tuple(r[k] for k in KEY[st]) for r in rows]
    assert len(keys) == len(set(keys)), "duplicate rows"
    subjects = sorted({r["subject"] for r in rows})
    for s in subjects:
        assert incl.get(s, (False,))[0], f"rows for a subject not included: {s}"
        nf = sum(r["subject"] == s and r["arm"] == "fake" for r in rows)
        nc = sum(r["subject"] == s and r["arm"] != "fake" for r in rows)
        assert (nf, nc) == (EXPECTED[st]["fake"], EXPECTED[st]["control"]), f"{s}: {nf} fake, {nc} control rows"
        assert {k for k in keys if k[0] == s} == expected_keys(st, s), f"{s}: key set differs from the design"
    assert all(r.get("n_perm") == 200 for r in rows), "rows with a number of draws other than 200"
    assert len({json.dumps(r.get("versions"), sort_keys=True) for r in rows}) <= 1, "rows from different package versions"
    missing = [s for s, (ok, _) in incl.items() if ok and s not in subjects]
    assert not missing, f"included subjects without rows: {missing}"
    decide = None

    cells = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    undefined = defaultdict(int)
    pairs, pairs_left_out = defaultdict(list), 0
    for r in rows:
        c = (r["arm"], r["prep"], r["split"])
        for k in RULES:
            if not finite(r.get(k)):
                undefined[(c, k)] += 1
                continue
            cells[c][k][r["subject"]].append(float(r[k] < 0.05))
        if r["arm"] == "fake" and r["split"] == "main" and r["prep"] == PRIMARY_PREP[st]:
            if finite(r.get("P2")) and finite(r.get("P5")):
                pairs[r["subject"]].append(float(r["P2"] < 0.05) - float(r["P5"] < 0.05))
            else:
                pairs_left_out += 1

    out = {"step": st, "n_rows": len(rows), "subjects_included": subjects,
           "subjects_excluded": {s: reason for s, (ok, reason) in incl.items() if not ok}}
    per_e = {s: float(np.mean(v)) for s, v in pairs.items()}
    decide = len(per_e) >= MIN_SUBJECTS                     # subjects with at least one defined pair
    out["decision_possible"] = decide
    m, ci = boot(list(per_e.values()))
    n_pos = sum(v > 0 for v in per_e.values())
    sign_p = float(stats.binomtest(n_pos, len(per_e), 0.5, alternative="greater").pvalue) if per_e else float("nan")
    out["primary"] = {"contrast": f"E = 1[P2] - 1[P5], fake, main, {PRIMARY_PREP[st]}", "mean": m, "ci95": ci,
                      "positive": (bool(ci[0] > 0) if decide else None), "per_subject": per_e,
                      "subjects_with_E_above_0": n_pos, "sign_test_p": sign_p, "pairs_left_out": pairs_left_out}
    lines = [f"# Step {st} summary", "", f"Rows: {len(rows)}. Included subjects: {', '.join(subjects)}. Excluded: "
             f"{out['subjects_excluded'] or 'none'}." + ("" if decide else " Fewer than 5 subjects: descriptive only, no decision."),
             "", f"## Primary contrast (E = P2 − P5 rejections, fake labels, main split, {PRIMARY_PREP[st]})",
             f"{100*m:.1f} points (95% {100*ci[0]:.1f} to {100*ci[1]:.1f}); "
             f"{'positive' if decide and ci[0] > 0 else ('not positive' if decide else 'no decision')}; "
             f"subjects with E > 0: {n_pos} of {len(per_e)} (sign test p = {sign_p:.3g}); pairs left out: {pairs_left_out}",
             "", "Rates: mean over subjects of the per-subject share of tests with p < 0.05 (subject bootstrap 95% interval); "
             "'inflated' = lower bound above 10%; 'subjects >= 5/30' = subjects with at least 5 rejections among 30 tests.", ""]
    out["cells"] = {}
    for c in sorted(cells):
        lines += [f"## {c[0]} / {c[1]} / split {c[2]}", "| rule | rate | 95% interval | inflated | subjects >= 5/30 | subjects | tests | undefined |",
                  "|---|---|---|---|---|---|---|---|"]
        for k in RULES:
            subj = cells[c][k]
            per = {s: float(np.mean(v)) for s, v in subj.items() if len(v)}
            mm, cc = boot(list(per.values()))
            infl = (bool(cc[0] > 0.10) if decide else None) if c[0] == "fake" else None
            n_hi = sum(sum(v) >= 5 for v in subj.values()) if c[0] == "fake" else None
            out["cells"][f"{c[0]}/{c[1]}/{c[2]}/{k}"] = {"mean": mm, "ci95": cc, "inflated": infl, "subjects_ge5": n_hi,
                                                         "per_subject": per, "tests": int(sum(len(v) for v in subj.values())),
                                                         "undefined": undefined.get((c, k), 0)}
            lines.append(f"| {k} | {100*mm:.1f}% | {100*cc[0]:.1f}–{100*cc[1]:.1f} | {'' if infl is None else ('yes' if infl else 'no')} | "
                         f"{'' if n_hi is None else n_hi} | {len(per)} | {sum(len(v) for v in subj.values())} | {undefined.get((c, k), 0)} |")
        lines.append("")
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "summary.json").write_text(json.dumps(out, indent=1))
    (Path(a.out) / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
