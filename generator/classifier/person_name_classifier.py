import json

from generator.classifier.classifier import Classifier
from generator.input_name import InputName, Interpretation
from generator.utils.person_names import PersonNames


class PersonNameClassifier(Classifier):
    TYPE = 'person'

    def __init__(self, config):
        super().__init__(config)
        self.pn = PersonNames(config)
        self.country2languages = json.load(open(config.person_names.country2langs_path))

    def classify(self, name: InputName):
        normalized_name = name.strip_eth_namehash_unicode_replace_invalid
        # take normalized name and process
        raw_interpretations = self.pn.tokenize(normalized_name, topn=1)  # TODO: parameter

        # asses probability
        interpretations = []
        for probability, country, tokenization, person_name_type, gender in raw_interpretations:
            features = {'country': country, 'person_name_type': person_name_type, 'gender': gender}
            lang = self.country2languages.get(country, ('en',))[0]
            interpretation = Interpretation(self.TYPE, lang, tokenization, probability, features=features)
            interpretations.append(interpretation)

        # calculate type prob

        # add information about type and tokenizations
        # TODO should normalize probability?
        for interpretation in interpretations:
            person_probability = interpretation.in_type_probability
            if person_probability > 1e-10:
                probability = 1.0
            else:
                probability = 0.5

            name.add_type(self.TYPE, interpretation.lang, probability, override=False)
            name.add_interpretation(interpretation)
