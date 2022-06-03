import logging
import sys

import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os
from timeit import default_timer as timer
from datetime import timedelta
from typing import List

from generator.xgenerator import Generator

logger = logging.getLogger('generator')


def generate_from_file(file):
    for line in file:
        query = line.strip()
        yield query


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config: DictConfig) -> List[List[str]]:
    generator = Generator(config)

    if config.app.input == 'query':
        queries = [config.app.query]
    elif config.app.input == 'stdin':
        queries = generate_from_file(sys.stdin)
    else:
        logger.error(f"ERROR: Invalid input type (app.input parameter): {config.app.input}")
        sys.exit(1)

    all_suggestions = []
    for query in queries:
        logger.info(f"Generating names for: {query}")
        start = timer()
        suggestions = generator.generate_names(query, config.app.suggestions)
        end = timer()
        all_suggestions.append(suggestions)
        logger.info(f"Generation time (s): {timedelta(seconds=end - start)}")
        print(suggestions)

    return all_suggestions


if __name__ == "__main__":
    generate()
