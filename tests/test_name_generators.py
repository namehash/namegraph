from typing import List

from pytest import mark
from hydra import initialize, compose

from namegraph.generation.categories_generator import MultiTokenCategoriesGenerator, Categories
from namegraph.preprocessor import Preprocessor
from namegraph.generation import (
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
    RandomAvailableNameGenerator,
    Wikipedia2VGenerator,
    SpecialCharacterAffixGenerator,
    SubstringMatchGenerator,
    OnSaleMatchGenerator,
    LeetGenerator,
    KeycapGenerator,
    PersonNameGenerator,
    PersonNameEmojifyGenerator,
    PersonNameExpandGenerator,
    SymbolGenerator,
    EasterEggGenerator,
    CollectionGenerator,
    ReverseGenerator,
    RhymesGenerator,
    W2VGeneratorRocks,
    Wikipedia2VGeneratorRocks
)
from namegraph.generated_name import GeneratedName

import pytest

from namegraph.domains import Domains
from namegraph.input_name import InputName

from namegraph.utils.suffixtree import HAS_SUFFIX_TREE
from namegraph.xcollections import CollectionMatcherForAPI, CollectionMatcherForGenerator

needs_suffix_tree = pytest.mark.skipif(not HAS_SUFFIX_TREE, reason='Suffix tree not available')


@pytest.fixture(autouse=True)
def run_around_tests():
    Domains.remove_self()
    Categories.remove_self()
    CollectionMatcherForAPI.remove_self()
    CollectionMatcherForGenerator.remove_self()
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
        strategy = W2VGeneratorRocks(config)
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


def test_symbol_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SymbolGenerator(config)
        tokenized_name = ('circle', 'ci')
        generated_names = list(strategy.generate(tokenized_name))

        all_tokenized = generated_names

        assert ('⬤', 'ci') in all_tokenized


def test_symbol_generator2():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SymbolGenerator(config)
        tokenized_name = ('produce', 'electric', 'power')
        generated_names = list(strategy.generate(tokenized_name))

        all_tokenized = generated_names

        assert ('produce', '⌁', '⏻') in all_tokenized
        assert ('produce', '⌁', 'power') in all_tokenized
        assert ('produce', 'electric', '⏻') in all_tokenized


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


@pytest.mark.skip(reason='CategoriesGenerator no longer returns deterministic results')
def test_categories():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = CategoriesGenerator(config)
        tokenized_name = ('wolf',)
        generated_names = list(strategy.generate(tokenized_name))

        assert generated_names.index(('lion',)) < generated_names.index(('cheetah',))


def test_single_token_categories_randomization():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        strategy = CategoriesGenerator(config)
        tokenized_name = ('pikachu',)

        generated_names_a = list(map(lambda x: x[0], list(strategy.generate(tokenized_name))))
        generated_names_b = list(map(lambda x: x[0], list(strategy.generate(tokenized_name))))
        assert generated_names_a != generated_names_b


