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
            confusable = [c for c  in confusable if len(c)==1]
            self.confusable_sets.append(confusable)

        self.confusable_chars = {}
        for confusable_set in self.confusable_sets:
            for char in confusable_set:
                if not char: continue
                # if char in self.confusable_chars:
                #     print('warning', [char, self.confusable_chars[char], confusable_set])
                self.confusable_chars[char] = confusable_set[0]

    def build(self):
        """Build confusables dict by iterrating over all characters and stripping accents."""

    def analyze(self, character):
        if regex.match(r'[a-z0-9-]', character):
            return False, None
        
        # without_accents=remove_accents(character)
        
        
        is_confusable = character in self.confusable_chars
        if is_confusable:
            confusables = self.confusable_chars[character]
            canonical = confusables[0]
            return is_confusable, canonical
        else:
            return False, None
