from __future__ import annotations

from typing import Any
from copy import deepcopy


class ElasticsearchQueryBuilder:
    def __init__(self):
        self._query = {
            'query': {
                'bool': {}
            },
        }

    def add_must(self, type: str, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a must query to the query builder

        :param type: type of query
        :param query: query
        :return: self
        """
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
        if 'should' not in self._query['query']['bool']:
            self._query['query']['bool']['should'] = []

        self._query['query']['bool']['should'].append({
            type: query
        })

        return self

    def add_filter(self, type: str, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a filter to the query builder

        :param type: type of filter
        :param field: field name
        :param value: value to filter
        :return: self
        """

        if 'filter' not in self._query['query']['bool']:
            self._query['query']['bool']['filter'] = []

        self._query['query']['bool']['filter'].append({
            type: query
        })

        return self

    def add_query(self, query: str, type: str = 'cross_fields', fields: list[str] = None) -> ElasticsearchQueryBuilder:
        """
        Adds a query to the query builder

        :param query: query string
        :param type: type of query
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

        return self.add_must('multi_match', {
            'query': query,
            'fields': fields,
            'type': type,
        })

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

    def set_source(self, value: Any) -> ElasticsearchQueryBuilder:
        """
        Sets the source of the query builder

        :return: self
        """
        self._query['_source'] = value
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

    def build(self):
        return deepcopy(self._query)
