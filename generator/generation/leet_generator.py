from typing import Any
import json
import itertools
import math

from .name_generator import NameGenerator


LEETSPEAK_PATH = 'data/leetspeak.json'


def get_replacement_combinations(replacements: dict[str, list[tuple[float, str]]]) -> list[dict[str, tuple[float, str]]]:
    '''
    Given multiple replacement options for each character, return a list of all possible combinations of 1:1 replacements.
    '''
    rs = list(replacements.items())
    combinations = itertools.product(*[[(src, r) for r in tgts] for (src, tgts) in rs])
    return [{src: r for (src, r) in combination} for combination in combinations]


class LeetGenerator(NameGenerator):
    def __init__(self, config):
        super().__init__()

        with open(LEETSPEAK_PATH) as f:
            leetspeak = json.load(f)

        # probability of a full token substitution being used
        self._sequence_logp = math.log2(0.8)
        self._no_sequence_logp = math.log2(0.2)

        # probability of a single letter substitution being used
        self._letter_logp = math.log2(0.6)
        self._no_letter_logp = math.log2(0.4)

        # collect all letter and sequence substitutions with probabilities
        self._letter_replaceables = set()
        self._letter_subs: dict[str, list[tuple[float, str]]] = {}
        for letter, subs in leetspeak['letters'].items():
            logp = self._letter_logp
            for sub_group in subs:
                for sub in sub_group:
                    # putting this in the inner loop handles empty substitution groups (used to lower the probability)
                    self._letter_replaceables.add(letter)
                    # add a fake 'no replacement' replacement
                    self._letter_subs[letter] = self._letter_subs.get(letter, [(self._no_letter_logp, letter)]) + [(logp, sub)]
                # each group is half as likely as the previous
                logp -= 1

        self._sequence_replaceables = set()
        self._sequence_subs: dict[str, list[tuple[float, str]]] = {}
        for sequence, subs in leetspeak['sequences'].items():
            logp = self._sequence_logp
            for sub_group in subs:
                for sub in sub_group:
                    self._sequence_replaceables.add(sequence)
                    self._sequence_subs[sequence] = self._sequence_subs.get(sequence, [(self._no_sequence_logp, sequence)]) + [(logp, sub)]
                logp -= 1

    def _get_alphabets(self, sequence_replaceables: set[str], letter_replaceables: set[str]) -> list[tuple[float, dict[str, str], dict[str, str]]]:
        '''
        Returns a list of all substitution alphabets (logp, letter_map, sequence_map)
        that can be made with the given replaceables.
        The list is sorted by probability.
        '''
        # collect all available substitutions
        letter_subs: dict[str, list[tuple[float, str]]] = {k: v for k, v in self._letter_subs.items() if k in letter_replaceables}
        sequence_subs: dict[str, list[tuple[float, str]]] = {k: v for k, v in self._sequence_subs.items() if k in sequence_replaceables}

        # for all subsets of substitutions, make an alphabet
        alphabets: list[tuple[float, dict[str, str], dict[str, str]]] = []
        for letter_map in get_replacement_combinations(letter_subs):
            for sequence_map in get_replacement_combinations(sequence_subs):
                if all(src == tgt for src, (_, tgt) in letter_map.items()) and all(src == tgt for src, (_, tgt) in sequence_map.items()):
                    # skip the no-replacement alphabet
                    continue
                # alphabet probability is the product of the probabilities of the substitutions
                logprob = sum(p for p, _ in letter_map.values()) + sum(p for p, _ in sequence_map.values())
                alphabets.append((logprob, {k: v[1] for k, v in letter_map.items()}, {k: v[1] for k, v in sequence_map.items()}))
        
        alphabets.sort(key=lambda alphabet: alphabet[0], reverse=True)
        return alphabets

    def _get_tokens_replaceables(self, tokens: tuple[str, ...]) -> tuple[set[str], set[str]]:
        '''
        Returns a set of all substitutions that can be made in the given tokens.
        '''
        sequence_replaceables = set()
        letter_replaceables = set()
        for token in tokens:
            if token in self._sequence_replaceables:
                sequence_replaceables.add(token)
            else:
                # this else blocks an edge case where a letter substitution conflicts with a sequence substitution
                # and the generator would create duplicates because the sequence substitution blocks the letter substitution
                for letter in token:
                    if letter in self._letter_replaceables:
                        letter_replaceables.add(letter)
        return sequence_replaceables, letter_replaceables

    def _leetify_token(self, token: str, letter_map: dict[str, str], sequence_map: dict[str, str]) -> str:
        if token in sequence_map:
            return sequence_map[token]
        return ''.join(letter_map.get(letter, letter) for letter in token)

    def _leetify(self, tokens: tuple[str, ...], letter_map: dict[str, str], sequence_map: dict[str, str]) -> tuple[str, ...]:
        return tuple(self._leetify_token(token, letter_map, sequence_map) for token in tokens)

    def generate(self, tokens: tuple[str, ...], params: dict[str, Any]) -> list[tuple[str, ...]]:
        # find all replaceable tokens/letters
        sequence_replaceables, letter_replaceables = self._get_tokens_replaceables(tokens)

        # get all alphabets that can be made with the replaceables
        alphabets = self._get_alphabets(sequence_replaceables, letter_replaceables)

        # for each alphabet, generate a leetified version of the input
        generated: list[tuple[str, ...]] = []
        for _, letter_map, sequence_map in alphabets:
            generated.append(self._leetify(tokens, letter_map, sequence_map))

        return generated
