"""Writes data-members.tsv from the manifests only (no data member is opened). Run from this folder or give paths.
Usage: python code/make_member_list.py [manifest-data.tsv] [manifest-figure-zips.tsv] [out.tsv]"""
import csv
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
man = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "manifest-zenodo-10529801.tsv"
fman = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "manifest-zenodo-10529801-figure-zips.tsv"
out = Path(sys.argv[3]) if len(sys.argv) > 3 else root / "data-members.tsv"
MIN = {("reward_end", 0), ("target", -600), ("target", -300), ("target", 0)}
rows = []
for r in csv.DictReader(open(man), delimiter="\t"):
    m = re.search(r"FR_(reward_end|target)_300_window_from_(-?\d+)_to_(-?\d+)/ID_(\d+)\.mat$", r["name"])
    if not m:
        continue
    ev, a = m.group(1), int(m.group(2))
    if (ev == "reward_end" and a in range(0, 301, 50)) or (ev == "target" and a in range(-600, 351, 50)):
        rows.append(("Data.zip", r["name"], r["file_size"], r["compress_size"], r["crc32"],
                     "minimum" if (ev, a) in MIN else "faithful-NaN-rule"))
for r in csv.DictReader(open(fman), delimiter="\t"):
    if r["zip"] == "Figure_2.zip" and r["name"].endswith("Figure_2_decoding_accuracy.mat"):
        rows.append((r["zip"], r["name"], r["file_size"], r["compress_size"], r["crc32"], "gate"))
rows.sort(key=lambda x: (x[5] != "gate", x[5] != "minimum", x[1]))
with open(out, "w", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["zip", "member", "file_size", "compress_size", "crc32", "role"])
    w.writerows(rows)
tot = {k: sum(int(r[2]) for r in rows if r[5] == k) for k in ("gate", "minimum", "faithful-NaN-rule")}
print(len(rows), "members;", tot)
