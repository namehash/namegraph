import math

# TODO do we really need this? better way?
from generator import logger


def ln(x: float, default: int = -1000) -> float:
    try:
        return math.log(x)
    except ValueError as ex:
        logger.warning(f'domain error for {x}, returning default value of {default}')
        return default


def logsumexp(log_xs: list[float]) -> float:
    log_x_max = max(log_xs)
    internal_sum = sum([math.exp(log_x - log_x_max) for log_x in log_xs])
    return log_x_max + math.log(internal_sum)
