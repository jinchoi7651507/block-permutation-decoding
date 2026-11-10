"""Reproduction gate for the Cell reanalysis (DESIGN.md section 6). Pure functions plus `run_gate`.
Every item is a dict {name, core, stops, passed, detail}. `stops` marks the items whose failure stops all tests
(G1, G2, G3, G9); G7 and G8 stop only the true-template tests; G4 and G5 decide the variant (cell_select)."""
from __future__ import annotations

import csv
import zlib
from pathlib import Path

import cell_env  # noqa: F401
import numpy as np

import cellport as cp
import cell_tests as ct

# published or stated numbers (DESIGN.md section 6)
PUB = {"sessions": 17, "blocks": 171, "templates_per_session": (5, 16),
       "est_neurons": 100, "est_prog": 61,                  # Methods, Fig. 2D (estimated template)
       "s3g_neurons": 113, "s3g_prog": 76,                  # Fig. S3G legend (true template)
       "val_grids": (("round", 36), ("ceil", 39)),          # 3 bins x n_val: round(0.2 x 61) = 12 gives 1/36, ceil gives 13 and 1/39
       "n_val_s3g": {"round": 15, "ceil": 16},             # round or ceil of 0.2 x 76
       "tol_region": 0.03, "tol_cell": 0.05, "min_cells": 8, "z_alpha": 0.01, "sd_factor": 2.0}
ROIS = ["LIP", "FEF", "LPFC"]
GATE_VARS = {"LIP": "LIP_mean_classification_net", "FEF": "FEF_mean_classification_net", "LPFC": "PFC_mean_classification_net"}
VARIANTS = [("as_written", {"as_written": True, "grid": "coarse"}),
            ("V1_intended", {"as_written": False, "grid": "coarse"}),
            ("V2_fine_grid", {"as_written": True, "grid": "fine"})]


def item(name, core, stops, passed, detail):
    return {"name": name, "core": core, "stops": stops, "passed": bool(passed), "detail": detail}


# ----------------------------------------------------------------------------- G1
def crc32_file(path, chunk=1 << 20):
    c = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            c = zlib.crc32(b, c)
    return "%08x" % (c & 0xFFFFFFFF)


def g1_integrity(members_tsv, root, roles=None):
    """Every listed member (optionally only these roles) exists under root and has the listed CRC-32. A row whose
    crc32 is not 8 hex digits is an error, not a skipped line."""
    bad, n = [], 0
    for r in csv.DictReader(open(members_tsv), delimiter="\t"):
        if roles and r["role"] not in roles:
            continue
        n += 1
        crc = r["crc32"].strip().lower()
        p = Path(root) / r["member"]
        if len(crc) != 8 or any(ch not in "0123456789abcdef" for ch in crc):
            bad.append("%s: malformed crc32 %r" % (r["member"], r["crc32"]))
        elif not p.is_file():
            bad.append("%s: missing" % r["member"])
        elif crc32_file(p) != crc:
            bad.append("%s: crc32 differs" % r["member"])
    return item("G1 file integrity", True, True, n > 0 and not bad, "%d members checked; %d problems %s" % (n, len(bad), bad[:5]))


# ----------------------------------------------------------------------------- G2, G3, G7, G8
def g2_sessions(sessions):
    nb = [len(np.unique(s.block)) for s in sessions]
    lo, hi = PUB["templates_per_session"]
    ok = len(sessions) == PUB["sessions"] and sum(nb) == PUB["blocks"] and all(lo <= n <= hi for n in nb)
    return item("G2 sessions and blocks", True, True, ok,
                "%d sessions, %d blocks, per session %s (stated: 17, 171, 5 to 16; the split 69/102 by monkey is not in the files)" % (len(sessions), sum(nb), nb))


def design_counts(sessions, roi_sessions, which):
    bins = [s.belief_bin if which == "estimated" else s.true_bin for s in sessions]
    d = cp.build_design(sessions, bins, ROIS, roi_sessions)
    return {"n_prog": d["n_prog"], "n_neurons": d["n_neurons"], "n_qual": d["n_qual"]}


