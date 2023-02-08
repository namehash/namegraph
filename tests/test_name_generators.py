from typing import List

from pytest import mark
from hydra import initialize, compose

from generator.preprocessor import Preprocessor
from generator.generation import (
    HyphenGenerator,
    AbbreviationGenerator,
    EmojiGenerator,
    FlagAffixGenerator,
    PermuteGenerator,
    PrefixGenerator,
    SuffixGenerator,
    WordnetSynonymsGenerator,
    W2VGenerator,
    CategoriesGenerator,
    RandomGenerator,
    RandomAvailableNameGenerator,
    Wikipedia2VGenerator,
    SpecialCharacterAffixGenerator,
    SubstringMatchGenerator,
    OnSaleMatchGenerator,
    LeetGenerator,
    KeycapGenerator,
)
from generator.generated_name import GeneratedName

import pytest

from generator.domains import Domains
from generator.input_name import InputName

from generator.utils.suffixtree import HAS_SUFFIX_TREE

needs_suffix_tree = pytest.mark.skipif(not HAS_SUFFIX_TREE, reason='Suffix tree not available')


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    yield


def test_permuter():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = PermuteGenerator(config)
        tokenized_name = ('asd', 'qwe', '123')
        generated_names = strategy.generate(tokenized_name)
        assert len(list(generated_names)) == 6


def test_permuter_limit():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = PermuteGenerator(config)
        tokenized_name = tuple(map(str, range(10)))  # 3628800 permutations
        generated_names = strategy.generate(tokenized_name)
        assert len(list(generated_names)) == config.generation.limit


