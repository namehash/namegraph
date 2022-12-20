import random, logging
from itertools import accumulate
from typing import List, Tuple, Any

import numpy as np
import numpy.typing as npt

from .name_generator import NameGenerator
from ..domains import Domains

logger = logging.getLogger('generator')


def _softmax(x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    exps = np.exp(x - np.amax(x))
    exps_totals = np.sum(exps)
    return exps / exps_totals


class RandomAvailableNameGenerator(NameGenerator):
    """
    Sample only available random names.
    """

    def __init__(self, config):
        super().__init__(config)
        self.domains = Domains(config)

        if len(self.domains.only_available) < self.limit:
            logger.warning('the number of available (primary) domains for RandomAvailableNameGenerator is smaller than '
                           'the generation limit')

        self.names, probabilities = list(zip(*self.domains.only_available.items()))
        # greatest value is 4.0, so that probability of sampling custom name is 20 times higher: exp(4) ~= 20 * exp(1)
        probabilities = np.clip(probabilities, 0.0, 4.0)
        self.probabilities: list[float] = _softmax(probabilities).tolist()
        self.accumulated_probabilities = list(accumulate(self.probabilities))

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        if len(self.domains.only_available) >= self.limit:
            result = random.choices(self.names, cum_weights=self.accumulated_probabilities, k=self.limit)
        else:
            result = self.names
        return [(x,) for x in result]
