from pytest import mark
from hydra import initialize, compose

from generator.do import Do

import pytest

from generator.the_name import TheName


def test_do():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        do = Do(config)
        name = TheName('chasered', {})
        do.do(name)

        print(name.types_probabilities)
        for type, interpretations in name.interpretations.items():
            for interpretation in interpretations:
                print(type, interpretation.tokenization, interpretation.in_type_probability, interpretation.features)
