"""Variant selection by code (DESIGN.md section 6). The gate items G4 and G5 decide the variant; the other core items
decide what may run. Any other variant than the adopted one is refused by `require_variant`."""
from __future__ import annotations

import json
from pathlib import Path

import cell_env  # noqa: F401

ORDER = ["as_written", "V1_intended", "V2_fine_grid"]
TRUE_TESTS = ("primary", "trial", "win600", "adjacent")
ALL_TESTS = TRUE_TESTS + ("estimated",)


def decide(items, runs):
    """items: static gate items (dicts with name, core, stops, passed). runs: {variant name: list of G4/G5 items}, in
    the order tried. Returns the selection record."""
    stop_all = [i["name"] for i in items if i["stops"] and not i["passed"]]
    true_stop = [i["name"] for i in items if i["core"] and not i["stops"] and not i["passed"] and i["name"][:2] in ("G7", "G8")]
    tried, adopted = [], None
    for name in ORDER:
        if name not in runs:
            break
        acc_ok = all(i["passed"] for i in runs[name] if i["core"])
        tried.append({"variant": name, "accuracy_items_passed": acc_ok})
        if acc_ok:
            adopted = name
            break
    if stop_all:
        allowed = []
    elif true_stop:
        allowed = ["estimated"]
    else:
        allowed = list(ALL_TESTS)
    if stop_all:
        label = "stopped: %s failed; no test is run" % "; ".join(stop_all)
    elif adopted is None:
        label = "not interpretable: no variant passed the accuracy items; tests are run with as_written and saved without a verdict"
    else:
        label = "interpretable (variant %s)" % adopted
    return {"adopted": adopted, "variant_for_tests": adopted or "as_written", "tried": tried, "stopped_by": stop_all,
            "true_template_blocked_by": true_stop, "allowed_tests": allowed, "label": label,
            "interpretable": bool(adopted) and not stop_all,
            "val_rule": next((i.get("val_rule") for i in items if i["name"][:2] == "G9"), None)}


def verify(sel):
    """The tried list must follow ORDER from the start and end at the adopted variant (no skipping)."""
    names = [t["variant"] for t in sel["tried"]]
    if names != ORDER[:len(names)]:
        raise SystemExit("select record: variants tried out of order: %s" % names)
    if sel["adopted"] is not None and names[-1] != sel["adopted"]:
        raise SystemExit("select record: adopted variant is not the last one tried")
    if sel["adopted"] is None and len(names) not in (0, len(ORDER)) and not sel["stopped_by"]:
        raise SystemExit("select record: no variant adopted but not all were tried")
    return True


def require_variant(sel_path, name, test):
    sel = json.loads(Path(sel_path).read_text())
    verify(sel)
    if test not in sel["allowed_tests"]:
        raise SystemExit("test %r is not allowed by the gate (%s)" % (test, sel["label"]))
    if name != sel["variant_for_tests"]:
        raise SystemExit("variant %r refused; the select step adopted %r" % (name, sel["variant_for_tests"]))
    return sel
