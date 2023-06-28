from __future__ import annotations

from typing import Any, Literal, Optional
from copy import deepcopy


class ElasticsearchQueryBuilder:
    def __init__(self):
        self._query = {
            'query': {},
        }

    def add_must(self, type: str, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a must query to the query builder

        :param type: type of query
        :param query: query
        :return: self
        """
        if 'bool' not in self._query['query']:
            self._query['query']['bool'] = {}

        if 'must' not in self._query['query']['bool']:
            self._query['query']['bool']['must'] = []

        self._query['query']['bool']['must'].append({
            type: query
        })

        return self

    def add_should(self, type: str, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a should query to the query builder

        :param type: type of query
        :param query: query
        :return: self
        """
        if 'bool' not in self._query['query']:
            self._query['query']['bool'] = {}

        if 'should' not in self._query['query']['bool']:
            self._query['query']['bool']['should'] = []

        self._query['query']['bool']['should'].append({
            type: query
        })

        return self

    def add_must_not(self, type: str, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a must_not query to the query builder

        :param type: type of query
        :param query: query
        :return: self
        """
        if 'bool' not in self._query['query']:
            self._query['query']['bool'] = {}

        if 'must_not' not in self._query['query']['bool']:
            self._query['query']['bool']['must_not'] = []

        self._query['query']['bool']['must_not'].append({
            type: query
        })

        return self

    def add_filter(self, type: str, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a filter to the query builder

        :param type: type of filter
        :param query: query
        :return: self
        """
        if 'bool' not in self._query['query']:
            self._query['query']['bool'] = {}

        if 'filter' not in self._query['query']['bool']:
            self._query['query']['bool']['filter'] = []

        self._query['query']['bool']['filter'].append({
            type: query
        })

        return self

    def set_term(self, field: str, value: Any) -> ElasticsearchQueryBuilder:
        """
        Sets a term of the query builder

        :param field: field name (shouldn't be analyzed)
        :param value: value to exactly match
        :return: self
        """

        self._query['query']['term'] = {field: value}

        return self

    def add_query(
            self,
            query: str,
            boolean_clause: Literal['must', 'should'] = 'must',
            type_: str = 'cross_fields',
            fields: list[str] = None
    ) -> ElasticsearchQueryBuilder:
        """
        Adds a query to the query builder

        :param query: query string
        :param boolean_clause: boolean_clause used with this query (must, should...)
        :param type_: type of query
        :param fields: fields to search in, if None, default fields will be used
        :return: self
        """
        if fields is None:
            fields = [
                'data.collection_name^3',
                'data.collection_name.exact^3',
                'data.collection_keywords^2',
                'data.names.normalized_name',
                'data.names.tokenized_name',
            ]

        if boolean_clause == 'must':
            return self.add_must('multi_match', {
                'query': query,
                'fields': fields,
                'type': type_,
            })
        elif boolean_clause == 'should':
            return self.add_should('multi_match', {
                'query': query,
                'fields': fields,
                'type': type_,
            })
        else:
            raise ValueError(f"Unexpected boolean_clause value: '{boolean_clause}'")


    def add_rank_feature(self, field: str, boost: int = None) -> ElasticsearchQueryBuilder:
        """
        Adds a rank feature to the query builder

        :param field: field name
        :param boost: boost value
        :return: self
        """
        rank_feature = {
            'field': field,
        }

        if boost is not None:
            rank_feature['boost'] = boost

        return self.add_should('rank_feature', rank_feature)

    def add_limit(self, limit: int) -> ElasticsearchQueryBuilder:
        """
        Adds a limit to the query builder

        :param limit: limit
        :return: self
        """
        self._query['size'] = limit
        return self

    def add_offset(self, offset: int) -> ElasticsearchQueryBuilder:
        """
        Adds an offset (ES from) to the query builder

        :param offset: offset (from)
        :return: self
        """
        self._query['from'] = offset
        return self

    def set_source(self, value: Any) -> ElasticsearchQueryBuilder:
        """
        Sets the source of the query builder

        :return: self
        """
        self._query['_source'] = value
        return self

    def set_sort_order(self, sort_order: Literal['A-Z', 'Z-A', 'AI-by-member', 'ES'],
                       field: Optional[str]) -> ElasticsearchQueryBuilder:
        """
        Sets the sort field of the query builder based on the sort_order.

        :return: self
        """
        if sort_order == 'ES':
            pass
        elif sort_order == 'AI-by-member':
            self._query['sort'] = [{"template.nonavailable_members_ratio.raw": {"order": "desc"}},
                                   {"metadata.members_count.raw": {"order": "desc"}}, "_score"]
        elif sort_order == 'A-Z':
            self._query['sort'] = [{field: {"order": "asc"}}, "_score"]
        elif sort_order == 'Z-A':
            self._query['sort'] = [{field: {"order": "desc"}}, "_score"]
        else:
            raise ValueError(f"Unexpected sort_order value: '{sort_order}'")

        return self

    def include_fields(self, fields: list[str]) -> ElasticsearchQueryBuilder:
        """
        List of fields to include in the response

        :return: self
        """
        if 'fields' not in self._query:
            self._query['fields'] = []

        self._query['fields'].extend(fields)
        return self

    def include_field(self, field: str) -> ElasticsearchQueryBuilder:
        """
        Field to include in the response

        :return: self
        """
        if 'fields' not in self._query:
            self._query['fields'] = []

        self._query['fields'].append(field)
        return self

    def include_script_field(self, name: str, script: str) -> ElasticsearchQueryBuilder:
        """
        Adds a script field to the query builder

        :param name: name of the field
        :param script: script
        :return: self
        """
        if 'script_fields' not in self._query:
            self._query['script_fields'] = {}

        self._query['script_fields'][name] = {
            'script': {
                'source': script
            }
        }

        return self

    def build_body(self):
        """For use as a `body` parameter in elasticsearch query."""
        return deepcopy(self._query)

    def build_params(self):
        """For use as separate parameters (**es_params) in elasticsearch query."""
        es_params = deepcopy(self._query)

        if 'source' in es_params:
            es_params['source'] = es_params['_source']
            del es_params['_source']

        if 'from_' in es_params:
            es_params['from_'] = es_params['from']
            del es_params['from']

        return es_params
