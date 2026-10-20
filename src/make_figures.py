import json, pathlib, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
ROOT = pathlib.Path(__file__).resolve().parents[1]
R = json.load(open(ROOT / "results/results.json"))
OUT = ROOT / "results/fig"
COL = {"HC": "#1f77b4", "SA": "#e8710a", "GA": "#2ca25f", "MA": "#8e5bb5"}
LAB = {"HC": "Hill-Climbing", "SA": "Simulated Annealing", "GA": "Genetic Algorithm", "MA": "Memetic GA"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25, "figure.dpi": 100})
names, co = R["names"], R["coords"]
xy = np.array([(c[1], c[0]) for c in co])
def hm(m): return f"{int(m//60):02d}:{int(m%60):02d}"
CATC = {"depot": "#000000", "sarapan": "#e8710a", "sepanjang hari": "#1f77b4", "siang": "#2ca25f", "dessert": "#d6409f", "malam": "#6a3d9a"}

# F1 dataset
fig, ax = plt.subplots(figsize=(7.5, 5.2))
for c in CATC:
    idx = [i for i in range(len(names)) if R["cat"][i] == c]
    ax.scatter(xy[idx, 0], xy[idx, 1], s=130 if c == "depot" else 70, c=CATC[c], marker="*" if c == "depot" else "o", label=c, zorder=3, edgecolor="white")
for i, (x, y) in enumerate(xy): ax.annotate(str(i), (x, y), xytext=(5, 4), textcoords="offset points", fontsize=8)
ax.set_xlabel("Bujur"); ax.set_ylabel("Lintang"); ax.set_title("Dataset: 20 titik kuliner Surabaya + depot (0)"); ax.legend(title="Kategori jam buka", fontsize=8, loc="lower left")
ax.set_aspect(1 / np.cos(np.radians(7.27)))
fig.tight_layout(); fig.savefig(OUT / "f1_dataset.png", dpi=200); plt.close(fig)

# F2 konvergensi
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
for ax, fn, ref, ttl in ((axs[0], "tsp", R["opt_tsp"], "TSP (jarak)"), (axs[1], "tw", R["best_tw"], "TSPTW (durasi + penalti)")):
    for a in COL:
        cv = np.array(R["E1"][fn][a]["curves"]); g = (cv / ref - 1) * 100
        x = np.arange(1, cv.shape[1] + 1) * (R["params"]["budget"] // 200)
        ax.plot(x, np.median(g, 0), color=COL[a], label=LAB[a], lw=2)
        ax.fill_between(x, np.percentile(g, 25, 0), np.percentile(g, 75, 0), color=COL[a], alpha=.15)
    ax.set_ylim(0, 25); ax.set_xlabel("Jumlah evaluasi"); ax.set_ylabel("Gap terhadap referensi (%)"); ax.set_title(ttl)
axs[0].legend(fontsize=8)
fig.suptitle("Konvergensi (median, pita = kuartil 1–3, 30 seed)", y=1.02); fig.tight_layout(); fig.savefig(OUT / "f2_convergence.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# F3 boxplot
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
for ax, fn, ref, ttl, un in ((axs[0], "tsp", R["opt_tsp"], "TSP", "km"), (axs[1], "tw", R["best_tw"], "TSPTW", "menit")):
    data = [R["E1"][fn][a]["vals"] for a in COL]
    bp = ax.boxplot(data, patch_artist=True, widths=.55, medianprops=dict(color="black"))
    for p, a in zip(bp["boxes"], COL): p.set_facecolor(COL[a]); p.set_alpha(.7)
    ax.set_xticklabels(list(COL)); ax.axhline(ref, color="gray", ls="--", lw=1); ax.set_ylabel(f"Biaya ({un})"); ax.set_title(ttl + (" — garis = optimum eksak" if fn == "tsp" else " — garis = best-known"))
fig.tight_layout(); fig.savefig(OUT / "f3_boxplot.png", dpi=200); plt.close(fig)

# F4 rute
def draw(ax, perm, ttl):
    path = [0] + list(perm) + [0]
    for k in range(len(path) - 1):
        a, b = xy[path[k]], xy[path[k + 1]]
        ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="->", color="#444", lw=1.1, shrinkA=4, shrinkB=4))
    ax.scatter(xy[1:, 0], xy[1:, 1], s=60, c="#1f77b4", zorder=3, edgecolor="white")
    ax.scatter(*xy[0], s=200, marker="*", c="black", zorder=4)
    for k, nd in enumerate(perm, 1): ax.annotate(str(k), xy[nd], xytext=(4, 4), textcoords="offset points", fontsize=8, color="#b00020", weight="bold")
    ax.set_title(ttl, fontsize=10); ax.set_aspect(1 / np.cos(np.radians(7.27))); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.8))
