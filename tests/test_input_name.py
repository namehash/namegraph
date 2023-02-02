from pytest import mark
from hydra import initialize, compose

from generator.preprocessor import Preprocessor

import pytest

from generator.input_name import InputName


def test_do():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        do = Preprocessor(config)
        name = InputName('chasered', {})
        do.do(name)

        print(name.types_probabilities)
        for type, interpretations in name.interpretations.items():
            for interpretation in interpretations:
                print(type, interpretation.tokenization, interpretation.in_type_probability, interpretation.features)
