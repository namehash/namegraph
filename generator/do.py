from generator.classifier.ngram_classifier import NGramClassifier
from generator.classifier.person_name_classifier import PersonNameClassifier
from generator.normalization import StripEthNormalizer, NamehashNormalizer, UnicodeNormalizer, ReplaceInvalidNormalizer
from generator.the_name import TheName


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

        # pipelines definition and execution

        # 1. choice type
        # 2. choice interpretation
        # 3. choice pipeline

        # jak obsluzyć generatory bez tokenizera?
        # czy wagi generatorów powinny być globalne. nie, bo dla imion w2v możmey ustawić na 1
        # czy wagi per typ? czy może na interpretację?

        # TODO znalezc input, który ma kilka interpretacji i zapytać Josiah