from typing import Optional


class Interpretation:
    def __init__(self, type: str, lang: str, tokenization, in_type_probability: float, features: Optional[dict] = None):
        self.type = type
        self.lang = lang
        self.tokenization = tokenization
        self.in_type_probability = in_type_probability
        self.features = features or {}

    def __str__(self):
        return f'Interpretation(type={self.type}, lang={self.lang}, tokenization={self.tokenization}'

    def __repr__(self):
        return str(self)

class InputName:
    """
    Stores everything related to one request.
    """

    def __init__(self, input_name, params):
        self.input_name = input_name
        self.params = params

        self.types_probabilities: dict[tuple[str, str], float] = {}
        self.interpretations: dict[tuple[str, str], list[Interpretation]] = {}

        self.strip_eth_namehash = None
        self.strip_eth_namehash_unicode = None
        self.strip_eth_namehash_unicode_replace_invalid = None
        self.strip_eth_namehash_unicode_replace_invalid_long_name = None
        self.strip_eth_namehash_unicode_long_name = None
        self.strip_eth_namehash_long_name = None

    def add_type(self, type: str, lang: str, probability: float, override: bool = True):
        if override or (type, lang) not in self.types_probabilities:
            self.types_probabilities[(type, lang)] = probability
        if type not in self.interpretations:
            self.interpretations[(type, lang)] = []

    def add_interpretation(self, interpretation: Interpretation):
        self.interpretations[(interpretation.type, interpretation.lang)].append(interpretation)
