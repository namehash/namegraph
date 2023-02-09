from generator.classifier.classifier import Classifier
from generator.input_name import InputName, Interpretation
from generator.tokenization import WordNinjaTokenizer
from namehash_common.ngrams import Ngrams


class NGramClassifier(Classifier):
    TYPE = 'ngram'
    LANG = 'en'

    def __init__(self, config):
        super().__init__(config)
        self.tokenizer = WordNinjaTokenizer(config)
        self.ngrams = Ngrams(config)

    def classify(self, name: InputName):
        normalized_name = name.strip_eth_namehash_unicode_replace_invalid_long_name
        # take normalized name and tokenize
        tokenizations = self.tokenizer.tokenize(normalized_name)

        # asses probability
        interpretations = []
        for tokenization in tokenizations:
            if tokenization:
                probability = self.ngrams.sequence_probability(tokenization)
                probability = max(probability, 1e-20)  # TODO
                interpretation = Interpretation(self.TYPE, self.LANG, tokenization, probability)
                interpretations.append(interpretation)

        # calculate type prob

        # add information about type and tokenizations
        # should normalize probability?
        # TODO: there will be problem if more interpretations with different languages will be returned
        for interpretation in interpretations:
            sequence_probability = interpretation.in_type_probability
            if sequence_probability > 1e-10:  # TODO
                probability = 1.0
            else:
                probability = 0.5
            name.add_type(self.TYPE, self.LANG, probability, override=False)
            name.add_interpretation(interpretation)
