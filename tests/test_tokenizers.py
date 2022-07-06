from typing import List

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
        config = compose(config_name="test_config")
        tokenizer = BigramWordnetTokenizer(config)
        tokenized_names = tokenizer.tokenize('repeatable')
        assert ('repeatable',) in tokenized_names
        assert ('rep', 'eatable') in tokenized_names
        assert ('repeat', 'able') in tokenized_names


def test_two_word_tokenizer():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
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
        config = compose(config_name="test_config")
        tokenizer = WordNinjaTokenizer(config)
        tokenized_names = tokenizer.tokenize('braverest')
        assert ('brave', 'rest') in tokenized_names


def test_word_ninja_tokenizer2():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        tokenizer = WordNinjaTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewyork123')
        assert ('york', 'new', 'york', '123') in tokenized_names


def test_none_tokenizer():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config")
        tokenizer = NoneTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewyork123')
        assert [('yorknewyork123',)] == tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=false", "tokenization.skip_non_words=false"]),
    ],
)
def test_all_tokenizer(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewŁyork123')  # 455 tokenizations
        print(len(tokenized_names))
        assert ('york', 'new', 'Ł', 'york', '123',) in tokenized_names
        assert ('y', 'o', 'r', 'k', 'new', 'Ł', 'york', '123',) in tokenized_names
        assert ('yorknewŁyork123',) not in tokenized_names


@mark.parametrize(
    "overrides",
    [
        (["tokenization.skip_one_letter_words=true", "tokenization.skip_non_words=false"]),
    ],
)
def test_all_tokenizer_skip_one_letter_words(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config", overrides=overrides)
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
        config = compose(config_name="test_config", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('yorknewŁyork123')  # 0 tokenizations
        assert tokenized_names == []

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
        config = compose(config_name="test_config", overrides=overrides)
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
        config = compose(config_name="test_config", overrides=overrides)
        tokenizer = AllTokenizer(config)
        tokenized_names = tokenizer.tokenize('laptop')  # 2 tokenizations

        assert ('laptop',) in tokenized_names
        assert ('lap', 'top',) in tokenized_names
        assert ('l', 'a', 'p', 'top',) not in tokenized_names

        tokenized_names = tokenizer.tokenize('ilaptop')
        assert ('i', 'laptop',) not in tokenized_names
        assert ('i', 'lap', 'top',) not in tokenized_names
