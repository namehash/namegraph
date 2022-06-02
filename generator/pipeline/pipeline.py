from ..generation import WordnetSynonymsGenerator
from ..tokenization import BigramWordnetTokenizer
from ..filtering import DomainFilter

class Pipeline:
    def __init__(self, definition, config):
        self.definition = definition
        self.config = config
        self.tokenizers = []
        self.generators = []
        self.filters = []
        self._build()

    def apply(self, word):

        # the tokenizers are applied in parallel
        decomposition_set = set()
        for tokenizer in self.tokenizers:
            decomposition_set.update(tokenizer.tokenize(word))

        # the generators are applied sequentially
        suggestions = decomposition_set
        for generator in self.generators:
            generator_suggestions = set()
            for decomposition in suggestions:
                generator_suggestions.update(generator.generate(decomposition))

            suggestions = generator_suggestions

        suggestions = [''.join(tokens) for tokens in suggestions]
        # the filters are applied sequentially
        for filter in self.filters:
            suggestions = filter.apply(suggestions)

        return suggestions

    def _build(self):
        for tokenizer_class in self.definition.tokenizers:
            self.tokenizers.append(globals()[tokenizer_class](self.config))

        for generator_class in self.definition.generators:
            self.generators.append(globals()[generator_class](self.config))

        for filter_class in self.definition.filters:
            self.filters.append(globals()[filter_class](self.config))
