#!/bin/bash
# Step 2 on the cloud machine: the simulation cells 0-176, the power pilot, the delta choice and the power cells.
# Resumable (every step skips replicates already written).
# Output: runs/ on the machine (copied back as runs_cloud/). Log: runs/chain.log
set -u
cd "$(dirname "$0")/.."
PY=${PY:-$HOME/venv-step2/bin/python}
W=${WORKERS:-56}
log() { echo "$(date -u '+%F %T') UTC $*" >> runs/chain.log; }
mkdir -p runs
log "cloud chain start, workers $W"
$PY code/run_sim_cells.py --workers "$W" >> runs/driver.out 2>&1; log "cells 0-176 done"
$PY code/run_sim_cells.py --workers "$W" --power-pilot >> runs/driver.out 2>&1; log "power pilot done"
D=$($PY code/choose_delta.py); log "delta choice $D"
$PY code/run_sim_cells.py --workers "$W" --power "$D" >> runs/driver.out 2>&1; log "power cells done"
log "cloud chain end"
