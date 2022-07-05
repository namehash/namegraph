import regex
from omegaconf import DictConfig


class Confusables:
    """https://www.unicode.org/Public/security/latest/confusablesSummary.txt"""

    def __init__(self, config: DictConfig):
        self.config = config
        self.confusable_sets = []
        for line in open(config.inspector.confusables):
            if not line.startswith('#'):
                continue
            line = line[:-1] if line[-1] == '\n' else line
            line = line[2:]
            # print(line)
            confusable = line.split('\t')
            # print(confusable)
            confusable = [c for c in confusable if len(c) == 1]
            self.confusable_sets.append(confusable)

        self.confusable_chars = {}
        for confusable_set in self.confusable_sets:
            for char in confusable_set:
                if not char: continue
                # if char in self.confusable_chars:
                #     print('warning', [char, self.confusable_chars[char], confusable_set])
                self.confusable_chars[char] = confusable_set[0]

    def build(self):
        """Build confusables dict by iterating over all characters and stripping accents."""
        pass

    def is_confusable(self, character):
        if regex.match(r'[a-z0-9-]', character):
            return False
        return character in self.confusable_chars

    def get_confusables(self, character):
        if self.is_confusable(character):
            return self.confusable_chars[character]
        else:
            return None

    def get_canonical(self, character):
        if self.is_confusable(character):
            return self.confusable_chars[character][0]
        else:
            return None

    def analyze(self, character):
        return self.is_confusable(character), self.get_canonical(character)