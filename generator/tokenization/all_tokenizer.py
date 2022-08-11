import collections
from typing import Tuple, Iterable
import ahocorasick

from .tokenizer import Tokenizer


class DFS:
    def __init__(self, automaton, name, skip_non_words=False, with_gaps=False):
        self.automaton = automaton
        self.name = name
        self.skip_non_words = skip_non_words
        self.with_gaps = with_gaps  # change non dictionary words into empty string

        # create graph
        self.g_out = collections.defaultdict(list)
        self.g_in = collections.defaultdict(list)
        for end_index, value in self.automaton.iter(name):
            start_index = end_index - len(value) + 1
            end_index += 1
            self.g_out[start_index].append(end_index)
            self.g_in[end_index].append(start_index)
        self.g_out[len(name)] = []
        self.result = []

    def all_paths(self):
        try:
            for r in self.dfs(0, []):
                t = []
                for start, end, in_dictionary in r:
                    if not in_dictionary and self.with_gaps:
                        t.append('')
                    else:
                        t.append(self.name[start:end])
                yield tuple(t)
        except RecursionError:
            return

    def dfs(self, index, result, gap_before=False):
        if index == len(self.name):
            yield result
            return

        found_next_token = False
        if index in self.g_out:
            for end in sorted(self.g_out[index], reverse=True):
                found_next_token = True
                yield from self.dfs(end, result + [(index, end, True)])

        if not self.skip_non_words and not gap_before:
            for potential_index in self.g_out.keys():
                if potential_index <= index: continue
                if index == 0 and potential_index == len(self.name): continue
                if found_next_token and potential_index == len(self.name): continue
                if potential_index not in self.g_in:
                    found_next_token = True
                    yield from self.dfs(potential_index, result + [(index, potential_index, False)], gap_before=True)


class AllTokenizer(Tokenizer):
    """Return all tokenizations. It is a generator."""

    def __init__(self, config):
        path = config.tokenization.dictionary
        self.skip_non_words = config.tokenization.skip_non_words
        self.with_gaps = config.tokenization.with_gaps

        self.automaton = ahocorasick.Automaton()
        skip_one_letter_words = config.tokenization.skip_one_letter_words
        with open(path) as f:
            for line in f:
                word = line.strip().lower()
                if skip_one_letter_words and len(word) == 1: continue
                self.automaton.add_word(word, word)

        if config.tokenization.add_letters_ias:
            for char in 'ias':
                self.automaton.add_word(char, char)

        self.automaton.make_automaton()

    def tokenize(self, name: str) -> Iterable[Tuple[str, ...]]:
        dfs = DFS(self.automaton, name, self.skip_non_words, self.with_gaps)
        tokenizations = dfs.all_paths()
        return tokenizations
