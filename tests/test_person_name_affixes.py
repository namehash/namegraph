from hydra import initialize, compose
from ens_normalize import is_ens_normalized
import json



def test_affixes_are_ens_normalized():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        affixes = json.load(open(config.generation.person_name_affixes_path))
        names = ['xd', 'lol', 'lmao', 'piotr', 'qwerty', 'gandalf', 'funnyshitass', 'pikachu']

        prefixes: set[str] = set(affixes['m_prefixes'].keys())
        prefixes.update(affixes['f_prefixes'].keys())

        suffixes: set[str] = set(affixes['m_suffixes'].keys())
        suffixes.update(affixes['f_suffixes'].keys())

        for name in names:
            for prefix in prefixes:
                new_name = prefix + name
                assert is_ens_normalized(new_name), f'unnormalized name with prefix: "{new_name}"'
            for suffix in suffixes:
                new_name = name + suffix
                assert is_ens_normalized(new_name), f'unnormalized name with suffix: "{new_name}"'
