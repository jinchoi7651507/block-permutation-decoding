"""Runner for the Cell reanalysis (DESIGN.md sections 3, 5 to 8). Stages, in this order:

  python -I run_cell.py determinism                                  synthetic only, no data
  python -I run_cell.py inspect --extract-root R [--out O]           lists fields of the extracted members; no accuracy
  python -I run_cell.py gate    --extract-root R [--out O] [--workers 6]
  python -I run_cell.py select  [--out O]                            adopts a variant by code from the gate runs
  python -I run_cell.py test --name primary|trial|win600|estimated|adjacent --extract-root R [--out O] [--workers 6]
  python -I summarize_cell.py [--out O]                              tables, verdict sentences, predictions

R is the folder that holds Data/ and Figure_2/ as extracted from the Zenodo zips; paths in all outputs are relative to
R or O. The environment is pinned (cell_env.PINNED) and checked at run time; thread variables are set to 1 on import.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))   # also works under python -I
import cell_env  # noqa: F401  (must be the first import)

import argparse
import hashlib
import json
import os
import pickle
import re
import sys
from pathlib import Path

import numpy as np

import cell_gate as cg
import cell_select as cs
import cell_tests as ct
import cellport as cp

HERE = Path(__file__).resolve().parent
P_DEFAULT, D_DEFAULT, D_GATE = 1000, 10, 100
# test name -> (kind, window, label set, purpose code, role)
TESTS = {"primary": ("block", "900", "true", 1, "primary"),
         "trial": ("trial", "900", "true", 2, "secondary (c) trial-shuffle reference"),
         "win600": ("block", "600", "true", 3, "secondary 600 ms pre-target window"),
         "estimated": ("sequence", "900", "estimated", 4, "secondary (d) estimated template, option A"),
         "adjacent": ("block_adjacent", "900", "true", 5, "secondary (f) adjacent-pair sensitivity (D10)")}
CODE_FILES = ["run_cell.py", "cell_env.py", "cell_gate.py", "cell_select.py", "cell_tests.py", "cellport.py", "cell_loader.py"]
GATE_PURPOSE = {"estimated": 21, "true": 22}


def _clean(o):
    """Recursively convert numpy values to Python values; NaN becomes null."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if o != o else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def jdump(obj, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(_clean(obj), indent=1))


def jload(path):
    return json.loads(Path(path).read_text())


def out_dir(a):
    return Path(a.out) if a.out else HERE.parent / "out"


def data_paths(a):
    r = Path(a.extract_root)
    return r / "Data" / "FR_around_event", r / "Figure_2" / "plot_figure_2" / "Figure_2_decoding_accuracy.mat"


def load_sessions(a, o):
    from cell_loader import load_all
    cache = o / "sessions.pkl"
    if a.cache and cache.is_file():
        return pickle.loads(cache.read_bytes())
    root, _ = data_paths(a)
    sessions, rs = load_all(root)
    if a.cache:
        cache.write_bytes(pickle.dumps((sessions, rs)))
    return sessions, rs


# ----------------------------------------------------------------------------- resume header (N1)
def code_hashes():
    return {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in CODE_FILES}


def check_pd(perms, draws, addendum):
    """P and D other than the design's (P = 1,000, D = 10) are refused unless a dated addendum name is given."""
    if addendum is not None and not re.search(r"\d{4}-\d{2}-\d{2}", addendum):
        raise SystemExit("refused: --addendum needs a dated name (YYYY-MM-DD in it), got %r" % addendum)
    if (perms, draws) != (P_DEFAULT, D_DEFAULT) and addendum is None:
        raise SystemExit("refused: P = %d, D = %d differ from the design (P = %d, D = %d); give --addendum <dated name> to run them" % (perms, draws, P_DEFAULT, D_DEFAULT))


def make_header(name, variant, grid, window, perms, draws, val_rule, addendum):
    return {"test": name, "variant": variant, "grid": grid, "window": window, "P": perms, "D": draws, "val_rule": val_rule,
            "master_seed": cell_env.MASTER_SEED, "platform": cell_env.platform_record(), "code_sha256": code_hashes(),
            "addendum": addendum}


