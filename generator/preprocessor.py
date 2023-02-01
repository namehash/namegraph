from generator.classifier.ngram_classifier import NGramClassifier
from generator.classifier.person_name_classifier import PersonNameClassifier
from generator.normalization import StripEthNormalizer, NamehashNormalizer, UnicodeNormalizer, ReplaceInvalidNormalizer, \
    LongNameNormalizer
from generator.the_name import TheName, Interpretation


class Preprocessor:
    def __init__(self, config):
        self.strip_eth_normalizer = StripEthNormalizer(config)
        self.namehash_normalizer = NamehashNormalizer(config)
        self.unicode_normalizer = UnicodeNormalizer(config)
        self.replace_invalid_normalizer = ReplaceInvalidNormalizer(config)
        self.long_name_normalizer = LongNameNormalizer(config)

        self.ngram_classifier = NGramClassifier(config)
        self.person_name_classifier = PersonNameClassifier(config)

    def normalize(self, name: TheName):
        strip_eth = self.strip_eth_normalizer.normalize(name.input_name)
        name.strip_eth_namehash = self.namehash_normalizer.normalize(strip_eth)

        name.strip_eth_namehash_unicode = self.unicode_normalizer.normalize(name.strip_eth_namehash)
        name.strip_eth_namehash_unicode_replace_invalid = self.replace_invalid_normalizer.normalize(
            name.strip_eth_namehash_unicode)
        name.strip_eth_namehash_unicode_replace_invalid_long_name = self.long_name_normalizer.normalize(
            name.strip_eth_namehash_unicode_replace_invalid)

        name.strip_eth_namehash_unicode_long_name = self.long_name_normalizer.normalize(name.strip_eth_namehash_unicode)
        name.strip_eth_namehash_long_name = self.long_name_normalizer.normalize(name.strip_eth_namehash)

    def classify(self, name: TheName):
        if name.strip_eth_namehash:
            self.ngram_classifier.classify(name)
            # self.person_name_classifier.classify(name)
            # self.add_other_type(name)

    def add_other_type(self, name: TheName):
        OTHER_PROBABILITY = 0.1
        OTHER_TYPE = 'other'
        name.add_type(OTHER_TYPE, OTHER_PROBABILITY)

        interpretation = Interpretation(OTHER_TYPE, (name.strip_eth_namehash_unicode_replace_invalid_long_name,), 1.0) #TODO none?
        name.add_interpretation(interpretation)

    def do(self, name: TheName):
        self.normalize(name)
        self.classify(name)

        # pipelines definition and execution
        # 1. zbuduj wszystkie piepeliney
        # 2. utwórz sorter dla każdej interpretacji

        # 1. choice type
        # 2. choice interpretation
        # 3. choice pipeline

        # jak obsluzyć generatory bez tokenizera?
        # co gdy każdy typ ma 0%? generatory nie wymagające tokenizacji powinny działać
        # czy wagi generatorów powinny być globalne. nie, bo dla imion w2v możmey ustawić na 1
        # czy wagi per typ? czy może na interpretację?

        # TODO znalezc input, który ma kilka interpretacji i zapytać Josiah

        # przygotować kilka przykładów
        # ngram-en, ngram-pl, name-en, name-pl
        # ngram-en
        # ngram-pl
        # name-en
        # name-pl
        # none

        # w arkuszu rozpisać rozwiązania
