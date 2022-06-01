from typing import List

class BigramTokenizer:
    def __init__(self, config):
        pass

    def tokenize(self, word: str) -> List[tuple]:
        result = []
        for i in range(1, len(word)):
            prefix = word[:i]
            suffix = word[i:]
            result.append((prefix, suffix))

        return result

