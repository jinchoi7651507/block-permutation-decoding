#!/usr/bin/env python3
"""Step 2b summary (DESIGN.md v2 §6; addendum DESIGN-v2-ADDENDUM.md §6). Written before any EEG row exists.

Unit of inference = subject. For every arm x split x readout x variant x rule: per subject the share of its
assignments with p < 0.05 (NaN p excluded; P3 errors excluded, and separately counted as non-rejections), the
mean over subjects, and a subject-level bootstrap interval (B = 20,000, seed 20261024). "Inflated" = lower bound of
that interval above 10%.
Primary contrast E: rate(P2) - rate(P5), S-main, balanced arm, cleaned_s5, main readout; paired at (subject,
assignment), averaged per subject, subject bootstrap.
Fixed-order arms (one assignment per subject): rejection rate over subjects with a Wilson interval, and the pooled
p-value distribution (Kolmogorov-Smirnov distance from uniform, and the share below 0.05, 0.10, 0.20).
Group level (Q3), balanced arm, S-main, main readout, cleaned_s5: for each of the 50 assignment indices, across
subjects (a) one-sample t-test of accuracy against 0.5, (b) a Stelzer-style group test: group null = mean over
subjects of one P5 null accuracy drawn per subject, 2,000 draws (seed 20261025); share of the 50 indices with
p < 0.05 for (a) and (b), with a subject-bootstrap interval (200 resamples, each recomputing both shares with
500 group-null draws).
Logged: within each subject, Spearman between |correlation of an assignment's labels with block index| and its P2
rejection, averaged over subjects. Dropped subjects listed per variant (the analysis set is fixed on cleaned_s5).
Enumerated arms (ec_only, eo_only, long120): P5's rate is fixed by construction (noted, not a finding). P3 cells in which
every row errors print "undefined (error by construction)". The t-test is one-sided (greater than 0.5); the KS distance
in fixed-order arms is descriptive only (discrete p values). Size-adjusted power of pos_graded (S-main) uses the
balanced_graded arm as its null (see size_adjusted).

  python summarize_2b.py --rows ../runs --out ../results
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

RULES = ("P1", "P2", "P3", "P4", "P5")
BOOT_B, BOOT_SEED = 20000, 20261024


def ok(p):
    return p is not None and np.isfinite(p)


def boot(v, seed=BOOT_SEED, B=BOOT_B, flag=True):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), (B, len(v)))
    lo, hi = np.percentile(v[idx].mean(1), [2.5, 97.5])
    out = {"mean": float(v.mean()), "ci95": [float(lo), float(hi)], "n_subjects": int(len(v))}
    if flag:
        out["inflated"] = bool(lo > 0.10)
    return out


ENUMERATED = ("ec_only", "eo_only", "long120")


def size_adjusted(null_rows, alt_rows, rule, seed=20261027, B=2000):
    """Size-adjusted power of pos_graded (addendum §6): threshold q = pooled 5% quantile ('lower') of the rule's p over
    all balanced_graded rows (S-main), P3 errors / NaN as p = 1; randomised at the tie (g) so the expected size is 5%.
    Subject bootstrap resamples subjects jointly over both arms."""
    def pmap(rows):
        d = defaultdict(list)
        for r in rows:
            d[r["subject"]].append(r[rule] if ok(r.get(rule)) else 1.0)
        return {s: np.array(v) for s, v in d.items()}
    n0, n1 = pmap(null_rows), pmap(alt_rows)
    subs = sorted(set(n0) & set(n1))
    if not subs:
        return None

    def est_(ss):
        p0 = np.concatenate([n0[s] for s in ss])
        q = float(np.quantile(p0, 0.05, method="lower"))
        lt0, eq0 = np.mean(p0 < q - 1e-12), np.mean(np.abs(p0 - q) <= 1e-12)
        g = 0.0 if eq0 == 0 else min(1.0, max(0.0, (0.05 - lt0) / eq0))
        per = [np.mean(n1[s] < q - 1e-12) + g * np.mean(np.abs(n1[s] - q) <= 1e-12) for s in ss]
        return float(np.mean(per)), q, float(lt0 + eq0), g
    m, q, size_plain, g = est_(subs)
    rng = np.random.default_rng(seed)
    bs = [est_(list(rng.choice(subs, len(subs), replace=True)))[0] for _ in range(B)]
    raw = float(np.mean([np.mean(n1[s] < 0.05) for s in subs]))
    return {"raw_power": raw, "size_adjusted_power": m, "ci95": np.percentile(bs, [2.5, 97.5]).tolist(), "threshold_q": q,
            "size_plain_le_q": size_plain, "tie_prob_g": g, "n_subjects": len(subs)}


def wilson(k, n):
    if n == 0:
        return None
    z = 1.959963985
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [float(c - h), float(c + h)]


def group_tests(acc, nulls, rng, n_null):
    """acc: subjects; nulls: subjects x draws matrix of P5 null accuracies (NaN allowed). Returns (t p, group p)."""
    t = stats.ttest_1samp(acc, 0.5, alternative="greater").pvalue
    obs = acc.mean()
    S, D = nulls.shape
    pick = nulls[np.arange(S)[None, :], rng.integers(0, D, (n_null, S))]
    g = np.nanmean(pick, axis=1)
    return float(t), float((1 + np.sum(g >= obs)) / (n_null + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default=str(Path(__file__).resolve().parent.parent / "runs"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "results"))
    args = ap.parse_args()
    rows = [json.loads(l) for f in sorted(Path(args.rows).glob("rows*.jsonl")) for l in f.read_text().splitlines()]
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    dropped = {}
    for r in rows:
        if r.get("dropped"):
            dropped.setdefault(r["variant"], set()).add(r["subject"])
    dropped = {k: sorted(v) for k, v in dropped.items()}
    rows = [r for r in rows if not r.get("dropped")]
    groups = defaultdict(list)
    for r in rows:
        groups[(r["arm"], r["split"], r["readout"], r["variant"])].append(r)
    res = {"dropped_subjects": dropped, "cells": {}}
    for key, rs in sorted(groups.items()):
        by = defaultdict(list)
        for r in rs:
            by[r["subject"]].append(r)
        cell = {"n_subjects": len(by), "n_rows": len(rs)}
        fixed = key[0].startswith("fixed_")
        for rule in RULES:
            if fixed:
                ps = [r[rule] for r in rs if ok(r.get(rule))]
                k = sum(p < 0.05 for p in ps)
                cell[rule] = {"rate": k / len(ps) if ps else None, "wilson95": wilson(k, len(ps)), "n": len(ps),
                              "ks_uniform": float(stats.kstest(ps, "uniform").statistic) if ps else None,
                              "share_below": {str(a): float(np.mean([p < a for p in ps])) if ps else None for a in (0.05, 0.1, 0.2)}}
                continue
            per = [np.mean([r[rule] < 0.05 for r in v if ok(r.get(rule))]) for v in by.values()
                   if any(ok(r.get(rule)) for r in v)]
            cell[rule] = boot(per)
        per3 = [np.mean([ok(r.get("P3")) and r["P3"] < 0.05 for r in v]) for v in by.values()]
        cell["P3_error_share_of_rows"] = float(np.mean([bool(r.get("P3_error")) for r in rs]))
        if cell["P3_error_share_of_rows"] == 1.0:
            cell["P3"] = "undefined (error by construction)"
            cell["P3_errors_as_nonreject"] = "undefined (error by construction)"
        else:
            cell["P3_errors_as_nonreject"] = boot(per3) if not fixed else float(np.mean(per3))
        if key[0] in ENUMERATED:
            cell["P5_note"] = ("all 35 distinct assignments tested: P5's per-subject rate is fixed by construction "
                               "(about 0.036, at most about 3/35); not evidence of validity")
        if not fixed and not key[0].startswith("pos"):
            # within-subject: |label-block correlation| of each assignment vs its P2 rejection (Spearman per subject, mean)
            rs_ = []
            for v in by.values():
                a = np.array([abs(r["label_block_corr"]) for r in v if ok(r.get("P2"))])
                b = np.array([float(r["P2"] < 0.05) for r in v if ok(r.get("P2"))])
                if len(a) > 2 and a.std() > 0 and b.std() > 0:
                    rs_.append(stats.spearmanr(a, b).statistic)
            cell["P2_vs_abs_label_block_corr_within_subject_spearman_mean"] = float(np.mean(rs_)) if rs_ else None
        res["cells"]["/".join(key)] = cell
    prim = groups.get(("balanced", "main", "main", "cleaned_s5"), [])
    by = defaultdict(list)
    for r in prim:
        by[r["subject"]].append(r)
    d = [np.mean([float(r["P2"] < 0.05) - float(r["P5"] < 0.05) for r in v if ok(r.get("P2")) and ok(r.get("P5"))])
         for v in by.values()]
    res["contrast_E_P2_minus_P5"] = boot(d, flag=False)
    g0 = groups.get(("balanced_graded", "main", "main", "cleaned_s5"), [])
    g1 = groups.get(("pos_graded", "main", "main", "cleaned_s5"), [])
    if g0 and g1:
        res["size_adjusted_power_pos_graded"] = {rule: size_adjusted(g0, g1, rule) for rule in RULES}
    # group level
    subs = sorted(by)
    if len(subs) >= 3:
        A = {s: {r["assignment"]: r for r in by[s]} for s in subs}
        idx = sorted(set.intersection(*[set(A[s]) for s in subs]))
        rng = np.random.default_rng(20261025)

        def shares(sub_list, n_null):
            t_hits = g_hits = 0
            for a in idx:
                acc = np.array([A[s][a]["acc"] for s in sub_list])
                nulls = np.array([[np.nan if x is None else x for x in A[s][a]["P5_null_acc"]] for s in sub_list], float)
                tp, gp = group_tests(acc, nulls, rng, n_null)
                t_hits += tp < 0.05
                g_hits += gp < 0.05
            return t_hits / len(idx), g_hits / len(idx)
        t_share, g_share = shares(subs, 2000)
        bs = []
        brng = np.random.default_rng(20261026)
        for _ in range(200):
            bs.append(shares(list(brng.choice(subs, len(subs), replace=True)), 500))
        bs = np.array(bs)
        res["group_level"] = {"n_assignments": len(idx), "t_test_share": t_share, "group_null_share": g_share,
                              "t_test_ci95": np.percentile(bs[:, 0], [2.5, 97.5]).tolist(),
                              "group_null_ci95": np.percentile(bs[:, 1], [2.5, 97.5]).tolist()}
    (out / "summary_2b.json").write_text(json.dumps(res, indent=1))
    lines = ["# Step 2b summary (summarize_2b.py)", "", f"Dropped subjects: {dropped or 'none'}", "",
             "| arm/split/readout/variant | P1 | P2 | P3 | P4 | P5 |", "|---|---|---|---|---|---|"]

    def f(e):
        if not e or e.get("rate", e.get("mean")) is None:
            return "–"
        m = e.get("mean", e.get("rate"))
        ci = e.get("ci95") or e.get("wilson95") or [None, None]
        return f"{100 * m:.1f} ({100 * ci[0]:.1f}–{100 * ci[1]:.1f})" if ci[0] is not None else f"{100 * m:.1f}"
    def fr(c, r):
        v = c.get(r)
        return v if isinstance(v, str) else f(v)
    for k, c in res["cells"].items():
        lines.append(f"| {k} | " + " | ".join(fr(c, r) for r in RULES) + " |")
    e = res.get("contrast_E_P2_minus_P5")
    lines += ["", f"Contrast E (P2 − P5, S-main, balanced, cleaned): {f(e)}"]
    if "group_level" in res:
        g = res["group_level"]
        lines.append(f"Group level over {g['n_assignments']} assignments: t-test rejects {100 * g['t_test_share']:.0f}%, "
                     f"group null rejects {100 * g['group_null_share']:.0f}%")
    (out / "summary_2b.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
