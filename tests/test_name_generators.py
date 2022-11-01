from typing import List

from pytest import mark
from hydra import initialize, compose

from generator.generation import (
    HyphenGenerator,
    AbbreviationGenerator,
    FlagAffixGenerator,
    PermuteGenerator,
    PrefixGenerator,
    SuffixGenerator,
    WordnetSynonymsGenerator,
    W2VGenerator,
    CategoriesGenerator,
    Wikipedia2VGenerator,
    SpecialCharacterAffixGenerator,
    SubstringMatchGenerator,
)
from generator.generated_name import GeneratedName

import pytest

from generator.generation.random_generator import RandomGenerator
from generator.generation.secondary_matcher import SecondaryMatcher
from generator.domains import Domains

from generator.generation.substringmatch_generator import HAS_SUFFIX_TREE
needs_suffix_tree = pytest.mark.skipif(not HAS_SUFFIX_TREE, reason='Suffix tree not available')


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


def test_permuter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PermuteGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == 6
        # print([x.applied_strategies for x in generated_names])


def test_permuter_limit():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PermuteGenerator(config)
        tokenized_name = GeneratedName(tuple(map(str, range(10))))  # 3628800 permutations
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == config.generation.limit


def test_prefix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PrefixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == 2
        assert ('0x', 'asd', 'qwe', '123') in [x.tokens for x in generated_names]
        assert ('the', 'asd', 'qwe', '123') in [x.tokens for x in generated_names]


