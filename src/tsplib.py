"""Inti proyek: data, fungsi biaya, dan 4 algoritma (HC, SA, GA, Memetic GA).

Dua varian masalah (semua rute berawal & berakhir di depot = node 0):
  * TSP    : minimalkan total jarak tempuh (km)
  * TSPTW  : minimalkan durasi total tur (menit, termasuk menunggu) + penalti keterlambatan
             terhadap jam buka/tutup tiap tempat (soft time window).
Semua algoritma memakai anggaran evaluasi fungsi biaya yang SAMA agar adil.
"""
import csv, math, random, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
DETOUR = 1.30        # faktor jalan: jarak jalan ~ 1.3 x garis lurus (jika OSRM tidak tersedia)
SPEED_KMH = 25.0     # kecepatan rata-rata kota
SERVICE_MIN = 20     # lama makan/icip di tiap titik
START_MIN = 8 * 60   # mulai 08:00
LATE_PEN = 5.0       # penalti per menit keterlambatan (setara menit durasi)


def hhmm(s):
    if ":" in s:
        h, m = s.split(":"); return int(h) * 60 + int(m)
    return int(s)


def haversine(a, b):
    R = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dphi = p2 - p1; dl = math.radians(b[1] - a[1])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


class Instance:
    def __init__(self, use_osrm=False, n_random=0, seed=42):
        """n_random=0: dataset kuliner Surabaya (20 titik). n_random>0: titik antar-paket acak di
        bounding box Surabaya (untuk uji skalabilitas), service 5 menit."""
        rows = list(csv.DictReader(open(ROOT / "data/places.csv", encoding="utf-8")))
        self.service = SERVICE_MIN
        if n_random:
            rr = random.Random(seed); dep = rows[0]
            rows = [dep]
            for i in range(1, n_random + 1):
                o = rr.randrange(8 * 60, 15 * 60, 15); w = rr.randrange(180, 481, 15)
                rows.append(dict(name=f"Paket {i}", lat=rr.uniform(-7.34, -7.22), lon=rr.uniform(112.68, 112.80),
                                 open=str(o), close=str(o + w), category="antar"))
            self.service = 5
            use_osrm = False
        self.names = [r["name"] for r in rows]
        self.coords = [(float(r["lat"]), float(r["lon"])) for r in rows]
        self.open = [hhmm(r["open"]) for r in rows]
        self.close = [hhmm(r["close"]) for r in rows]
        self.cat = [r["category"] for r in rows]
        n = len(rows)
        self.n = n                      # termasuk depot
        self.m = n - 1                  # jumlah pelanggan
        if use_osrm:
            self.D = np.load(ROOT / "data/dist_osrm.npy").tolist()
            self.T = np.load(ROOT / "data/time_osrm.npy").tolist()
            self.source = "OSRM (jarak jalan asli)"
        else:
            self.D = [[haversine(self.coords[i], self.coords[j]) * DETOUR for j in range(n)] for i in range(n)]
            self.T = [[d / SPEED_KMH * 60 for d in row] for row in self.D]
            self.source = f"Haversine x {DETOUR} (aproksimasi jarak jalan)"

    # ---------- fungsi biaya ----------
    def cost_tsp(self, perm):
        D = self.D; prev = 0; s = 0.0
        for c in perm:
            s += D[prev][c]; prev = c
        return s + D[prev][0]

    def simulate(self, perm):
        """Kembalikan jadwal rinci: list (node, tiba, mulai, selesai, telat) + total."""
        T = self.T; t = START_MIN; prev = 0; late = 0.0; wait = 0.0; sched = []
        for c in perm:
            t += T[prev][c]; arr = t
            if t < self.open[c]:
                wait += self.open[c] - t; t = self.open[c]
            lt = max(0.0, t - self.close[c]); late += lt
            sched.append((c, arr, t, t + self.service, lt))
            t += self.service; prev = c
        t += T[prev][0]
        return sched, t, late, wait

    def cost_tw(self, perm):
        T = self.T; op = self.open; cl = self.close; sv = self.service
        t = START_MIN; prev = 0; late = 0.0
        for c in perm:
            t += T[prev][c]
            o = op[c]
            if t < o: t = o
            x = t - cl[c]
            if x > 0: late += x
            t += sv; prev = c
        t += T[prev][0]
        return (t - START_MIN) + LATE_PEN * late


# ---------- operator tetangga ----------
def neighbor(p, rng):
    n = len(p); q = p[:]
    r = rng.random()
    i = rng.randrange(n); j = rng.randrange(n)
    while j == i: j = rng.randrange(n)
    if i > j: i, j = j, i
    if r < 0.5:                      # 2-opt (balik segmen)
        q[i:j + 1] = q[i:j + 1][::-1]
    elif r < 0.75:                   # swap
        q[i], q[j] = q[j], q[i]
    else:                            # insert / relocate
        x = q.pop(j); q.insert(i, x)
    return q


