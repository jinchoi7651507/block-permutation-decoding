"""Checks of the Addendum 2 wrapper without data (synthetic .mat files only).
Run: python -I test_run_cell_a2.py"""
import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.io import savemat

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_cell_a2 as a2  # noqa: E402
from cell_gate import GATE_VARS, read_gate_file  # noqa: E402

FIRST, SECOND = list(a2.CANDIDATES)


def refused(fn, text):
    try:
        fn()
    except SystemExit as e:
        return text in str(e)
    return False


def write(root, member, with_vars):
    p = Path(root) / member
    p.parent.mkdir(parents=True, exist_ok=True)
    d = {v: np.full((3, 100), 0.5) for v in GATE_VARS.values()} if with_vars else {"other": np.zeros(2)}
    savemat(p, d)
    return p


def case(first_has, second_has):
    root = Path(tempfile.mkdtemp())
    p1, p2 = write(root, FIRST, first_has), write(root, SECOND, second_has)
    a2.CANDIDATES = {FIRST: a2.crc32_of(p1), SECOND: a2.crc32_of(p2)}
    return root, p1, p2


checks = {}
a2.rc.cell_env.require_platform_fixed = lambda *args, **kw: None     # this check only: the laptop is not the design platform
empty = Path(tempfile.mkdtemp())
checks["entry point: stages use the wrapper's gate file (missing file refused)"] = refused(
    lambda: a2.main(["inspect", "--extract-root", str(empty), "--out", str(empty / "out")]), "addendum 2 gate file missing")
checks["entry point: --addendum refused"] = refused(lambda: a2.main(["gate", "--extract-root", "x", "--addendum", "2026-11-08-a2"]), "without --addendum")
checks["entry point: --addendum=... and abbreviations refused"] = all(refused(lambda f=f: a2.main(["gate", "--extract-root", "x", f]), "without --addendum") for f in ("--addendum=2026-11-08-a2", "--add=2026-11-08-a2"))
root, p1, p2 = case(True, False)
ns = argparse.Namespace(extract_root=str(root))
checks["first candidate with the variables is the gate file"] = a2.data_paths(ns)[1] == p1
root, p1, p2 = case(False, True)
ns = argparse.Namespace(extract_root=str(root))
checks["second candidate used when the first lacks the variables"] = a2.data_paths(ns)[1] == p2
root, p1, p2 = case(False, False)
ns = argparse.Namespace(extract_root=str(root))
gate = a2.data_paths(ns)[1]
checks["neither holds them: the stamped gate stops"] = gate == p1 and refused(lambda: read_gate_file(gate), "gate file lacks")
root, p1, p2 = case(True, False)
p1.write_bytes(p1.read_bytes() + b"x")
checks["altered gate file refused"] = refused(lambda: a2.data_paths(argparse.Namespace(extract_root=str(root))), "CRC-32 differs")
root, p1, p2 = case(True, False)
savemat(Path(root) / a2.COMBINED_FILE, {v.replace("_net", "_combined"): np.full((100, 3), 0.25) for v in GATE_VARS.values()})
a2.compare_names(str(root), str(root))
checks["compare-names writes the largest difference per region"] = (Path(root) / "a2_net_vs_combined.json").read_text().count("0.25") == 3
_, stamped_gate = a2.STAMPED_DATA_PATHS(argparse.Namespace(extract_root="x"))
checks["stamped data_paths unchanged"] = stamped_gate.name == "Figure_2_decoding_accuracy.mat"
for k, v in checks.items():
    print("%s %s" % ("PASS" if v else "FAIL", k))
assert all(checks.values())
print("all checks passed")