def read_partial(part, header):
    """Returns the finished labellings of an existing partial file (empty if there is none). A file without a header
    line, or with a header that differs from the current one, is refused."""
    done = {}
    if not part.is_file() or part.stat().st_size == 0:
        return done
    lines = part.read_text().splitlines()
    first = json.loads(lines[0])
    if "header" not in first:
        raise SystemExit("refused: %s has no header line; not resumed" % part.name)
    old, new = _clean(first["header"]), _clean(header)
    if old != new:
        diff = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
        raise SystemExit("refused: header of %s differs from this run in %s; not resumed" % (part.name, ", ".join(diff)))
    for line in lines[1:]:
        d = json.loads(line)
        done[d["i"]] = d
    return done


# ----------------------------------------------------------------------------- stages
def stage_determinism(a):
    """Reruns three synthetic labellings through the whole pipeline (serial and in two worker processes) and checks
    that the output is identical."""
    from synthetic_data import make_sessions
    if cp.MIN_TRIALS != 18:
        raise SystemExit("the determinism stage uses the scaled-down synthetic sizes: run it with CELL_MIN_TRIALS=18 (the test suite sets it)")
    S, rs = make_sessions(31, n_sess=5, n_blocks=9, n_neur=5, signal=0.5, rois=["A", "B", "C"])
    bins = [s.true_bin for s in S]
    ok = True
    for kind in ("obs", "block", "trial"):
        args = [(kind, i, S, bins, ["A", "B", "C"], rs, 2, "across", True, 7, "coarse") for i in (1, 2, 3)]
        r1 = [ct.one_labelling(x) for x in args]
        r2 = [ct.one_labelling(x) for x in args]
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(2) as ex:
            r3 = list(ex.map(ct.one_labelling, args))
        same = repr(r1) == repr(r2) == repr(r3)
        if not same:
            for j, (x, y, z) in enumerate(zip(r1, r2, r3)):
                if not (repr(x) == repr(y) == repr(z)):
                    print("  labelling %d differs:\n   %r\n   %r\n   %r" % (j + 1, x, y, z))
        print("determinism %-6s identical across reruns and worker counts: %s" % (kind, same))
        ok &= same
    return 0 if ok else 1


