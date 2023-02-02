from generator.classifier.ngram_classifier import NGramClassifier
from generator.classifier.person_name_classifier import PersonNameClassifier
from generator.normalization import (
    StripEthNormalizer,
    NamehashNormalizer,
    UnicodeNormalizer,
    ReplaceInvalidNormalizer,
    LongNameNormalizer
)
from generator.input_name import InputName, Interpretation

from omegaconf import DictConfig


class Preprocessor:
    def __init__(self, config: DictConfig) -> None:
        self.strip_eth_normalizer = StripEthNormalizer(config)
        self.namehash_normalizer = NamehashNormalizer(config)
        self.unicode_normalizer = UnicodeNormalizer(config)
        self.replace_invalid_normalizer = ReplaceInvalidNormalizer(config)
        self.long_name_normalizer = LongNameNormalizer(config)

        self.ngram_classifier = NGramClassifier(config)
        self.person_name_classifier = PersonNameClassifier(config)

    def normalize(self, name: InputName) -> None:
        strip_eth = self.strip_eth_normalizer.normalize(name.input_name)
        name.strip_eth_namehash = self.namehash_normalizer.normalize(strip_eth)

        name.strip_eth_namehash_unicode \
            = self.unicode_normalizer.normalize(name.strip_eth_namehash)
        name.strip_eth_namehash_unicode_replace_invalid \
            = self.replace_invalid_normalizer.normalize(name.strip_eth_namehash_unicode)
        name.strip_eth_namehash_unicode_replace_invalid_long_name \
            = self.long_name_normalizer.normalize(name.strip_eth_namehash_unicode_replace_invalid)

        name.strip_eth_namehash_unicode_long_name \
            = self.long_name_normalizer.normalize(name.strip_eth_namehash_unicode)
        name.strip_eth_namehash_long_name \
            = self.long_name_normalizer.normalize(name.strip_eth_namehash)

    def classify(self, name: InputName) -> None:
        if name.strip_eth_namehash:
            self.ngram_classifier.classify(name)
            self.person_name_classifier.classify(name)
            self.add_other_type(name)

    def add_other_type(self, name: InputName) -> None:
        OTHER_PROBABILITY = 0.1
        OTHER_TYPE = 'other'
        name.add_type(OTHER_TYPE, OTHER_PROBABILITY)

        interpretation = Interpretation(
            OTHER_TYPE, (name.strip_eth_namehash_unicode_replace_invalid_long_name,), 1.0
        )  # TODO none?
        name.add_interpretation(interpretation)

    def do(self, name: InputName) -> None:
        self.normalize(name)
        self.classify(name)
