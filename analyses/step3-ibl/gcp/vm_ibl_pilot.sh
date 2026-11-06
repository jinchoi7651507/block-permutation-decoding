#!/bin/bash
# Step 3 timing pilot on the run machine type (code addendum 1 §2 "Pilot isolation", §3, §4). Stamped code unchanged:
# 2 pilot processes (run_ibl.py --pilot, separate pilot output and claims, one per pilot session) and W - 2 dummy-load
# processes (run_ibl.py --dummy-load) at once, W = vCPUs. p values are discarded inside run_ibl.py.
# W = vCPUs is the conservative upper bound: the RAM limit comes from this pilot and the disk limit from its freed_gb,
# so a lower W chosen afterwards can only overestimate t_rs (fewer sessions). Draft 2 after review
# (review-pilot-script-ibl.txt); draft 4 after attempt 1: W before the thread exports, pilot order from pilot_order.py. Every exit path archives runs/ and powers off; each pilot process is stopped at 330 min
# (timeout) so the trap archives normally; shutdown after 360 min is only a last resort.
sudo shutdown -h +360
B=$HOME/pe/results/step3-ibl
L=$B/runs/pilot.log; log() { echo "$(date -u '+%F %T') UTC $*" >> $L; }
STOP=$HOME/pilot_stop
trap 'touch $STOP; pkill -f -- --dummy-load; cd $B; tar czf ~/runs_pilot.tgz runs; sha256sum ~/runs_pilot.tgz > ~/runs_pilot.sha; sudo poweroff' EXIT
for i in $(seq 1 90); do grep -q "SETUP DONE" ~/setup.log 2>/dev/null && break; sleep 20; done
grep -q "SETUP DONE" ~/setup.log || { log "SETUP NOT DONE, stop"; exit 1; }
cd $B
log "pilot start; watchdog power-off in 360 min"
sha256sum -c DESIGN-v1.sha256 DESIGN-v1-CODE-ADDENDUM.sha256 DESIGN-v1-CODE-ADDENDUM-2.sha256 > runs/hash_check_pilot.txt 2>&1 || { log "HASH MISMATCH, stop"; exit 1; }
sha256sum -c runs_prep.sha >> runs/hash_check_pilot.txt 2>&1 || { log "PREP ARCHIVE MISMATCH, stop"; exit 1; }
tar -xOzf runs_prep.tgz runs/ORDER.json | cmp - runs/ORDER.json || { log "ORDER differs from prep archive, stop"; exit 1; }
log "hash check ok (stamped files, prep archive, ORDER.json)"
[ -e runs/claims_pilot ] || ls runs/pilot.w*.jsonl >/dev/null 2>&1 && { log "pilot claims or output exist, stop"; exit 1; }
P=~/ve312/bin/python
$P -c "from one.api import ONE; ONE.setup(base_url='https://openalyx.internationalbrainlab.org', username='intbrainlab', silent=True)" >> $L 2>&1
U=$($P -c "from one.api import ONE; o=ONE(base_url='https://openalyx.internationalbrainlab.org', password='international', silent=True); print(o.alyx.user)" 2>> $L | tail -1)
[ "$U" = "intbrainlab" ] || { log "ONE login check failed ($U), stop"; exit 1; }
log "ONE username set and login checked: $U (RUNNOTE)"
bash ~/vm_ibl_machine.sh && log "machine record written"
W=$(nproc --all)   # before the thread exports: GNU nproc honours OMP_NUM_THREADS (attempt 1 got W = 1)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONWARNINGS=ignore
log "nproc $W; free -g: $(free -g | awk '/Mem/{print $2" total, "$3" used"}')"
rm -f $STOP
cd code
# attempt 2 (RUNNOTE): pilot order = first sessions of ORDER.json that pass the runner's trial gate and have a region-session
PYTHONPATH=. $P ~/pilot_order.py --order ../runs/ORDER.json --meta ../runs/BUDGET-META.json --out ../runs/PILOT-ORDER.json >> $L 2>&1 || { log "pilot order failed, stop"; exit 1; }
log "pilot order written: $(grep 'pilot sessions at positions' $L | tail -1)"
# every 30 s: used memory, load, received bytes, disk, RSS of every python process (RAM and disk limits of §3)
( while [ ! -f $STOP ]; do
    echo "$(date -u '+%T') mem_used_mb $(free -m | awk '/Mem/{print $3}') load $(cut -d' ' -f1 /proc/loadavg) rx_bytes $(cat /sys/class/net/ens*/statistics/rx_bytes | awk '{s+=$1} END{print s}') disk_used $(df -h ~ | tail -1 | awk '{print $3}')"
    ps -o pid=,rss=,args= -C python3.12,python | awk '{print "  rss_kb", $1, $2, ($0 ~ /--pilot/ ? "pilot" : "dummy")}'
    sleep 30; done ) > ../runs/pilot_mem.log &
for d in $(seq 1 $((W - 2))); do
  $P run_ibl.py --order ../runs/ORDER.json --n-sessions 2 --out ../runs/pilot_dummy.jsonl --cache ~/cache_dummy --claims ../runs/claims_pilot_dummy --dummy-load $STOP > /dev/null 2>> ../runs/pilot_dummy_err.txt &
done
log "$((W - 2)) dummy-load processes started (W = $W); dummies are 400 x 30 synthetic region-sessions (understate memory contention)"
PIDS=""
for k in 0 1; do
  timeout 330m /usr/bin/time -v -o ../runs/pilot_time.w$k.txt $P run_ibl.py --order ../runs/PILOT-ORDER.json --n-sessions 2 --out ../runs/pilot.w$k.jsonl --cache ~/cache_pilot_$k --claims ../runs/claims_pilot --pilot 2> ../runs/pilot_err.w$k.txt &
  PIDS="$PIDS $!"
  log "pilot process $k started (pid $!)"
done
for p in $PIDS; do wait $p; log "pilot process pid $p ended rc $? (124 = 330-min timeout)"; done
touch $STOP
for k in 0 1; do
  f=../runs/pilot.w$k.jsonl
  log "pilot.w$k: session_seconds rows $(grep -c session_seconds $f 2>/dev/null), skipped $(grep -c '"skipped"' $f 2>/dev/null), error $(grep -c '"error"' $f 2>/dev/null), region_error $(grep -c region_error $f 2>/dev/null)"
done
sleep 60
log "dummy loads still running after 60 s: $(pgrep -fc -- '--dummy-load') (killed)"
pkill -f -- '--dummy-load'
log "pilot end"
