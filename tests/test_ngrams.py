from hydra import initialize, compose

from generator.namehash_common.ngrams import Ngrams


def test_ngrams():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
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