def g3_estimated_counts(sessions, roi_sessions):
    d = design_counts(sessions, roi_sessions, "estimated")
    ok = d["n_neurons"] == PUB["est_neurons"] and d["n_prog"] == PUB["est_prog"]
    return item("G3 design counts, estimated template", True, True, ok,
                "N_neurons %s, N_progression %s (stated 100 and 61; Fig. 2D)" % (d["n_neurons"], d["n_prog"]))


S3G_LEGEND_WORDING = "estimated template color bin"


def g7_s3g_counts(sessions, roi_sessions, rule="round"):
    """Fig. S3G legend: 113 neurons per region, 76 trials per progression level and colour bin, three levels, three
    bins, 80/20 split. The split gives 15 (rule round) or 16 (rule ceil) validation trials per cell; the rule is the one
    fixed by G9 from the gate file."""
    d = design_counts(sessions, roi_sessions, "true")
    n_va = None if d["n_prog"] is None else cp.n_val(d["n_prog"], rule)
    ok = (d["n_neurons"] == PUB["s3g_neurons"] and d["n_prog"] == PUB["s3g_prog"]
          and cp.N_PROG == 3 and cp.N_BINS == 3 and n_va == PUB["n_val_s3g"][rule])
    detail = ("N_neurons %s, N_progression %s, validation per cell %s (stated 113, 76, 80/20 so %d with rule %s; three levels, three bins)"
              % (d["n_neurons"], d["n_prog"], n_va, PUB["n_val_s3g"][rule], rule))
    if not ok:
        detail += '; the S3G legend wording: "%s"' % S3G_LEGEND_WORDING
    return item("G7 design counts, true template (Fig. S3G)", True, False, ok, detail)


def g8_true_labels(sessions, roi_sessions):
    ok, msg = ct.check_true_labels(sessions, [s.true_bin for s in sessions])
    d = design_counts(sessions, roi_sessions, "true")
    defined = d["n_prog"] is not None
    return item("G8 true-template labelling constant within blocks, design defined", True, False, ok and defined,
                "%s; design %s (N_neurons %s, N_progression %s)" % (msg, "defined" if defined else "undefined", d["n_neurons"], d["n_prog"]))


# ----------------------------------------------------------------------------- gate file, G9
def read_gate_file(path):
    from cell_loader import read_mat
    m = read_mat(path)
    out = {}
    for roi, var in GATE_VARS.items():
        if var not in m:
            raise SystemExit("gate file lacks %s; variables found: %s (a dated addendum must map the names)" % (var, [k for k in m if not k.startswith("_")]))
        a = np.asarray(m[var], float)
        if a.shape == (100, 3):
            a = a.T
        if a.shape != (3, 100):
            raise SystemExit("gate variable %s has shape %s, expected (3, 100)" % (var, a.shape))
        out[roi] = a
    return out


def val_rule_from_gate(pub):
    """Fixed rule, data-driven: if every published gate value is a multiple of 1/36 the validation size is round(0.2 N)
    (12 per cell for N = 61); else if every value is a multiple of 1/39 it is ceil(0.2 N) (13); else None. 1/36 is tried
    first, so values that fit both grids (for example only 0, 1/3, 2/3, 1) take round."""
    vals = np.concatenate([np.asarray(a).ravel() for a in pub.values()])
    fits = lambda g: bool(np.all(np.abs(vals * g - np.round(vals * g)) < 1e-6))
    for rule, g in PUB["val_grids"]:
        if fits(g):
            return rule, g
    return None, None


def g9_validation_size(pub):
    """Run before any port draw: the published accuracies are means over 3 x n_va validation trials per level. Multiples
    of 1/36 give rule round (n_va = 12), multiples of 1/39 give rule ceil (n_va = 13); stop only if neither grid fits,
    and report the smallest grid that fits. The item carries the chosen rule in `val_rule`."""
    vals = np.concatenate([a.ravel() for a in pub.values()])
    fits = lambda g: bool(np.all(np.abs(vals * g - np.round(vals * g)) < 1e-6))
    implied = next((n for n in range(1, 41) if fits(3 * n)), None)
    rule, grid = val_rule_from_gate(pub)
    it = item("G9 validation size from the gate file", True, True, rule is not None,
              "%d values; multiples of 1/36: %s, of 1/39: %s; rule %s; smallest grid 1/(3 x n_val) that fits: n_val = %s"
              % (len(vals), fits(36), fits(39), rule, implied))
    it["val_rule"] = rule
    return it