class Budget:
    """Pencacah evaluasi + log konvergensi (best-so-far tiap `step` evaluasi)."""
    def __init__(self, total, f, step=None):
        self.total, self.f, self.step = total, f, step or max(1, total // 200)
        self.used = 0; self.best = float("inf"); self.best_perm = None; self.curve = []

    def __call__(self, p):
        v = self.f(p); self.used += 1
        if v < self.best:
            self.best = v; self.best_perm = p[:]
        if self.used % self.step == 0:
            self.curve.append(self.best)
        return v

    @property
    def left(self): return self.total - self.used


def rand_perm(m, rng):
    p = list(range(1, m + 1)); rng.shuffle(p); return p


# ---------- 1) Hill Climbing (random-restart, first-improvement) ----------
def hill_climbing(inst, f, budget, seed, patience=1000):
    rng = random.Random(seed); B = Budget(budget, f)
    while B.left > 0:
        cur = rand_perm(inst.m, rng); cv = B(cur); fails = 0
        while B.left > 0 and fails < patience:
            q = neighbor(cur, rng); qv = B(q)
            if qv < cv: cur, cv, fails = q, qv, 0
            else: fails += 1
    return B


# ---------- 2) Simulated Annealing (jadwal geometrik sadar-anggaran) ----------
def simulated_annealing(inst, f, budget, seed, t0_frac=0.03, t_ratio=1e-2):
    rng = random.Random(seed); B = Budget(budget, f)
    cur = rand_perm(inst.m, rng); cv = B(cur)
    scale = sum(f(rand_perm(inst.m, rng)) for _ in range(20)) / 20   # skala biaya (tidak dihitung ke anggaran)
    T0 = t0_frac * scale; Tend = T0 * t_ratio
    while B.left > 0:
        T = T0 * (Tend / T0) ** (B.used / budget)
        q = neighbor(cur, rng); qv = B(q)
        d = qv - cv
        if d <= 0 or rng.random() < math.exp(-d / T):
            cur, cv = q, qv
    return B


# ---------- 3) Genetic Algorithm (OX + tournament + elitism) ----------
def order_crossover(a, b, rng):
    n = len(a); i, j = sorted(rng.sample(range(n), 2))
    child = [None] * n; child[i:j + 1] = a[i:j + 1]
    used = set(child[i:j + 1]); pos = (j + 1) % n
    for g in b[j + 1:] + b[:j + 1]:
        if g not in used:
            child[pos] = g; pos = (pos + 1) % n
    return child


def genetic_algorithm(inst, f, budget, seed, pop=60, pc=0.9, pm=0.9, k=5, elite=2, memetic=0):
    """memetic>0: tiap anak diperbaiki dengan `memetic` langkah hill-climbing (Memetic GA)."""
    rng = random.Random(seed); B = Budget(budget, f)
    P = [rand_perm(inst.m, rng) for _ in range(pop)]
    V = [B(p) for p in P]
    def tourn():
        c = rng.sample(range(pop), k); return P[min(c, key=lambda i: V[i])]
    while B.left > 0:
        order = sorted(range(pop), key=lambda i: V[i])
        NP = [P[i][:] for i in order[:elite]]; NV = [V[i] for i in order[:elite]]
        while len(NP) < pop and B.left > 0:
            a, b = tourn(), tourn()
            c = order_crossover(a, b, rng) if rng.random() < pc else a[:]
            if rng.random() < pm: c = neighbor(c, rng)
            cv = B(c)
            for _ in range(memetic):
                if B.left <= 0: break
                q = neighbor(c, rng); qv = B(q)
                if qv < cv: c, cv = q, qv
            NP.append(c); NV.append(cv)
        P, V = NP, NV
        pop_now = len(P)
        if pop_now < pop:   # anggaran habis di tengah generasi
            break
    return B


def memetic_ga(inst, f, budget, seed):
    return genetic_algorithm(inst, f, budget, seed, pop=30, pc=0.9, pm=0.5, k=5, elite=2, memetic=5)


# ---------- baseline & optimum ----------
def nearest_neighbor(inst, start_time_aware=False):
    left = set(range(1, inst.n)); cur = 0; p = []
    while left:
        nx = min(left, key=lambda j: inst.D[cur][j]); p.append(nx); left.remove(nx); cur = nx
    return p


def held_karp(D):
    """Optimum eksak TSP (DP bitmask, tervektorisasi). D: (n x n) termasuk depot=0."""
    D = np.array(D); n = D.shape[0] - 1; Dc = D[1:, 1:]; d0 = D[0, 1:]; d1 = D[1:, 0]
    N = 1 << n; INF = 1e18
    dp = np.full((N, n), INF); par = np.full((N, n), -1, dtype=np.int8)
    for j in range(n): dp[1 << j, j] = d0[j]
    masks = np.arange(N); pc = np.array([bin(x).count("1") for x in range(N)])
    for layer in range(2, n + 1):
        ms = masks[pc == layer]
        for k in range(n):
            mk = ms[(ms >> k) & 1 == 1]
            prev = mk ^ (1 << k)
            cand = dp[prev, :] + Dc[:, k][None, :]
            j = cand.argmin(axis=1)
            dp[mk, k] = cand[np.arange(len(mk)), j]; par[mk, k] = j
    full = N - 1
    tot = dp[full, :] + d1; last = int(tot.argmin()); best = float(tot[last])
    path = []; m = full; k = last
    while k != -1:
        path.append(k + 1); pk = int(par[m, k]); m ^= (1 << k); k = pk
    return best, path[::-1]


ALGOS = {"HC": hill_climbing, "SA": simulated_annealing, "GA": genetic_algorithm, "MA": memetic_ga}
ALGO_NAMES = {"HC": "Hill-Climbing (restart)", "SA": "Simulated Annealing", "GA": "Genetic Algorithm", "MA": "Memetic GA (GA+HC)"}