def stage_inspect(a):
    cell_env.require_platform_fixed(getattr(a, "addendum", None))
    from cell_loader import SESSION_IDS, window_dir, read_mat, ROI_VAR, mat_format
    o = out_dir(a)
    root, gate_file = data_paths(a)
    lines = ["# fields found in the extracted members (no accuracy computed)"]
    for sid in SESSION_IDS:
        p = window_dir(root, 0) / ("ID_%d.mat" % sid)
        fmt = mat_format(p)
        m = read_mat(p)
        c = m.get("Conditions")
        lines.append("ID_%d (%s): variables %s" % (sid, fmt, [k for k in m if not k.startswith("_")]))
        if c is not None:
            lines.append("   Conditions fields: %s" % (getattr(c, "_fieldnames", None) or [k for k in vars(c) if not k.startswith("_")]))
            for f in ("block_nb", "trial_in_block", "rule", "belief"):
                if hasattr(c, f):
                    lines.append("   %s shape %s" % (f, np.shape(getattr(c, f))))
        for v in ROI_VAR.values():
            if v in m:
                lines.append("   %s shape %s" % (v, np.shape(m[v])))
    gm = read_mat(gate_file)
    lines.append("gate file variables: %s" % {k: np.shape(v) for k, v in gm.items() if not k.startswith("_")})
    o.mkdir(parents=True, exist_ok=True)
    (o / "fields.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:6]), "\n... written to fields.txt")
    return 0


def stage_gate(a):
    cell_env.require_platform_fixed(getattr(a, "addendum", None))
    o = out_dir(a)
    if not (o / "fields.txt").is_file():
        raise SystemExit("run the inspect stage first (fields.txt is missing)")
    cell_env.check_environment()
    root, gate_file = data_paths(a)
    members = HERE.parent / "data-members.tsv"
    pub = cg.read_gate_file(gate_file)
    items = [cg.g9_validation_size(pub)]                        # first, before any port draw
    val_rule = items[0]["val_rule"]
    if val_rule:
        os.environ["CELL_VAL_RULE"] = val_rule                  # inherited by the worker processes
    items.append(cg.g1_integrity(members, a.extract_root))
    if not items[0]["passed"]:
        return _finish_gate(o, items, {}, None)
    sessions, rs = load_sessions(a, o)
    items += [cg.g2_sessions(sessions), cg.g3_estimated_counts(sessions, rs), cg.g7_s3g_counts(sessions, rs, val_rule),
              cg.g8_true_labels(sessions, rs)]
    if any(i["stops"] and not i["passed"] for i in items):
        return _finish_gate(o, items, {}, None)
    runs, estim = {}, [s.belief_bin for s in sessions]
    for name, spec in cg.VARIANTS:
        f = o / "gate-runs" / (name + ".json")
        if f.is_file():
            rec = jload(f)
        else:
            acc, hp, des = cg.gate_draws(sessions, rs, estim, D_GATE, GATE_PURPOSE["estimated"], spec, a.workers)
            rec = {"variant": name, "spec": spec, "design": {"n_prog": des["n_prog"], "n_neurons": des["n_neurons"]},
                   "acc": {r: acc[r].tolist() for r in cg.ROIS}, "hp": hp, "platform": cell_env.platform_record()}
            jdump(rec, f)
        its = cg.accuracy_items({r: np.array(rec["acc"][r]) for r in cg.ROIS}, pub)
        runs[name] = its
        if all(i["passed"] for i in its if i["core"]):
            break
    sel_name = next((n for n, its in runs.items() if all(i["passed"] for i in its if i["core"])), None)
    spec = dict(cg.VARIANTS)[sel_name or "as_written"]
    extra = {"blocks_per_bin_true": cg.blocks_per_bin(sessions, rs)}
    byname = {i["name"][:2]: i for i in items}
    if byname["G7"]["passed"] and byname["G8"]["passed"]:
        acc, hp, des = cg.gate_draws(sessions, rs, [s.true_bin for s in sessions], D_GATE, GATE_PURPOSE["true"], spec, a.workers)
        extra["true_template_descriptive_G11"] = {"variant": sel_name or "as_written", "mean_per_region": {r: float(np.mean(acc[r])) for r in cg.ROIS},
                                                  "mean_per_region_level": {r: np.mean(acc[r], 0).tolist() for r in cg.ROIS}, "hp": hp,
                                                  "design": {"n_prog": des["n_prog"], "n_neurons": des["n_neurons"]}}
    return _finish_gate(o, items, runs, extra)


def _finish_gate(o, items, runs, extra):
    sel = cs.decide(items, runs)
    rec = {"static_items": items, "variant_items": {k: v for k, v in runs.items()}, "extra": extra or {}, "platform": cell_env.platform_record()}
    jdump(rec, o / "gate.json")
    jdump(sel, o / "select.json")
    for i in items:
        print("%s %s: %s" % ("PASS" if i["passed"] else "FAIL", i["name"], i["detail"]))
    for k, v in runs.items():
        for i in v:
            print("%s [%s] %s: %s" % ("PASS" if i["passed"] else "FAIL", k, i["name"], i["detail"]))
    print(sel["label"])
    return 0


def stage_select(a):
    cell_env.require_platform_fixed(getattr(a, "addendum", None))
    o = out_dir(a)
    g = jload(o / "gate.json")
    sel = cs.decide(g["static_items"], g["variant_items"])
    cs.verify(sel)
    jdump(sel, o / "select.json")
    print(sel["label"])
    return 0


def stage_test(a):
    cell_env.require_platform_fixed(getattr(a, "addendum", None))
    addendum = getattr(a, "addendum", None)
    check_pd(a.perms, a.draws, addendum)
    o = out_dir(a)
    cell_env.check_environment()
    kind, window, labels, purpose, role = TESTS[a.name]
    sel = cs.require_variant(o / "select.json", a.variant or jload(o / "select.json")["variant_for_tests"], a.name)
    spec = dict(cg.VARIANTS)[sel["variant_for_tests"]]
    g = jload(o / "gate.json")
    now = cell_env.platform_record()
    diff = [k for k in ("platform", "python_build", "versions") if g.get("platform", {}).get(k) != now.get(k)]
    if diff and addendum is None:
        raise SystemExit("refused: the gate ran on a different platform or environment (%s differ); gate and tests must share one platform" % ", ".join(diff))
    val_rule = sel.get("val_rule")
    if val_rule not in ("round", "ceil"):
        raise SystemExit("refused: select.json has no validation size rule (G9 did not set one)")
    os.environ["CELL_VAL_RULE"] = val_rule
    sessions, rs = load_sessions(a, o)
    sessions = cp.with_window(sessions, window)
    bins = [s.true_bin if labels == "true" else s.belief_bin for s in sessions]
    if labels == "true":
        ok, msg = ct.check_true_labels(sessions, bins)
        if not ok:
            raise SystemExit("true-template labels are not constant within blocks (%s): not interpretable" % msg)
    rois = cg.ROIS
    n_perm = a.perms
    part = o / ("%s.partial.jsonl" % a.name)
    header = make_header(a.name, sel["variant_for_tests"], spec["grid"], window, n_perm, a.draws, val_rule, addendum)
    done = read_partial(part, header)
    todo = [i for i in range(0, n_perm + 1) if i not in done]
    jobs = [("obs" if i == 0 else kind, i, sessions, bins, rois, rs, a.draws, "across", spec["as_written"], purpose, spec["grid"]) for i in todo]
    from concurrent.futures import ProcessPoolExecutor
    with open(part, "a") as f:
        if not done and part.stat().st_size == 0:
            f.write(json.dumps({"header": _clean(header)}) + "\n")
            f.flush()
        if a.workers > 1:
            with ProcessPoolExecutor(a.workers) as ex:
                it = ex.map(ct.one_labelling, jobs, chunksize=1)
                for r in it:
                    _append(f, r, done)
        else:
            for j in jobs:
                _append(f, ct.one_labelling(j), done)
    out = [(d["i"], {r: (np.nan if d["stat"][r] is None else d["stat"][r]) for r in rois}, d["n_prog"], d["n_neurons"], d["hp"]) for d in (done[i] for i in range(n_perm + 1))]
    res = ct.collect(out, rois)
    raw = np.array([res[r]["p"] for r in rois])
    tested = all(res[r]["status"] == "tested" for r in rois)
    holm = ct.holm(raw) if tested else np.full(3, np.nan)
    rec = {"test": a.name, "role": role, "kind": kind, "window": window, "labels": labels, "P": n_perm, "D": a.draws,
           "variant": sel["variant_for_tests"], "selection_label": sel["label"],
           "regions": {r: {"observed": res[r]["observed"], "null": res[r]["null"], "p": res[r]["p"], "p_holm": float(holm[k]) if tested else None,
                           "status": res[r]["status"]} for k, r in enumerate(rois)},
           "val_rule": val_rule, "addendum": addendum, "design_obs": res["design_obs"], "design_null": res["design_null"], "chosen_C_at_upper_edge": res["hp"],
           "platform": cell_env.platform_record()}
    jdump(rec, o / ("test-%s.json" % a.name))
    print("%s: p %s, Holm %s" % (a.name, dict(zip(rois, raw.round(4))), holm.round(4)))
    return 0


def _append(f, r, done):
    i, st, npg, nn, hp = r
    d = {"i": i, "stat": {k: (None if not np.isfinite(v) else float(v)) for k, v in st.items()}, "n_prog": npg, "n_neurons": nn, "hp": hp}
    f.write(json.dumps(d) + "\n")
    f.flush()
    done[i] = d


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["determinism", "inspect", "gate", "select", "test"])
    ap.add_argument("--extract-root")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--name", choices=sorted(TESTS))
    ap.add_argument("--perms", type=int, default=P_DEFAULT)
    ap.add_argument("--draws", type=int, default=D_DEFAULT)
    ap.add_argument("--variant")
    ap.add_argument("--addendum", help="dated name (YYYY-MM-DD in it) that allows P or D other than the design's; recorded in the header and output")
    ap.add_argument("--cache", action="store_true", help="cache the loaded sessions in the out folder")
    a = ap.parse_args(argv)
    if a.stage in ("inspect", "gate", "test") and not a.extract_root:
        raise SystemExit("--extract-root is required")
    if a.stage == "test" and not a.name:
        raise SystemExit("--name is required")
    return {"determinism": stage_determinism, "inspect": stage_inspect, "gate": stage_gate, "select": stage_select, "test": stage_test}[a.stage](a)


if __name__ == "__main__":
    sys.exit(main())
