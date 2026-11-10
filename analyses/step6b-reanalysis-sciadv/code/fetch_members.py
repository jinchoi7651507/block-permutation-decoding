"""List a remote zip by HTTP range requests and extract chosen members, without downloading the whole archive.

  python -I fetch_members.py --url URL --size BYTES list MANIFEST.tsv
  python -I fetch_members.py --url URL --size BYTES extract OUTDIR MEMBER [MEMBER ...]
  python -I fetch_members.py --url URL --size BYTES extract --data OUTDIR MEMBER [...]   (stage 2 only)

Without --data only code and documentation members are extracted (.m .py .ipynb .txt .md .json .docx); the
CRC-32 of every member is checked by zipfile. --data allows only the data members named in DATA_ALLOWED,
which DESIGN.md lists; it is for stage 2, after DESIGN.md is fixed and stamped.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import urllib.request
import zipfile

CODE_EXT = (".m", ".py", ".ipynb", ".txt", ".md", ".json", ".docx")
DATA_ALLOWED = ("Data Structures/Switching_2p_Struc_Main.mat", "Data Structures/Switching_Behav_Struc.mat",
                "Data Structures/clusters_fig2.mat")


class HTTPFile(io.RawIOBase):
    def __init__(self, url, size):
        self.url, self.size, self.pos, self.fetched = url, size, 0, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, b):
        n = len(b)
        if n == 0 or self.pos >= self.size:
            return 0
        end = min(self.pos + n, self.size) - 1
        req = urllib.request.Request(self.url, headers={"Range": "bytes=%d-%d" % (self.pos, end)})
        with urllib.request.urlopen(req, timeout=300) as r:
            if r.status != 206:
                raise IOError("range request not honoured (HTTP %d)" % r.status)
            d = r.read()
        b[:len(d)] = d
        self.pos += len(d)
        self.fetched += len(d)
        return len(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("cmd", choices=["list", "extract"])
    ap.add_argument("--data", action="store_true")
    ap.add_argument("dest")
    ap.add_argument("members", nargs="*")
    a = ap.parse_args()
    raw = HTTPFile(a.url, a.size)
    z = zipfile.ZipFile(io.BufferedReader(raw, buffer_size=1 << 20))
    if a.cmd == "list":
        with open(a.dest, "w") as out:
            out.write("name\tfile_size\tcompress_size\tcrc32\tdate_time\n")
            for i in z.infolist():
                out.write("%s\t%d\t%d\t%08x\t%04d-%02d-%02d %02d:%02d:%02d\n"
                          % ((i.filename, i.file_size, i.compress_size, i.CRC) + tuple(i.date_time)))
        print("members: %d" % len(z.infolist()))
    else:
        for name in a.members:
            ok = name in DATA_ALLOWED if a.data else name.lower().endswith(CODE_EXT)
            if not ok:
                print("REFUSED\t%s" % name)
                continue
            info = z.getinfo(name)
            dest = os.path.join(a.dest, name)
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            h = hashlib.sha256()
            with z.open(info) as src, open(dest, "wb") as o:      # streams; CRC checked at the end
                for chunk in iter(lambda: src.read(1 << 22), b""):
                    o.write(chunk)
                    h.update(chunk)
            print("EXTRACTED\t%s\t%d\tcrc32=%08x\tsha256=%s" % (name, info.file_size, info.CRC, h.hexdigest()))
    print("bytes fetched: %d" % raw.fetched)


if __name__ == "__main__":
    main()
