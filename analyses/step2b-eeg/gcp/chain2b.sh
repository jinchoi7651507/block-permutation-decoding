#!/bin/bash
set -u
cd "<repo>/results/step2b-eeg"
PY=<home>/Downloads/trackA-school/venv-2b/bin/python
F=<home>/Downloads/trackA-school/lemon/features
log() { echo "$(date '+%F %T') $*" >> runs/prep.log; }
log "chain2b start"
until ots upgrade DESIGN-v2-ADDENDUM.sha256.ots 2>&1 | grep -q "Success! Timestamp complete"; do sleep 300; done
log "addendum attested"
shasum -a 256 -c DESIGN-v2-ADDENDUM.sha256 >> runs/prep.log 2>&1 || { log "HASH MISMATCH, stop"; exit 1; }
./code/download_pilot.sh >> runs/prep.log 2>&1; log "pilot download done"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 $PY code/preprocess.py --subjects eligibility/SUBJECTS.txt --out $F >> runs/prep.out 2>&1; log "main 40 preprocessed rc $?"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 $PY code/preprocess.py --subjects eligibility/PILOT-SUBJECTS.txt --out $F >> runs/prep.out 2>&1; log "pilot 5 preprocessed rc $?"
log "chain2b done"
