"""Addendum 2 (2026-11-08): the gate reads the authors' Fig. 2D values from Figure_2/plot_figure_2/Figure_2.mat.

The stamped design names Figure_2_decoding_accuracy.mat as the gate file; that file has no *_mean_classification_net
variables. The authors' Plot_Figure_2_github.m loads Figure_2.mat, Figure_2_PCA.mat and Figure_2_decoding_accuracy.mat
and plots Fig. 2D from *_mean_classification_net. This wrapper runs the stamped run_cell.py unchanged; it only makes
run_cell.data_paths return the gate file: the first of Figure_2.mat and Figure_2_PCA.mat (in that order) that holds
all three variables with shape (3, 100) or (100, 3). If neither does, the stamped gate stops as before. Variable names
and every gate rule are unchanged. Run every stage through this wrapper without --addendum.

    python -I run_cell_a2.py fetch-gate --extract-root ROOT       extract the two candidate files (CRC-32 checked)
    python -I run_cell_a2.py STAGE [run_cell.py options]          inspect, gate, select or test with this gate file
    python -I run_cell_a2.py compare-names --extract-root ROOT --out OUT
        descriptive, after the gate: largest absolute difference per region between *_mean_classification_net (gate
        file) and *_mean_classification_combined (Figure_2_decoding_accuracy.mat); written to OUT/a2_net_vs_combined.json
"""
import json
import sys
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch_members as fm  # noqa: E402
import run_cell as rc  # noqa: E402
from cell_gate import GATE_VARS  # noqa: E402
from cell_loader import read_mat  # noqa: E402

GATE_ZIP = "https://zenodo.org/records/10529801/files/Figure_2.zip?download=1"
GATE_ZIP_SIZE = 4637807                                    # zenodo-files-10529801.tsv
CANDIDATES = {"Figure_2/plot_figure_2/Figure_2.mat": "ab452acd",          # manifest-zenodo-10529801-figure-zips.tsv
              "Figure_2/plot_figure_2/Figure_2_PCA.mat": "fcbe3358"}
COMBINED_FILE = "Figure_2/plot_figure_2/Figure_2_decoding_accuracy.mat"
STAMPED_DATA_PATHS = rc.data_paths


def crc32_of(path):
    crc = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            crc = zlib.crc32(chunk, crc)
    return "%08x" % crc


def holds_gate_vars(path):
    m = read_mat(path)
    return all(v in m and np.asarray(m[v]).shape in ((3, 100), (100, 3)) for v in GATE_VARS.values())


def gate_file_of(root):
    """First candidate, in order, with the listed CRC-32 that holds the three gate variables; None if neither."""
    for member, crc in CANDIDATES.items():
        p = Path(root) / member
        if not p.is_file() or crc32_of(p) != crc:
            raise SystemExit("addendum 2 gate file missing or its CRC-32 differs from %s: %s" % (crc, p))
        if holds_gate_vars(p):
            return p
    return None


def data_paths(a):
    root, stamped_gate = STAMPED_DATA_PATHS(a)
    chosen = gate_file_of(a.extract_root)
    return root, chosen if chosen is not None else Path(a.extract_root) / next(iter(CANDIDATES))   # None: gate stops


def compare_names(root, out):
    net = read_mat(gate_file_of(root))
    comb = read_mat(Path(root) / COMBINED_FILE)
    diff = {}
    for roi, var in GATE_VARS.items():
        a = np.asarray(net[var], float)
        b = np.asarray(comb[var.replace("_net", "_combined")], float)
        b = b.T if b.shape != a.shape else b
        diff[roi] = float(np.nanmax(np.abs(a - b))) if b.shape == a.shape else "shapes differ: %s vs %s" % (a.shape, b.shape)
    Path(out, "a2_net_vs_combined.json").write_text(json.dumps(diff, indent=1))
    print(diff)


def main(argv):
    if argv[:1] == ["fetch-gate"]:
        root = argv[argv.index("--extract-root") + 1]
        members = list(CANDIDATES)
        fm.DATA_ALLOWED = tuple(members)
        sys.argv = ["fetch_members.py", "--url", GATE_ZIP, "--size", str(GATE_ZIP_SIZE), "extract", "--data", root] + members
        fm.main()
        for member, crc in CANDIDATES.items():
            print("%s crc32 %s (expected %s)" % (member, crc32_of(Path(root) / member), crc))
        return 0
    if argv[:1] == ["compare-names"]:
        compare_names(argv[argv.index("--extract-root") + 1], argv[argv.index("--out") + 1])
        return 0
    if any(x.startswith("--a") for x in argv):     # --addendum, --addendum=... and abbreviations (no other runner option starts with --a)
        raise SystemExit("addendum 2: run the stages without --addendum (P, D and the platform checks stay in force)")
    rc.data_paths = data_paths
    return rc.main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
