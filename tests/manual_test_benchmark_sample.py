import random
from itertools import accumulate

import numpy as np

from generator.generation.random_available_name_generator import _softmax

random.seed(0)
np.random.seed(0)

n = 70  # 250000 70
a = list(range(n))
probabilities = [random.random() for _ in range(n)]
probabilities[0] = 100
probabilities = np.clip(probabilities, 0.0, 4.0)
probabilities: list[float] = _softmax(probabilities).tolist()
accumulated_probabilities = list(accumulate(probabilities))

k = 200
k = min(n, k)

rng = np.random.default_rng()

import heapq
import math
import random


def WeightedSelectionWithoutReplacement():
    elt = [(math.log(random.random()) / probabilities[i], i) for i in range(len(probabilities))]
    return [x[1] for x in heapq.nlargest(k, elt)]


def numpy_w_replace():
    return np.random.choice(a, size=k, replace=True, p=probabilities)


def numpy_wo_replace():
    return np.random.choice(a, size=k, replace=False, p=probabilities)


def random_w_replace_acc():
    return random.choices(a, cum_weights=accumulated_probabilities, k=k)


def random_w_replace():
    return random.choices(a, weights=probabilities, k=k)


def weighted_shuffle():
    # http://utopia.duth.gr/~pefraimi/research/data/2007EncOfAlg.pdf ?
    order = sorted(range(len(a)), key=lambda i: random.random() ** (1.0 / probabilities[i]))
    return [a[i] for i in order[:k]]


def weighted_shuffle_tree():
    items = a
    weights = probabilities
    if len(items) != len(weights):
        raise ValueError("Unequal lengths")

    n = len(items)
    nodes = [None for _ in range(n)]

    def left_index(i):
        return 2 * i + 1

    def right_index(i):
        return 2 * i + 2

    def total_weight(i=0):
        if i >= n:
            return 0
        this_weight = weights[i]
        if this_weight <= 0:
            raise ValueError("weight can't be zero or negative")
        left_weight = total_weight(left_index(i))
        right_weight = total_weight(right_index(i))
        nodes[i] = [this_weight, left_weight, right_weight]
        return this_weight + left_weight + right_weight

    def sample(i=0):
        this_w, left_w, right_w = nodes[i]
        total = this_w + left_w + right_w
        r = total * random.random()
        if r < this_w:
            nodes[i][0] = 0
            return i
        elif r < this_w + left_w:
            chosen = sample(left_index(i))
            nodes[i][1] -= weights[chosen]
            return chosen
        else:
            chosen = sample(right_index(i))
            nodes[i][2] -= weights[chosen]
            return chosen

    total_weight()  # build nodes tree

    return (items[sample()] for _ in range(k))


def rng_wo_replace_shuffle_false():
    return rng.choice(a, k, replace=False, p=probabilities, shuffle=False)


def rng_wo_replace_shuffle_true():
    return rng.choice(a, k, replace=False, p=probabilities, shuffle=True)


def rng_w_replace_shuffle_false():
    return rng.choice(a, k, replace=True, p=probabilities, shuffle=False)


def rng_w_replace_shuffle_true():
    return rng.choice(a, k, replace=True, p=probabilities, shuffle=True)


def fast_choice(options, probs):
    x = random.random()
    cum = 0
    for i, p in enumerate(probs):
        cum += p
        if x < cum:
            return options[i]
    return options[-1]


def check(r):
    print(len(set(r)))


def test_numpy_wo_replace(benchmark):
    r = benchmark(numpy_wo_replace)
    check(r)


def test_numpy_w_replace(benchmark):
    r = benchmark(numpy_w_replace)
    check(r)


def test_random_w_replace_acc(benchmark):
    r = benchmark(random_w_replace_acc)
    check(r)


def test_random_w_replace(benchmark):
    r = benchmark(random_w_replace)
    check(r)


def test_weighted_shuffle(benchmark):
    r = benchmark(weighted_shuffle)
    check(r)


def test_weighted_shuffle_tree(benchmark):
    r = benchmark(weighted_shuffle_tree)
    check(r)


def test_rng_wo_replace_shuffle_false(benchmark):
    r = benchmark(rng_wo_replace_shuffle_false)
    check(r)


def test_rng_wo_replace_shuffle_true(benchmark):
    r = benchmark(rng_wo_replace_shuffle_true)
    check(r)


def test_rng_w_replace_shuffle_false(benchmark):
    r = benchmark(rng_w_replace_shuffle_false)
    check(r)


def test_rng_w_replace_shuffle_true(benchmark):
    r = benchmark(rng_w_replace_shuffle_true)
    check(r)


def test_WeightedSelectionWithoutReplacement(benchmark):
    r = benchmark(WeightedSelectionWithoutReplacement)
    check(r)