# ----------------------------------------------------------------------------- G4, G5, G6
def accuracy_items(port, pub):
    """port: roi -> (n_draws, 3) validation accuracy per level; pub: roi -> (3, 100)."""
    reg, cells = {}, {}
    for r in ROIS:
        pm = np.asarray(port[r]).mean(0)          # per level
        um = pub[r].mean(1)
        reg[r] = abs(float(np.mean(port[r])) - float(np.mean(pub[r])))
        cells[r] = np.abs(pm - um)
    n_cell_ok = int(sum(np.sum(c <= PUB["tol_cell"]) for c in cells.values()))
    reg_ok = all(v <= PUB["tol_region"] for v in reg.values())
    g4 = item("G4 accuracy, across decoder", True, False, reg_ok and n_cell_ok >= PUB["min_cells"],
              "region mean differences %s (tolerance 0.03); %d of 9 cells within 0.05 (need 8)" % ({k: round(v, 4) for k, v in reg.items()}, n_cell_ok))
    pz = {r: [cp.z_test(np.asarray(port[r])[:, k]) for k in range(3)] for r in ROIS}
    g5 = item("G5 verdict pattern (z-test)", True, False, all(p < PUB["z_alpha"] for v in pz.values() for p in v),
              "z-test p per region and level %s (need all < 0.01)" % {k: [float("%.2g" % p) for p in v] for k, v in pz.items()})
    ratios = {r: float(np.mean(np.std(np.asarray(port[r]), axis=0, ddof=1)) / np.mean(np.std(pub[r], axis=1, ddof=1))) for r in ROIS}
    g6 = item("G6 spread (SD over draws)", False, False, all(1 / PUB["sd_factor"] <= v <= PUB["sd_factor"] for v in ratios.values()),
              "port SD / published SD per region %s (within a factor of 2)" % {k: round(v, 2) for k, v in ratios.items()})
    return [g4, g5, g6]


# ----------------------------------------------------------------------------- descriptive items
def blocks_per_bin(sessions, roi_sessions):
    """Descriptive (G10): mean number of blocks per true-template bin, per ROI, over the sessions of the ROI."""
    out = {}
    for r in ROIS:
        v = []
        for si in roi_sessions[r]:
            s = sessions[si]
            _, lab = ct.block_labels(s.block, s.true_bin)
            v.append(np.mean([np.sum(lab == c) for c in (1, 2, 3)]))
        out[r] = float(np.mean(v)) if v else None
    return out


# ----------------------------------------------------------------------------- draws for the gate
def _gate_job(args):
    sessions, design, roi, idx, variant, as_written, grid, purpose = args
    out, hp = [], []
    for d in idx:
        rng = ct.rng_for(purpose, 10 + ROIS.index(roi), d)
        out.append(cp.decode_draw(sessions, design, roi, rng, variant, as_written, grid, hp))
    return roi, idx, np.array(out), hp


def gate_draws(sessions, roi_sessions, bins, n_draws, purpose, spec, workers=1, variant="across", chunk=5):
    """n_draws pseudo-population draws per ROI for one labelling, one stream per (purpose, ROI, draw index), so the
    result does not depend on the number of workers. Returns (acc roi -> (n_draws, 3), hp roi -> [fits, at top], design)."""
    des = cp.build_design(sessions, bins, ROIS, roi_sessions)
    if des["n_prog"] is None:
        return None, None, des
    jobs = []
    for r in ROIS:
        for a in range(0, n_draws, chunk):
            jobs.append((sessions, des, r, list(range(a, min(a + chunk, n_draws))), variant, spec["as_written"], spec["grid"], purpose))
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            res = list(ex.map(_gate_job, jobs, chunksize=1))
    else:
        res = [_gate_job(j) for j in jobs]
    acc = {r: np.empty((n_draws, 3)) for r in ROIS}
    hp = {r: [] for r in ROIS}
    for roi, idx, a, h in res:
        acc[roi][idx] = a
        hp[roi] += h
    return acc, ct.hp_counts(hp), des
