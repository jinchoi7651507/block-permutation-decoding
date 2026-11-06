#!/usr/bin/env python3
"""Step 2b preprocessing (DESIGN.md v2 §3; addendum DESIGN-v2-ADDENDUM.md). Labels are not used here.

Per subject (raw BrainVision files in LEMON_DIR):
  blocks  condition segments from the marker file (S200 = eyes open, S210 = eyes closed; markers repeat every 2 s
          inside a segment). Block k runs from its first marker to the earlier of the next segment's first marker
          and its own last marker + 2 s.
  crop    from the first block onset to the last block end, then resample to 250 Hz.
  cleaned (primary)  band-pass 1-45 Hz (FIR, MNE defaults), 50 Hz notch; inter-block gaps annotated BAD_gap and
          left out of the channel statistics and the ICA fit; bad channels = flat (peak-to-peak below 1 uV inside
          the blocks) or local robust z > 5 (log variance minus the median of its 4 nearest non-flat neighbours; robust z of
          these differences, median and 1.4826 MAD over the non-flat channels; one-sided),
          interpolated (standard_1005 positions) before the average reference of the 61 EEG channels; ICA (20
          components, FastICA, random_state 20261021) fitted on these 1-45 Hz data, components with |r| > 0.5 against
          VEOG removed; epochs with EEG peak-to-peak > 150 uV rejected after ICA. Logged: robust z, flat channels, ICA
          iterations, VEOG amplitude, pseudo-HEOG (F7 - F8) correlations, the 50 Hz line ratio of the cleaned PSD.
  minimal (sensitivity)  band-pass 1-45 Hz, average reference, 300 uV rejection, no notch, interpolation or ICA.
  epochs  non-overlapping 2-s windows inside each block, skipping the first 5 s and the last 2 s (sensitivity:
          2 s and 2 s).
  features log band power per EEG channel (delta 1-4, theta 4-8, alpha 8-13, beta 13-30, gamma 30-45 Hz; Welch,
          1-s windows, 50% overlap) -> 61 x 5 = 305 features.
Outputs per subject: <out>/<subject>.npz with, for each pipeline x skip variant, the feature matrix, block index and
condition (EC = 1, EO = 0) of every kept epoch; <out>/<subject>.qc.json (blocks, bad channels, ICA components and
correlations, epochs kept per block, posterior alpha EC/EO ratio, versions).

  python preprocess.py --subjects ../eligibility/SUBJECTS.txt --out <features dir> [--worker k --of n]
"""
import argparse
import json
import os
import re
from pathlib import Path

import mne
import numpy as np
import scipy
import sklearn

LEMON_DIR = Path(os.environ.get("LEMON_DIR", "/Users/jinchoi/Downloads/trackA-school/lemon/raw"))
FS = 250.0
BANDS = ((1, 4), (4, 8), (8, 13), (13, 30), (30, 45))
POSTERIOR = ("O1", "Oz", "O2", "PO3", "POz", "PO4", "PO7", "PO8", "P3", "Pz", "P4")
VARIANTS = {"cleaned_s5": ("cleaned", 5.0, 2.0), "cleaned_s2": ("cleaned", 2.0, 2.0),
            "minimal_s5": ("minimal", 5.0, 2.0), "minimal_s2": ("minimal", 2.0, 2.0)}
mne.set_log_level("ERROR")


def blocks_from_markers(vmrk, fs_raw):
    mk = []
    for line in vmrk.splitlines():
        m = re.match(r"Mk\d+=([^,]*),([^,]*),(\d+),", line)
        if m and m.group(2).replace(" ", "") in ("S200", "S210"):
            mk.append((m.group(2).replace(" ", ""), int(m.group(3)) - 1))       # BrainVision positions are 1-based
    seg = []
    for d, p in mk:
        if not seg or seg[-1]["code"] != d:
            seg.append({"code": d, "start": p, "last": p})
        else:
            seg[-1]["last"] = p
    two_s = int(round(2.0 * fs_raw))
    for i, s in enumerate(seg):
        own_end = s["last"] + two_s
        s["end"] = min(seg[i + 1]["start"], own_end) if i + 1 < len(seg) else own_end
        s["cond"] = 1 if s["code"] == "S210" else 0
    return seg


def band_features(data):
    """data: epochs x channels x samples (V) -> epochs x (channels * 5) log band power."""
    psd, freqs = mne.time_frequency.psd_array_welch(data, sfreq=FS, fmin=1.0, fmax=45.0, n_fft=int(FS),
                                                    n_per_seg=int(FS), n_overlap=int(FS / 2), verbose=False)
    out = []
    for lo, hi in BANDS:
        sel = (freqs >= lo) & (freqs < hi) if hi < 45 else (freqs >= lo) & (freqs <= hi)
        out.append(np.log(psd[:, :, sel].mean(axis=2)))
    return np.concatenate(out, axis=1)                                       # band-major: [delta ch1..61, theta ...]


