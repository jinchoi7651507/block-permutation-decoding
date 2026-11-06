#!/usr/bin/env python3
"""Step 3 (IBL) summary, DESIGN.md v1 §7 and code addendum 1 §4 (items i-xiii), as specified in code addendum 2.
Written before any IBL row exists.

  python summarize_ibl.py --rows ../runs --order ../runs/ORDER.json --stim ../runs/STIM-REGIONS.json \
         --realism ../runs/REALISM.json --region-info <paper repo>/brainwidemap/meta/region_info.csv > ../runs/SUMMARY.md
  (tests only: --synthetic --boot N)

Rules (fixed):
- rows deduplicated by (eid, region, label, row type), first occurrence kept; pilot rows ignored; completed prefix =
  the largest m with sessions 0..m-1 finished, skipped or errored; later sessions dropped.
- rejection = p < 0.05 strictly; None/NaN p excluded per cell and counted.
- aggregation: per region-session (share over its usable draws), then mean per mouse, then mean over mice;
  paired contrasts the same way on per-draw differences (both values usable).
- interval: mouse-cluster BCa (B = 20,000, seed 20261023, one generator for every interval in output order;
  acceleration from the mouse jackknife; z0 from the mid-rank of the observed value among the bootstrap values, ties
  within 1e-12); fewer than 2 mice -> no interval. 95% interval for every quantity; Bonferroni 98.3% for the three
  primary contrasts F, V, S only.
- decisions: a contrast is "positive" if its 95% lower bound > 0; a rate is "inflated" if its 95% lower bound > 10%.
  V gets no decision when the realism response makes Q2 descriptive.
- secondary contrasts (§7), same pairing and interval, no decision: P1, P4, PS-fixed minus PS-refit (S-main, fake
  labels); S-block: P2-block minus P2 (fake labels); P1 minus IID-P1.
"""
import argparse
import collections
import json
from pathlib import Path

import numpy as np
from scipy import stats

SEED = 20261023
B = [20000]
ROWS_Q1 = ["P1", "P2", "P4", "PS-refit", "PS-fixed", "P2-block", "PS-refit-block", "SEL-repeat", "SEL-fixed",
           "IID-SEL-repeat", "IID-SEL-fixed", "IID-P1", "IID-P2", "IID-P4"]
ROWS_Q2 = ["P1", "P2", "P4", "PS-refit", "PS-fixed", "P1-block", "P2-block", "P4-block", "PS-refit-block",
           "PS-fixed-block", "SEL-repeat", "SEL-fixed"]


def rej(p):
    return None if p is None or not np.isfinite(p) else float(p < 0.05)


def load(rows_dir):
    seen, rows = set(), []
    for f in sorted(Path(rows_dir).glob("rows.w*.jsonl")):
        for r in map(json.loads, f.read_text().splitlines()):
            if r.get("pilot"):
                continue
            kind = next((k for k in ("session_seconds", "skipped", "error", "excluded", "region_error") if k in r), "row")
            key = (r.get("eid"), r.get("region"), r.get("label"), kind)
            if key not in seen:
                seen.add(key)
                rows.append(r)
    return rows


def prefix(rows, n_order):
    final = {r["session_index"] for r in rows if any(k in r for k in ("session_seconds", "skipped", "error"))}
    m = 0
    while m < n_order and m in final:
        m += 1
    return m


def mouse_values(per_rs, mouse_of):
    """per_rs: {(eid, region): [values]} -> {mouse: array of per-region-session means}."""
    out = collections.defaultdict(list)
    for key, v in per_rs.items():
        if v:
            out[mouse_of[key]].append(float(np.mean(v)))
    return {k: np.array(v) for k, v in out.items()}


def mean_of_mice(data):
    return float(np.mean([np.mean(x) for x in data])) if data else float("nan")


