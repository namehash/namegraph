from pytest import mark
from hydra import initialize, compose

from generator.generation import (
    PermuteGenerator,
    PrefixGenerator,
    SuffixGenerator,
    WordnetSynonymsGenerator,
    W2VGenerator,
    CategoriesGenerator,
    Wikipedia2VGenerator,
    SubstringMatchGenerator,
)
from generator.generated_name import GeneratedName

import pytest

from generator.generation.random_generator import RandomGenerator
from generator.generation.secondary_matcher import SecondaryMatcher


def test_permuter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PermuteGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 6
        # print([x.applied_strategies for x in generated_names])


def test_permuter_limit():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PermuteGenerator(config)
        tokenized_name = GeneratedName(list(range(10)))  # 3628800 permutations
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == config.generation.limit


def test_prefix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PrefixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 2
        assert ('0x', 'asd', 'qwe', '123') in [x.tokens for x in generated_names]
        assert ('the', 'asd', 'qwe', '123') in [x.tokens for x in generated_names]


def test_prefix_prefixed():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PrefixGenerator(config)
        tokenized_name = GeneratedName(('0', 'xqwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 1
        assert ('0x', '0', 'xqwe', '123') not in [x.tokens for x in generated_names]
        assert ('the', '0', 'xqwe', '123') in [x.tokens for x in generated_names]


def test_suffix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SuffixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 2
        assert ('asd', 'qwe', '123', 'man') in [x.tokens for x in generated_names]
        assert ('asd', 'qwe', '123', 'coin') in [x.tokens for x in generated_names]


def test_suffix_suffixed():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SuffixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwem', 'an'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 1
        assert ('asd', 'qwem', 'an', 'man') not in [x.tokens for x in generated_names]
        assert ('asd', 'qwem', 'an', 'coin') in [x.tokens for x in generated_names]


def test_wordnetsynonyms():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = WordnetSynonymsGenerator(config)
        tokenized_name = GeneratedName(('my', 'domain', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert ('my', 'domain', '123') in [x.tokens for x in generated_names]
        assert ('my', 'area', '123') in [x.tokens for x in generated_names]


@pytest.mark.slow
def test_w2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = W2VGenerator(config)
        tokenized_name = GeneratedName(('my', 'pikachu', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert ('your', 'pikachu', '123') in [x.tokens for x in generated_names]
        assert ('my', 'mickey', '123') in [x.tokens for x in generated_names]


def test_categories():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = CategoriesGenerator(config)
        tokenized_name = GeneratedName(('my', 'pol', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert ('my', 'ukr', '123') in [x.tokens for x in generated_names]
        assert ('my', 'usa', '123') in [x.tokens for x in generated_names]


def test_categories_csv():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = CategoriesGenerator(config)
        tokenized_name = GeneratedName(('my', '0x8', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert ('my', '0x1', '123') in [x.tokens for x in generated_names]
        assert ('my', '0x2', '123') in [x.tokens for x in generated_names]


def test_random():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = RandomGenerator(config)
        tokenized_name = GeneratedName(('my', 'domain', '123'))
        generated_names = strategy.apply(tokenized_name)
        print(generated_names)
        assert len(
            set([x.tokens[0] for x in generated_names]) & {'google', 'youtube', 'facebook', 'baidu', 'yahoo', 'amazon',
                                                           'wikipedia', 'qq',
                                                           'twitter', 'live', 'global', '00002'}) == 8


def test_secondary_matcher():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SecondaryMatcher(config)
        tokenized_name = GeneratedName(('pay', 'fire', '123'))
        generated_names = strategy.apply(tokenized_name)
        print(generated_names)
        assert ('payshare',) in [x.tokens for x in generated_names]
        assert ('payfix',) in [x.tokens for x in generated_names]
        assert ('paygreen',) in [x.tokens for x in generated_names]
        assert ('paytrust',) in [x.tokens for x in generated_names]
        assert ('fire',) in [x.tokens for x in generated_names]


def test_wikipedia2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = Wikipedia2VGenerator(config)
        tokenized_name = GeneratedName(('billy', 'corgan'))
        generated_names = strategy.apply(tokenized_name)
        print(generated_names)
        assert ('the', 'smashing', 'pumpkins',) in [x.tokens for x in generated_names]


def test_substringmatchgenerator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = GeneratedName(('00', '-00', '-69-00'))
        generated_names = strategy.apply(tokenized_name)
        assert ('00-00-69-00',) in [x.tokens for x in generated_names]


def test_substringmatchgenerator_short():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = GeneratedName(('4',))
        generated_names = strategy.apply(tokenized_name)
        assert ('0000400',) in [x.tokens for x in generated_names]


def test_substringmatchgenerator_re_equals_tree():
    from generator.generation.substringmatch_generator import SuffixTreeImpl, ReImpl

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        re_impl = ReImpl(config)
        tree_impl = SuffixTreeImpl(config)

        assert '00000000000000000000000' in list(re_impl.find('0'))
        assert '00000000000000000000000' in list(tree_impl.find('0'))
        assert sorted(re_impl.find('0')) == sorted(tree_impl.find('0'))
