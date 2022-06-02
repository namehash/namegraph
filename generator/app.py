import sys

import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os
from timeit import default_timer as timer
from datetime import timedelta
from typing import List

from generator.xgenerator import Generator


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config: DictConfig) -> List[str]:
    generator = Generator(config)

    start = timer()
    suggestions = generator.generate_names(config.app.query, config.app.suggestions)
    end = timer()

    print(f"Generation time (s): {timedelta(seconds=end - start)}", file=sys.stderr)
    print(suggestions)
    return suggestions


if __name__ == "__main__":
    generate()
