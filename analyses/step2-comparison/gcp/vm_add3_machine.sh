#!/bin/bash
# Step 2 addendum 3: runs_add3/MACHINE.txt (§2d). Provisioning from instance/scheduling/preemptible (the step 2 and 2b
# records queried a non-existent path and hold an HTTP 404 page); the laptop also logs `gcloud compute instances describe`.
cd ~/pe/results/step2-comparison
M='http://metadata.google.internal/computeMetadata/v1/instance'
q() { curl -s -H 'Metadata-Flavor: Google' "$M/$1"; }
{
echo "written: $(date -u '+%F %T') UTC"
echo "instance: $(q machine-type | awk -F/ '{print $NF}')  zone: $(q zone | awk -F/ '{print $NF}')  preemptible: $(q scheduling/preemptible)"
echo "cpu: $(lscpu | grep 'Model name' | sed 's/ *Model name: *//')  vCPU: $(nproc)"
echo "os: $(. /etc/os-release; echo $PRETTY_NAME)  kernel: $(uname -r)"
echo "git commit: $(cat ~/pe/GIT_COMMIT)"
echo "threads: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; workers: ${W:-?}"
echo "octave: $(octave --version | head -1)"; octave --no-gui -q --eval "v=version('-blas'); disp(v)" 2>/dev/null | head -2
echo "cosmomvpa: $(git -C ~/CoSMoMVPA rev-parse HEAD)"
echo "mvpa2: $(~/ve39/bin/python -c 'import mvpa2; print(mvpa2.__version__)' 2>/dev/null); libsvm: bundled extension $(ls ~/ve39/lib/python3.9/site-packages/mvpa2/clfs/libsvmc/_svmc*.so | xargs -n1 basename)"
echo "sklearn (step 2 env): $(~/venv-step2/bin/python -c 'import sklearn; print(sklearn.__version__)')"
echo "== code sha256"; sha256sum code/*.py code/*.m code/*.sh
echo "== pip freeze (step 2 env)"; ~/venv-step2/bin/pip freeze
echo "== pip freeze (PyMVPA env)"; ~/ve39/bin/python -m pip freeze 2>/dev/null || ~/.local/bin/uv pip freeze --python ~/ve39/bin/python
echo "== numpy.show_config()"; ~/venv-step2/bin/python -c "import numpy; numpy.show_config()"
echo "== threadpoolctl"; ~/venv-step2/bin/python -c "import numpy, sklearn, threadpoolctl, json; print(json.dumps(threadpoolctl.threadpool_info(), indent=1))"
} > runs_add3/MACHINE.txt
