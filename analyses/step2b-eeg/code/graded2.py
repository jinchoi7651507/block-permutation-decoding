#!/usr/bin/env python3
"""Step 2b addendum 2: graded positive control with a label-free noise ladder (DESIGN-v2-ADDENDUM-2.md).

The addendum 1 ladder (R1-R5, Q30-Q48) did not reach the target band on the first pilot subjects; the mixing steps were
found to be a design error (they exchange epochs between paired opposite-state blocks, which makes the observed EC/EO
vector the least favourable member of the P5 null set; review-graded-pilot-statistician.txt). This module adds a
weakening that does not use the labels or the block structure:

  N<c>  every feature value plus independent Gaussian noise with standard deviation c x (that feature's standard
        deviation over all kept epochs of the subject, computed once, before any label is used), c in NOISE_LADDER.

The stamped files (run_2b.py, graded_pilot.py, sim.py) are not edited: weaken2() handles the N rules and passes every
other rule to run_2b.weaken unchanged; install() registers the N rules in run_2b for the main run.
"""
import numpy as np

import run_2b as r

NOISE_LADDER = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24)   # EEG review S1: finer steps
NOISE_RULES = {f"N{c}": ("noise", None, float(c)) for c in NOISE_LADDER}
NOISE_ORDER = tuple(NOISE_RULES)
_stamped_weaken = r.weaken


def weaken2(X, blk, chs, rule, rng):
    """N rules: label-free additive noise (blocks and epochs unchanged). Other rules: run_2b.weaken as stamped."""
    if rule not in NOISE_RULES:
        return _stamped_weaken(X, blk, chs, rule, rng)
    c = NOISE_RULES[rule][2]
    sd = X.std(axis=0, ddof=1)
    return X + rng.standard_normal(X.shape) * (c * sd), blk


def install():
    """Register the N rules in run_2b (for run_graded2.py). An N rule is not deterministic (third field c > 0), so
    run_2b.main keeps all 50 pos_graded weakenings."""
    r.GRADED_RULES.update(NOISE_RULES)
    r.weaken = weaken2
