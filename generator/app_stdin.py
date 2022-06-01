import sys

import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os
from timeit import default_timer as timer
from datetime import timedelta
from typing import List

from generator.xgenerator import Generator


def generate_from_file(file):
    for line in file:
        query = line.strip()
        yield query


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config: DictConfig):
    generator = Generator(config)

    for query in generate_from_file(sys.stdin):
        start = timer()
        suggestions = generator.generate_names(query, config.app.suggestions)
        end = timer()
        print(f"Generation time (s): {timedelta(seconds=end - start)}", file=sys.stderr)
        print(suggestions)


if __name__ == "__main__":
    generate()
