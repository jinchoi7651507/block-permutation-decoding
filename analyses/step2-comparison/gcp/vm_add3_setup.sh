#!/bin/bash
# Step 2 addendum 3 machine set-up (§2d): step 2 Python 3.12 environment (requirements-step2.txt = laptop pip freeze),
# Octave + CoSMoMVPA fe5acaf, PyMVPA 2.6.5 under Python 3.9 (recipe from the 2026-10-26 install pilot).
set -e
exec > ~/setup.log 2>&1
sudo apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q octave git python3.12-venv python3-dev swig build-essential libsvm-dev curl
python3.12 -m venv ~/venv-step2 && ~/venv-step2/bin/pip install -q --upgrade pip && ~/venv-step2/bin/pip install -q -r ~/requirements-step2.txt
git clone -q https://github.com/CoSMoMVPA/CoSMoMVPA.git ~/CoSMoMVPA && git -C ~/CoSMoMVPA checkout -q fe5acaf3034dbaac6f1a05cc00e969cae8db760b
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.9 && uv venv -p 3.9 ~/ve39
. ~/ve39/bin/activate
uv pip install "numpy==1.21.6" "scipy==1.7.3" "scikit-learn==1.0.2" "setuptools<58" wheel h5py
uv pip install --reinstall --no-deps --no-cache --no-build-isolation pymvpa2==2.6.5
python -c "import mvpa2; from mvpa2.clfs.svm import LinearCSVMC; from mvpa2.clfs.skl.base import SKLLearnerAdapter; print('mvpa2', mvpa2.__version__)"
deactivate
echo SETUP DONE
