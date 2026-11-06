import sys, numpy as np, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
import sim
which, reps, w, of = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
out = []
for rep in range(reps):
    if rep % of != w: continue
    rng = np.random.default_rng([77, rep])
    n = 240
    y = rng.permutation(np.arange(n) % 2)
    X = rng.poisson(5.5, size=(n, 89)).astype(float)       # fully independent Poisson, no latent at all
    b = np.arange(n) // 20
    fl = sim.folds("main", X, y, b, seed=rep)
    est = sim.pipeline()
    p = sim.p1_binomial(est, X, y, fl) if which == "P1" else sim.p4_train_only(est, X, y, fl, 200, rng)
    out.append(p)
print(" ".join(f"{p:.5f}" for p in out))
