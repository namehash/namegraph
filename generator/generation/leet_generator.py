from typing import Any
import json
import itertools
import math

from .name_generator import NameGenerator


LEETSPEAK_PATH = 'data/leetspeak.json'


class LeetGenerator(NameGenerator):
    def __init__(self, config):
        super().__init__()

        with open(LEETSPEAK_PATH) as f:
            self._leetspeak: dict[str, dict[str, list[list[str]]]] = json.load(f)

        # probability of a full token substitution being used
        self._sequence_logp = math.log2(0.8)
        self._no_sequence_logp = math.log2(0.2)

        # probability of a single letter substitution being used
        self._letter_logp = math.log2(0.6)
        self._no_letter_logp = math.log2(0.4)

        # collect all letter and sequence substitutions with probabilities
        self._letter_replaceables = set()
        self._letter_subs: list[tuple[float, str, str]] = []
        for letter, subs in self._leetspeak['letters'].items():
            logp = 0
            for sub_group in subs:
                for sub in sub_group:
                    # putting this in the inner loop handles empty substitution groups (used to lower the probability)
                    self._letter_replaceables.add(letter)
                    self._letter_subs.append((logp, letter, sub))
                # each group is half as likely as the previous
                logp -= 1
        
        self._sequence_replaceables = set()
        self._sequence_subs: list[tuple[float, str, str]] = []
        for sequence, subs in self._leetspeak['sequences'].items():
            logp = 0
            for sub_group in subs:
                for sub in sub_group:
                    self._sequence_replaceables.add(sequence)
                    self._sequence_subs.append((logp, sequence, sub))
                logp -= 1

    def _get_alphabets(self, sequence_replaceables: set[str], letter_replaceables: set[str]) -> list[tuple[float, dict[str, str], dict[str, str]]]:
        '''
        Returns a list of all substitution alphabets (logp, letter_map, sequence_map)
        that can be made with the given replaceables.
        The list is sorted by probability.
        '''        
        # collect all available substitutions
        letter_subs: list[tuple[float, str, str]] = []
        for logp, letter, sub in self._letter_subs:
            if letter in letter_replaceables:
                letter_subs.append((logp, letter, sub))

        sequence_subs: list[tuple[float, str, str]] = []
        for logp, sequence, sub in self._sequence_subs:
            if sequence in sequence_replaceables:
                sequence_subs.append((logp, sequence, sub))

        # for all subsets of substitutions, make an alphabet
        alphabets: list[tuple[float, dict[str, str], dict[str, str]]] = []
        # TODO allow for empty subsets
        for letter_subset_len in range(1, len(letter_subs) + 1):
            # TODO combinations create duplicates because they pick different substitutions for the same letter
            for letter_subset in itertools.combinations(letter_subs, letter_subset_len):
                letter_map = {letter: sub for _, letter, sub in letter_subset}
                
                for sequence_subset_len in range(1, len(sequence_subs) + 1):
                    for sequence_subset in itertools.combinations(sequence_subs, sequence_subset_len):
                        sequence_map = {sequence: sub for _, sequence, sub in sequence_subset}
        
                        # alphabet probability is the product of the probabilities of the substitutions
                        logprob = 0
                        for logp, _, _ in letter_subset:
                            logprob += logp + self._letter_logp
                        for logp, _, _ in sequence_subset:
                            logprob += logp + self._sequence_logp

                        # include the probability of not using other substitutions
                        logprob += (len(letter_subs) - letter_subset_len) * self._no_letter_logp
                        logprob += (len(sequence_subs) - sequence_subset_len) * self._no_sequence_logp

                        alphabets.append((logprob, letter_map, sequence_map))
        
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
