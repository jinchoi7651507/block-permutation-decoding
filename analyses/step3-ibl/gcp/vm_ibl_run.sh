#!/bin/bash
# Step 3 main run (code addendum 1 §2, §3, §4; budget outcome BUDGET-OUTCOME.md). Stamped code unchanged. Draft 2 after
# review (review-run-script-ibl.txt). Launch: setsid nohup bash vm_ibl_run.sh > ~/run.out 2>&1 &
# W, N and the cap are read from the stamped budget outcome (budget/BUDGET-OUTCOME.json); nothing is passed by hand.
# Out-of-memory / dead-worker procedure (fixed before the stamp):
#  - every 60 s each worker is checked; a worker that ends with a code other than 0 (finished) or 124 (time cap) is a
#    dead worker (137 = SIGKILL, e.g. the kernel OOM killer; the kernel log is saved at the end);
#  - at the first dead worker, if at least 60 min remain: all workers are stopped (SIGTERM, then wait), the rows files
#    are cleaned (below), run_ibl.py --requeue releases the claims of sessions without a final row, the dead workers'
#    cache folders are emptied, and the workers are restarted once with W/2 workers (less memory per machine; same
#    command and file names; restarted workers loop from session 0 and fill the released sessions first). At most one
#    restart. With less than 60 min left, no restart: the prefix rule of summarize_ibl.py handles the gap.
#  - row clean-up (after every stop and before the archive): a line that does not parse, and every row of a session
#    without a final row (session_seconds / skipped / error) in any rows file, are moved to runs/partial_lines.txt;
#    each rows file is rewritten through a temporary file and os.replace. Values are never printed.
set -u
B=$HOME/pe/results/step3-ibl
L=$B/runs/run.log; log() { echo "$(date -u '+%F %T') UTC $*" >> $L; }
P=$HOME/ve312/bin/python
PAT="^$P run_ibl.py --order"
STARTED=0
cleanup_rows() {
  $P - $B/runs >> $L 2>&1 <<'PY'
import json, os, sys
from pathlib import Path
d = Path(sys.argv[1]); files = sorted(d.glob("rows.w*.jsonl")); parsed = {}; bad = []
for f in files:
    good = []
    for l in f.read_text().split("\n"):
        if not l:
            continue
        try:
            good.append((l, json.loads(l)))
        except ValueError:
            bad.append((f.name, l))
    parsed[f] = good
final = {r["session_index"] for g in parsed.values() for _, r in g
         if not r.get("pilot") and any(k in r for k in ("session_seconds", "skipped", "error"))}
moved = len(bad)
with open(d / "partial_lines.txt", "a") as fh:
    for name, l in bad:
        fh.write(name + "\tunparsable\t" + l + "\n")
    for f, g in parsed.items():
        keep = [l for l, r in g if r.get("session_index") in final]
        for l, r in g:
            if r.get("session_index") not in final:
                fh.write(f.name + "\tno-final-row\t" + l + "\n"); moved += 1
        tmp = f.with_suffix(".tmp")
        tmp.write_text("".join(l + "\n" for l in keep))
        os.replace(tmp, f)
print("row clean-up: moved", moved, "line(s); sessions with a final row:", len(final))
PY
}
finish() {
  [ -n "${MEMPID:-}" ] && kill $MEMPID 2>/dev/null
  pkill -TERM -f "$PAT"; sleep 5
  if [ "$STARTED" = 1 ]; then
  cleanup_rows
  log "end: sessions with a final row and completed prefix (indices only):"
  $P - $B/runs >> $L 2>&1 <<'PY'
import json, sys
from pathlib import Path
d = Path(sys.argv[1]); done = set()
for f in d.glob("rows.w*.jsonl"):
    for l in f.read_text().splitlines():
        r = json.loads(l)
        if any(k in r for k in ("session_seconds", "skipped", "error")):
            done.add(r["session_index"])
m = 0
while m in done:
    m += 1
print("  final rows:", len(done), "| completed prefix m =", m)
PY
  sudo journalctl -k --no-pager | grep -iE 'oom-kill|out of memory' > $B/runs/kernel_oom.txt 2>/dev/null
  log "kernel OOM lines: $(wc -l < $B/runs/kernel_oom.txt); peak mem/disk in run_mem.log; run_ibl.py sha256 $(sha256sum $B/code/run_ibl.py | cut -c1-16)"
  fi
  cd $B; tar czf ~/runs_ibl.tgz runs; sha256sum ~/runs_ibl.tgz > ~/runs_ibl.sha
  sudo poweroff
}
trap finish EXIT
for i in $(seq 1 90); do grep -q "SETUP DONE" ~/setup.log 2>/dev/null && break; sleep 20; done
grep -q "SETUP DONE" ~/setup.log || { log "SETUP NOT DONE, stop"; exit 1; }
cd $B
log "run start"
sha256sum -c DESIGN-v1.sha256 DESIGN-v1-CODE-ADDENDUM.sha256 DESIGN-v1-CODE-ADDENDUM-2.sha256 BUDGET-OUTCOME.sha256 runs_prep.sha > runs/hash_check_run.txt 2>&1 || { log "HASH MISMATCH, stop"; exit 1; }
tar -xOzf runs_prep.tgz runs/ORDER.json | cmp - runs/ORDER.json || { log "ORDER differs from prep archive, stop"; exit 1; }
log "hash check ok (stamped files, budget outcome, prep archive, ORDER.json)"
read W N CAP NORDER <<< "$($P -c "import json; b=json.load(open('budget/BUDGET-OUTCOME.json')); o=json.load(open('runs/ORDER.json'))['sessions']; print(int(b['workers']), int(b['sessions']), int(b['time_cap_minutes']), len(o))")"
[ -n "$CAP" ] && [ "$N" -le "$NORDER" ] || { log "budget values unreadable or N $N > order length $NORDER, stop"; exit 1; }
log "from BUDGET-OUTCOME.json: W $W, sessions $N, cap $CAP min"
NPROC=$(nproc --all)
[ "$W" -le "$NPROC" ] || { log "W $W > nproc $NPROC, stop"; exit 1; }
{ [ -d runs/claims ] && ls runs/claims | grep -q .; } && { log "claims not empty at the first start, stop"; exit 1; }
ls runs/rows.w*.jsonl >/dev/null 2>&1 && { log "rows files exist at the first start, stop"; exit 1; }
$P -c "from one.api import ONE; ONE.setup(base_url='https://openalyx.internationalbrainlab.org', username='intbrainlab', silent=True)" >> $L 2>&1
U=$($P -c "from one.api import ONE; o=ONE(base_url='https://openalyx.internationalbrainlab.org', password='international', silent=True); print(o.alyx.user)" 2>> $L | tail -1)
[ "$U" = "intbrainlab" ] || { log "ONE login check failed ($U), stop"; exit 1; }
log "ONE login checked: $U (RUNNOTE)"
bash ~/vm_ibl_machine.sh && log "machine record written"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONWARNINGS=ignore
END=$(( $(date +%s) + CAP * 60 ))
sudo shutdown -h +$((CAP + 45))
log "nproc $NPROC, $(free -g | awk '/Mem/{print $2}') GB RAM; worker end $(date -u -d @$END '+%F %T') UTC; shutdown at cap + 45 min"
( while true; do echo "$(date -u '+%T') mem_used_mb $(free -m | awk '/Mem/{print $3}') load $(cut -d' ' -f1 /proc/loadavg) disk_used $(df -h ~ | tail -1 | awk '{print $3}') workers $(pgrep -fc "$PAT")"
    ps -o rss= -p "$(pgrep -d, -f "$PAT")" 2>/dev/null | sort -n | tail -1 | awk '{print "  max_rss_kb", $1}'; sleep 60; done ) > runs/run_mem.log &
