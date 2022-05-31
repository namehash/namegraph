from generator.generation import (
        PermuteGenerator,
        GeneratedName,
        PrefixGenerator,
        SuffixGenerator,
        WordNetSynonymsGenerator,
        W2VGenerator,
        CategoriesGenerator,
)

import pytest

def test_permuter():
    strategy = PermuteGenerator()
    tokenized_name = GeneratedName(['asd', 'qwe', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert len(generated_names) == 6
    # print([x.applied_strategies for x in generated_names])


def test_prefix():
    prefixes = ['top', 'best']
    strategy = PrefixGenerator(prefixes)
    tokenized_name = GeneratedName(['asd', 'qwe', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert len(generated_names) == 2
    assert ['top', 'asd', 'qwe', '123'] in [x.tokens for x in generated_names]
    assert ['best', 'asd', 'qwe', '123'] in [x.tokens for x in generated_names]


def test_suffix():
    suffixes = ['top', 'best']
    strategy = SuffixGenerator(suffixes)
    tokenized_name = GeneratedName(['asd', 'qwe', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert len(generated_names) == 2
    assert ['asd', 'qwe', '123', 'top'] in [x.tokens for x in generated_names]
    assert ['asd', 'qwe', '123', 'best'] in [x.tokens for x in generated_names]


def test_wordnetsynonyms():
    strategy = WordNetSynonymsGenerator()
    tokenized_name = GeneratedName(['my', 'domain', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert ['my', 'domain', '123'] in [x.tokens for x in generated_names]
    assert ['my', 'area', '123'] in [x.tokens for x in generated_names]

@pytest.mark.slow
def test_w2vsimilarity():
    strategy = W2VGenerator()
    tokenized_name = GeneratedName(['my', 'pikachu', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert ['your', 'pikachu', '123'] in [x.tokens for x in generated_names]
    assert ['my', 'mickey', '123'] in [x.tokens for x in generated_names]

def test_categories():
    strategy = CategoriesGenerator({'Pokemon': ['pikachu', 'bulbazaur']})
    tokenized_name = GeneratedName(['my', 'pikachu', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert ['my', 'pikachu', '123'] in [x.tokens for x in generated_names]
    assert ['my', 'bulbazaur', '123'] in [x.tokens for x in generated_names]