def test_multi_categories():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = MultiTokenCategoriesGenerator(config)
        tokenized_name = ('my', 'pol', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('my', 'ukr', '123') in generated_names
        assert ('my', 'usa', '123') in generated_names


def test_multi_categories_eth():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = MultiTokenCategoriesGenerator(config)
        tokenized_name = ('king', 'lion')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('king', 'cheetah') in generated_names
        assert ('king', 'wolf') in generated_names


def test_multi_categories_csv():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = MultiTokenCategoriesGenerator(config)
        tokenized_name = ('my', '0x8', '123')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('my', '0x1', '123') in generated_names
        assert ('my', '0x2', '123') in generated_names


def test_single_token_categories():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = CategoriesGenerator(config)
        tokenized_name = ('0x8',)
        generated_names = list(strategy.generate(tokenized_name))
        assert ('0x1',) in generated_names
        assert ('0x2',) in generated_names


@mark.parametrize(
    "overrides",
    [
        ["app.domains=tests/data/suggestable_domains_for_only_primary.csv",
         "generation.generator_limits.RandomAvailableNameGenerator=7"]
    ]
)
@mark.xfail(reason="sampling with replacement is much faster and should work fine in production")
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
        assert ('pay', 'share',) in generated_names
        assert ('pay', 'fix',) in generated_names
        assert ('pay', 'green',) in generated_names
        assert ('pay', 'trust',) in generated_names
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
        assert ('field', 'marshal',) in generated_tokens  # intersting_score = 300.0
        assert ('fire',) in generated_tokens  # intersting_score = 190.5115

        orange_pos = generated_tokens.index(('orange',))
        alibaba_pos = generated_tokens.index(('field', 'marshal',))
        fire_pos = generated_tokens.index(('fire',))

        assert alibaba_pos < fire_pos < orange_pos


def test_wikipedia2vsimilarity():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = Wikipedia2VGeneratorRocks(config)
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
        assert ('ξ', 'billy', 'corgan',) in generated_names
        assert ('billy', 'corgan', 'ξ',) in generated_names


def test_special_character_affix_generator_non_ascii():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = SpecialCharacterAffixGenerator(config)
        tokenized_name = ('авада', 'кедавра')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('$', 'авада', 'кедавра',) in generated_names
        assert ('_', 'авада', 'кедавра',) in generated_names
        assert ('ξ', 'авада', 'кедавра',) not in generated_names
        assert ('авада', 'кедавра', 'ξ',) not in generated_names


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

        assert ('00042069',) in generated_tokens  # sort_score = 988
        assert ('0000042069',) in generated_tokens  # sort_score = 227

        longer_pos = generated_tokens.index(('0000042069',))
        shorter_pos = generated_tokens.index(('00042069',))

        assert shorter_pos < longer_pos


@needs_suffix_tree
def test_substringmatchgenerator_re_equals_tree():
    from namegraph.generation.substringmatch_generator import SuffixTreeImpl, ReImpl, HAS_SUFFIX_TREE

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


def test_person_name():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = PersonNameGenerator(config)
        tokenized_name = ('chris',)
        generated_names = list(strategy.generate(tokenized_name))
        assert ('iam', 'chris') in generated_names


def test_easteregg_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = EasterEggGenerator(config)

        tokenized_name = ('byczong',)
        generated_names = list(map(lambda x: x[0], list(strategy.generate(tokenized_name))))
        assert all(['byczong' in name or
                    name in (
                        'i-am-so-tired-of-making-suggestions',
                        'please-stop-typing-so-fast',
                        'you-hurting-me'
                    ) for name in generated_names])


@pytest.mark.integration_test
def test_collection_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="prod_config_new")
        strategy = CollectionGenerator(config)
        tokenized_name = ('pink', 'floyd')
        generated_names = list(strategy.generate(tokenized_name))
        assert ('us', 'and', 'them') in generated_names


def test_reverse_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = ReverseGenerator(config)
        tokenized_name = ('piotrus',)
        generated_names = list(strategy.generate(tokenized_name))
        assert len(generated_names) == 1
        assert generated_names[0] == ('surtoip',)


def test_rhymes_generator():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        strategy = RhymesGenerator(config)

        tokenized_name = ('caravan',)
        gen = strategy.generate(tokenized_name)
        generated_names = list(map(lambda x: ''.join(x), list(gen)))
        expected_names = map(lambda s: tokenized_name[0] + s, (
            "van", "fan", "sullivan", "ivan", "stefan", "evan",
            "ativan", "donovan", "stephan", "orphan", "minivan", "sylvan")
                             )
        assert all([name in generated_names for name in expected_names])

        tokenized_name = ('van', 'fan', 'sullivan')
        gen = strategy.generate(tokenized_name)
        generated_names = list(map(lambda x: ''.join(x), list(gen)))
        discarded_names = map(lambda s: ''.join(tokenized_name) + s,
                              ("van", "fan", "sullivan"))
        assert all([name not in generated_names for name in discarded_names])


@mark.skip(reason="not using dynamic grouping category anymore (PersonNameGenerator)")
def test_person_name_dynamic_grouping_category():
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pn = PersonNameGenerator(config)
        assert pn.get_grouping_category(output_name=None) == 'expand'
        assert pn.get_grouping_category(output_name='piotrbyczong') == 'expand'
        assert pn.get_grouping_category(output_name='piotr🐂byczong') == 'emojify'
        assert pn.get_grouping_category(output_name='piotrbyczońg') == 'emojify'  # non-ascii -> emojify


@mark.parametrize(
    "tokens, gender",
    [
        (('david', 'gilmour'), 'M'),
        (('amy', 'whinehouse'), 'F'),
        (('pink', 'floyd'), None),
    ]
)
def test_person_name_emojify_generator(tokens: tuple[str, ...], gender: str):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pn = PersonNameEmojifyGenerator(config)
        assert pn.get_grouping_category() == 'emojify'

        generated_names = list(pn.generate(tokens, gender))
        for name_tokens in generated_names:
            name = ''.join(name_tokens)
            assert not name.isascii()


@mark.parametrize(
    "tokens, gender",
    [
        (('david', 'gilmour'), 'M'),
        (('amy', 'whinehouse'), 'F'),
        (('pink', 'floyd'), None),
    ]
)
def test_person_name_expand_generator(tokens: tuple[str, ...], gender: str):
    with initialize(version_base=None, config_path="../conf/"):
        config = compose(config_name="test_config_new")
        pn = PersonNameExpandGenerator(config)
        assert pn.get_grouping_category() == 'expand'

        generated_names = list(pn.generate(tokens, gender))
        for name_tokens in generated_names:
            name = ''.join(name_tokens)
            assert name.isascii()
