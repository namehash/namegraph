import logging
import sys

import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os
from timeit import default_timer as timer
from datetime import timedelta
from typing import List, Dict

from generator.xgenerator import Generator

logger = logging.getLogger('generator')


def generate_from_file(file):
    for line in file:
        query = line.strip()
        yield query


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config: DictConfig) -> List[Dict[str, List[str]]]:
    logger.setLevel(config.app.logging_level)
    for handler in logger.handlers:
        handler.setLevel(config.app.logging_level)

    generator = Generator(config)

    if config.app.input == 'query':
        queries = [config.app.query]
    elif config.app.input == 'stdin':
        queries = generate_from_file(sys.stdin)
    else:
        logger.error(f"Invalid input type (app.input parameter): {config.app.input}")
        sys.exit(1)

    logger.info(f"Processing queries: {queries}")
    all_suggestions = []
    for query in queries:
        logger.info(f"Generating names for: {query}")
        start = timer()
        suggestions = generator.generate_names(query)
        end = timer()
        all_suggestions.append(suggestions)
        logger.info(f"Generation time (s): {timedelta(seconds=end - start)}")

    return all_suggestions


if __name__ == "__main__":
    generate()
