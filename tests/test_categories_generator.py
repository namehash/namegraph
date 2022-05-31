from generator.categories import (
        CategoriesGenerator,
        )
from generator.generation import GeneratedName

def test_categories():
    strategy = CategoriesGenerator({'Pokemon': ['pikachu', 'bulbazaur']})
    tokenized_name = GeneratedName(['my', 'pikachu', '123'])
    generated_names = strategy.apply(tokenized_name)
    assert ['my', 'pikachu', '123'] in [x.tokens for x in generated_names]
    assert ['my', 'bulbazaur', '123'] in [x.tokens for x in generated_names]
