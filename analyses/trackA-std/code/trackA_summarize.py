#!/usr/bin/env python3
"""Track A summary (pre-registered in PREREG-trackA.md). Reads the outputs of
ephys-matched-null.py (P1 and its sensitivity runs) and trackA_extra.py, checks the
gates, computes every pre-registered estimand at the animal level and writes
results.json and results.md (the template filled in).

  python3 trackA_summarize.py --runs <folder with the run outputs> --out <folder>

Expected files in --runs (names fixed by README step 5):
  p1_good.log, p1_good_draws.json      primary (Allen quality == good)
  p1_all.log,  p1_all_draws.json       sensitivity (every sorted cluster, as planned in 2026-09)
  p1_sdk.log,  p1_sdk_draws.json       sensitivity (AllenSDK default unit filter)
  extra.jsonl                          P2, P3, C
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
STD6 = ("VISp", "VISl", "VISal", "VISrl", "VISam", "VISpm")
BOOT_B = 20000
BOOT_SEED = 20261015
MC_SEEDS = (BOOT_SEED, 1, 2, 3, 4)          # verdicts use BOOT_SEED only; the rest show Monte Carlo spread


SESSIONS_CSV = PKG / "sessions_trackA.csv"
SMOKE = False


def sessions():
    rows = list(csv.DictReader(SESSIONS_CSV.open(encoding="utf-8")))
    return {r["session_id"]: r for r in rows}


def read_p1(log: Path, draws: Path):
    units = {}
    for ln in log.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(\d+)\s+(VIS\S*)\s+(\d+)\s+(\d+)\s", ln)
        if m:
            units[(m.group(1), m.group(2))] = (int(m.group(3)), int(m.group(4)))
    out = []
    for d in json.loads(draws.read_text(encoding="utf-8")):
        nd = np.asarray(d["null_draws"], float)
        free, const = float(d["free"]), float(d["const"])
        out.append({"session": d["session"], "area": d["area"], "free": free, "const": const,
                    "null": float(np.nanmean(nd)), "g_null": free - float(np.nanmean(nd)),
                    "d": float(np.nanmean(nd)) - const, "g_const": free - const,
                    "p_spec": float((1 + (nd >= free).sum()) / (len(nd) + 1)),
                    "n_units": units.get((d["session"], d["area"]), (None, None))[0]})
    return out


def animal_means(rows, key, S):
    by = {}
    for r in rows:
        if r.get(key) is None or not np.isfinite(r[key]):
            continue
        by.setdefault(S[r["session"]]["specimen_id"], []).append(r[key])
    animals = sorted(by)
    return animals, np.array([np.mean(by[a]) for a in animals])


def boot(vals, seed=BOOT_SEED, stat=np.mean):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(vals), (BOOT_B, len(vals)))
    return np.percentile(stat(vals[idx], axis=1), [2.5, 97.5])


def estimate(rows, key, S):
    animals, v = animal_means(rows, key, S)
    if len(v) == 0:
        return {"n_animals": 0}
    ci = boot(v)
    spread = [boot(v, seed=s).tolist() for s in MC_SEEDS]
    return {"n_animals": len(v), "n_area_units": sum(1 for r in rows if r.get(key) is not None and np.isfinite(r[key])),
            "mean": float(v.mean()), "ci": [float(ci[0]), float(ci[1])],
            "ci_mc_range": [[min(x[0] for x in spread), max(x[0] for x in spread)],
                            [min(x[1] for x in spread), max(x[1] for x in spread)]]}


def ratio(rows, S):
    """R = mean over animals of d / mean over animals of g_const (ratio of means)."""
    a1, d = animal_means(rows, "d", S)
    a2, g = animal_means(rows, "g_const", S)
    assert a1 == a2
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(d), (BOOT_B, len(d)))
    num, den = d[idx].mean(1), g[idx].mean(1)
    ok = den > 0
    r = num[ok] / den[ok]
    lo, hi = np.percentile(r, [2.5, 97.5])
    shares = [name for name, val in (("a quarter", 0.25), ("a third", 1 / 3), ("half", 0.5)) if lo <= val <= hi]
    return {"R": float(d.mean() / g.mean()), "ci": [float(lo), float(hi)], "ci_conditional_on_positive_denominator": True,
            "undefined_resamples": int((~ok).sum()), "single_share_in_ci": shares[0] if len(shares) == 1 else None}


def m3_branch(est):
    """PREREG section 5/7: share phrase, ratio number, or d with its interval."""
    d_ok = est["d"].get("ci", [0])[0] > 0
    g_ok = est["g_const"].get("ci", [0])[0] > 0
    r = est.get("ratio", {})
    if d_ok and g_ok and r.get("undefined_resamples", 1) == 0:
        return ("share", r["single_share_in_ci"]) if r.get("single_share_in_ci") else ("ratio", round(r["R"], 2))
    return ("d", None)


def proportion(rows, key, S, alpha=0.05):
    for r in rows:
        r["_hit"] = None if r.get(key) is None else float(r[key] < alpha)
    est = estimate(rows, "_hit", S)
    est["n_hit"] = int(sum(1 for r in rows if r.get("_hit") == 1.0))
    return est


def subset(rows, S, which, areas):
    keep = []
    for r in rows:
        st = S[r["session"]]["set"]
        if which != "all32" and st != which:
            continue
        if areas == "std6" and r["area"] not in STD6:
            continue
        keep.append(r)
    return keep


def gate(runs: Path):
    """The two original sessions must reproduce the committed seed-1 outputs exactly."""
    res = {}
    for tag, exp in (("good", "ephys-matched-null-seed1-goodonly-draws.json"), ("all", "ephys-matched-null-seed1-draws.json")):
        got = [d for d in json.loads((runs / f"p1_{tag}_draws.json").read_text(encoding="utf-8"))
               if d["session"] in ("715093703", "719161530")]
        if not got:
            res[tag] = "not run (original sessions absent)" if SMOKE else False
            continue
        want = json.loads((PKG / "expected" / exp).read_text(encoding="utf-8"))
        res[tag] = got == want
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sessions-csv", default=None, help="smoke test only")
    ap.add_argument("--smoke", action="store_true", help="synthetic smoke test: original sessions absent is allowed")
    ap.add_argument("--excluded", default="", help="comma-separated sessions removed under PREREG section 6 (reported)")
    args = ap.parse_args()
    global SESSIONS_CSV, SMOKE
    SMOKE = args.smoke
    if args.sessions_csv:
        SESSIONS_CSV = Path(args.sessions_csv)
    runs, outd = Path(args.runs), Path(args.out)
    outd.mkdir(parents=True, exist_ok=True)
    S = sessions()
    R = {"gates": gate(runs)}
    if any(v is False for v in R["gates"].values()):
        (outd / "results.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
        raise SystemExit(f"GATE FAILED {R['gates']}: stop and report (PREREG section 6). No estimate computed.")
    p1 = {t: read_p1(runs / f"p1_{t}.log", runs / f"p1_{t}_draws.json") for t in ("good", "all", "sdk")}
    extra = [json.loads(x) for x in (runs / "extra.jsonl").read_text(encoding="utf-8").splitlines()]
    logs = " ".join((runs / f"p1_{t}.log").read_text(encoding="utf-8") for t in ("good", "all", "sdk"))
    missing = [sid for sid in S if f"{sid}: file missing" in logs or sid not in {r["session"] for r in extra}]
    p1_keys = {(r["session"], r["area"]) for r in p1["good"]}
    ex_p = {(r["session"], r["area"]) for r in extra if "p3" in r}
    mism = [k for k in p1_keys ^ ex_p]
    free_diff = [(r["session"], r["area"]) for r in extra if "p3" in r for q in p1["good"]
                 if (q["session"], q["area"]) == (r["session"], r["area"]) and abs(q["free"] - r["p3"]["obs"]) > 1e-9]
    R["checks"] = {"sessions_missing_or_unread": missing, "p1_vs_extra_area_mismatch": mism,
                   "p1_free_vs_p3_obs_mismatch": free_diff,
                   "logistic_nonconverged": int(sum(r.get("logistic_nonconverged", 0) for r in extra)),
                   "c_skipped_sessions": sorted({r["session"]: r.get("c_skipped") for r in extra if r.get("c_skipped")}.items()),
                   "dg_trials_overlapping_invalid": sum({r["session"]: r.get("dg_invalid_overlap", 0) for r in extra}.values()),
                   "excluded_under_section_6": [x for x in args.excluded.split(",") if x]}
    bad = [m for m in missing if m not in R["checks"]["excluded_under_section_6"]]
    if bad or mism or free_diff:
        (outd / "results.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
        raise SystemExit(f"CHECK FAILED (missing {bad}, area mismatch {mism}, free mismatch {free_diff}): "
                         "follow PREREG section 6; no estimate computed.")

    # P1 primary: new 30 animals, standard six areas, quality == good
    R["P1"] = {}
    for tag in ("good", "all", "sdk"):
        for which in ("new", "original", "all32"):
            for areas in ("std6", "allvis"):
                rows = subset(p1[tag], S, which, areas)
                key = f"{tag}/{which}/{areas}"
                R["P1"][key] = {k: estimate(rows, k, S) for k in ("g_null", "d", "g_const")}
                if rows:
                    R["P1"][key]["ratio"] = ratio(rows, S)
                    R["P1"][key]["units_g_null_pos"] = [int(sum(r["g_null"] > 0 for r in rows)), len(rows)]
                    R["P1"][key]["units_p_spec_lt05"] = [int(sum(r["p_spec"] < 0.05 for r in rows)), len(rows)]
    prim = R["P1"]["good/new/std6"]
    prim["m3_branch"] = m3_branch(prim)
    for which in ("new", "original"):
        rows = subset(p1["good"], S, which, "std6")
        in_set = [sid for sid, r in S.items() if r["set"] == which]
        R[f"P1_mice/{which}"] = {"included": len({S[r['session']]['specimen_id'] for r in rows}), "in_set": len(in_set)}
    per = {}
    for which in ("new", "original"):
        for r in subset(p1["good"], S, which, "std6"):
            m = per.setdefault(S[r["session"]]["specimen_id"], {"set": which, "genotype": S[r["session"]]["genotype"], "rows": []})
            m["rows"].append(r)
    R["per_mouse_for_fig1a"] = {k: {"set": v["set"], "genotype": v["genotype"], "n_areas": len(v["rows"]),
                                    "best_gain": float(np.mean([x["g_const"] for x in v["rows"]])),
                                    "null_gain": float(np.mean([x["d"] for x in v["rows"]])),
                                    "g_null": float(np.mean([x["g_null"] for x in v["rows"]]))} for k, v in per.items()}
    R["verdict_P1"] = {"g_null_replicated": bool(prim["g_null"].get("ci", [0])[0] > 0),
                       "d_replicated": bool(prim["d"].get("ci", [0])[0] > 0)}

    # genotype (descriptive only)
    gt = {}
    for r in subset(p1["good"], S, "new", "std6"):
        g = "wt" if S[r["session"]]["genotype"].startswith("wt") else "Cre"
        gt.setdefault(g, []).append(r)
    R["P1_genotype"] = {g: {k: estimate(v, k, S) for k in ("g_null", "d")} for g, v in gt.items()}

    # P2, P3, C
    for r in extra:
        if "p2" in r:
            r["p2_delta"] = r["p2"]["obs"] - r["p2"]["null_mean"]
            r["p2_gain"] = r["p2"]["obs"] - r["p2"]["const"]
            r["p2_p"] = r["p2"]["p"]
        if "p3" in r:
            r["p3_excess"] = r["p3"]["obs"] - r["p3"]["null_mean"]
            r["p3_p"] = r["p3"]["p"]
        for sch in ("iid", "segment", "random_blocks"):
            c = r.get(f"c_{sch}")
            if c:
                for t in ("q2_p", "full_p", "spec_p", "block_p"):
                    if t in c:
                        r[f"c_{sch}_{t}"] = c[t]
        if "p2" in r:
            r["p2_k"] = r["p2"]["k"]
    for which, areas in (("new", "std6"), ("new", "allvis"), ("original", "std6"), ("original", "allvis")):
        rows = subset(extra, S, which, areas)
        tag = areas if which == "new" else f"original/{areas}"
        R[f"P2/{tag}"] = {"delta": estimate(rows, "p2_delta", S), "gain": estimate(rows, "p2_gain", S),
                            "p_lt05": proportion(rows, "p2_p", S)}
        R[f"P2/{tag}"]["k_chosen"] = np.bincount([r["p2_k"] for r in rows if "p2_k" in r], minlength=41)[[5, 10, 20, 40]].tolist()
        R[f"P2/{tag}"]["null_k"] = np.sum([r["p2"]["null_k"] for r in rows if "p2" in r], axis=0).tolist() if any("p2" in r for r in rows) else []
        R[f"P3/{tag}"] = {"excess": estimate(rows, "p3_excess", S), "p_lt05": proportion(rows, "p3_p", S)}
        R[f"C/{tag}"] = {f"{sch}/{t}": proportion(rows, f"c_{sch}_{t}", S)
                           for sch in ("iid", "segment", "random_blocks") for t in ("q2_p", "full_p", "spec_p", "block_p")
                           if any(f"c_{sch}_{t}" in r for r in rows)}
    R["verdict_P2"] = {"delta_ci_above_0": bool(R["P2/std6"]["delta"].get("ci", [0])[0] > 0)}
    newx = subset(extra, S, "new", "std6")
    sess_rows = {r["session"]: r for r in extra}
    rc = [v.get("run_cal") for v in sess_rows.values() if v.get("run_cal") is not None]
    rt = [v.get("run_test") for v in sess_rows.values() if v.get("run_test") is not None]
    R["descriptive"] = {"mean_running_speed_calibration_half": float(np.mean(rc)) if rc else None,
                        "mean_running_speed_heldout_half": float(np.mean(rt)) if rt else None,
                        "units_presence_below_0_9_in_std6_new": int(sum(r.get("n_low_presence", 0) for r in newx)),
                        "pseudo_trials_overlapping_invalid": int(sum(v.get("pseudo_invalid_overlap", 0) for v in sess_rows.values())),
                        "null_nan_counts": int(sum(r.get(k, {}).get("null_nan", 0) for r in extra for k in ("p2", "p3")))}

    (outd / "results.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
    write_md(R, outd / "results.md")
    print(json.dumps({"gates": R["gates"], "checks": R["checks"], "verdict_P1": R["verdict_P1"],
                      "verdict_P2": R["verdict_P2"]}, indent=1))


def fmt(e, nd=1):
    if not e or "mean" not in e:
        return "n/a"
    return f"{e['mean']:.{nd}f} ({e['ci'][0]:.{nd}f} to {e['ci'][1]:.{nd}f}; animals {e['n_animals']}, area units {e['n_area_units']})"


def write_md(R, path):
    t = (PKG / "RESULTS_TEMPLATE.md").read_text(encoding="utf-8")
    p = R["P1"]["good/new/std6"]
    fill = {
        "GATE_GOOD": str(R["gates"]["good"]), "GATE_ALL": str(R["gates"]["all"]),
        "P1_GNULL": fmt(p["g_null"]), "P1_D": fmt(p["d"]), "P1_GCONST": fmt(p["g_const"]),
        "P1_RATIO": f"{p['ratio']['R']:.3f} ({p['ratio']['ci'][0]:.3f} to {p['ratio']['ci'][1]:.3f}; conditional on positive denominators, undefined resamples {p['ratio']['undefined_resamples']}); single share in interval: {p['ratio']['single_share_in_ci']}",
        "P1_UNITS": f"g_null > 0 in {p['units_g_null_pos'][0]}/{p['units_g_null_pos'][1]}; p_spec < 0.05 in {p['units_p_spec_lt05'][0]}/{p['units_p_spec_lt05'][1]}",
        "V_GNULL": str(R["verdict_P1"]["g_null_replicated"]), "V_D": str(R["verdict_P1"]["d_replicated"]),
        "P2_DELTA": fmt(R["P2/std6"]["delta"]), "P2_GAIN": fmt(R["P2/std6"]["gain"]),
        "P2_PLT": fmt(R["P2/std6"]["p_lt05"], 3), "V_P2": str(R["verdict_P2"]["delta_ci_above_0"]),
        "P3_EXCESS": fmt(R["P3/std6"]["excess"]), "P3_PLT": fmt(R["P3/std6"]["p_lt05"], 3),
    }
    for k, v in R["C/std6"].items():
        fill["C_" + k.replace("/", "_").upper()] = fmt(v, 3)
    sens = []
    for key, v in R["P1"].items():
        if "g_null" in v and "mean" in v["g_null"]:
            sens.append(f"| {key} | {fmt(v['g_null'])} | {fmt(v['d'])} | {v['ratio']['R']:.3f} |")
    fill["SENSITIVITY_TABLE"] = "\n".join(sens)
    fill["CHECKS"] = json.dumps(R["checks"])
    fill["M3_BRANCH"] = str(p["m3_branch"])
    fill["P1_MICE"] = f"{R['P1_mice/new']['included']} / {R['P1_mice/new']['in_set']}"
    fill["DESCRIPTIVE"] = json.dumps(R["descriptive"])
    fill["P2_K"] = f"observed k chosen (5/10/20/40): {R['P2/std6'].get('k_chosen')}; null k: {R['P2/std6'].get('null_k')}"
    o = R.get("P2/original/std6", {})
    fill["ORIG_P2"] = fmt(o.get("delta")) if o else "n/a"
    fill["ORIG_P3"] = fmt(R.get("P3/original/std6", {}).get("excess")) if o else "n/a"
    fill["GENOTYPE"] = "\n".join(f"| {g} | {fmt(v['g_null'])} | {fmt(v['d'])} |" for g, v in R["P1_genotype"].items())
    for k, v in fill.items():
        t = t.replace("{{" + k + "}}", v)
    t = re.sub(r"\{\{C_[A-Z_]+\}\}", "n/a", t)
    path.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