draw(axs[0], R["opt_path"], f"TSP optimum eksak: {R['opt_tsp']:.1f} km")
draw(axs[1], R["best_tw_perm"], f"TSPTW terbaik: {R['best_tw_detail']['dist']:.1f} km, selesai {hm(R['best_tw_detail']['finish'])}")
fig.suptitle("Urutan kunjungan (angka merah = urutan, bintang = depot)", y=1.0); fig.tight_layout(); fig.savefig(OUT / "f4_routes.png", dpi=200); plt.close(fig)

# F5 timeline
sch = R["best_tw_detail"]["sched"]
fig, ax = plt.subplots(figsize=(9, 6))
for k, (nd, arr, st, en, lt) in enumerate(sch):
    y = len(sch) - k
    ax.barh(y, R["close"][nd] - R["open"][nd], left=R["open"][nd], color="#d9d9d9", height=.55)
    ax.barh(y, en - st, left=st, color="#1f77b4", height=.55)
ax.set_yticks(range(len(sch), 0, -1)); ax.set_yticklabels([f"{k+1}. {names[s[0]]}" for k, s in enumerate(sch)], fontsize=8)
xt = list(range(8 * 60, 25 * 60, 120)); ax.set_xticks(xt); ax.set_xticklabels([hm(x % 1440) for x in xt]); ax.set_xlim(8 * 60, 24.5 * 60)
ax.legend(handles=[Patch(color="#d9d9d9", label="Jam buka"), Patch(color="#1f77b4", label="Waktu kunjungan (20 mnt)")], loc="lower right", fontsize=8)
ax.set_title("Jadwal rute TSPTW terbaik: semua kunjungan dalam jam buka (0 menit telat)")
fig.tight_layout(); fig.savefig(OUT / "f5_timeline.png", dpi=200); plt.close(fig)

# F6 anggaran
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
for ax, fn, ref, ttl in ((axs[0], "tsp", R["opt_tsp"], "TSP"), (axs[1], "tw", R["best_tw"], "TSPTW")):
    bs = sorted(int(b) for b in R["E2"][fn])
    for a in COL:
        ax.plot(bs, [(R["E2"][fn][str(b)][a]["mean"] / ref - 1) * 100 for b in bs], "-o", color=COL[a], label=LAB[a], lw=2, ms=4)
    ax.set_xscale("log"); ax.set_xlabel("Anggaran evaluasi"); ax.set_ylabel("Gap rata-rata (%)"); ax.set_title(ttl)
axs[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT / "f6_budget.png", dpi=200); plt.close(fig)

# F7 skalabilitas
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
for ax, fn, ttl in ((axs[0], "tsp", "TSP"), (axs[1], "tw", "TSPTW")):
    w = .2
    for k, nr in enumerate(("30", "60")):
        best = min(R["E3"][nr][fn][a]["mean"] for a in COL)
        for j, a in enumerate(COL):
            d = R["E3"][nr][fn][a]
            ax.bar(k + (j - 1.5) * w, d["mean"] / best, w, yerr=d["std"] / best, color=COL[a], label=LAB[a] if k == 0 else None, capsize=2)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["30 titik antar-paket", "60 titik antar-paket"]); ax.set_ylabel("Biaya rata-rata / terbaik (1,0 = terbaik)"); ax.set_title(ttl + " (50.000 evaluasi)")
axs[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT / "f7_scale.png", dpi=200); plt.close(fig)
print("ok")
