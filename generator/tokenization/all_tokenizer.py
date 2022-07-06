import collections
from typing import List, Tuple
import ahocorasick


class DFS:
    def __init__(self, automaton, name, skip_non_words=False):
        self.automaton = automaton
        self.name = name
        self.skip_non_words = skip_non_words

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
        self.dfs(0, [])
        for r in self.result:
            t = []
            for start, end in r:
                t.append(self.name[start:end])
            yield tuple(t)

    def dfs(self, index, result):
        if index == len(self.name):
            self.result.append(result)
            return

        if index in self.g_out:
            for end in self.g_out[index]:
                self.dfs(end, result + [(index, end)])

        if not self.skip_non_words:
            for potential_index in self.g_out.keys():
                if potential_index <= index: continue
                if index == 0 and potential_index == len(self.name): continue
                if potential_index not in self.g_in:
                    self.dfs(potential_index, result + [(index, potential_index)])


class AllTokenizer():
    """Return all tokenizations."""

    def __init__(self, config):
        path = config.tokenization.dictionary
        self.skip_non_words = config.tokenization.skip_non_words

        self.automaton = ahocorasick.Automaton()
        skip_one_letter_words = config.tokenization.skip_one_letter_words
        with open(path) as f:
            for line in f:
                word = line.strip().lower()
                if skip_one_letter_words and len(word) == 1: continue
                # if re.match(r'^\w+$', word):
                self.automaton.add_word(word, word)

        self.automaton.make_automaton()

    def tokenize(self, name: str) -> List[Tuple[str, ...]]:
        dfs = DFS(self.automaton, name, self.skip_non_words)
        tokenizations = list(dfs.all_paths())
        return tokenizations
