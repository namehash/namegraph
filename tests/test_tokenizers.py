from hydra import initialize, compose

from generator.tokenization import (
    BigramTokenizer,
    WordNinjaTokenizer,
    BigramWordnetTokenizer,
    BigramDictionaryTokenizer
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
