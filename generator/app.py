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
else:
    from .sorting import CountSorter
    from .tokenization import BigramTokenizer
    from .filtering import DomainFilter
    from .generation import WordnetSynonymsGenerator


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config : DictConfig) -> List[str]:

    root = Path(os.path.abspath(__file__)).parents[1]

    tokenizer = BigramTokenizer(config)
    generator = WordnetSynonymsGenerator(config)
    filter = DomainFilter(config, root)
    sorter = CountSorter(config)

    start = timer()

    decomposition_list = tokenizer.tokenize(config.generator.query)
    suggestions = []
    for decomposition in decomposition_list:
        suggestions.extend(generator.generate(decomposition))
    suggestions = sorter.sort(suggestions)
    suggestions = filter.apply(suggestions)

    end = timer()
    print(f"Generation time (s): {timedelta(seconds=end-start)}")
    print(suggestions)
    return suggestions

if __name__ == "__main__":
    generate()
