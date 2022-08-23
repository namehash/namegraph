from typing import List, Dict

from generator.generated_name import GeneratedName


def aggregate_duplicates(names: List[GeneratedName], by_tokens: bool = False) -> List[GeneratedName]:
    names2obj: Dict[str, GeneratedName] = dict()
    for name in names:
        if by_tokens:
            word = name.tokens
        else:
            word = str(name)

        duplicate = names2obj.get(word, None)
        if duplicate is not None:
            duplicate.add_strategies(name.applied_strategies)
        else:
            names2obj[word] = name

    return list(names2obj.values())
