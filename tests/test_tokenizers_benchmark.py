import math
from typing import Dict, List, Tuple, Iterable

from generator.tokenization import AllTokenizer, WordNinjaTokenizer
from hydra import initialize, compose
from namehash_common.ngrams import Ngrams

LABEL = 'laptopsyorknewyorks'


def test_word_ninja_tokenizer(benchmark):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        tokenizer = WordNinjaTokenizer(config)
        tokenized_names = benchmark(tokenizer.tokenize, (LABEL))


def test_all_tokenizer(benchmark):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        tokenizer = AllTokenizer(config)
        tokenized_names = benchmark(tokenizer.tokenize, (LABEL))


def uniq_gaps(tokenized: Iterable[str]) -> List[str]:
    result = []
    before_empty = False
    for token in tokenized:
        if token != '':
            result.append(token)
            before_empty = False
        else:
            if not before_empty:
                before_empty = True
                result.append('')
    return result


def test_all_tokenizer_with_ngrams(benchmark) -> Tuple[List[Dict], bool]:
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        ngrams = Ngrams(config)
        tokenizer = AllTokenizer(config)

        benchmark(tokenize, LABEL, ngrams, tokenizer, 1000)


def tokenize(label, ngrams, tokenizer, tokenizations_limit):
    tokenizeds_iterator = tokenizer.tokenize(label)
    tokenizeds = []
    partial_tokenization = False
    try:
        used = set()
        i = 0
        for tokenized in tokenizeds_iterator:
            if tokenized not in used:
                if i == tokenizations_limit:
                    partial_tokenization = True
                    break
                used.add(tokenized)
                i += 1
                tokenizeds.append(tokenized)
    except RecursionError:
        partial_tokenization = True

    # tokenizeds = list(islice(tokenizeds_iterator, tokenizations_limit))
    tokenizeds = [
        {
            'tokens': tokenized,
            'log_probability': ngrams.sequence_log_probability(tokenized)
        }
        for tokenized in tokenizeds
    ]

    for tokenized in tokenizeds:
        tokenized['tokens'] = tuple(uniq_gaps(tokenized['tokens']))
        tokenized['probability'] = math.exp(tokenized['log_probability'])

    # sort so highest probability with the same tokenization is first
    tokenizeds = sorted(tokenizeds, key=lambda tokenized: tokenized['probability'], reverse=True)
    # remove duplicates after empty duplicates removal
    # used = set()
    # tokenizeds = [x for x in tokenizeds if x['tokens'] not in used and (used.add(x['tokens']) or True)]

    return tokenizeds, partial_tokenization


LABELS = ['creampiebandit', 'richmondrealestate', 'nashvillerealestate', 'youngjin', 'prototyped', 'markscheinberg',
          'nftpain', 'videobox', 'alterity', 'lassuranceretraite', 'vestir', 'disneyworldhotels', 'softdrinkswap',
          'ugandagoldmines', 'metabadboy', 'massagedao', 'newyorksecond', 'avalance', 'iphone520', 'axiewallet',
          'earnmetaverse', 'cannabisgummies', 'othersidesludge', 'homosapienssapiens', 'nonfungiblebasterds',
          'redpointchinaventures', 'pattycakes', 'mattythekid', 'mygiftcardsupply', 'crazycryptonft', 'cryptocashflow',
          'weightlossdiet', 'notcodermaster', 'funnyshitass', 'funnyshitshit', 'slutwife', 'sportsbet', 'ass', 'hotass',
          'wetpussycum', 'fuckpussycum', 'bitcoin', 'greenriver', 'americanairlines', 'usarmy', 'xchange', 'bball',
          'counterstrike', 'livecam', 'rocknroll', 'sanfrancisco']


# TODO add bitcoin as specific

def test_quality():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        word_ninja_tokenizer = WordNinjaTokenizer(config)
        all_tokenizer = AllTokenizer(config)
        ngrams = Ngrams(config)

        word_ninja_tokenize = lambda x: word_ninja_tokenizer.tokenize(x)
        all_tokenize = lambda x: all_tokenizer.tokenize(x)
        all_tokenize_ngram = lambda x: tokenize(x, ngrams, all_tokenizer, 1000)
        for label in LABELS:
            t1 = word_ninja_tokenize(label)[0]
            t2 = list(all_tokenize(label))[0]
            t3 = list(all_tokenize_ngram(label))[0][0]['tokens']

            if len(set([t1, t3])) > 1:
                print('-', label, t1, t3)
            else:
                print(label, t1,  t3)
