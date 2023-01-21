from generator.generated_name import GeneratedName
import time


class LogEntry:
    def __init__(self, domains):
        self.start_time = time.time()
        self.domains = domains

    def create_log_entry(self, request: dict, result: list[GeneratedName]) -> dict:
        request.update({'user': None, 'session': None})
        entry = {
            'type': 'Request&Response',
            'request': request,
            'input_name': {'status': self.domains.get_name_status(request['name']),  # TODO strip .eth?
                           'price': None,
                           'real_status': None,
                           'name_guard': None},
            'response': [self.convert_suggestion_to_log_entry(gn) for gn in result],
            'start_time': self.start_time,
            'end_time': time.time(),
        }
        return entry

    def convert_suggestion_to_log_entry(self, suggestion: GeneratedName) -> dict:
        return {
            'name': str(suggestion),
            'tokens': suggestion.tokens,
            'pipeline_name': suggestion.pipeline_name,
            'status': suggestion.category,
            'applied_strategies': suggestion.applied_strategies,
            'price': None,
            'real_status': None,
            'name_guard': None
        }
