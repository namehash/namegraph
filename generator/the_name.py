from typing import Optional


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

    def __init__(self, input_name, params):
        self.input_name = input_name
        self.params = params

        self.types_probabilities: dict[str, float] = {}
        self.interpretations: dict[str, list[Interpretation]] = {}

        self.strip_eth_namehash = None
        self.strip_eth_namehash_unicode = None
        self.strip_eth_namehash_unicode_replace_invalid = None
        self.strip_eth_namehash_unicode_replace_invalid_long_name = None
        self.strip_eth_namehash_unicode_long_name = None
        self.strip_eth_namehash_long_name = None

    def add_type(self, type: str, probability: float):
        self.types_probabilities[type] = probability
        if type not in self.interpretations:
            self.interpretations[type] = []

    def add_interpretation(self, interpretation: Interpretation):
        self.interpretations[interpretation.type].append(interpretation)
