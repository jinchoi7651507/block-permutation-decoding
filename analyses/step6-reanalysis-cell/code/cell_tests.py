"""Tests for the Cell reanalysis: block permutation of the template among the blocks of each session (the whole
pipeline refitted), trial-level label shuffle with refit (reference), group helpers, smallest attainable p."""
from __future__ import annotations

import math
from collections import Counter

import cell_env  # noqa: F401  (thread variables = 1 before numpy)
import numpy as np

SEED = cell_env.MASTER_SEED   # master seed 20261107, fixed. Streams: SeedSequence([SEED, purpose, kind, index])


def rng_for(*keys):
    return np.random.default_rng(np.random.SeedSequence([SEED, *[int(k) for k in keys]]))


# ----------------------------------------------------------------------------- block labels
def block_labels(block, bins):
    """Per-block label (in order of np.unique(block)); 0 = no label. Raises if a block holds two labels."""
    ub = np.unique(block)
    out = []
    for b in ub:
        v = np.unique(bins[block == b])
        if len(v) != 1:
            raise ValueError("labels must be constant within a block (block %r holds %s)" % (b, v))
        out.append(int(v[0]))
    return ub, np.array(out)


def _adjacent_same(lab):
    """Number of consecutive block pairs (in session order, labelled blocks only) with the same bin."""
    l = lab[lab > 0]
    return int(np.sum(l[1:] == l[:-1]))


def permute_blocks(sess, bins, rng, match_adjacent=False, max_tries=10000):
    """New per-trial labels: the labels of the labelled blocks are permuted among the labelled blocks of the
    session (counts per bin kept). Blocks without a label stay without. With match_adjacent, only permutations
    with the same number of consecutive same-bin block pairs as observed are kept (rejection sampling): the
    pre-specified sensitivity for the penalty that makes a colour near the previous one less likely."""
    ub, lab = block_labels(sess.block, bins)
    idx = np.where(lab > 0)[0]
    obs_adj = _adjacent_same(lab)
    for _ in range(max_tries):
        new = lab.copy()
        new[idx] = lab[rng.permutation(idx)]
        if not match_adjacent or _adjacent_same(new) == obs_adj:
            break
    else:
        new = lab.copy()      # no matching arrangement found: the observed labelling (the session adds no information)
    out = np.zeros_like(bins)
    for b, l in zip(ub, new):
        out[sess.block == b] = l
    return out


def permute_block_sequences(sess, seq_bins, rng):
    """Estimated-template secondary (option A of PRECHECK section 5): whole within-block label sequences are
    permuted among the labelled blocks of the session, aligned by progression in the block: the receiving block
    of length L takes the label at relative position i/(L-1) of the donor sequence. seq_bins: per-column labels
    that may change within a block (0 = no label)."""
    ub = np.unique(sess.block)
    seqs = [seq_bins[sess.block == b] for b in ub]
    cols = [np.where(sess.block == b)[0] for b in ub]
    idx = [i for i, s in enumerate(seqs) if np.any(s > 0)]
    donor = rng.permutation(idx)
    out = np.zeros_like(seq_bins)
    for i, d in zip(idx, donor):
        L, Ld = len(cols[i]), len(seqs[d])
        pos = np.rint(np.arange(L) * (Ld - 1) / max(L - 1, 1)).astype(int)
        out[cols[i]] = seqs[d][pos]
    return out


def permute_trials(sess, bins, rng):
    """Reference: permute the labels among the labelled trials of the session."""
    out = bins.copy()
    idx = np.where(bins > 0)[0]
    out[idx] = bins[rng.permutation(idx)]
    return out


# ----------------------------------------------------------------------------- counting
def n_arrangements(bin_counts):
    """Distinct assignments of bins to the blocks of one session with the observed counts per bin."""
    n = math.factorial(sum(bin_counts))
    for c in bin_counts:
        n //= math.factorial(c)
    return n


def min_p_session(bin_counts, relabel_invariant=True):
    """Smallest attainable exact p for a session-level test with a statistic that depends only on the partition of
    blocks into bins. If the statistic is invariant to renaming the bins, each renaming of the observed labelling that
    keeps the counts (equal counts permute) is another arrangement with the same value."""
    n = n_arrangements(bin_counts)
    twins = 1
    if relabel_invariant:
        cnt = Counter(bin_counts)
        twins = int(np.prod([math.factorial(v) for v in cnt.values()]))
    return twins / n, n, twins


def log10_joint_arrangements(per_session_counts):
    return float(sum(math.log10(n_arrangements(c)) for c in per_session_counts))


