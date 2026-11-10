"""Stage 2 data download (Addendum 1b). Runs the stamped fetch_members.py unchanged; only DATA_ALLOWED is set at run
time, to exactly the members that the stamped data-members.tsv lists for the zip being read (DESIGN section 3: "data
option off until then"). No other member can be extracted. zipfile checks each member's CRC-32 while reading; gate G1
checks the extracted files again against data-members.tsv.

  python -I fetch_data.py DEST              extract the 460 listed members (Figure_2.zip, then Data.zip) under DEST
  python -I fetch_data.py --check-refusal   read only the Figure_2.zip central directory and confirm that a data member
                                         not in the list is refused (no data member is read)
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch_members as fm  # noqa: E402

RECORD = "https://zenodo.org/records/10529801/files/%s?download=1"
SIZES = {"Data.zip": 20364869417, "Figure_2.zip": 4637807}   # zenodo-files-10529801.tsv


def listed(zipname):
    rows = csv.DictReader(open(HERE.parent / "data-members.tsv"), delimiter="\t")
    return [r["member"] for r in rows if r["zip"] == zipname]


def run(zipname, dest, names):
    fm.DATA_ALLOWED = tuple(listed(zipname))
    sys.argv = ["fetch_members.py", "--url", RECORD % zipname, "--size", str(SIZES[zipname]), "extract", "--data", dest] + names
    fm.main()


def main():
    if sys.argv[1:] == ["--check-refusal"]:
        z = zipfile.ZipFile(io.BufferedReader(fm.HTTPFile(RECORD % "Figure_2.zip", SIZES["Figure_2.zip"]), buffer_size=1 << 20))
        other = [i.filename for i in z.infolist() if i.filename.endswith(".mat") and i.filename not in listed("Figure_2.zip")][:1]
        if not other:
            raise SystemExit("no unlisted .mat member in Figure_2.zip: the refusal is not tested")
        print("listed: Figure_2.zip %d, Data.zip %d" % (len(listed("Figure_2.zip")), len(listed("Data.zip"))))
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            run("Figure_2.zip", "refusal-check-unused", other)
        print(buf.getvalue(), end="")
        if ("REFUSED\t%s" % other[0]) not in buf.getvalue() or Path("refusal-check-unused").exists():
            raise SystemExit("refusal check FAILED")
        print("refusal check passed: %s refused, nothing written" % other[0])
        return
    dest = sys.argv[1]
    for zipname in ("Figure_2.zip", "Data.zip"):
        run(zipname, dest, listed(zipname))


if __name__ == "__main__":
    main()