def epochs_for(raw, seg, t0, skip_start, skip_end, ptp_uv):
    eeg = raw.copy().pick("eeg")
    x = eeg.get_data()
    n_win = int(2 * FS)
    feats_idx, blk, cond, rej = [], [], [], {}
    windows = []
    for k, s in enumerate(seg):
        a = (s["start"] / s["fs_raw"] - t0) + skip_start
        b = (s["end"] / s["fs_raw"] - t0) - skip_end
        i = int(round(a * FS))
        kept = rejected = 0
        while i + n_win <= int(round(b * FS)) and i + n_win <= x.shape[1]:
            w = x[:, i:i + n_win]
            if np.ptp(w, axis=1).max() * 1e6 > ptp_uv:
                rejected += 1
            else:
                windows.append(w)
                blk.append(k)
                cond.append(s["cond"])
                kept += 1
            i += n_win
        rej[k] = {"kept": kept, "rejected": rejected}
    data = np.stack(windows) if windows else np.zeros((0, x.shape[0], n_win))
    return data, np.array(blk), np.array(cond), rej, eeg.ch_names


def preprocess(subject, out):
    vhdr = LEMON_DIR / f"{subject}.vhdr"
    vmrk = (LEMON_DIR / f"{subject}.vmrk").read_text(encoding="latin-1")
    raw = mne.io.read_raw_brainvision(vhdr, preload=False)
    fs_raw = raw.info["sfreq"]
    seg = blocks_from_markers(vmrk, fs_raw)
    for s in seg:
        s["fs_raw"] = fs_raw
    t0 = seg[0]["start"] / fs_raw
    t1 = min(seg[-1]["end"] / fs_raw, raw.times[-1])
    raw.crop(tmin=t0, tmax=t1).load_data()
    raw.set_channel_types({"VEOG": "eog"})
    raw.resample(FS)
    raw.set_montage("standard_1005", on_missing="raise")
    qc = {"subject": subject, "n_blocks": len(seg), "first": "EC" if seg[0]["cond"] else "EO",
          "blocks": [{"cond": "EC" if s["cond"] else "EO", "dur_s": round((s["end"] - s["start"]) / fs_raw, 2)} for s in seg],
          "versions": {"mne": mne.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
                       "sklearn": sklearn.__version__}}
    res = {}
    # minimal
    mini = raw.copy().filter(1.0, 45.0, picks=["eeg", "eog"]).set_eeg_reference("average")
    # cleaned
    cl = raw.copy().filter(1.0, 45.0, picks=["eeg", "eog"]).notch_filter(50.0, picks=["eeg", "eog"])
    # samples inside blocks (inter-block gaps excluded from channel statistics and from the ICA fit; review S2)
    inside = np.zeros(cl.n_times, bool)
    on, du = [], []
    prev_end = None
    for s in seg:
        a = int(round((s["start"] / fs_raw - t0) * FS))
        b = int(round((s["end"] / fs_raw - t0) * FS))
        inside[max(a, 0):min(b, cl.n_times)] = True
        if prev_end is not None and a > prev_end:
            on.append(prev_end / FS)
            du.append((a - prev_end) / FS)
        prev_end = b
    if on:
        cl.set_annotations(mne.Annotations(on, du, ["BAD_gap"] * len(on)))
    eeg_only = cl.copy().pick("eeg")
    x = eeg_only.get_data()[:, inside]
    names = eeg_only.ch_names                                            # names of the picked channels (review M1)
    assert len(names) == x.shape[0] == 61 and "VEOG" not in names
    ptp = np.ptp(x, axis=1) * 1e6
    flat = ptp < 1.0
    # local robust z (re-review of M2): each channel's log variance minus the median over its 4 nearest neighbours
    # (standard_1005 positions, flat neighbours excluded); robust z of these differences over the non-flat channels.
    # Spatially broad physiological signals (posterior alpha, frontal blinks) are shared with the neighbours and do
    # not count; a single deviating channel does.
    pos = np.array([eeg_only.info["chs"][i]["loc"][:3] for i in range(len(names))])
    lv = np.full(len(names), np.nan)
    lv[~flat] = np.log(np.var(x[~flat], axis=1))
    dist = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2)
    local = np.full(len(names), np.nan)
    for i in np.where(~flat)[0]:
        nb = [j for j in np.argsort(dist[i]) if j != i and not flat[j]][:4]
        local[i] = lv[i] - np.median(lv[nb])
    ok_ = np.isfinite(local)
    med = np.median(local[ok_])
    mad = 1.4826 * np.median(np.abs(local[ok_] - med))
    rz = np.full(len(names), np.nan)
    rz[ok_] = (local[ok_] - med) / mad if mad > 0 else 0.0
    bads = [names[i] for i in range(len(names)) if flat[i] or (np.isfinite(rz[i]) and rz[i] > 5)]
    cl.info["bads"] = bads
    if bads:
        cl.interpolate_bads(reset_bads=True)
    cl.set_eeg_reference("average")
    ica = mne.preprocessing.ICA(n_components=20, method="fastica", random_state=20261021, max_iter=1000)
    ica.fit(cl, picks="eeg", reject_by_annotation=True)
    src = ica.get_sources(cl).get_data()[:, inside]
    veog = cl.copy().pick("eog").get_data()[0][inside]
    r = np.array([np.corrcoef(src[i], veog)[0, 1] for i in range(src.shape[0])])
    eegd = cl.copy().pick("eeg")
    heog = (eegd.get_data(picks=["F7"])[0] - eegd.get_data(picks=["F8"])[0])[inside]   # pseudo-HEOG (review S4), logged only
    rh = np.array([np.corrcoef(src[i], heog)[0, 1] for i in range(src.shape[0])])
    excl = [int(i) for i in np.where(np.abs(r) > 0.5)[0]]
    ica.exclude = excl
    ica.apply(cl)
    psd, fr = mne.time_frequency.psd_array_welch(cl.copy().pick("eeg").get_data()[:, inside], sfreq=FS, fmin=1.0, fmax=60.0,
                                                 n_fft=int(FS), verbose=False)
    m = psd.mean(axis=0)
    line = m[(fr >= 49) & (fr <= 51)].mean() / m[(fr >= 40) & (fr <= 44)].mean()
    qc.update({"local_robust_z_log_variance": [None if not np.isfinite(v) else round(float(v), 2) for v in rz],
               "flat_channels": [names[i] for i in np.where(flat)[0]],
               "ica_n_iter": int(getattr(ica, "n_iter_", -1)),
               "ica_converged": bool(0 <= int(getattr(ica, "n_iter_", -1)) < 1000),   # n_iter = max_iter means not converged (EEG re-review)
               "mad_zero": bool(not mad > 0),                                          # robust z set to 0 (EEG re-review COULD)
               "ica_pseudo_heog_r": [round(float(v), 3) for v in rh],
               "veog_ptp_uv": round(float(np.ptp(veog) * 1e6), 1), "veog_sd_uv": round(float(np.std(veog) * 1e6), 2),
               "psd_50Hz_over_40_44Hz": round(float(line), 4), "gap_seconds_total": round(float(sum(du)), 2)})
    qc.update({"bad_channels": bads, "ica_veog_r": [round(float(v), 3) for v in r], "ica_excluded": excl})
    for name, (pipe, s_start, s_end) in VARIANTS.items():
        src_raw, thr = (cl, 150.0) if pipe == "cleaned" else (mini, 300.0)
        data, blk, cond, rej, chs = epochs_for(src_raw, seg, t0, s_start, s_end, thr)
        feats = band_features(data) if len(data) else np.zeros((0, 305))
        res[f"{name}_X"], res[f"{name}_block"], res[f"{name}_cond"] = feats.astype(np.float32), blk, cond
        qc[f"{name}_epochs"] = rej
        if name == "cleaned_s5" and len(data):
            post = [chs.index(c) for c in POSTERIOR if c in chs]
            alpha = feats[:, 2 * len(chs):3 * len(chs)][:, post].mean(axis=1)    # log alpha, posterior mean
            ec, eo = alpha[cond == 1].mean(), alpha[cond == 0].mean()
            qc["posterior_log_alpha_EC_minus_EO"] = round(float(ec - eo), 4)
            qc["alpha_check_EC_gt_EO"] = bool(ec > eo)
    res["channels"] = np.array(chs)
    np.savez_compressed(out / f"{subject}.npz", **res)
    (out / f"{subject}.qc.json").write_text(json.dumps(qc, indent=1))
    return qc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    subs = [s.strip() for s in Path(args.subjects).read_text().splitlines() if s.strip()]
    for i, s in enumerate(subs):
        if i % args.of != args.worker or (out / f"{s}.qc.json").exists():
            continue
        qc = preprocess(s, out)
        print(s, qc["n_blocks"], qc["first"], "bads", qc["bad_channels"], "ica", qc["ica_excluded"], flush=True)


if __name__ == "__main__":
    main()