def test_prefix_prefixed():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PrefixGenerator(config)
        tokenized_name = GeneratedName(('0', 'xqwe', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == 1
        assert ('0x', '0', 'xqwe', '123') not in [x.tokens for x in generated_names]
        assert ('the', '0', 'xqwe', '123') in [x.tokens for x in generated_names]


def test_suffix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SuffixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == 2
        assert ('asd', 'qwe', '123', 'man') in [x.tokens for x in generated_names]
        assert ('asd', 'qwe', '123', 'coin') in [x.tokens for x in generated_names]


def test_suffix_suffixed():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SuffixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwem', 'an'))
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == 1
        assert ('asd', 'qwem', 'an', 'man') not in [x.tokens for x in generated_names]
        assert ('asd', 'qwem', 'an', 'coin') in [x.tokens for x in generated_names]


def test_wordnetsynonyms():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = WordnetSynonymsGenerator(config)
        tokenized_name = GeneratedName(('my', 'domain', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert ('my', 'domain', '123') in [x.tokens for x in generated_names]
        assert ('my', 'area', '123') in [x.tokens for x in generated_names]


def test_abbreviation_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = AbbreviationGenerator(config)
        tokenized_name = GeneratedName(('my', 'domain', '123', 'aa22'))
        generated_names = strategy.apply([tokenized_name])
        print([x.tokens for x in generated_names])

        assert ('my', 'd', '123', 'aa22') in [x.tokens for x in generated_names]
        assert ('m', 'd', '123', 'aa22') in [x.tokens for x in generated_names]
        assert ('m', 'domain', '123', 'aa22') in [x.tokens for x in generated_names]

        assert ('m', 'd', '1', 'aa22') not in [x.tokens for x in generated_names]
        assert ('my', 'domain', '1', 'aa22') not in [x.tokens for x in generated_names]
        assert ('my', 'domain', '123', 'aa22') not in [x.tokens for x in generated_names]


@pytest.mark.slow
def test_w2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = W2VGenerator(config)
        tokenized_name = GeneratedName(('my', 'pikachu', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert ('your', 'pikachu', '123') in [x.tokens for x in generated_names]
        assert ('my', 'mickey', '123') in [x.tokens for x in generated_names]


def test_hyphen_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = HyphenGenerator(config)
        tokenized_name = GeneratedName(('my', 'pikachu', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert ('my', '-', 'pikachu', '-', '123') == generated_names[0].tokens
        assert ('my', 'pikachu', '-', '123') in [x.tokens for x in generated_names]
        assert ('my', '-', 'pikachu', '123') in [x.tokens for x in generated_names]
        assert ('my', 'pikachu', '123') not in [x.tokens for x in generated_names]


def test_hyphen_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = FlagAffixGenerator(config)

        tokenized_name = GeneratedName(('adam', 'mickiewicz'))
        generated_names = strategy.apply([tokenized_name], params={'country': 'pl'})
        assert len(generated_names) == 1
        assert ('adam', 'mickiewicz', '🇵🇱') == generated_names[0].tokens

        tokenized_name = GeneratedName(('taras', 'shevchenko'))
        generated_names = strategy.apply([tokenized_name], params={'country': 'ua'})
        assert len(generated_names) == 1
        assert ('taras', 'shevchenko', '🇺🇦') == generated_names[0].tokens


def test_categories():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = CategoriesGenerator(config)
        tokenized_name = GeneratedName(('my', 'pol', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert ('my', 'ukr', '123') in [x.tokens for x in generated_names]
        assert ('my', 'usa', '123') in [x.tokens for x in generated_names]


def test_categories_csv():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = CategoriesGenerator(config)
        tokenized_name = GeneratedName(('my', '0x8', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert ('my', '0x1', '123') in [x.tokens for x in generated_names]
        assert ('my', '0x2', '123') in [x.tokens for x in generated_names]


@mark.parametrize(
    "overrides",
    [
        ["app.internet_domains=tests/data/top_internet_names_short.csv"]
    ]
)
def test_random(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        strategy = RandomGenerator(config)
        tokenized_name = GeneratedName(('my', 'domain', '123'))
        generated_names = strategy.apply([tokenized_name])
        assert len(
            set([x.tokens[0] for x in generated_names]) & {'google', 'youtube', 'facebook', 'baidu', 'yahoo', 'amazon',
                                                           'wikipedia', 'qq',
                                                           'twitter', 'live', 'global', '00002'}) == 8


def test_secondary_matcher():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SecondaryMatcher(config)
        tokenized_name = GeneratedName(('pay', 'fire', '123'))
        generated_names = strategy.apply([tokenized_name])
        print(generated_names)
        assert ('payshare',) in [x.tokens for x in generated_names]
        assert ('payfix',) in [x.tokens for x in generated_names]
        assert ('paygreen',) in [x.tokens for x in generated_names]
        assert ('paytrust',) in [x.tokens for x in generated_names]
        assert ('fire',) in [x.tokens for x in generated_names]


def test_secondary_matcher_sorting():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SecondaryMatcher(config)
        tokenized_name = GeneratedName(('fire', 'baba', 'orange'))
        generated_names = strategy.apply([tokenized_name])
        generated_tokens = [x.tokens for x in generated_names]

        assert ('orange',) in generated_tokens  # intersting_score = 69.98
        assert ('alibaba',) in generated_tokens  # intersting_score = 300.0
        assert ('fire',) in generated_tokens  # intersting_score = 190.5115

        orange_pos = generated_tokens.index(('orange',))
        alibaba_pos = generated_tokens.index(('alibaba',))
        fire_pos = generated_tokens.index(('fire',))

        assert alibaba_pos < fire_pos < orange_pos

def test_wikipedia2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = Wikipedia2VGenerator(config)
        tokenized_name = GeneratedName(('billy', 'corgan'))
        generated_names = strategy.apply([tokenized_name])
        print(generated_names)
        assert ('the', 'smashing', 'pumpkins',) in [x.tokens for x in generated_names]


def test_special_character_affix_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SpecialCharacterAffixGenerator(config)
        tokenized_name = GeneratedName(('billy', 'corgan'))
        generated_names = strategy.apply([tokenized_name])
        assert ('$', 'billy', 'corgan',) in [x.tokens for x in generated_names]
        assert ('_', 'billy', 'corgan',) in [x.tokens for x in generated_names]


def test_substringmatchgenerator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = GeneratedName(('00', '-00', '-69-00'))
        generated_names = strategy.apply([tokenized_name])
        assert ('00-00-69-00',) in [x.tokens for x in generated_names]


def test_substringmatchgenerator_short():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = GeneratedName(('4',))
        generated_names = strategy.apply([tokenized_name])
        assert ('0000400',) in [x.tokens for x in generated_names]


def test_substringmatchgenerator_sorting():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = GeneratedName(('0004206',))
        generated_names = strategy.apply([tokenized_name])
        generated_tokens = [x.tokens for x in generated_names]

        assert ('00042069',) in generated_tokens  # interesting_score = 988
        assert ('0000042069',) in generated_tokens  # interesting_score = 227

        longer_pos = generated_tokens.index(('0000042069',))
        shorter_pos = generated_tokens.index(('00042069',))

        assert shorter_pos < longer_pos


@needs_suffix_tree
@pytest.mark.xfail(reason='Suffix tree ignores unicode')
def test_substringmatchgenerator_re_equals_tree():
    from generator.generation.substringmatch_generator import SuffixTreeImpl, ReImpl, HAS_SUFFIX_TREE

    if not HAS_SUFFIX_TREE:
        pytest.skip()

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        re_impl = ReImpl(config)
        tree_impl = SuffixTreeImpl(config)
        assert sorted(re_impl.find('0')) == sorted(tree_impl.find('0'))


@needs_suffix_tree
def test_substringmatchgenerator_suffixtree_ignores_unicode():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = GeneratedName(('٢٣',))
        generated_names = strategy.apply([tokenized_name])
        assert len(generated_names) == 0
