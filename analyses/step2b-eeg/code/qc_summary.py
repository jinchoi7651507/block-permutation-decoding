#!/usr/bin/env python3
"""Step 2b QC summary (addendum DESIGN-v2-ADDENDUM.md §2-§3). Reads only the per-subject QC files written by
preprocess.py (no feature matrix, no label-dependent result). Prints, for the 40 main and the 5 pilot subjects:
first condition, bad and flat channels (count of subjects with Fp1/Fp2 or O1/Oz/O2 flagged), ICA convergence and
removed components, VEOG amplitude, 50 Hz line ratio, epochs per block (cleaned 5/2 s) and the subjects below the
20-epoch rule, and the posterior alpha check (EC > EO) with the addendum §3 rule applied.

  python qc_summary.py --features <dir> --out ../QC-NOTE.md
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ELIG = HERE.parent / "eligibility"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    main_s = [s.strip() for s in (ELIG / "SUBJECTS.txt").read_text().splitlines() if s.strip()]
    pilot_s = [s.strip() for s in (ELIG / "PILOT-SUBJECTS.txt").read_text().splitlines() if s.strip()]
    lines = ["# Step 2b preprocessing QC (qc_summary.py; QC files only, no label-dependent result)", ""]
    for name, subs in (("main", main_s), ("pilot", pilot_s)):
        qcs, missing = [], []
        for s in subs:
            f = Path(a.features) / f"{s}.qc.json"
            if f.exists():
                qcs.append(json.loads(f.read_text()))
            else:
                missing.append(s)
        n = len(qcs)
        fp = [q["subject"] for q in qcs if {"Fp1", "Fp2"} & set(q["bad_channels"])]
        oc = [q["subject"] for q in qcs if {"O1", "Oz", "O2"} & set(q["bad_channels"])]
        nconv = [q["subject"] for q in qcs if not q.get("ica_converged", True)]
        noica = [q["subject"] for q in qcs if not q["ica_excluded"]]
        madz = [q["subject"] for q in qcs if q.get("mad_zero")]
        low = []
        for q in qcs:
            kept = [v["kept"] for v in q["cleaned_s5_epochs"].values()]
            if min(kept) < 20:
                low.append((q["subject"], min(kept)))
        alpha_pass = [q["subject"] for q in qcs if q.get("alpha_check_EC_gt_EO")]
        share = len(alpha_pass) / n if n else float("nan")
        if name == "main":
            rule = ("codes swapped for all subjects" if share < 0.25 else
                    "codes unreliable: state-only arms reported as odd/even blocks" if share <= 0.75 else
                    "codes kept; failing subjects left out of the positive-control plot only")
        else:
            rule = "(pilot: not in the main tables)"
        nbad = [len(q["bad_channels"]) for q in qcs]
        lines += [f"## {name} ({n} of {len(subs)} preprocessed)" + (f"; missing: {', '.join(missing)}" if missing else ""),
                  f"- first condition: " + ", ".join(f"{k} {sum(q['first'] == k for q in qcs)}" for k in ("EC", "EO")),
                  f"- bad channels per subject: median {sorted(nbad)[len(nbad) // 2] if nbad else '-'}, max {max(nbad) if nbad else '-'}; "
                  f"Fp1/Fp2 flagged in {len(fp)}, O1/Oz/O2 flagged in {len(oc)}; flat channels in "
                  f"{sum(1 for q in qcs if q['flat_channels'])}; MAD zero in {len(madz)}",
                  f"- ICA: not converged in {len(nconv)} {nconv if nconv else ''}; no component removed in {len(noica)} {noica if noica else ''}",
                  f"- VEOG ptp (uV): min {min(q['veog_ptp_uv'] for q in qcs):.0f}, max {max(q['veog_ptp_uv'] for q in qcs):.0f}" if qcs else "- VEOG: -",
                  f"- 50 Hz / 40-44 Hz power ratio: max {max(q['psd_50Hz_over_40_44Hz'] for q in qcs):.3f}" if qcs else "- line ratio: -",
                  f"- epochs per block (cleaned 5/2 s): subjects below 20 in some block: {low if low else 'none'}",
                  f"- posterior alpha EC > EO: {len(alpha_pass)} of {n} ({100 * share:.0f}%) -> {rule}",
                  f"- failing the alpha check: {[q['subject'] for q in qcs if not q.get('alpha_check_EC_gt_EO')]}", ""]
    Path(a.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
