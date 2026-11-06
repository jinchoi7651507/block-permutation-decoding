#!/usr/bin/env python3
"""Step 4 (DESIGN.md §2-§3): from one subject folder of the PyMVPA Haxby 2001 distribution (bold.nii.gz,
labels.txt, mask4_vt.nii.gz) to a feature file. Runs listed in DROP are removed before anything else (subj5,
chunk 8: corrupted, per the distribution's README). Writes <out>/<subject>.npz with, for the non-rest volumes in time
order: X_detrended (per-run linear detrend and z-score over all volumes of the run, rest included), X_raw, block
(0..K-1), run, category, and the per-block run and category; and <out>/<subject>.json with the block lengths, the
volumes kept per block (m) and whether the subject is included (with the reason if not). A subject is included only
if every run has 8 blocks, one per category, and the block count is 96 (88 for subj5).

  python prepare_haxby.py --subject-dir <data>/subj1 --subject subj1 --out <features dir>
"""
import argparse
import json
from pathlib import Path

import numpy as np

CATS = ("bottle", "cat", "chair", "face", "house", "scissors", "scrambledpix", "shoe")
DROP = {"subj5": [8]}
EXPECTED_BLOCKS = {"subj5": 88}


def read_labels(path):
    lines = [l.split() for l in Path(path).read_text().splitlines() if l.strip()]
    if lines[0][0].lower() in ("labels", "targets"):
        lines = lines[1:]
    lab = np.array([l[0] for l in lines])
    run = np.array([int(l[1]) for l in lines])
    return lab, run


def blocks_of(lab, run):
    """Block id per volume (-1 for rest): a maximal run of equal non-rest labels inside one run."""
    blk = np.full(len(lab), -1)
    b = -1
    for i in range(len(lab)):
        if lab[i] == "rest":
            continue
        if i == 0 or lab[i] != lab[i - 1] or run[i] != run[i - 1] or lab[i - 1] == "rest":
            b += 1
        blk[i] = b
    return blk


def preprocess(vox, run):
    """vox: volumes x voxels. Returns (X_detrended, X_raw) over all volumes."""
    from scipy.signal import detrend
    raw = vox.astype(float)
    det = np.empty_like(raw)
    for r in np.unique(run):
        idx = run == r
        d = detrend(raw[idx], axis=0, type="linear")
        sd = d.std(axis=0)
        sd[sd == 0] = 1.0
        det[idx] = (d - d.mean(axis=0)) / sd
    return det, raw


def build(vox, lab, run, subject):
    """vox: volumes x voxels (VT mask applied). Returns (features or None, info)."""
    if run.min() != 0 or sorted(np.unique(run)) != list(range(run.max() + 1)):
        return None, {"subject": subject, "included": False, "reason": f"run numbers {sorted(set(run.tolist()))}, expected 0..11"}
    keep_runs = ~np.isin(run, DROP.get(subject, []))
    info = {"subject": subject, "dropped_runs": DROP.get(subject, []),
            "labels_in_dropped_runs": {str(k): int(v) for k, v in zip(*np.unique(lab[~keep_runs], return_counts=True))}}
    vox, lab, run = vox[keep_runs], lab[keep_runs], run[keep_runs]
    det, raw = preprocess(vox, run)
    blk = blocks_of(lab, run)
    K = int(blk.max()) + 1
    b_run = np.array([run[blk == b][0] for b in range(K)])
    b_cat = np.array([lab[blk == b][0] for b in range(K)])
    lens = np.array([(blk == b).sum() for b in range(K)])
    info.update({"n_blocks": K, "block_lengths": lens.tolist(), "n_voxels": int(vox.shape[1]),
                 "runs": [int(r) for r in np.unique(b_run)]})
    reasons = [f"run {r}: blocks {sorted(b_cat[b_run == r].tolist())}" for r in np.unique(b_run)
               if sorted(b_cat[b_run == r].tolist()) != sorted(CATS)]
    if K != EXPECTED_BLOCKS.get(subject, 96):
        reasons.append(f"{K} blocks, expected {EXPECTED_BLOCKS.get(subject, 96)}")
    if reasons:
        info.update({"included": False, "reason": "; ".join(reasons)})
        return None, info
    m = int(lens.min())
    sel = np.sort(np.concatenate([np.where(blk == b)[0][:m] for b in range(K)]))   # the first m volumes of each block
    feat = {"X_detrended": det[sel], "X_raw": raw[sel], "block": blk[sel], "run": run[sel], "category": lab[sel],
            "block_run": b_run, "block_category": b_cat}
    info.update({"included": True, "m": m})
    return feat, info


def main():
    import nibabel as nib
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject-dir", required=True)
    ap.add_argument("--subject", required=True, choices=[f"subj{i}" for i in range(1, 7)])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = Path(a.subject_dir)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        lab, run = read_labels(d / "labels.txt")
        bold = np.asanyarray(nib.load(str(d / "bold.nii.gz")).dataobj)
        mask = np.asanyarray(nib.load(str(d / "mask4_vt.nii.gz")).dataobj) > 0
        assert bold.shape[3] == len(lab), f"{bold.shape[3]} volumes, {len(lab)} labels"
        feat, info = build(bold[mask].T, lab, run, a.subject)
    except Exception as e:                                  # any failure excludes the subject, with its reason
        feat, info = None, {"subject": a.subject, "included": False, "reason": f"exception {type(e).__name__}: {e}"}
    if feat is not None:
        np.savez_compressed(out / f"{a.subject}.npz", **feat)
    (out / f"{a.subject}.json").write_text(json.dumps(info, indent=1))
    print(json.dumps({k: info[k] for k in info if k != "block_lengths"}))


if __name__ == "__main__":
    main()
