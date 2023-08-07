from typing import Tuple, Iterator
from random import shuffle

from generator.generation import NameGenerator
from ..input_name import InputName, Interpretation



class EasterEggGenerator(NameGenerator):
    """
    Return an EasterEgg message.
    """

    def __init__(self, config):
        super().__init__(config)
        self.messages = [
            'i-dont-like-{name}',
            'i-wish-i-was-{name}',
            'you-think-being-creative-everyone-is-typing-{name}',
            'i-am-so-tired-of-making-suggestions',
            'please-stop-typing-so-fast',
            'you-hurting-me'
        ]

    def generate(self, tokens: Tuple[str, ...]) -> Iterator[Tuple[str, ...]]:
        if len(''.join(tokens)) == 0:
            return []

        name = ''.join(tokens)
        shuffle(self.messages)
        return ((m.format(name=name),) for m in self.messages)

    def generate2(self, name: InputName, interpretation: Interpretation) -> Iterator[Tuple[str, ...]]:
        return self.generate(**self.prepare_arguments(name, interpretation))

    def prepare_arguments(self, name: InputName, interpretation: Interpretation):
        return {'tokens': (name.strip_eth_namehash_unicode_replace_invalid_long_name,)}
