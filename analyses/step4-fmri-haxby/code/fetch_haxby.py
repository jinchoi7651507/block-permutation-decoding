#!/usr/bin/env python3
"""Step 4 (DESIGN.md §2): download the six subject tarballs of the PyMVPA Haxby 2001 distribution, check each
against the server's MD5SUMS (stop on a mismatch), extract, and write MANIFEST.sha256 of the extracted files used
(bold.nii.gz, labels.txt, mask4_vt.nii.gz per subject). Files already present with the right MD5 are not fetched again.

  python fetch_haxby.py --dir <data dir>
"""
import argparse
import hashlib
import tarfile
import urllib.request
from pathlib import Path

BASE = "http://data.pymvpa.org/datasets/haxby2001/"
SUBJ = [f"subj{i}-2010.01.14.tar.gz" for i in range(1, 7)]
USED = ("bold.nii.gz", "labels.txt", "mask4_vt.nii.gz")


def digest(p, algo):
    h = hashlib.new(algo)
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    d = Path(ap.parse_args().dir)
    d.mkdir(parents=True, exist_ok=True)
    md5 = {l.split()[1]: l.split()[0] for l in urllib.request.urlopen(BASE + "MD5SUMS").read().decode().splitlines() if l.strip()}
    for name in SUBJ:
        tgz = d / name
        if not (tgz.exists() and digest(tgz, "md5") == md5[name]):
            urllib.request.urlretrieve(BASE + name, tgz)
        if digest(tgz, "md5") != md5[name]:
            raise SystemExit(f"MD5 mismatch for {name}; stop")
        with tarfile.open(tgz) as t:
            t.extractall(d, filter="data")
    lines = []
    for i in range(1, 7):
        for f in USED:
            p = d / f"subj{i}" / f
            lines.append(f"{digest(p, 'sha256')}  subj{i}/{f}")
    (d / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
