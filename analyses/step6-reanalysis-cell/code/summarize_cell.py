"""Summary of the Cell reanalysis: reads out/select.json, out/gate.json and out/test-*.json and writes summary.md and
summary.json. The verdict sentences and the prediction marks are generated here, not edited by hand (DESIGN.md sections
5, 9). Run: python -I summarize_cell.py [--out O]"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))   # also works under python -I
import cell_env  # noqa: F401

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROIS = ["LIP", "FEF", "LPFC"]
MODEL = "which assumes that blocks are exchangeable under the null, with the colour-selection penalty unmodelled"


def fmt_p(p):
    return "n/a" if p is None else ("%.4f" % p)


def verdict_sentence(region, p_holm, status, interpretable):
    """Sentence for the primary test (true template, 900 ms), per region."""
    if not interpretable:
        return "%s: not interpretable (gate); no verdict is written." % region
    if status != "tested" or p_holm is None:
        return "%s: no test, because the observed design is undefined." % region
    if p_holm < 0.05:
        return ("%s: under the block permutation test, %s, the null hypothesis of no association between population "
                "activity and the template bin is rejected (Holm-adjusted p = %s)." % (region, MODEL, fmt_p(p_holm)))
    return ("%s: under the block permutation test, %s, template decoding is not established (Holm-adjusted p = %s). "
            "With 3 to 4 blocks per bin the test has limited power and this result does not show that the template is "
            "absent." % (region, MODEL, fmt_p(p_holm)))


def secondary_sentence(role, region, p, p_holm, status):
    if status != "tested":
        return "%s, %s: no test, because the observed design is undefined." % (role, region)
    return "%s, %s: observed statistic compared with the permutation null, p = %s (Holm-adjusted %s); not part of the verdict." % (
        role, region, fmt_p(p), fmt_p(p_holm))


def _tested(t):
    return t is not None and all(t["regions"][r]["status"] == "tested" for r in ROIS)


def mark_predictions(sel, gate, tests):
    """Returns {id: (mark, reason)}; marks are held, not held, not tested. Definitions: DESIGN.md section 9."""
    out = {}
    tried = sel.get("tried", []) if sel else []
    # P1
    if not tried:
        out["P1"] = ("not tested", "the gate stopped before the accuracy items")
    else:
        out["P1"] = (("held" if sel["adopted"] == "as_written" else "not held"), "adopted variant: %s" % sel["adopted"])
    # P2
    if not tried:
        out["P2"] = ("not tested", "the gate stopped before the accuracy items")
    else:
        last = tried[-1]["variant"]
        g5 = next((i for i in gate["variant_items"][last] if i["name"].startswith("G5")), None)
        out["P2"] = (("held" if g5 and g5["passed"] else "not held"), "G5 in variant %s" % last)
    interp = bool(sel and sel.get("interpretable"))
    pr, tr, es, ad = (tests.get(k) for k in ("primary", "trial", "estimated", "adjacent"))
    # P3
    if not _tested(tr):
        out["P3"] = ("not tested", "trial-shuffle test absent or without a defined design")
    else:
        floor = 1.0 / (tr["P"] + 1)
        ok = all(abs(tr["regions"][r]["p"] - floor) < 1e-12 for r in ROIS)
        out["P3"] = (("held" if ok else "not held"), "p = 1/(P+1) = %.6f in all three regions required" % floor)
    # P4
    if not (_tested(pr) and interp):
        out["P4"] = ("not tested", "primary test absent, undefined or not interpretable")
    else:
        n = sum(pr["regions"][r]["p_holm"] < 0.05 for r in ROIS)
        out["P4"] = (("held" if n >= 1 else "not held"), "%d of 3 regions with Holm p < 0.05" % n)
    # P5
    if not (_tested(es) and interp):
        out["P5"] = ("not tested", "estimated-template test absent, undefined or not interpretable")
    else:
        n = sum(es["regions"][r]["p_holm"] >= 0.05 for r in ROIS)
        out["P5"] = (("held" if n >= 1 else "not held"), "%d of 3 regions with Holm p >= 0.05" % n)
    # P6
    if pr is None:
        out["P6"] = ("not tested", "primary test absent")
    else:
        o = (pr["design_obs"]["n_prog"], pr["design_obs"]["n_neurons"])
        diff = sum(1 for d in pr["design_null"] if d[0] is None or tuple(d) != o)
        out["P6"] = (("held" if diff >= 1 else "not held"), "%d of %d permutations differ from the observed design or are undefined" % (diff, len(pr["design_null"])))
    # P7
    if not (_tested(pr) and _tested(ad)):
        out["P7"] = ("not tested", "primary or adjacent-pair test absent or undefined")
    else:
        n = sum(ad["regions"][r]["p"] <= pr["regions"][r]["p"] + 1e-12 for r in ROIS)
        out["P7"] = (("held" if n >= 2 else "not held"), "adjacent-pair p <= primary p in %d of 3 regions (raw p)" % n)
    return out


def edge_report(tests, gate):
    rep = {}
    for k, t in tests.items():
        rep[k] = {r: (None if t["chosen_C_at_upper_edge"][r][0] == 0 else t["chosen_C_at_upper_edge"][r][1] / t["chosen_C_at_upper_edge"][r][0]) for r in ROIS}
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    o = Path(a.out) if a.out else HERE.parent / "out"
    sel = json.loads((o / "select.json").read_text()) if (o / "select.json").is_file() else None
    gate = json.loads((o / "gate.json").read_text()) if (o / "gate.json").is_file() else None
    tests = {p.stem[5:]: json.loads(p.read_text()) for p in sorted(o.glob("test-*.json"))}
    L = ["# Summary (generated by summarize_cell.py; nothing edited by hand)", ""]
    if gate:
        L += ["## Gate", "selection: %s" % sel["label"], "", "| item | core | passed | detail |", "|---|---|---|---|"]
        for i in gate["static_items"]:
            L.append("| %s | %s | %s | %s |" % (i["name"], i["core"], i["passed"], i.get("detail", "")))
        for v, its in gate["variant_items"].items():
            for i in its:
                L.append("| [%s] %s | %s | %s | %s |" % (v, i["name"], i["core"], i["passed"], i.get("detail", "")))
        L.append("")
    interp = bool(sel and sel.get("interpretable"))
    pr = tests.get("primary")
    if pr:
        L += ["## Primary: true template, 900 ms window (variant %s)" % pr["variant"], ""]
        for r in ROIS:
            g = pr["regions"][r]
            L.append("- " + verdict_sentence(r, g["p_holm"], g["status"], interp))
        L.append("")
    for k, t in tests.items():
        if k == "primary":
            continue
        L += ["## Secondary: %s (variant %s)" % (t["role"], t["variant"]), ""]
        for r in ROIS:
            g = t["regions"][r]
            L.append("- " + secondary_sentence(t["role"], r, g["p"], g["p_holm"], g["status"]))
        L.append("")
    if tests:
        L += ["## Design counts and the chosen C at the upper edge (log10 C = 1)", ""]
        for k, t in tests.items():
            nd = len(t["design_null"])
            und = sum(1 for d in t["design_null"] if d[0] is None)
            L.append("- %s: observed N_progression %s, N_neurons %s; %d of %d permutations differ from the observed design or are undefined (%d undefined)" % (
                k, t["design_obs"]["n_prog"], t["design_obs"]["n_neurons"],
                sum(1 for d in t["design_null"] if d[0] is None or tuple(d) != (t["design_obs"]["n_prog"], t["design_obs"]["n_neurons"])), nd, und))
        for k, v in edge_report(tests, gate).items():
            L.append("- %s: share of SVM fits with chosen C at the upper edge: %s" % (k, {r: (None if x is None else round(x, 3)) for r, x in v.items()}))
        L.append("")
    preds = mark_predictions(sel, gate, tests) if (sel and gate) else {}
    if preds:
        L += ["## Predictions (DESIGN.md section 9)", "", "| id | mark | reason |", "|---|---|---|"]
        for k, (m, why) in preds.items():
            L.append("| %s | %s | %s |" % (k, m, why))
    (o / "summary.md").write_text("\n".join(L) + "\n")
    (o / "summary.json").write_text(json.dumps({"predictions": {k: list(v) for k, v in preds.items()}, "interpretable": interp}, indent=1))
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    main()