MEMPID=$!
cd code
declare -A PID
start_workers() {   # $1 = number of workers, $2 = tag
  local n=0
  for k in $(seq 0 $(( $1 - 1 ))); do
    left=$(( END - $(date +%s) )); [ $left -le 0 ] && break
    timeout ${left}s $P run_ibl.py --order ../runs/ORDER.json --n-sessions $N --out ../runs/rows.w$k.jsonl --cache ~/cache_$k --claims ../runs/claims 2>> ../runs/err.w$k.txt &
    PID[$k]=$!; n=$((n + 1))
  done
  log "$2: started $n of $1 workers"
}
monitor() {   # returns 0 when all workers have ended normally or at the cap; 1 at the first dead worker
  while true; do
    alive=0
    for k in "${!PID[@]}"; do p=${PID[$k]}
      if kill -0 $p 2>/dev/null; then alive=$((alive + 1)); continue; fi
      wait $p; rc=$?; log "worker $k (pid $p) ended rc $rc"; unset "PID[$k]"
      if [ $rc -ne 0 ] && [ $rc -ne 124 ]; then DEADK=$k; DEADRC=$rc; return 1; fi
    done
    [ $alive -eq 0 ] && return 0
    sleep 60
  done
}
STARTED=1
start_workers $W "start"
RESTARTED=0
while ! monitor; do
  left=$(( END - $(date +%s) ))
  if [ $RESTARTED -eq 1 ] || [ $left -lt 3600 ]; then
    log "dead worker $DEADK (rc $DEADRC); no restart (restarted $RESTARTED, $((left / 60)) min left); remaining workers continue"
    continue
  fi
  log "dead worker $DEADK (rc $DEADRC), $((left / 60)) min left: stopping all workers for the restart"
  pkill -TERM -f "$PAT"; for k in "${!PID[@]}"; do wait ${PID[$k]}; log "worker $k stopped rc $?"; unset "PID[$k]"; done
  cleanup_rows
  out=$($P run_ibl.py --order ../runs/ORDER.json --n-sessions $N --out ../runs/rows.w0.jsonl --cache ~/cache_0 --claims ../runs/claims --requeue 2>&1)
  log "requeue: $out"
  echo "$out" | grep -q released || { log "requeue failed, no restart"; break; }
  for k in $(seq 0 $((W - 1))); do find ~/cache_$k -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null; done   # session folders left by stopped or killed workers (cache tables are files at the root and stay)
  log "disk before restart: $(df -h ~ | tail -1 | awk '{print $3" used"}')"
  RESTARTED=1
  start_workers $(( W / 2 )) "restart after dead worker"
done
log "workers done (restarted $RESTARTED); time left $(( (END - $(date +%s)) / 60 )) min"
