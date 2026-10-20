"""Jalankan semua eksperimen. Usage: python src/run_experiments.py [--osrm]"""
import sys, json, time, random, statistics as st
import numpy as np
from scipy.stats import mannwhitneyu
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from tsplib import *

use_osrm = "--osrm" in sys.argv
R = {"source": None}
I = Instance(use_osrm=use_osrm); R["source"] = I.source
SEEDS = list(range(30))
BUD1 = 5000

def run(inst, fname, budget, seeds, algos=ALGOS):
    f = inst.cost_tsp if fname == "tsp" else inst.cost_tw
    out = {}
    for a, fn in algos.items():
        runs = []
        for s in seeds:
            t = time.perf_counter(); B = fn(inst, f, budget, s); dt = time.perf_counter() - t
            runs.append(dict(best=B.best, perm=B.best_perm, curve=B.curve, time=dt))
        out[a] = runs
    return out

# ---- referensi ----
opt, opt_path = held_karp(I.D)
R["opt_tsp"] = opt; R["opt_path"] = opt_path
nn = nearest_neighbor(I); R["nn_tsp"] = I.cost_tsp(nn); R["nn_tw"] = I.cost_tw(nn); R["nn_perm"] = nn
rr = random.Random(0); rp = [rand_perm(I.m, rr) for _ in range(2000)]
R["rand_tsp"] = float(np.mean([I.cost_tsp(p) for p in rp])); R["rand_tw"] = float(np.mean([I.cost_tw(p) for p in rp]))
# efek mengabaikan time window: rute TSP-optimal dievaluasi pada model TW
sch, fin, late, wait = I.simulate(opt_path)
R["opt_tsp_under_tw"] = dict(cost=I.cost_tw(opt_path), late=late, wait=wait, finish=fin, n_late=sum(1 for x in sch if x[4] > 0))

# ---- E1: perbandingan utama (Surabaya-20) ----
E1 = {"tsp": run(I, "tsp", BUD1, SEEDS), "tw": run(I, "tw", BUD1, SEEDS)}
# ---- E2: sensitivitas anggaran ----
BUDS = [1000, 2000, 5000, 10000, 50000]; E2 = {}
for fn_ in ("tsp", "tw"):
    E2[fn_] = {}
    for b in BUDS:
        o = run(I, fn_, b, list(range(15)))
        E2[fn_][b] = {a: [r["best"] for r in rs] for a, rs in o.items()}
# ---- E3: skalabilitas ----
E3 = {}
for nr in (30, 60):
    inst = Instance(n_random=nr, seed=42); E3[nr] = {}
    for fn_ in ("tsp", "tw"):
        o = run(inst, fn_, 50000, list(range(30)))
        E3[nr][fn_] = {a: dict(best=[r["best"] for r in rs], time=[r["time"] for r in rs]) for a, rs in o.items()}
        E3[nr][fn_]["nn"] = inst.cost_tsp(nearest_neighbor(inst)) if fn_ == "tsp" else inst.cost_tw(nearest_neighbor(inst))

# ---- best-known TW (Surabaya-20) ----
allbest = min(r["best"] for rs in E1["tw"].values() for r in rs)
for b in E2["tw"].values():
    for v in b.values(): allbest = min(allbest, min(v))
R["best_tw"] = allbest
bestrun = min((r for rs in E1["tw"].values() for r in rs), key=lambda r: r["best"])
R["best_tw_perm"] = bestrun["perm"]
sch, fin, late, wait = I.simulate(bestrun["perm"])
R["best_tw_detail"] = dict(finish=fin, late=late, wait=wait, sched=sch, dist=I.cost_tsp(bestrun["perm"]))

# ---- ringkasan + uji statistik ----
def summ(vals):
    return dict(mean=float(np.mean(vals)), std=float(np.std(vals)), best=float(np.min(vals)), worst=float(np.max(vals)), median=float(np.median(vals)))
R["E1"] = {}
for fn_ in ("tsp", "tw"):
    ref = opt if fn_ == "tsp" else allbest
    R["E1"][fn_] = {}
    for a, rs in E1[fn_].items():
        v = [r["best"] for r in rs]; d = summ(v)
        d["gap_mean_pct"] = (d["mean"] / ref - 1) * 100; d["hit_pct"] = 100 * sum(1 for x in v if x <= ref * 1.001) / len(v)
        d["time_s"] = float(np.mean([r["time"] for r in rs])); d["curves"] = [r["curve"] for r in rs]
        d["vals"] = v; d["perm_best"] = min(rs, key=lambda r: r["best"])["perm"]
        R["E1"][fn_][a] = d
R["tests"] = {}
for fn_ in ("tsp", "tw"):
    R["tests"][fn_] = {}
    names = list(ALGOS)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            try: p = float(mannwhitneyu(R["E1"][fn_][a]["vals"], R["E1"][fn_][b]["vals"]).pvalue)
            except ValueError: p = 1.0
            R["tests"][fn_][f"{a}-{b}"] = p
R["E2"] = {fn_: {str(b): {a: summ(v) for a, v in d.items()} for b, d in E2[fn_].items()} for fn_ in E2}
R["E3"] = {str(nr): {fn_: {a: (summ(v["best"]) | dict(time_s=float(np.mean(v["time"])))) if a != "nn" else v for a, v in d.items()} for fn_, d in E3[nr].items()} for nr in E3}
R["names"] = I.names; R["coords"] = I.coords; R["open"] = I.open; R["close"] = I.close; R["cat"] = I.cat
R["params"] = dict(detour=DETOUR, speed=SPEED_KMH, service=SERVICE_MIN, start=START_MIN, late_pen=LATE_PEN, budget=BUD1)
json.dump(R, open(ROOT / "results/results.json", "w"), ensure_ascii=False)
print("selesai")
for fn_ in ("tsp", "tw"):
    for a, d in R["E1"][fn_].items():
        print(fn_, a, {k: round(v, 2) for k, v in d.items() if isinstance(v, float)})
print(R["opt_tsp"], R["best_tw"], R["opt_tsp_under_tw"], R["nn_tsp"], R["nn_tw"])
