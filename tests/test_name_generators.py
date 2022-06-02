from pytest import mark
from hydra import initialize, compose

from generator.generation import (
    PermuteGenerator,
    GeneratedName,
    PrefixGenerator,
    SuffixGenerator,
    WordnetSynonymsGenerator,
    W2VGenerator,
    CategoriesGenerator,
)

import pytest


def test_permuter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PermuteGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 6
        # print([x.applied_strategies for x in generated_names])


def test_prefix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = PrefixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 2
        assert ('0x', 'asd', 'qwe', '123') in [x.tokens for x in generated_names]
        assert ('the', 'asd', 'qwe', '123') in [x.tokens for x in generated_names]


def test_suffix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        strategy = SuffixGenerator(config)
        tokenized_name = GeneratedName(('asd', 'qwe', '123'))
        generated_names = strategy.apply(tokenized_name)
        assert len(generated_names) == 2
        assert ('asd', 'qwe', '123', 'man') in [x.tokens for x in generated_names]
        assert ('asd', 'qwe', '123', 'coin') in [x.tokens for x in generated_names]

def test_wordnetsynonyms():
    strategy = WordnetSynonymsGenerator({})
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
