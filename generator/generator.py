from typing import List

from generator.strategies import WordNetSynonyms, GeneratedName
from generator.tokenizers import TwoWordWordNetTokenizer
from generator.utils import uniq


class Generator():
    def __init__(self):
        self.domains = set()
        self.tokenizer = TwoWordWordNetTokenizer()
        self.strategies = [WordNetSynonyms()]

    def read_domains(self, path):
        with open(path) as domains_file:
            for line in domains_file:
                self.domains.add(line.strip()[:-4])
        return self.domains

    def generate_names(self, name: str, count: int) -> List[str]:
        suggestions = []
        for tokenized_name in self.tokenizer.tokenize(name):
            for strategy in self.strategies:
                generated_names = strategy.apply(GeneratedName(tokenized_name))
                suggestions.extend(generated_names)

        suggestions = [str(name) for name in suggestions]

        suggestions = uniq(suggestions)

        # suggestions = [s for s in suggestions if not s in self.domains]

        return suggestions[:count]
