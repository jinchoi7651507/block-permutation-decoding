#!/usr/bin/env python3
"""Check every hash list in analyses/ against the files of this repository.

A list names its files relative to its own folder or to its step folder. Two special cases:
step3-ibl/BUDGET-OUTCOME.sha256 names seven cloud scripts by their path in the working repository
(../../working-archive/2026-10-26/gcp/), which are in step3-ibl/gcp/ here; runs_ibl.sha and runs_pilot.sha
name their archive by its path on the cloud machine. Lists of downloaded recordings or derived features
(data manifests) are reported, not checked: check them after downloading the data. Hashes are computed with
Python's hashlib, so no external tool is needed.

    python prereg/check_hash_lists.py          # from the repository root
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "analyses"
DATA = {"MANIFEST.sha256", "EEG-MANIFEST.sha256", "EEG-MANIFEST-PILOT.sha256", "EEG-MANIFEST-PILOT2.sha256",
        "FEATURES-MANIFEST.sha256", "MANIFEST-haxby.sha256", "MANIFEST-pamap2.sha256", "fulltext-MANIFEST.sha256"}
GCP = ("../../working-archive/2026-10-26/gcp/", "gcp/")


def check(listing, cwd):
    text = listing.read_text()
    if listing.name == "BUDGET-OUTCOME.sha256":
        text = text.replace(*GCP)
    bad = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 1)
        if len(parts) == 1 and listing.suffix == ".sha":    # a bare hash: the archive of the same name (.tgz)
            digest, name = parts[0], listing.with_suffix(".tgz").name
        else:
            digest, name = parts[0], parts[1].lstrip("*")   # "*" marks binary mode in shasum output
        try:
            ok = hashlib.sha256((cwd / name).read_bytes()).hexdigest() == digest.lower()
        except OSError:
            bad.append(f"{name}: FAILED open or read")
            continue
        if not ok:
            bad.append(f"{name}: FAILED")
    return bad, len(text.splitlines())


def main():
    failed = 0
    for h in sorted(A.rglob("*.sha256")) + sorted(A.rglob("*.sha")):
        rel = h.relative_to(ROOT)
        if h.name in DATA:
            print(f"data manifest  {rel} ({len(h.read_text().splitlines())} files; check after download)")
            continue
        words = h.read_text().split()
        if len(words) == 2 and words[1].startswith("/"):
            ok = hashlib.sha256((h.parent / Path(words[1]).name).read_bytes()).hexdigest() == words[0]
            print(f"{'OK' if ok else 'FAILED':<14} {rel} (hash of {Path(words[1]).name})")
            failed += not ok
            continue
        step = next(p for p in [h.parent, *h.parents] if p.parent == A)
        for cwd in dict.fromkeys([h.parent, step]):
            bad, n = check(h, cwd)
            if not bad:
                break
        print(f"{'OK' if not bad else 'FAILED':<14} {rel} ({n} files)")
        for l in bad[:5]:
            print("    ", l)
        failed += bool(bad)
    print("ALL OK" if not failed else f"{failed} list(s) failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