def bca(by_mouse, rng, bonferroni=False):
    mice = sorted(by_mouse)
    data = [by_mouse[k] for k in mice]
    th = mean_of_mice(data)
    n = len(data)
    if n < 2:
        return th, None
    boots = np.array([mean_of_mice([data[i] for i in rng.integers(0, n, n)]) for _ in range(B[0])])
    less = np.sum(boots < th - 1e-12)
    tie = np.sum(np.abs(boots - th) <= 1e-12)
    z0 = stats.norm.ppf(np.clip((less + 0.5 * tie) / len(boots), 1e-6, 1 - 1e-6))
    jack = np.array([mean_of_mice(data[:i] + data[i + 1:]) for i in range(n)])
    d = jack.mean() - jack
    a = np.sum(d ** 3) / (6 * np.sum(d ** 2) ** 1.5) if np.sum(d ** 2) > 0 else 0.0
    out = {}
    levels = [("95", 0.05)] + ([("98.3", 0.05 / 3)] if bonferroni else [])
    for name, alpha in levels:
        qs = []
        for q in (alpha / 2, 1 - alpha / 2):
            zq = stats.norm.ppf(q)
            qs.append(float(np.quantile(boots, stats.norm.cdf(z0 + (z0 + zq) / (1 - a * (z0 + zq))))))
        out[name] = qs
    return th, out


