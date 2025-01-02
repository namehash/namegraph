from hydra import initialize, compose

from name_graph.namehash_common.ngrams import Ngrams
from name_graph.tokenization.all_tokenizer import AllTokenizer


def test_ngrams():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        ngrams = Ngrams(config)
        assert ngrams.unigram_count('the') > ngrams.unigram_count('cat')
        assert ngrams.word_probability('the') > ngrams.word_probability('cat')
        assert ngrams.word_probability('the') > ngrams.word_probability('sdfghsldhgsldk')
        assert ngrams.word_probability('sdfghsldhgsldk') > 0

        assert ngrams.sequence_probability(['the', 'cat']) > ngrams.sequence_probability(['sdfghsldhgsldk'])
        assert ngrams.sequence_probability(['the', 'cat']) > ngrams.sequence_probability(['white', 'cat'])
        assert ngrams.sequence_probability(['cat']) > ngrams.sequence_probability(['c', 'a', 't'])
        assert ngrams.sequence_probability(['the', 'cat']) > ngrams.sequence_probability(['cat', 'the'])
        assert ngrams.sequence_probability(['i', 'have', 'been', 'here', 'before']) \
             > ngrams.sequence_probability(['here', 'been', 'have', 'i', 'before'])  # master Yoda style :)

        assert ngrams.sequence_probability(['Ł', 'cat', 'Ł']) > ngrams.sequence_probability(['Łc', 'a', 'tŁ'])

        assert ngrams.sequence_probability(['repeatable']) > ngrams.sequence_probability(['repeat', 'able'])
        assert ngrams.sequence_probability(['bothering']) > ngrams.sequence_probability(['bo', 'the', 'ring'])

        assert ngrams.sequence_probability(['nft']) > ngrams.sequence_probability(['n', 'f', 't'])
        assert ngrams.sequence_probability(['nft']) > ngrams.sequence_probability(['sdfghsldhgsldk'])
        assert ngrams.sequence_probability(['rakuten']) > ngrams.sequence_probability(['sdfghsldhgsldk'])


def test_gap_prob():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        ngrams = Ngrams(config)
        tokenizer = AllTokenizer(config)

        toks = tokenizer.tokenize('ŁcatŁ')
        tok1 = None
        tok2 = None
        for t in toks:
            if t == ('', 'a', ''):
                tok1 = t
            elif t == ('', 'cat', ''):
                tok2 = t
            if None not in (tok1, tok2):
                break
        assert ngrams.sequence_probability(tok1) < ngrams.sequence_probability(tok2)
