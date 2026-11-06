#!/bin/bash
# On the addendum 3 VM: wait for the set-up, write MACHINE.txt, run add3_run.sh, archive runs_add3 with its hash,
# power off (the laptop watcher then copies the archive back and deletes the machine).
until grep -q "SETUP DONE" ~/setup.log 2>/dev/null; do
  if grep -qi "error" ~/setup.log 2>/dev/null && ! pgrep -f vm_add3_setup.sh >/dev/null; then echo "SETUP FAILED" >> ~/go.log; sudo shutdown -h now; exit 1; fi
  sleep 30
done
export W=56 PY312=~/venv-step2/bin/python PY39=~/ve39/bin/python COSMO=~/CoSMoMVPA
cd ~/pe/results/step2-comparison && mkdir -p runs_add3 && bash ~/vm_add3_machine.sh
echo "$(date -u '+%F %T') UTC machine record written" >> ~/go.log
cd ~/pe/results/step2-comparison/code && bash add3_run.sh >> ~/go.log 2>&1
cd ~/pe/results/step2-comparison && tar czf ~/runs_add3.tgz runs_add3 && sha256sum ~/runs_add3.tgz | cut -d' ' -f1 > ~/runs_add3.sha
echo "$(date -u '+%F %T') UTC archived; powering off" >> ~/go.log
sudo shutdown -h now
