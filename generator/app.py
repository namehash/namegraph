import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os
from timeit import default_timer as timer
from datetime import timedelta
from typing import List

if __name__ == "__main__":
    from sorting import CountSorter
    from tokenization import BigramTokenizer
    from filtering import DomainFilter
    from generation import WordnetSynonymsGenerator
    from pipeline import Pipeline
else:
    from .sorting import CountSorter
    from .tokenization import BigramTokenizer
    from .filtering import DomainFilter
    from .generation import WordnetSynonymsGenerator
    from .pipeline import Pipeline


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config : DictConfig) -> List[str]:

    start = timer()

    suggestions = []
    for definition in config.app.pipelines:
        suggestions.extend(Pipeline(definition, config).apply(config.app.query))

    end = timer()

    print(f"Generation time (s): {timedelta(seconds=end-start)}")
    print(suggestions)
    return suggestions

if __name__ == "__main__":
    generate()
