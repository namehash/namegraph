import logging
from operator import itemgetter

from nltk.corpus import wordnet as wn
from typing import List, Dict, Tuple, Any
import itertools
import collections

from .combination_limiter import CombinationLimiter, prod
from .name_generator import NameGenerator
from ..input_name import InputName, Interpretation

logger = logging.getLogger('generator')


class WordnetSynonymsGenerator(NameGenerator):
    """
    Replace tokens with synonyms.
    """

    def __init__(self, config):
        super().__init__(config)
        wn.synsets('dog')  # init wordnet
        self.combination_limiter = CombinationLimiter(self.limit)

    def generate(self, tokens: Tuple[str, ...]) -> List[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        result = []
        synsets = [list(self._get_lemmas_for_word(t).items()) for t in tokens]

        synsets = self.combination_limiter.limit(synsets)

        synset_lengths = [len(synset) for synset in synsets]
        combinations = prod(synset_lengths)
        logger.debug(f'Wordnet synsets lengths: {synset_lengths} gives {combinations}')
        logger.debug(f'Wordnet synsets: {[[synset_tuple[0] for synset_tuple in synset][:100] for synset in synsets]}')

        for synset_tuple in itertools.product(*synsets):
            tokens = [t[0] for t in synset_tuple]
            counts = [t[1] for t in synset_tuple]
            result.append((tokens, sum(counts)))

        result = (tuple(x[0]) for x in sorted(result, key=lambda x: x[1], reverse=True))
        return result

    def _get_lemmas_for_word(self, word: str) -> Dict[str, int]:
        synsets = wn.synsets(word)
        lemmas = []
        for synset in synsets:
            lemmas.extend([str(lemma.name()) for lemma in synset.lemmas()])
        lemmas = [l for l in lemmas if '_' not in l]

        stats = collections.defaultdict(int)
        for l in lemmas:
            stats[l] += 1

        # keep the original token in the output
        stats[word] += 1

        return dict(sorted(stats.items(), key=itemgetter(1), reverse=True))

    def generate2(self, name: InputName, interpretation: Interpretation) -> List[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': interpretation.tokenization}
