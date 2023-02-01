from generator.generated_name import GeneratedName
import time


class LogEntry:
    def __init__(self, domains):
        self.start_time = time.time()
        self.domains = domains

    def create_log_entry(self, request: dict, result: list[GeneratedName]) -> dict:
        request.update({'user': '0x35b3ab43ebe7709f4aef1a9c3e6d1f99be343128', 'session': 'RudderEncrypt%3A123123123132132132132'})
        entry = {
            'type': 'Request&Response',
            'schema_version': 0.1,
            'request': request,
            'input_name': {'status': self.domains.get_name_status(request['name']),  # TODO strip .eth?
                           'price': 1.2345,
                           'real_status': 'available',
                           'name_guard': 'green'},
            'start_time': self.start_time,
            'end_time': time.time(),
            'response': [self.convert_suggestion_to_log_entry(gn) for gn in result],
        }
        return entry

    def convert_suggestion_to_log_entry(self, suggestion: GeneratedName) -> dict:
        return {
            'name': str(suggestion),
            'tokens': suggestion.tokens,
            'pipeline_name': suggestion.pipeline_name,
            'status': suggestion.category,
            'applied_strategies': suggestion.applied_strategies,
            'price': 1.2345,
            'real_status': 'available',
            'name_guard': 'green'
        }
