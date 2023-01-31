from generator.classifier.classifier import Classifier
from generator.the_name import TheName, Interpretation
from generator.tokenization import WordNinjaTokenizer
from namehash_common.ngrams import Ngrams


class NGramClassifier(Classifier):
    TYPE = 'ngram'

    def __init__(self, config):
        super().__init__(config)
        self.tokenizer = WordNinjaTokenizer(config)
        self.ngrams = Ngrams(config)

    def classify(self, name: TheName):
        normalized_name = name.strip_eth_namehash_unicode_replace_invalid
        # take normalized name and tokenize
        tokenizations = self.tokenizer.tokenize(normalized_name)

        # asses probability
        interpretations = []
        for tokenization in tokenizations:
            if tokenization:
                probability = self.ngrams.sequence_probability(tokenization)
                probability =max(probability, 1e-20) #TODO
                interpretation = Interpretation(self.TYPE, tokenization, probability)
                interpretations.append(interpretation)

        # calculate type prob
        if interpretations:
            highest_probability = interpretations[0].in_type_probability
            if highest_probability > 1e-10:  # TODO
                probability = 1.0
            else:
                probability = 0.5
        else:
            probability = 0.0
        name.add_type(self.TYPE, probability)

        # add information about type and tokenizations
        # should normalize probability?
        for interpretation in interpretations:
            name.add_interpretation(interpretation)
