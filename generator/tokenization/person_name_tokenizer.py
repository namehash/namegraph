from typing import List, Tuple, Any, Optional

from .tokenizer import Tokenizer
from ..generated_name import GeneratedName
from ..utils.person_names import PersonNames


class PersonNameTokenizer(Tokenizer):
    """"""

    def __init__(self, config):
        super().__init__()
        self.pn = PersonNames(config)

    def apply(
            self,
            tokenized_names: List[GeneratedName],
            params: Optional[dict[str, Any]] = None
    ) -> List[GeneratedName]:
        result = []
        for name in tokenized_names:
            for token in name.tokens:
                for prob, country, tokenized, type, genders in self.pn.tokenize(token,
                                                                                user_country=params.get('country')):
                    gn = GeneratedName(
                        tokenized,
                        pipeline_name=name.pipeline_name,
                        applied_strategies=[sublist + [self.__class__.__name__] for sublist in name.applied_strategies]
                    )
                    # TODO add meta info about country, gender and prob?
                    result.append(gn)

        return result
