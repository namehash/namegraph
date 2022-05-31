from generator.tokenizers import TwoWordWordNetTokenizer, TwoWordTokenizer, WordNinjaTokenizer


def test_two_word_wordnet_tokenizer():
    tokenizer = TwoWordWordNetTokenizer()
    tokenized_names = tokenizer.tokenize('repeatable')
    assert ['repeatable'] in tokenized_names
    assert ['rep', 'eatable'] in tokenized_names
    assert ['repeat', 'able'] in tokenized_names


def test_two_word_tokenizer():
    tokenizer = TwoWordTokenizer()
    tokenized_names = tokenizer.tokenize('repeatable')
    assert ['repeatable'] in tokenized_names
    assert ['rep', 'eatable'] in tokenized_names
    assert ['repeat', 'able'] in tokenized_names


# def test_two_word_tokenizer2():
#     tokenizer=TwoWordTokenizer()
#     tokenized_names = tokenizer.tokenize('yorknewyork')
#     assert ['york', 'new', 'york'] in tokenized_names

def test_word_ninja_tokenizer():
    tokenizer = WordNinjaTokenizer()
    tokenized_names = tokenizer.tokenize('braverest')
    assert ['brave', 'rest'] in tokenized_names


def test_word_ninja_tokenizer2():
    tokenizer = WordNinjaTokenizer()
    tokenized_names = tokenizer.tokenize('yorknewyork123')
    assert ['york', 'new', 'york', '123'] in tokenized_names
