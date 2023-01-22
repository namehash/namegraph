from typing import Optional

from generator.classifier.ngram_classifier import NGramClassifier
from generator.classifier.person_name_classifier import PersonNameClassifier
from generator.normalization import StripEthNormalizer, NamehashNormalizer, UnicodeNormalizer, ReplaceInvalidNormalizer


class Interpretation:
    def __init__(self, type: str, tokenization, in_type_probability: float, features: Optional[dict] = None):
        self.type = type
        self.tokenization = tokenization
        self.in_type_probability = in_type_probability
        self.features = features or {}


class TheName:
    """
    Stores everything related to one request.
    """

    def __init__(self, input_name):
        self.input_name = input_name

        self.types_probabilities: dict[str, float] = {}
        self.interpretations: dict[str, list[Interpretation]] = {}

        self.strip_eth_namehash = None
        self.strip_eth_namehash_unicode = None
        self.strip_eth_namehash_unicode_replace_invalid = None

    def add_type(self, type: str, probability: float):
        self.types_probabilities[type] = probability
        if type not in self.interpretations:
            self.interpretations[type] = []

    def add_interpretation(self, interpretation: Interpretation):
        self.interpretations[interpretation.type].append(interpretation)


class Do:
    def __init__(self, config):
        self.strip_eth_normalizer = StripEthNormalizer(config)
        self.namehash_normalizer = NamehashNormalizer(config)
        self.unicode_normalizer = UnicodeNormalizer(config)
        self.replace_invalid_normalizer = ReplaceInvalidNormalizer(config)

        self.ngram_classifier = NGramClassifier(config)
        self.person_name_classifier = PersonNameClassifier(config)

    def normalize(self, name: TheName):
        strip_eth = self.strip_eth_normalizer.normalize(name.input_name)
        name.strip_eth_namehash = self.namehash_normalizer.normalize(strip_eth)

        name.strip_eth_namehash_unicode = self.unicode_normalizer.normalize(name.strip_eth_namehash)
        name.strip_eth_namehash_unicode_replace_invalid = self.replace_invalid_normalizer.normalize(
            name.strip_eth_namehash_unicode)

    def classify(self, name: TheName):
        self.ngram_classifier.classify(name)
        self.person_name_classifier.classify(name)

    def do(self, name: TheName):
        self.normalize(name)
        self.classify(name)
