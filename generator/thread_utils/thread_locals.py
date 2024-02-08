import threading
import hashlib
import logging
import random
import numpy.random as np_random


logger = logging.getLogger('generator')

thread_locals = threading.local()


def init_seed_for_thread(seed_label: str):
    global thread_locals

    hashed = hashlib.md5(seed_label.encode('utf-8')).digest()
    seed = int.from_bytes(hashed, 'big') & 0xff_ff_ff_ff
    logger.info(f"Setting seed for a thread: {seed}")
    thread_locals.random_rng = random.Random(seed)
    thread_locals.numpy_rng = np_random.default_rng(seed)
