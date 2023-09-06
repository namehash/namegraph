from typing import Optional
import time

from omegaconf import DictConfig

from generator.generated_name import GeneratedName
from generator.generation.categories_generator import Categories
from generator.domains import Domains


class LogEntry:
    def __init__(self, config: DictConfig):
        self.start_time = time.time()
        self.config = config
        self.domains: Domains = Domains(config)
        self.categories: Categories = Categories(config)

    def create_grouped_log_entry(self, request: dict, result: dict[str, list[GeneratedName]]) -> dict:
        request.update({
            'user': '0x35b3ab43ebe7709f4aef1a9c3e6d1f99be343128',  # dummy
            'session': 'RudderEncrypt%3A123123123132132132132'  # dummy
        })
        entry = {
            'type': 'Request&Response',
            'schema_version': 0.2,
            'request': request,
            'input_name': {'status': self.domains.get_name_status(request['label']),  # TODO strip .eth?
                           'price': 1.2345,  # dummy
                           'real_status': 'available',  # dummy
                           'name_guard': 'green'  # dummy
                           },
            'start_time': self.start_time,
            'end_time': time.time(),
            'user_currency': 'USD',  # dummy
            'response': {category: [self.convert_suggestion_to_log_entry(gn) for gn in gns] for category, gns in result.items()},
        }
        return entry
    
    def create_log_entry(self, request: dict, result: list[GeneratedName]) -> dict:
        request.update({
            'user': '0x35b3ab43ebe7709f4aef1a9c3e6d1f99be343128',  # dummy
            'session': 'RudderEncrypt%3A123123123132132132132'  # dummy
        })
        entry = {
            'type': 'Request&Response',
            'schema_version': 0.2,
            'request': request,
            'input_name': {'status': self.domains.get_name_status(request['label']),  # TODO strip .eth?
                           'price': 1.2345,  # dummy
                           'real_status': 'available',  # dummy
                           'name_guard': 'green'  # dummy
                           },
            'start_time': self.start_time,
            'end_time': time.time(),
            'user_currency': 'USD',  # dummy
            'response': [self.convert_suggestion_to_log_entry(gn) for gn in result],
        }
        return entry

    def convert_suggestion_to_log_entry(self, suggestion: GeneratedName) -> dict:
        return {
            'name': str(suggestion),
            'tokens': suggestion.tokens,
            'pipeline_name': suggestion.pipeline_name,
            'interpretation': suggestion.interpretation,
            'cached_status': suggestion.status,
            'applied_strategies': suggestion.applied_strategies,
            'price': 1.2345,  # dummy
            'real_status': 'available',  # dummy
            'name_guard': 'green',  # dummy
            'normalized_price': '2.34',  # dummy
            'price_in_user_currency': '3.45',  # dummy
            'categories': self.categories.get_categories(str(suggestion)),
            'cached_interesting_score': self.domains.get_interesting_score(suggestion)
        }
