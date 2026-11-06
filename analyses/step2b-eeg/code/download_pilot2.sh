#!/bin/bash
# Download the raw BrainVision files (.vhdr, .vmrk, .eeg) of the 5 second-round pilot subjects (eligibility/PILOT2-SUBJECTS.txt; addendum 2;
# hash-stamped before any .eeg download) into $LEMON_DIR (outside the repository), resumable (curl -C -),
# then write eligibility/EEG-MANIFEST-PILOT2.sha256 (it hashes every .vhdr/.vmrk/.eeg in LEMON_DIR: main, pilot 1 and pilot 2).
# Data are not redistributed.
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
LEMON_DIR="${LEMON_DIR:?set LEMON_DIR to the raw-data folder}"
RAW=https://ftp.gwdg.de/pub/misc/MPI-Leipzig_Mind-Brain-Body-LEMON/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID
mkdir -p "$LEMON_DIR"
(cd "$HERE" && shasum -a 256 -c eligibility/PILOT2-SUBJECTS.sha256) || { echo "PILOT2-SUBJECTS.txt hash mismatch; stop"; exit 1; }
while read -r s; do
  [ -z "$s" ] && continue
  for ext in vhdr vmrk eeg; do
    f="$LEMON_DIR/$s.$ext"
    for try in 1 2 3; do
      curl -sS -L -C - --retry 3 -o "$f" "$RAW/$s/RSEEG/$s.$ext" && break
      sleep 10
    done
  done
  echo "$(date '+%F %T') $s $(stat -f %z "$LEMON_DIR/$s.eeg" 2>/dev/null)"
done < "$HERE/eligibility/PILOT2-SUBJECTS.txt"
(cd "$LEMON_DIR" && shasum -a 256 *.vhdr *.vmrk *.eeg) > "$HERE/eligibility/EEG-MANIFEST-PILOT2.sha256"
echo DONE
