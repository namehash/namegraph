import random
import numpy.random as np_random
import hashlib
from contextlib import contextmanager


# todo: remove prints
# todo: raise ValueError if no rng set for a thread

# todo: is "sth in globals()" thread-safe? what are the alternatives?


def label2seed(label: str) -> int:
    hashed = hashlib.md5(label.encode('utf-8')).digest()
    seed = int.from_bytes(hashed, 'big') & 0xff_ff_ff_ff
    return seed


def init_seed_for_thread(seed_label: str):
    seed = label2seed(seed_label)
    thread_locals = globals()['thread_locals']
    thread_locals.random_rng = random.Random(seed)
    thread_locals.numpy_rng = np_random.default_rng(seed)
    print(f"setting seed to {seed} (from label '{seed_label}')")


@contextmanager
def random_rng():
    """A context manager yielding a `random.Random` object for a thread or a `random` module."""
    if 'thread_locals' in globals():
        thread_locals = globals()['thread_locals']
        rng = getattr(thread_locals, 'random_rng', None)
        if rng is None:
            print(f'[warning] random_rng not set in thread_locals')
        rng = rng if rng is not None else random
    else:
        rng = random

    try:
        yield rng
    finally:
        pass


@contextmanager
def numpy_rng():
    """A context manager yielding a `np.random.default_rng` object for a thread or a `np.random` module."""
    if 'thread_locals' in globals():
        thread_locals = globals()['thread_locals']
        rng = getattr(thread_locals, 'numpy_rng', None)
        if rng is None:
            print(f'[warning] numpy_rng not set in thread_locals')
        rng = rng if rng is not None else np_random
    else:
        rng = np_random

    try:
        yield rng
    finally:
        pass