def mc_p(obs, null, undefined_counts_as_exceedance=True):
    """p = (1 + #{null >= obs} + #{null undefined}) / (len(null) + 1); an undefined observed value gives NaN."""
    null = np.asarray(null, float)
    if obs is None or not np.isfinite(obs):
        return float("nan")
    nan = np.isnan(null)
    ge = np.sum(null[~nan] >= obs - 1e-12) + (nan.sum() if undefined_counts_as_exceedance else 0)
    return float((1 + ge) / (len(null) + 1))


def holm(pvals):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


# ----------------------------------------------------------------------------- statistic and tests
def statistic(result, roi):
    """Primary statistic: mean over draws and the three progression levels of validation accuracy; None if the
    design does not exist for this labelling."""
    a = result["acc"][roi]
    return None if a is None else float(np.mean(a))


def check_true_labels(sessions, bins_by_session):
    """Gate item G8, part 1: the labels are constant within every block of every session. Returns (ok, message)."""
    for s, b in zip(sessions, bins_by_session):
        try:
            block_labels(s.block, b)
        except ValueError as e:
            return False, "session %s: %s" % (s.sid, e)
    return True, "constant within blocks in all %d sessions" % len(sessions)


def design_summary(sessions, bins_by_session, rois, roi_sessions):
    """Design of a labelling: dict with n_prog (None if undefined), n_neurons, n_qual per ROI."""
    from cellport import build_design
    d = build_design(sessions, bins_by_session, rois, roi_sessions)
    return {"n_prog": d["n_prog"], "n_neurons": d["n_neurons"], "n_qual": d["n_qual"], "defined": d["n_prog"] is not None}


def hp_counts(hp):
    """{roi: [n SVM fits, n fits whose chosen log10 C is at the upper edge of the grid]}"""
    from cellport import GRID_TOP
    return {r: [len(v), int(sum(1 for x in v if abs(x - GRID_TOP) < 1e-9))] for r, v in hp.items()}


def one_labelling(args):
    """Worker: args = (kind, index, sessions, bins_by_session, rois, roi_sessions, n_draws, variant, as_written,
    purpose, grid). kind: 'obs', 'block', 'trial', 'block_adjacent' or 'sequence'.
    Returns (index, {roi: stat or nan}, n_prog, n_neurons, hp_counts)."""
    from cellport import run_decoder
    kind, i, sessions, bins, rois, roi_sessions, n_draws, variant, as_written, purpose, grid = args
    rng = rng_for(purpose, {"obs": 0, "block": 1, "trial": 2, "block_adjacent": 3, "sequence": 4}[kind], i)
    if kind == "block":
        bins = [permute_blocks(s, b, rng) for s, b in zip(sessions, bins)]
    elif kind == "block_adjacent":
        bins = [permute_blocks(s, b, rng, match_adjacent=True) for s, b in zip(sessions, bins)]
    elif kind == "sequence":
        bins = [permute_block_sequences(s, b, rng) for s, b in zip(sessions, bins)]
    elif kind == "trial":
        bins = [permute_trials(s, b, rng) for s, b in zip(sessions, bins)]
    res = run_decoder(sessions, bins, rois, roi_sessions, n_draws, rng, variant, as_written, grid)
    st = {r: (np.nan if statistic(res, r) is None else statistic(res, r)) for r in rois}
    return i, st, res["n_prog"], res["n_neurons"], hp_counts(res["hp"])


def permutation_test(sessions, bins, rois, roi_sessions, n_perm, n_draws, kind="block", variant="across",
                     as_written=True, purpose=1, workers=1, grid="coarse"):
    """Observed statistic and null per ROI. The observed labelling and every permuted labelling go through the same
    function (design, trial sampling, hyperparameter search, calibration, combiner), each with n_draws draws.
    If the observed design is undefined the p is NaN and the status says 'no test'."""
    jobs = [("obs", 0, sessions, bins, rois, roi_sessions, n_draws, variant, as_written, purpose, grid)]
    jobs += [(kind, i, sessions, bins, rois, roi_sessions, n_draws, variant, as_written, purpose, grid)
             for i in range(1, n_perm + 1)]
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            out = list(ex.map(one_labelling, jobs, chunksize=1))
    else:
        out = [one_labelling(j) for j in jobs]
    return collect(out, rois)


def collect(out, rois):
    """out: list of one_labelling results, the observed labelling first. Builds the p values and the status."""
    obs = out[0]
    res = {}
    for r in rois:
        null = np.array([o[1][r] for o in out[1:]])
        p = mc_p(obs[1][r], null)
        res[r] = {"observed": obs[1][r], "null": null, "p": p,
                  "status": "no test: observed design undefined" if not np.isfinite(obs[1][r]) else "tested"}
    res["design_obs"] = {"n_prog": obs[2], "n_neurons": obs[3]}
    res["design_null"] = [(o[2], o[3]) for o in out[1:]]
    res["hp"] = {r: [sum(o[4][r][0] for o in out), sum(o[4][r][1] for o in out)] for r in rois}
    return res
