#!/bin/bash
# Step 3: runs/MACHINE.txt (code addendum 1 §3; provisioning from instance/scheduling/preemptible).
cd ~/pe/results/step3-ibl
M='http://metadata.google.internal/computeMetadata/v1/instance'
q() { curl -s -H 'Metadata-Flavor: Google' "$M/$1"; }
{
echo "written: $(date -u '+%F %T') UTC"
echo "instance: $(q machine-type | awk -F/ '{print $NF}')  zone: $(q zone | awk -F/ '{print $NF}')  preemptible: $(q scheduling/preemptible)"
echo "cpu: $(lscpu | grep 'Model name' | sed 's/ *Model name: *//')  vCPU: $(nproc)  RAM: $(free -g | awk '/Mem/{print $2}') GB  disk: $(df -h ~ | tail -1 | awk '{print $2}')"
echo "os: $(. /etc/os-release; echo $PRETTY_NAME)  git commit: $(cat ~/pe/GIT_COMMIT)"
echo "threads: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1"
echo "== code sha256"; sha256sum code/*.py
echo "== versions"; ~/ve312/bin/python - <<'PY'
import inspect, hashlib, one, ibllib, sklearn, numpy, scipy, brainbox.task.closed_loop as c, brainwidemap.bwm_loading as b
print("one", one.__version__, "ibllib", ibllib.__version__, "sklearn", sklearn.__version__, "numpy", numpy.__version__, "scipy", scipy.__version__)
print("closed_loop.py sha256", hashlib.sha256(open(c.__file__, "rb").read()).hexdigest())
for f in ("load_trials_and_mask", "load_good_units", "bwm_query"):
    print(f, inspect.signature(getattr(b, f)))
PY
echo "paper repo: $(git -C ~/pbwm rev-parse HEAD)"
echo "== pip freeze"; ~/.local/bin/uv pip freeze --python ~/ve312/bin/python
} > runs/MACHINE.txt
