from hydra import initialize, compose

from name_graph.input_name import InputName
from name_graph.preprocessor import Preprocessor


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


def test_normalize():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        do = Preprocessor(config)

        name = InputName('$zeuś.eth', {})
        do.normalize(name)
        assert name.strip_eth_namehash == '$zeuś'
        assert name.strip_eth_namehash_unicode == '$zeus'
        assert name.strip_eth_namehash_unicode_replace_invalid == 'zeus'

        name = InputName('$zeuś' * 10, {})
        do.normalize(name)
        assert len(name.strip_eth_namehash_unicode_replace_invalid_long_name) == 30
        assert name.strip_eth_namehash_unicode_replace_invalid_long_name == 'zeuszeuszeuszeuszeuszeuszeusze'
        assert name.strip_eth_namehash_unicode_long_name == '$zeus$zeus$zeus$zeus$zeus$zeus'
        assert name.strip_eth_namehash_long_name == '$zeuś$zeuś$zeuś$zeuś$zeuś$zeuś'

        name = InputName('Zeus god', {})
        do.normalize(name)
        assert name.strip_eth_namehash == 'Zeus god'
        assert name.strip_eth_namehash_unicode == 'zeus god'
        assert name.strip_eth_namehash_unicode_replace_invalid == 'zeusgod'
        assert name.strip_eth_namehash_unicode_replace_invalid_long_name == 'zeusgod'
        assert name.strip_eth_namehash_unicode_long_name == 'zeus god'
        assert name.strip_eth_namehash_long_name == 'Zeus god'

        name = InputName('[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91]', {})
        do.normalize(name)
        assert name.strip_eth_namehash == ''
        assert name.strip_eth_namehash_unicode == ''
        assert name.strip_eth_namehash_unicode_replace_invalid == ''
        assert name.strip_eth_namehash_unicode_replace_invalid_long_name == ''
        assert name.strip_eth_namehash_unicode_long_name == ''
        assert name.strip_eth_namehash_long_name == ''