from hydra import initialize, compose

from inspector.ngrams import Ngrams


def test_ngrams():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config")
        ngrams = Ngrams(config)
        assert ngrams.word_count('the') > ngrams.word_count('cat')
        assert ngrams.word_probability('the') > ngrams.word_probability('cat')
        assert ngrams.word_probability('the') > ngrams.word_probability('sdfghsldhgsldk')
        assert ngrams.word_probability('sdfghsldhgsldk') > 0

        assert ngrams.sequence_probability(['the', 'cat']) > ngrams.sequence_probability(['sdfghsldhgsldk'])
        assert ngrams.sequence_probability(['the', 'cat']) > ngrams.sequence_probability(['white', 'cat'])
        assert ngrams.sequence_probability(['cat']) > ngrams.sequence_probability(['c', 'a', 't'])

        assert ngrams.sequence_probability(['repeatable']) > ngrams.sequence_probability(['repeat', 'able'])
