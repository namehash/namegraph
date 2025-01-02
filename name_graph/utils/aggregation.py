from typing import List, Dict

from name_graph.generated_name import GeneratedName


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


def extend_and_aggregate(name2suggestion: Dict[str, GeneratedName],
                         suggestions: List[GeneratedName],
                         max_suggestions: int) -> Dict[str, GeneratedName]:
    for suggestion in suggestions:
        if len(name2suggestion) >= max_suggestions:
            break

        name = str(suggestion)

        duplicate = name2suggestion.get(name, None)
        if duplicate is not None:
            duplicate.add_strategies(suggestion.applied_strategies)
        else:
            name2suggestion[name] = suggestion

    return name2suggestion