def test_prefix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = PrefixGenerator(config)
        tokenized_name = ('asd', 'qwe', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert len(generated_names) == 2
        assert ('0x', 'asd', 'qwe', '123') in generated_names
        assert ('the', 'asd', 'qwe', '123') in generated_names


def test_prefix_prefixed():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = PrefixGenerator(config)
        tokenized_name = ('0', 'xqwe', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert len(generated_names) == 1
        assert ('0x', '0', 'xqwe', '123') not in generated_names
        assert ('the', '0', 'xqwe', '123') in generated_names


def test_suffix():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SuffixGenerator(config)
        tokenized_name = ('asd', 'qwe', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert len(generated_names) == 2
        assert ('asd', 'qwe', '123', 'man') in generated_names
        assert ('asd', 'qwe', '123', 'coin') in generated_names


def test_suffix_suffixed():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SuffixGenerator(config)
        tokenized_name = ('asd', 'qwem', 'an')
        generated_names = list(strategy.generate(tokenized_name))
        assert len(generated_names) == 1
        assert ('asd', 'qwem', 'an', 'man') not in generated_names
        assert ('asd', 'qwem', 'an', 'coin') in generated_names


def test_wordnetsynonyms():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = WordnetSynonymsGenerator(config)
        tokenized_name = ('my', 'domain', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('my', 'domain', '123') in generated_names
        assert ('my', 'area', '123') in generated_names


def test_abbreviation_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = AbbreviationGenerator(config)
        tokenized_name = ('my', 'domain', '123', 'aa22')
        generated_names = list(strategy.generate(tokenized_name))
        print([x for x in generated_names])

        assert ('my', 'd', '123', 'aa22') in generated_names
        assert ('m', 'd', '123', 'aa22') in generated_names
        assert ('m', 'domain', '123', 'aa22') in generated_names

        assert ('m', 'd', '1', 'aa22') not in generated_names
        assert ('my', 'domain', '1', 'aa22') not in generated_names
        assert ('my', 'domain', '123', 'aa22') not in generated_names


def test_abbreviation_generator_order():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = AbbreviationGenerator(config)
        tokenized_name = ('aa', 'bb', 'cc')
        generated_names = list(strategy.generate(tokenized_name))
        tokens = generated_names

        one_abbr_indices = [
            tokens.index(abbr)
            for abbr in [('a', 'bb', 'cc'),
                         ('aa', 'b', 'cc'),
                         ('aa', 'bb', 'c')]
        ]
        two_abbr_indices = [
            tokens.index(abbr)
            for abbr in [('a', 'b', 'cc'),
                         ('aa', 'b', 'c'),
                         ('a', 'bb', 'c')]
        ]
        three_abbr_indices = [
            tokens.index(abbr)
            for abbr in [('a', 'b', 'c')]
        ]

        assert all(
            one_idx < two_idx
            for one_idx in one_abbr_indices
            for two_idx in two_abbr_indices
        )

        assert all(
            two_idx < three_idx
            for two_idx in two_abbr_indices
            for three_idx in three_abbr_indices
        )


@pytest.mark.slow
def test_w2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = W2VGenerator(config)
        tokenized_name = ('my', 'pikachu', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('your', 'pikachu', '123') in generated_names
        assert ('my', 'mickey', '123') in generated_names


def test_hyphen_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = HyphenGenerator(config)
        tokenized_name = ('my', 'pikachu', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('my', '-', 'pikachu', '-', '123') == generated_names[0]
        assert ('my', 'pikachu', '-', '123') in generated_names
        assert ('my', '-', 'pikachu', '123') in generated_names
        assert ('my', 'pikachu', '123') not in generated_names


@pytest.mark.execution_timeout(1)
def test_hyphen_generator_long():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = HyphenGenerator(config)
        tokenized_name = tuple(['a'] * 10000)
        generated_names = list(strategy.generate(tokenized_name))


@pytest.mark.execution_timeout(1)
def test_abbreviation_generator_long():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = AbbreviationGenerator(config)
        tokenized_name = tuple(['aa'] * 5000)
        generated_names = list(strategy.generate(tokenized_name))


def test_flag_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = FlagAffixGenerator(config)

        tokenized_name = ('adam', 'mickiewicz')
        generated_names = strategy.generate(tokenized_name, country='pl')
        assert len(generated_names) == 2
        assert ('adam', 'mickiewicz', '🇵🇱') == generated_names[0]
        assert ('🇵🇱', 'adam', 'mickiewicz') == generated_names[1]

        tokenized_name = ('taras', 'shevchenko')
        generated_names = strategy.generate(tokenized_name, country='ua')
        assert len(generated_names) == 2
        assert ('taras', 'shevchenko', '🇺🇦') == generated_names[0]

        tokenized_name = ('taras', 'shevchenko')
        generated_names = strategy.generate(tokenized_name, country='123')
        assert len(generated_names) == 0

        tokenized_name = ('taras', 'shevchenko')
        generated_names = strategy.generate(tokenized_name, country=None)
        assert len(generated_names) == 0

        # TODO
        # tokenized_name = ('taras', 'shevchenko')
        # generated_names = strategy.generate(tokenized_name, params={})
        # assert len(generated_names) == 0
        # 
        # tokenized_name = ('taras', 'shevchenko')
        # generated_names = strategy.generate(tokenized_name, params=None)
        # assert len(generated_names) == 0


def test_emoji_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = EmojiGenerator(config)
        tokenized_name = ('adore', 'your', 'eyes')
        generated_names = list(strategy.generate(tokenized_name))

        all_tokenized = generated_names

        assert ('🥰', 'your', '🤩') in all_tokenized
        assert ('🥰', 'your', '👀') in all_tokenized
        assert ('🥰', 'your', '😵‍💫') in all_tokenized
        assert ('🥰', 'your', 'eyes') in all_tokenized
        assert ('adore', 'your', '👀') in all_tokenized

        assert ('adore', 'your', 'eyes') not in all_tokenized


@mark.parametrize(
    "input_name, suborder",
    [
        (('look', 'into', 'dragon', 'eyes'), [
            ('look', 'into', '🐉', '👀'),
            ('look', 'into', '🀄', '😵‍💫'),
            ('look', 'into', 'dragon', '🤩'),
            ('look', 'into', '🐉', '🤩'),
            ('look', 'into', '🐉', 'eyes'),
        ])
    ]
)
def test_emoji_generator_order(input_name: tuple[str], suborder: list[tuple[str]]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = EmojiGenerator(config)
        tokenized_name = input_name
        generated_names = list(strategy.generate(tokenized_name))

        all_tokenized = generated_names

        last_index = all_tokenized.index(suborder[0])
        for next_name in suborder[1:]:
            index = all_tokenized.index(next_name)
            assert index > last_index
            last_index = index


@pytest.mark.execution_timeout(1)
def test_emoji_generator_long():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = EmojiGenerator(config)
        tokenized_name = ('face',) * 1000
        generated_names = list(strategy.generate(tokenized_name))


def test_categories():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = CategoriesGenerator(config)
        tokenized_name = ('my', 'pol', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('my', 'ukr', '123') in generated_names
        assert ('my', 'usa', '123') in generated_names


def test_categories_eth():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = CategoriesGenerator(config)
        tokenized_name = ('king', 'lion')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('king', 'cheetah') in generated_names
        assert ('king', 'wolf') in generated_names


def test_categories_csv():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = CategoriesGenerator(config)
        tokenized_name = ('my', '0x8', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('my', '0x1', '123') in generated_names
        assert ('my', '0x2', '123') in generated_names


@mark.parametrize(
    "overrides",
    [
        ["app.internet_domains=tests/data/top_internet_names_short.csv"]
    ]
)
def test_random(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        strategy = RandomGenerator(config)
        tokenized_name = ('my', 'domain', '123')
        generated_names = list(strategy.generate())
        assert len(
            set([x[0] for x in generated_names]) & {'google', 'youtube', 'facebook', 'baidu', 'yahoo', 'amazon',
                                                    'wikipedia', 'qq',
                                                    'twitter', 'live', 'global', '00002'}) == 8


@mark.parametrize(
    "overrides",
    [
        ["app.domains=tests/data/suggestable_domains_for_only_primary.csv",
         "generation.generator_limits.RandomAvailableNameGenerator=7"]
    ]
)
def test_only_primary_random(overrides: List[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        strategy = RandomAvailableNameGenerator(config)
        tokenized_name = ('my', 'domain', '123')
        generated_names = list(strategy.generate())

        available_names = {'taco', 'glintpay', 'drbaher', '9852222', 'wanadoo', 'conio', 'indulgente', 'theclown'}
        assert len(generated_names) == len(set(generated_names))
        assert len(set([x[0] for x in generated_names]) & available_names) == 7


def test_on_sale_matcher():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = OnSaleMatchGenerator(config)
        tokenized_name = ('pay', 'fire', '123')
        generated_names = list(strategy.generate(tokenized_name))
        print(generated_names)
        assert ('payshare',) in generated_names
        assert ('payfix',) in generated_names
        assert ('paygreen',) in generated_names
        assert ('paytrust',) in generated_names
        assert ('fire',) in generated_names


# this test does not detect non-deterministic behavior if run in different processes
@mark.parametrize(
    "overrides",
    [
        ["app.domains=tests/data/suggestable_domains_for_only_primary.csv"]
    ]
)
def test_on_sale_matcher_deterministic(overrides: list[str]):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new", overrides=overrides)
        tokenized_name = ('fire',)

        strategy = OnSaleMatchGenerator(config)
        generated_names = list(strategy.generate(tokenized_name))
        print(generated_names)

        for _ in range(10):
            Domains.remove_self()
            strategy = OnSaleMatchGenerator(config)
            generated_names2 = list(strategy.generate(tokenized_name))

            assert generated_names == generated_names2


def test_on_sale_matcher_sorting():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = OnSaleMatchGenerator(config)
        tokenized_name = ('fire', 'marshal', 'orange')
        generated_names = list(strategy.generate(tokenized_name))
        generated_tokens = generated_names

        assert ('orange',) in generated_tokens  # intersting_score = 69.98
        assert ('fieldmarshal',) in generated_tokens  # intersting_score = 300.0
        assert ('fire',) in generated_tokens  # intersting_score = 190.5115

        orange_pos = generated_tokens.index(('orange',))
        alibaba_pos = generated_tokens.index(('fieldmarshal',))
        fire_pos = generated_tokens.index(('fire',))

        assert alibaba_pos < fire_pos < orange_pos


def test_wikipedia2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = Wikipedia2VGenerator(config)
        tokenized_name = ('billy', 'corgan')
        generated_names = list(strategy.generate(tokenized_name))
        print(generated_names)
        assert ('the', 'smashing', 'pumpkins',) in generated_names


def test_special_character_affix_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SpecialCharacterAffixGenerator(config)
        tokenized_name = ('billy', 'corgan')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('$', 'billy', 'corgan',) in generated_names
        assert ('_', 'billy', 'corgan',) in generated_names


def test_substringmatchgenerator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = ('00', '-00', '-69-00')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('00-00-69-00',) in generated_names


def test_substringmatchgenerator_short():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = ('4',)
        generated_names = list(strategy.generate(tokenized_name))
        assert ('0000400',) in generated_names


def test_substringmatchgenerator_sorting():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SubstringMatchGenerator(config)
        tokenized_name = ('0004206',)
        generated_names = list(strategy.generate(tokenized_name))
        generated_tokens = generated_names

        assert ('00042069',) in generated_tokens  # interesting_score = 988
        assert ('0000042069',) in generated_tokens  # interesting_score = 227

        longer_pos = generated_tokens.index(('0000042069',))
        shorter_pos = generated_tokens.index(('00042069',))

        assert shorter_pos < longer_pos


@needs_suffix_tree
def test_substringmatchgenerator_re_equals_tree():
    from generator.generation.substringmatch_generator import SuffixTreeImpl, ReImpl, HAS_SUFFIX_TREE

    if not HAS_SUFFIX_TREE:
        pytest.skip()

    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        re_impl = ReImpl(config)
        tree_impl = SuffixTreeImpl(config)
        assert sorted(re_impl.find('0')) == sorted(tree_impl.find('0'))


def test_leet_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = LeetGenerator(config)
        tokenized_name = ('you', 'are', 'a', 'leet', 'hacker')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('u', 'r', '4', '1337', 'h4ck3r',) in generated_names
        assert ('you', 'are', 'a', 'leet', 'hacker',) not in generated_names


def test_keycap_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = KeycapGenerator(config)

        tokenized_name = ('fire', 'cell')
        generated_names = list(strategy.generate(tokenized_name))
        assert [('🅵🅸🆁🅴🅲🅴🅻🅻',)] == generated_names

        tokenized_name = ('fire', '-', 'cell')
        generated_names = list(strategy.generate(tokenized_name))
        assert not generated_names