def fmt(th, ci):
    if ci is None:
        return f"{100 * th:.1f}% (fewer than 2 mice: no interval)"
    s = f"{100 * th:.1f}% (95% {100 * ci['95'][0]:.1f} to {100 * ci['95'][1]:.1f}"
    if "98.3" in ci:
        s += f"; Bonferroni 98.3% {100 * ci['98.3'][0]:.1f} to {100 * ci['98.3'][1]:.1f}"
    return s + ")"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--order", required=True)
    ap.add_argument("--stim", required=True)
    ap.add_argument("--realism", required=True)
    ap.add_argument("--region-info", required=True, help="region_info.csv; only the Beryl column is read here")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--boot", type=int, default=20000)
    args = ap.parse_args()
    if args.boot != 20000 and not args.synthetic:
        raise SystemExit("B must be 20,000 except in synthetic tests (--synthetic)")
    B[0] = args.boot
    rng = np.random.default_rng(SEED)
    order = json.loads(Path(args.order).read_text())["sessions"]
    rows = load(args.rows)
    m = prefix(rows, len(order))
    rows = [r for r in rows if r.get("session_index", 10 ** 9) < m]
    sess = [r for r in rows if any(k in r for k in ("session_seconds", "skipped", "error"))]
    data = [r for r in rows if "label" in r]
    excl = [r for r in rows if "excluded" in r or "region_error" in r]
    realism = json.loads(Path(args.realism).read_text())
    assert "response" in realism, "REALISM.json lacks the response key"
    q2_descriptive = realism["response"] != "none"
    mouse_of = {(r["eid"], r["region"]): r["subject"] for r in data}
    print(f"# Step 3 summary\n\nB = {B[0]}, seed {SEED}{' (SYNTHETIC TEST)' if args.synthetic else ''}. "
          f"Completed prefix: {m} of {len(order)} sessions in the order.")
    print(f"Sessions in the prefix: finished {sum('session_seconds' in r for r in sess)}, skipped "
          f"{sum('skipped' in r for r in sess)}, errored {sum('error' in r for r in sess)}.")
    for k, v in sorted(collections.Counter(r.get("skipped") or ("session error" if "error" in r else None)
                                           for r in sess if "session_seconds" not in r).items()):
        print(f"- session {k}: {v}")
    for k, v in sorted(collections.Counter(r.get("excluded") or "region error" for r in excl).items()):
        print(f"- region-sessions excluded ({k}): {v}")

    def section_n(pred):
        d = [r for r in data if pred(r["label"])]
        return len({r["subject"] for r in d}), len({(r["eid"], r["region"]) for r in d})

    def fake(lab):
        return lab.startswith("fake")
    # ---------------------------------------------------------------- Q1
    nm, nrs = section_n(fake)
    print(f"\n## Q1 fake labels ({nm} mice, {nrs} region-sessions)\n")
    print("| row | rate (mouse-weighted) | mice | region-sessions | usable p | NaN/None p | region-sessions < 20 usable | rs-weighted | p in 0.03-0.07 |")
    print("|---|---|---|---|---|---|---|---|---|")
    q1_share = {}
    for row in ROWS_Q1:
        per = collections.defaultdict(list)
        nan, ps = 0, []
        for r in data:
            if fake(r["label"]):
                v = rej(r.get(row))
                if v is None:
                    nan += 1
                else:
                    per[(r["eid"], r["region"])].append(v)
                    ps.append(r[row])
        q1_share[row] = {k: float(np.mean(v)) for k, v in per.items() if v}
        bm = mouse_values(per, mouse_of)
        if not bm:
            print(f"| {row} | no usable value | 0 | 0 | 0 | {nan} | — | — | — |")
            continue
        th, ci = bca(bm, rng)
        flag = " **inflated**" if ci and ci["95"][0] > 0.10 else ""
        name = row + (" (sanity: exact by construction)" if row == "PS-refit" else "")
        short = sum(1 for v in per.values() if 0 < len(v) < 20)
        print(f"| {name} | {fmt(th, ci)}{flag} | {len(bm)} | {len(q1_share[row])} | {len(ps)} | {nan} | {short} | "
              f"{100 * np.mean(list(q1_share[row].values())):.1f}% | {100 * np.mean([(0.03 <= p <= 0.07) for p in ps]):.1f}% |")

    def paired(a_row, b_row, pred, bonf):
        per = collections.defaultdict(list)
        for r in data:
            if pred(r["label"]):
                a, b = rej(r.get(a_row)), rej(r.get(b_row))
                if a is not None and b is not None:
                    per[(r["eid"], r["region"])].append(a - b)
        bm = mouse_values(per, mouse_of)
        if not bm:
            return None
        th, ci = bca(bm, rng, bonferroni=bonf)
        return th, ci, len(bm), len(per), sum(len(v) for v in per.values())
    print("\n## Primary contrasts on fake labels (paired at region-session and draw)\n")
    for name, a, b in (("F = P2 - PS-refit (S-main)", "P2", "PS-refit"), ("S = SEL-fixed - SEL-repeat", "SEL-fixed", "SEL-repeat")):
        res = paired(a, b, fake, True)
        if res:
            th, ci, nmice, nrs_, npairs = res
            dec = " **positive**" if ci and ci["95"][0] > 0 else " not positive"
            print(f"- {name}: {fmt(th, ci)};{dec}; mice {nmice}, region-sessions {nrs_}, pairs {npairs}")
    res = paired("IID-SEL-fixed", "IID-SEL-repeat", fake, False)
    if res:
        print(f"- beside S, the same contrast in the i.i.d. control: {fmt(res[0], res[1])}; mice {res[2]}, pairs {res[4]}")
    print("\n## Secondary contrasts (§7; no decision)\n")
    for name, a, b in (("P1 - PS-refit", "P1", "PS-refit"), ("P4 - PS-refit", "P4", "PS-refit"),
                       ("PS-fixed - PS-refit", "PS-fixed", "PS-refit"), ("S-block: P2-block - P2", "P2-block", "P2"),
                       ("P1 - IID-P1 (Extended Data)", "P1", "IID-P1")):
        res = paired(a, b, fake, False)
        if res:
            print(f"- {name}: {fmt(res[0], res[1])}; mice {res[2]}, pairs {res[4]}")
    # ---------------------------------------------------------------- Q2
    real = [r for r in data if r["label"] == "real"]
    nm, nrs = section_n(lambda lab: lab == "real")
    print(f"\n## Q2 real labels ({nm} mice, {nrs} region-sessions)" + (" — descriptive only (realism response)" if q2_descriptive else "") + "\n")
    res = paired("P2", "PS-refit", lambda lab: lab == "real", True)
    if res:
        th, ci, nmice, nrs_, npairs = res
        dec = "no decision (realism response)" if q2_descriptive else ("**positive**" if ci and ci["95"][0] > 0 else "not positive")
        print(f"V = share P2 - share PS-refit: {fmt(th, ci)}; {dec}; mice {nmice}, region-sessions with both verdicts {npairs}")
    tab = collections.Counter()
    for r in real:
        a, b = rej(r.get("P2")), rej(r.get("PS-refit"))
        if a is not None and b is not None:
            tab[(a, b)] += 1
    print(f"\n| | PS-refit sig | PS-refit not |\n|---|---|---|\n| P2 sig | {tab[(1.0, 1.0)]} | {tab[(1.0, 0.0)]} |\n| P2 not | {tab[(0.0, 1.0)]} | {tab[(0.0, 0.0)]} |")
    disc = tab[(1.0, 0.0)] + tab[(0.0, 1.0)]
    pmc = stats.binomtest(tab[(1.0, 0.0)], disc, 0.5).pvalue if disc else float("nan")
    print(f"\nDiscordant: P2 only {tab[(1.0, 0.0)]}, PS-refit only {tab[(0.0, 1.0)]}; exact McNemar-type p {pmc:.4f} "
          "(descriptive: region-sessions are not independent).")
    xt = collections.Counter()
    for r in real:
        a, b = rej(r.get("P2")), rej(r.get("PS-refit"))
        if a is None or b is None:
            continue
        grp = "P2 only" if (a, b) == (1.0, 0.0) else "other verdicts"
        f = q1_share["P2"].get((r["eid"], r["region"]))
        xt[(grp, "no fake value" if f is None else "> 10%" if f > 0.10 else "<= 10%")] += 1
    print("\n| real-label verdict | own fake-label P2 rate > 10% | <= 10% | no fake value |\n|---|---|---|---|")
    for g in ("P2 only", "other verdicts"):
        print(f"| {g} | {xt[(g, '> 10%')]} | {xt[(g, '<= 10%')]} | {xt[(g, 'no fake value')]} |")
    print("\n| row | rate (mouse-weighted) | mice | usable | NaN/None | rs-weighted | p in 0.03-0.07 |\n|---|---|---|---|---|---|---|")
    for row in ROWS_Q2:
        per = collections.defaultdict(list)
        ps, nan = [], 0
        for r in real:
            v = rej(r.get(row))
            if v is None:
                nan += 1
            else:
                per[(r["eid"], r["region"])].append(v)
                ps.append(r[row])
        bm = mouse_values(per, mouse_of)
        if not bm:
            print(f"| {row} | no usable value | 0 | 0 | {nan} | — | — |")
            continue
        th, ci = bca(bm, rng)
        print(f"| {row} | {fmt(th, ci)} | {len(bm)} | {len(ps)} | {nan} | {100 * np.mean([np.mean(v) for v in per.values()]):.1f}% | "
              f"{100 * np.mean([(0.03 <= p <= 0.07) for p in ps]):.1f}% |")
    # ---------------------------------------------------------------- positive control
    import pandas as pd
    stim = json.loads(Path(args.stim).read_text())
    sig_set, nov_set = set(stim["stim_significant"]), set(stim["no_value"])
    all_regions = set(pd.read_csv(args.region_info, usecols=["Beryl"])["Beryl"].astype(str))
    pc, pcm, pc_nan = collections.Counter(), collections.defaultdict(set), 0
    for r in data:
        if r["label"] == "stim":
            v = rej(r.get("PS-refit"))
            if v is None:
                pc_nan += 1
                continue
            grp = "stimulus-significant" if r["region"] in sig_set else (
                "no value" if (r["region"] in nov_set or r["region"] not in all_regions) else "other")
            pc[(grp, v)] += 1
            pcm[grp].add(r["subject"])
    print("\n## Positive control (stimulus side, PS-refit p < 0.05)\n\n| region group | significant | not | mice |\n|---|---|---|---|")
    for g in ("stimulus-significant", "other", "no value"):
        print(f"| {g} | {pc[(g, 1.0)]} | {pc[(g, 0.0)]} | {len(pcm[g])} |")
    print(f"\nRegion-sessions with no usable PS-refit p (excluded): {pc_nan}")
    # ---------------------------------------------------------------- Extended Data
    spr = collections.defaultdict(set)
    for r in real:
        spr[r["region"]].add(r["eid"])
    print("\n## Extended Data: regions with >= 3 sessions (real labels; significant / usable; descriptive)\n")
    for reg in sorted(k for k, v in spr.items() if len(v) >= 3):
        rr = [r for r in real if r["region"] == reg]
        u2 = [rej(r.get("P2")) for r in rr if rej(r.get("P2")) is not None]
        u5 = [rej(r.get("PS-refit")) for r in rr if rej(r.get("PS-refit")) is not None]
        print(f"- {reg}: P2 {int(sum(u2))}/{len(u2)}, PS-refit {int(sum(u5))}/{len(u5)}")


if __name__ == "__main__":
    main()
