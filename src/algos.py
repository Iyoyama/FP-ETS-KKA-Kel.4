"""Hill-Climbing, Simulated Annealing, Genetic Algorithm and a Memetic Algorithm.

All algorithms use the same evaluation budget (number of cost-function calls) so that
the comparison is fair.  A tour is a permutation of nodes 1..n-1 (depot 0 is implicit).
"""
import math
import random


class Evaluator:
    def __init__(self, prob, budget, grid=250):
        self.prob, self.budget, self.grid = prob, budget, grid
        self.n = 0
        self.best = float("inf")
        self.best_perm = None
        self.history = []  # best-so-far sampled every `grid` evaluations

    def __call__(self, perm):
        c = self.prob.cost(perm)
        self.n += 1
        if c < self.best:
            self.best, self.best_perm = c, list(perm)
        if self.n % self.grid == 0:
            self.history.append(self.best)
        return c

    def done(self):
        return self.n >= self.budget


# ---------------------------------------------------------------- neighbourhood
def random_move(perm, rng):
    m = len(perm)
    new = perm[:]
    r = rng.random()
    i, j = sorted(rng.sample(range(m), 2))
    if r < 0.5:                       # 2-opt: reverse a segment
        new[i:j + 1] = reversed(new[i:j + 1])
    elif r < 0.75:                    # swap two stops
        new[i], new[j] = new[j], new[i]
    else:                             # insertion: move one stop elsewhere
        x = new.pop(i)
        new.insert(j, x)
    return new


def random_perm(m, rng):
    p = list(range(1, m + 1))
    rng.shuffle(p)
    return p


# ---------------------------------------------------------------- Hill-Climbing
def hill_climbing(ev, rng, patience=400):
    """Stochastic first-improvement hill climbing with random restarts."""
    m = ev.prob.m
    while not ev.done():
        cur = random_perm(m, rng)
        c = ev(cur)
        stall = 0
        while stall < patience and not ev.done():
            nb = random_move(cur, rng)
            cn = ev(nb)
            if cn < c:
                cur, c, stall = nb, cn, 0
            else:
                stall += 1
    return ev


# ---------------------------------------------------------------- Simulated Annealing
def simulated_annealing(ev, rng, t0_factor=1.0, t_ratio=1e-3):
    m = ev.prob.m
    cur = random_perm(m, rng)
    c = ev(cur)
    # calibrate the initial temperature from random moves
    deltas = []
    for _ in range(100):
        d = abs(ev(random_move(cur, rng)) - c)
        deltas.append(d)
    t0 = t0_factor * (sum(deltas) / len(deltas))
    remaining = max(1, ev.budget - ev.n)
    alpha = t_ratio ** (1.0 / remaining)
    T = t0
    while not ev.done():
        nb = random_move(cur, rng)
        cn = ev(nb)
        d = cn - c
        if d < 0 or rng.random() < math.exp(-d / max(T, 1e-12)):
            cur, c = nb, cn
        T *= alpha
    return ev


# ---------------------------------------------------------------- Genetic Algorithm
def order_crossover(p1, p2, rng):
    m = len(p1)
    a, b = sorted(rng.sample(range(m), 2))
    child = [None] * m
    child[a:b + 1] = p1[a:b + 1]
    used = set(child[a:b + 1])
    fill = [g for g in p2[b + 1:] + p2[:b + 1] if g not in used]
    idx = list(range(b + 1, m)) + list(range(0, a))
    for pos, g in zip(idx, fill):
        child[pos] = g
    return child


def _tournament(pop, fit, k, rng):
    best = None
    for _ in range(k):
        i = rng.randrange(len(pop))
        if best is None or fit[i] < fit[best]:
            best = i
    return pop[best]


def genetic_algorithm(ev, rng, pop_size=100, p_cx=0.9, p_mut=0.3, k=3, elite=2,
                      ls_prob=0.0, ls_steps=0):
    """GA with OX crossover; if ls_prob>0 it becomes a Memetic Algorithm (GA + local search)."""
    m = ev.prob.m
    pop = [random_perm(m, rng) for _ in range(pop_size)]
    fit = [ev(p) for p in pop]
    while not ev.done():
        order = sorted(range(len(pop)), key=fit.__getitem__)
        new_pop = [pop[i][:] for i in order[:elite]]
        new_fit = [fit[i] for i in order[:elite]]
        while len(new_pop) < pop_size and not ev.done():
            p1, p2 = _tournament(pop, fit, k, rng), _tournament(pop, fit, k, rng)
            child = order_crossover(p1, p2, rng) if rng.random() < p_cx else p1[:]
            if rng.random() < p_mut:
                child = random_move(child, rng)
            cc = ev(child)
            if ls_prob and rng.random() < ls_prob:       # Lamarckian local search
                for _ in range(ls_steps):
                    if ev.done():
                        break
                    nb = random_move(child, rng)
                    cn = ev(nb)
                    if cn < cc:
                        child, cc = nb, cn
            new_pop.append(child)
            new_fit.append(cc)
        pop, fit = new_pop, new_fit
    return ev


def memetic_algorithm(ev, rng):
    return genetic_algorithm(ev, rng, pop_size=40, ls_prob=0.2, ls_steps=40)


ALGOS = {
    "HC": hill_climbing,
    "SA": simulated_annealing,
    "GA": genetic_algorithm,
    "MA": memetic_algorithm,
}
