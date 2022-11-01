from typing import List, Tuple, Any

from .name_generator import NameGenerator


class FlagAffixGenerator(NameGenerator):
    """
    Adds suffix in the form of country emoji depending on the request's parameter
    """

    def __init__(self, config):
        super().__init__()
        # todo
        self.country2emoji = {
            'pl': '🇵🇱',
            'ua': '🇺🇦'
        }

    def generate(self, tokens: Tuple[str, ...], params: dict[str, Any]) -> List[Tuple[str, ...]]:
        # todo should we raise an exception if we do not know this country?
        # todo except the fact that it should be validated by pydantic models
        print('params', params)
        if 'country' not in params or params['country'] not in self.country2emoji:
            return []

        return [tokens + (self.country2emoji[params['country']],)]
