from itertools import islice
from typing import List

import pytest
from pytest import mark
from hydra import initialize, compose

from generator.tokenization import (
    BigramTokenizer,
    WordNinjaTokenizer,
    BigramWordnetTokenizer,
    BigramDictionaryTokenizer, AllTokenizer
)

# repeatable, braverest, semisoft, chinamen
from generator.tokenization.none_tokenizer import NoneTokenizer


def test_two_word_wordnet_tokenizer():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        tokenizer = BigramWordnetTokenizer(config)
        tokenized_names = tokenizer.tokenize('repeatable')
        assert ('repeatable',) in tokenized_names
        assert ('rep', 'eatable') in tokenized_names
        assert ('repeat', 'able') in tokenized_names


def test_two_word_tokenizer():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        tokenizer = BigramDictionaryTokenizer(config)
        tokenized_names = tokenizer.tokenize('repeatable')
        assert ('repeatable',) in tokenized_names
        assert ('rep', 'eatable') in tokenized_names
        assert ('repeat', 'able') in tokenized_names


# def test_two_word_tokenizer2():
#     tokenizer = TwoWordTokenizer()
#     tokenized_names = tokenizer.tokenize('yorknewyork')
#     assert ['york', 'new', 'york'] in tokenized_names

def test_word_ninja_tokenizer():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        tokenizer = WordNinjaTokenizer(config)
        tokenized_names = tokenizer.tokenize('braverest')
        assert ('brave', 'rest') in tokenized_names


def test_word_ninja_tokenizer2():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        tokenizer = WordNinjaTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewyork123')
        assert ('york', 'newyork', '123') in tokenized_names

        print(tokenizer.tokenize('vitalik'))
        print(tokenizer.tokenize('avsa'))
        print(tokenizer.tokenize('brantly'))


@mark.parametrize(
    "name,tokenized_name", [
        ['funny💩', ('funny', '💩')],
        ['funny💩💩', ('funny', '💩','💩')],
        ['7️⃣7️⃣7️⃣', ('7️⃣', '7️⃣', '7️⃣')],
        ['namehash©', ('name', 'hash', '©')],
        ['🅵🅸🆃', ('🅵🅸🆃',)],
        ['john🇺🇸', ('john', '🇺🇸')],
        ['_yumi', ('_', 'yumi')],
        ['español', ('espa','ñ','ol')],
        ['‍420', ('‍', '420',)],
        ['٠٠٩', ('٠٠٩',)],
        ['عليكم٠٠٩', ('عليكم', '٠٠٩')],
        ['•5776', ('•', '5776')],
        ['سعودي', ('سعودي',)],
        ['京a00002', ('京', 'a', '00002')],
    ])
def test_new_word_ninja_tokenizer(name, tokenized_name):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        tokenizer = WordNinjaTokenizer(config)
        tokenized_names = tokenizer.tokenize(name)
        assert tokenized_names[0] == tokenized_name


def test_none_tokenizer():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        tokenizer = NoneTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewyork123')
        assert [('yorknewyork123',)] == tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=false", "tokenization.skip_non_words=false",
          "tokenization.with_gaps=false"]),
    ],
)
def test_all_tokenizer(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewŁyork123')  # 455 tokenizations
        assert ('york', 'new', 'Ł', 'york', '123',) in tokenized_names
        assert ('y', 'o', 'r', 'k', 'new', 'Ł', 'york', '123',) in tokenized_names
        assert ('yorknewŁyork123',) not in tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=false",
          "tokenization.with_gaps=false"]),
    ],
)
def test_all_tokenizer_skip_one_letter_words(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewŁyork123')  # 63 tokenizations

        assert ('york', 'new', 'Ł', 'york', '123',) in tokenized_names
        assert ('y', 'o', 'r', 'k', 'new', 'Ł', 'york', '123',) not in tokenized_names
        assert ('yorknewŁyork123',) not in tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=false", "tokenization.skip_non_words=true"]),
    ],
)
def test_all_tokenizer_skip_non_words(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewŁyork123')  # 0 tokenizations
        assert list(tokenized_names) == []

        tokenized_names = tokenizer.tokenize('laptop')  # 13 tokenizations
        assert ('laptop',) in tokenized_names
        assert ('lap', 'top',) in tokenized_names
        assert ('l', 'a', 'p', 'top',) in tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=true"]),
    ],
)
def test_all_tokenizer_skip_one_letter_words_and_non_words(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('laptop')  # 2 tokenizations

        assert ('laptop',) in tokenized_names
        assert ('lap', 'top',) in tokenized_names
        assert ('l', 'a', 'p', 'top',) not in tokenized_names

        tokenized_names = tokenizer.tokenize('ilaptop')
        assert ('i', 'laptop',) in tokenized_names
        assert ('i', 'lap', 'top',) in tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=true",
          "tokenization.add_letters_ias=false"]),
    ],
)
def test_all_tokenizer_skip_one_letter_words_and_non_words_no_ias(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('laptop')  # 2 tokenizations

        assert ('laptop',) in tokenized_names
        assert ('lap', 'top',) in tokenized_names
        assert ('l', 'a', 'p', 'top',) not in tokenized_names

        tokenized_names = tokenizer.tokenize('ilaptop')
        assert ('i', 'laptop',) not in tokenized_names
        assert ('i', 'lap', 'top',) not in tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=false",
          "tokenization.add_letters_ias=false",
          "tokenization.with_gaps=true"]),
    ],
)
def test_all_tokenizer_skip_one_letter_words_and_non_words_no_ias_with_gaps(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('lapŁtop')

        assert ('lap', '', 'top',) in tokenized_names
        assert ('', 'top',) in tokenized_names


@pytest.mark.execution_timeout(10)
@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=false",
          "tokenization.add_letters_ias=false",
          "tokenization.with_gaps=true"]),
    ],
)
def test_all_tokenizer_time(overrides):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan')


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=false",
          "tokenization.add_letters_ias=false",
          "tokenization.with_gaps=true"]),
    ],
)
def test_all_tokenizer_skip_one_letter_words_and_non_words_no_ias_with_gaps23(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = list(tokenizer.tokenize('laptop😀ą'))
        print(tokenized_names)
        assert ('laptop', '') in tokenized_names
        assert ('lap', 'top', '') in tokenized_names
        assert ('lap', '',) not in tokenized_names
