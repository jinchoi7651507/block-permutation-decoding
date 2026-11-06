#!/bin/bash
# Addendum 2 chain (laptop): attestation -> hash checks -> download of the 5 second-round pilot subjects -> preprocessing.
set -u
cd "<repo>/results/step2b-eeg"
L=runs/prep2.log
log() { echo "$(date '+%F %T') $*" >> $L; }
log "chain add2 start"
until ots upgrade DESIGN-v2-ADDENDUM-2.sha256.ots 2>&1 | grep -q "Success! Timestamp complete"; do sleep 300; done
log "addendum 2 attested"
shasum -a 256 -c DESIGN-v2-ADDENDUM-2.sha256 DESIGN-v2-ADDENDUM.sha256 >> $L 2>&1 || { log "HASH MISMATCH, stop"; exit 1; }
LEMON_DIR=<home>/Downloads/trackA-school/lemon/raw bash code/download_pilot2.sh >> $L 2>&1; log "pilot2 download done"
cd code && nice -n 10 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 <home>/Downloads/trackA-school/venv-2b/bin/python preprocess.py --subjects ../eligibility/PILOT2-SUBJECTS.txt --out <home>/Downloads/trackA-school/lemon/features >> ../runs/prep2.out 2>&1; log "pilot2 preprocessed rc $?"
