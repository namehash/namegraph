from generator.classifier.classifier import Classifier
from generator.the_name import TheName, Interpretation
from generator.utils.person_names import PersonNames


class PersonNameClassifier(Classifier):
    TYPE = 'person'

    def __init__(self, config):
        super().__init__(config)
        self.pn = PersonNames(config)

    def classify(self, name: TheName):
        normalized_name = name.strip_eth_namehash_unicode_replace_invalid
        # take normalized name and process
        raw_interpretations = self.pn.tokenize(normalized_name)

        # asses probability
        interpretations = []
        for probability, country, tokenization, person_name_type, gender in raw_interpretations:
            features = {'country': country, 'person_name_type': person_name_type, 'gender': gender}
            interpretation = Interpretation(self.TYPE, tokenization, probability, features=features)
            interpretations.append(interpretation)

        # calculate type prob
        if interpretations:
            highest_probability = interpretations[0].in_type_probability
            if highest_probability > 1e-10:
                probability = 1.0
            else:
                probability = 0.5
        else:
            probability = 0.0
        name.add_type(self.TYPE, probability)

        # add information about type and tokenizations
        # TODO should normalize probability?
        for interpretation in interpretations:
            name.add_interpretation(interpretation)
