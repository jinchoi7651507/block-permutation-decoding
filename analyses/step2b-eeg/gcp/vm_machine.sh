#!/bin/bash
# On the VM: write runs/MACHINE.txt (addendum 2 §6).
cd ~/pe/results/step2b-eeg
{
echo "written: $(date -u '+%F %T') UTC"
echo "instance: $(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/machine-type | awk -F/ '{print $NF}')  zone: $(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/zone | awk -F/ '{print $NF}')  scheduling: $(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/scheduling/provisioning-model)"
echo "cpu: $(lscpu | grep 'Model name' | sed 's/ *Model name: *//')  vCPU: $(nproc)"
echo "os: $(. /etc/os-release; echo $PRETTY_NAME)  kernel: $(uname -r)"
echo "git commit: $(cat ~/pe/GIT_COMMIT)"
echo "threads: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; workers: ${WORKERS:-?}"
echo "== code sha256"; (cd ~/pe/results && sha256sum step2b-eeg/code/*.py step2b-eeg/code/*.sh step2-comparison/code/sim.py)
echo "== pip freeze"; ~/venv-2b/bin/pip freeze
echo "== numpy.show_config()"; ~/venv-2b/bin/python -c "import numpy; numpy.show_config()"
echo "== threadpoolctl"; ~/venv-2b/bin/python -c "import numpy, sklearn, threadpoolctl, json; print(json.dumps(threadpoolctl.threadpool_info(), indent=1))"
} > runs/MACHINE.txt
