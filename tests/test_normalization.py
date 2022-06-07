from generator.normalization import *


def test_unicode_normalization1():
    name = 'áąółś😀❤'
    normalizer = UnicodeNormalizer({})
    assert normalizer.normalize(name) == 'aaols'


def test_unicode_normalization2():
    name = 'kožušček'
    normalizer = UnicodeNormalizer({})
    assert normalizer.normalize(name) == 'kozuscek'


def test_unicode_normalization3():
    name = 'ᴄeo'  # c in small caps
    normalizer = UnicodeNormalizer({})
    assert normalizer.normalize(name) == 'ceo'


def test_strip_eth():
    name = 'dog.eth'
    normalizer = StripEthNormalizer({})
    assert normalizer.normalize(name) == 'dog'


def test_only_valid_characters():
    name = 'dog_cat'
    normalizer = ReplaceInvalidNormalizer({})
    assert normalizer.normalize(name) == 'dogcat'


def test_ignore_namehash():
    name = '[59204fd55f432a2d32b0d89aaf9455324dc11671927bedd3d91ce7b7968e5f80]'
    normalizer = NamehashNormalizer({})
    assert normalizer.normalize(name) == ''
