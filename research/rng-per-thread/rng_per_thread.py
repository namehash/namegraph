import concurrent.futures
import threading
import random
import hashlib
from contextlib import contextmanager



def label2seed(label: str) -> int:
    hashed = hashlib.md5(label.encode('utf-8')).digest()
    seed = int.from_bytes(hashed, 'big') & 0xff_ff_ff_ff
    return seed


@contextmanager
def thread_rng():
    if 'thread_locals' in globals():
        thread_locals = globals()['thread_locals']
        rng = getattr(thread_locals, 'rng', None)
        rng = rng if rng is not None else random
    else:
        rng = random

    try:
        yield rng
    finally:
        pass


def init_seed_for_thread(seed_label: str):
    seed = label2seed(seed_label)
    thread_locals = globals()['thread_locals']
    thread_locals.rng = random.Random(seed)
    print(f"setting seed to {seed} (from label '{seed_label}')")


def thread_task(seed_label: str, t_id: int):
    init_seed_for_thread(seed_label)

    for _ in range(t_id):
        with thread_rng() as rng:
            print(f'[t{t_id}] sampling random value: {rng.random()}')


def execute_for_label(label: str):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(thread_task, seed_label=label, t_id=i): i for i in range(5)}

        for future in concurrent.futures.as_completed(futures):
            future.result()



if __name__ == '__main__':
    globals()['thread_locals'] = threading.local()

    execute_for_label('qwerty')
    print()
    execute_for_label('vitalik')
