import numpy as np
import numpy.typing as npt


def softmax(x: npt.NDArray[np.float]):
    exps = np.exp(x - np.amax(x))
    exps_totals = np.sum(exps)
    return exps / exps_totals
