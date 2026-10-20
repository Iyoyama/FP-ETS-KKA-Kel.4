"""Problem definition: route optimisation over Surabaya culinary spots.

Two cost models share the same instance:
  * "distance": closed tour from the depot (node 0), minimise total road distance (km).
  * "tw":       same tour, but each stop has a time window; arriving after the window
                closes is penalised (soft time windows).  cost = km + LAMBDA * minutes_late.
Road distance/duration matrices come from OSRM (asymmetric: one-way streets matter).
"""
import csv
import json
import math
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent.parent / "data"
LAMBDA = 1.0  # km-equivalent penalty per minute of lateness


def load_instance():
    with open(DATA / "places.csv", newline="", encoding="utf-8") as f:
        places = list(csv.DictReader(f))
    for p in places:
        p["lat"], p["lon"] = float(p["lat"]), float(p["lon"])
        for k in ("service_min", "tw_open_min", "tw_close_min"):
            p[k] = float(p[k])
    D = np.array(json.load(open(DATA / "dist_m.json"))) / 1000.0  # km
    T = np.array(json.load(open(DATA / "dur_s.json"))) / 60.0      # minutes
    return places, D, T


def haversine_matrix(places):
    n = len(places)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            la1, lo1, la2, lo2 = map(math.radians, (places[i]["lat"], places[i]["lon"],
                                                    places[j]["lat"], places[j]["lon"]))
            a = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
            H[i, j] = 6371.0 * 2 * math.asin(math.sqrt(a))
    return H


class Problem:
    def __init__(self, places, D, T, mode="distance", lam=LAMBDA):
        self.places, self.D, self.T = places, D, T
        self.Dl, self.Tl = D.tolist(), T.tolist()
        self.n = len(places)
        self.m = self.n - 1                     # nodes to permute (depot fixed at 0)
        self.mode, self.lam = mode, lam
        self.svc = [p["service_min"] for p in places]
        self.open = [p["tw_open_min"] for p in places]
        self.close = [p["tw_close_min"] for p in places]

    def details(self, perm):
        tour = [0] + list(perm) + [0]
        dist = trav = wait = late = 0.0
        viol = 0
        t = 0.0
        for a, b in zip(tour, tour[1:]):
            dist += self.Dl[a][b]
            t += self.Tl[a][b]
            trav += self.Tl[a][b]
            if b == 0:
                break
            if t < self.open[b]:
                wait += self.open[b] - t
                t = self.open[b]
            if t > self.close[b]:
                late += t - self.close[b]
                viol += 1
            t += self.svc[b]
        return dict(dist_km=dist, travel_min=trav, wait_min=wait, late_min=late,
                    violations=viol, makespan_min=t)

    def cost(self, perm):
        Dl = self.Dl
        if self.mode == "distance":
            d, prev = 0.0, 0
            for b in perm:
                d += Dl[prev][b]
                prev = b
            return d + Dl[prev][0]
        Tl, svc, op, cl = self.Tl, self.svc, self.open, self.close
        d = late = t = 0.0
        prev = 0
        for b in perm:
            d += Dl[prev][b]
            t += Tl[prev][b]
            if t < op[b]:
                t = op[b]
            if t > cl[b]:
                late += t - cl[b]
            t += svc[b]
            prev = b
        d += Dl[prev][0]
        return d + self.lam * late


def held_karp(D):
    """Exact optimum of the asymmetric closed tour from node 0 (dynamic programming)."""
    n = D.shape[0]
    m = n - 1
    INF = float("inf")
    dp = np.full((1 << m, m), INF)
    par = np.full((1 << m, m), -1, dtype=np.int16)
    for j in range(m):
        dp[1 << j, j] = D[0, j + 1]
    Dm = D[1:, 1:]
    for mask in range(1, 1 << m):
        for j in range(m):
            if not (mask >> j) & 1 or mask == (1 << j):
                continue
            pm = mask ^ (1 << j)
            cand = dp[pm] + Dm[:, j]
            k = int(np.argmin(cand))
            dp[mask, j] = cand[k]
            par[mask, j] = k
    full = (1 << m) - 1
    tot = dp[full] + D[1:, 0]
    j = int(np.argmin(tot))
    best = float(tot[j])
    path, mask = [], full
    while j != -1:
        path.append(j + 1)
        pj = int(par[mask, j])
        mask ^= 1 << j
        j = pj
    return best, path[::-1]


def nearest_neighbour(prob):
    left = set(range(1, prob.n))
    cur, perm = 0, []
    while left:
        nxt = min(left, key=lambda j: prob.D[cur, j])
        perm.append(nxt)
        left.remove(nxt)
        cur = nxt
    return perm
