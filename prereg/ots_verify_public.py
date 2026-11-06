"""Verify OpenTimestamps proofs without a local Bitcoin node.

For each .ots proof: check the file's SHA-256 equals the digest in the proof, walk the proof to
every BitcoinBlockHeaderAttestation, and compare the committed value with the merkle root of that
block fetched from a public explorer (blockstream.info). Prints the earliest Bitcoin block and its time (UTC), which
is the latest time the file can have been created. A proof can carry several attestations (one per calendar
server); the earliest one is the third-party time.

    pip install opentimestamps
    python prereg/ots_verify_public.py $(find analyses -name '*.ots')
"""
import datetime
import hashlib
import json
import sys
import urllib.request

from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
from opentimestamps.core.serialize import StreamDeserializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile

API = "https://blockstream.info/api"


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()


def main():
    ok_all = True
    for proof in sys.argv[1:]:
        target = proof[:-4]
        with open(proof, "rb") as f:
            dtf = DetachedTimestampFile.deserialize(StreamDeserializationContext(f))
        with open(target, "rb") as f:
            digest = hashlib.sha256(f.read()).digest()
        same = digest == dtf.file_digest
        best = None
        for msg, att in dtf.timestamp.all_attestations():
            if not isinstance(att, BitcoinBlockHeaderAttestation):
                continue
            h = get(f"{API}/block-height/{att.height}").strip()
            blk = json.loads(get(f"{API}/block/{h}"))
            match = blk["merkle_root"] == msg[::-1].hex()
            t = datetime.datetime.fromtimestamp(blk["timestamp"], datetime.timezone.utc)
            if match and (best is None or t < best[1]):
                best = (att.height, t)
            if not match:
                ok_all = False
                print(f"  MISMATCH {proof} block {att.height}")
        status = "OK" if same and best else "FAIL"
        ok_all &= status == "OK"
        print(f"{status}  {target}: file sha256 matches proof {same}; earliest Bitcoin block "
              f"{best[0] if best else '-'} at {best[1].isoformat() if best else '-'}")
    print("ALL OK" if ok_all else "SOME FAILED")


if __name__ == "__main__":
    main()
