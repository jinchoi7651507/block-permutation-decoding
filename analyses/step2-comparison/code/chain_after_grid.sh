#!/bin/bash
# Step 2 chain (addendum 1): wait for the addendum's Bitcoin attestation and for the running grid driver (cells 0-143,
# PID 42874) to exit; then cells 144-176, the power pilot, the delta choice, the power cells, and the Allen cells.
# Resumable: every step skips replicates/rows already written. Log: runs/chain.log
set -u
cd "$(dirname "$0")/.."
PY=<home>/Downloads/trackA-school/venv-step2/bin/python
log() { echo "$(date '+%F %T') $*" >> runs/chain.log; }
log "chain start"
until ots upgrade DESIGN-v2-ADDENDUM.sha256.ots 2>&1 | grep -q "Success! Timestamp complete"; do sleep 600; done
ots verify DESIGN-v2-ADDENDUM.sha256.ots >> runs/chain.log 2>&1 || true
log "addendum attested"
while kill -0 42874 2>/dev/null; do sleep 600; done
log "grid 0-143 driver exited"
shasum -a 256 -c DESIGN-v2.sha256 DESIGN-v2-ADDENDUM.sha256 >> runs/chain.log 2>&1 || { log "HASH MISMATCH, stop"; exit 1; }
$PY code/run_sim_cells.py --workers 6 --only 144-176 >> runs/driver.out 2>&1; log "cells 144-176 done"
$PY code/run_sim_cells.py --workers 6 --power-pilot >> runs/driver.out 2>&1; log "power pilot done"
D=$($PY code/choose_delta.py); log "delta choice $D"
$PY code/run_sim_cells.py --workers 6 --power "$D" >> runs/driver.out 2>&1; log "power cells done"
mkdir -p runs_allen
for k in 0 1 2 3 4 5; do
  OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore $PY code/allen_cells.py --dir <home>/Downloads/trackA-school/allen --out runs_allen/rows.w$k.jsonl --worker $k --of 6 > runs_allen/log.w$k.txt 2>&1 &
done
wait
log "Allen cells done"
