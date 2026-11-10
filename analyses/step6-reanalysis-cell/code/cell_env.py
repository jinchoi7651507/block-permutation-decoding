"""Environment control for the Cell reanalysis. Import this module FIRST in every entry point and worker module:
it sets the BLAS/OpenMP thread variables to 1 before numpy is imported (so the MLP L-BFGS and the SVM fits are
deterministic and do not depend on the number of cores), pins the package versions and records the platform."""
from __future__ import annotations

import os
import platform
import re
import sys

THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")
for _v in THREAD_VARS:
    os.environ[_v] = "1"

PINNED = {"python": "3.12.3", "numpy": "2.5.4", "scipy": "1.18.1", "scikit-learn": "1.9.1", "h5py": "3.14.0"}
PLATFORM_PLACEHOLDER = "PLATFORM: to be fixed by the author before the stamp"
DEFAULT_PLATFORM = "Linux x86_64"   # author 2026-11-08: GCP c2d-highcpu-56, asia-northeast3, Ubuntu 24.04 LTS (DESIGN.md sections 7 and 8)
MASTER_SEED = 20261107               # fixed in DESIGN.md section 8; every stream is derived from it (cell_tests.rng_for)


def versions():
    import importlib.metadata as md
    out = {"python": platform.python_version()}
    for k in PINNED:
        if k != "python":
            try:
                out[k] = md.version(k)
            except md.PackageNotFoundError:
                out[k] = None
    return out


def environment_problems(found=None):
    """List of mismatches between the found versions and PINNED (empty list = pinned environment)."""
    found = versions() if found is None else found
    return ["%s: pinned %s, found %s" % (k, v, found.get(k)) for k, v in PINNED.items() if found.get(k) != v]


def check_environment():
    """Stops the run if a pinned package differs; also checks that the thread variables are 1."""
    bad = environment_problems()
    if os.environ.get("CELL_MIN_TRIALS", "60") != "60":
        bad.append("CELL_MIN_TRIALS is set (%s); only the synthetic suite may lower the 60-trial rule" % os.environ["CELL_MIN_TRIALS"])
    bad += ["%s is %r, must be '1'" % (v, os.environ.get(v)) for v in THREAD_VARS if os.environ.get(v) != "1"]
    if bad:
        raise SystemExit("environment differs from the pinned one:\n  " + "\n  ".join(bad))


def require_platform_fixed(addendum=None):
    """Every data stage calls this first. Refused while the placeholder is present, and refused on any other
    platform than DEFAULT_PLATFORM unless a dated addendum name is given (review of 2026-11-08, F1)."""
    if DEFAULT_PLATFORM == PLATFORM_PLACEHOLDER:
        raise SystemExit("refused: the platform is not fixed (cell_env.DEFAULT_PLATFORM holds the placeholder %r)" % PLATFORM_PLACEHOLDER)
    rec = platform_record()
    if not rec["is_default_platform"]:
        if addendum is None or not re.search(r"\d{4}-\d{2}-\d{2}", addendum):
            raise SystemExit("refused: this platform is %r, the design fixes %r; give --addendum <dated name> to run elsewhere"
                             % (rec["platform"], DEFAULT_PLATFORM))


def cpu_model():
    """CPU model string (Linux /proc/cpuinfo, macOS sysctl); recorded in every header (review SHOULD)."""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    try:
        import subprocess
        return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip() or None
    except Exception:
        return None


def platform_record():
    sysname = {"Darwin": "macOS"}.get(platform.system(), platform.system())
    mach = platform.machine()
    desc = "%s %s" % (sysname, mach)
    return {"platform": desc, "release": platform.release(), "python_build": sys.version.split("\n")[0],
            "versions": versions(), "threads": {v: os.environ.get(v) for v in THREAD_VARS},
            "master_seed": MASTER_SEED, "is_default_platform": desc == DEFAULT_PLATFORM, "cpu_model": cpu_model()}
