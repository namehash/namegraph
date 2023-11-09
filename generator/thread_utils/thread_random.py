import logging
import random

import numpy.random as np_random

from .thread_locals import thread_locals


# todo: is "sth in globals()" and "globals()['thread_locals']" thread-safe?

logger = logging.getLogger('generator')

def get_random_rng():
    """Returns a `random.Random` object for a thread or a `random` module."""
    if 'thread_locals' in globals():
        rng_per_thread = getattr(globals()['thread_locals'], 'random_rng', None)
        if rng_per_thread is None:
            logger.warning(f'Using random module instead of a thread-specific rng!')
        rng = rng_per_thread if rng_per_thread is not None else random
    else:
        logger.warning(f'Using random module instead of a thread-specific rng!')
        rng = random
    return rng


def get_numpy_rng():
    """Returns a `np.random.default_rng` object for a thread or a `np.random` module."""
    if 'thread_locals' in globals():
        rng_per_thread = getattr(globals()['thread_locals'], 'numpy_rng', None)
        if rng_per_thread is None:
            logger.warning(f'Using numpy.random module instead of a thread-specific rng!')
        rng = rng_per_thread if rng_per_thread is not None else np_random
    else:
        logger.warning(f'Using numpy.random module instead of a thread-specific rng!')
        rng = np_random

    return rng
