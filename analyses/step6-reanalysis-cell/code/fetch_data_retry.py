"""Operational retry around the stamped fetch_data.py (2026-11-09, Addendum 3 run): Zenodo answered HTTP 500 on range
requests. Extracts only members not yet present with their listed CRC-32, in small batches, through the unchanged
fetch_data.run and the unchanged allow-list. Run: python -I fetch_data_retry.py DEST"""
import csv
import sys
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch_data as fd  # noqa: E402

BATCH, TRIES, PAUSE = 25, 60, 45


def crc(p):
    c = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            c = zlib.crc32(chunk, c)
    return "%08x" % c


def missing(dest):
    rows = list(csv.DictReader(open(HERE.parent / "data-members.tsv"), delimiter="\t"))
    return [r for r in rows if not (Path(dest) / r["member"]).is_file() or crc(Path(dest) / r["member"]) != r["crc32"]]


def main(dest):
    for t in range(TRIES):
        todo = missing(dest)
        print("try %d: %d members missing" % (t, len(todo)), flush=True)
        if not todo:
            return 0
        for z in ("Figure_2.zip", "Data.zip"):
            names = [r["member"] for r in todo if r["zip"] == z][:BATCH]
            if not names:
                continue
            try:
                fd.run(z, dest, names)
            except Exception as e:
                print("error (%s): %s" % (type(e).__name__, e), flush=True)
                time.sleep(PAUSE)
        time.sleep(5)
    print("members still missing:", len(missing(dest)), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
