import numpy as np


def softmax(x: np.ndarray):
    exps = np.exp(x - np.amax(x))
    exps_totals = np.sum(exps)
    return exps / exps_totals
