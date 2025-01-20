from __future__ import annotations

from typing import Any, Literal, Optional
from copy import deepcopy
from enum import Enum


class SortOrder(Enum):
    AZ = 'A-Z'
    ZA = 'Z-A'
    AI = 'AI'
    AI_BY_MEMBER = 'AI-by-member'
    RELEVANCE = 'Relevance'


class ElasticsearchQueryBuilder:
    def __init__(self):
        self._query = {
            'query': {},
        }

    def add_ids(self, ids: list[str]) -> ElasticsearchQueryBuilder:
        """
        Adds ids to the query builder

        :param ids: list of ids
        :return: self
        """
        self._query['query']['ids'] = {
            'values': ids
        }

        return self

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

    def set_terms(self, field: str, values: list[Any]) -> ElasticsearchQueryBuilder:
        """
        Sets terms of the query builder

        :param field: field name (shouldn't be analyzed)
        :param values: list of terms (match if document contains at least one of the terms)
        :return: self
        """

        self._query['query']['terms'] = {field: values}

        return self

    def add_query(
            self,
            query: str,
            boolean_clause: Literal['must', 'should'] = 'must',
            type_: str = 'cross_fields',
            fields: list[str] = None,
            type2: str = 'multi_match',
    ) -> ElasticsearchQueryBuilder:
        """
        Adds a query to the query builder

        :param query: query string
        :param boolean_clause: boolean_clause used with this query (must, should...)
        :param type_: type of query, e.g. cross_fields, most_fields
        :param fields: fields to search in, if None, default fields will be used
        :param type2: type of query, e.g. multi_match, query_string
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
            return self.add_must(type2, {
                'query': query,
                'fields': fields,
                'type': type_,
            })
        elif boolean_clause == 'should':
            return self.add_should(type2, {
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

    def set_sort_order(self, sort_order: Literal[SortOrder.AZ, SortOrder.ZA, SortOrder.AI_BY_MEMBER, SortOrder.RELEVANCE],
                       field: Optional[str]) -> ElasticsearchQueryBuilder:
        """
        Sets the sort field of the query builder based on the sort_order.

        :param sort_order: SortOrder enum value specifying how to sort the results
        :param field: Optional field to sort by (required for ALPHABETICAL_ASC and ALPHABETICAL_DESC)
        :return: self
        """
        if sort_order == SortOrder.RELEVANCE:
            pass
        elif sort_order == SortOrder.AI_BY_MEMBER:
            self._query['sort'] = [{"template.nonavailable_members_ratio.raw": {"order": "desc"}},
                                   {"metadata.members_count.raw": {"order": "desc"}}, "_score"]
        elif sort_order == SortOrder.AZ:
            self._query['sort'] = [{field: {"order": "asc"}}, "_score"]
        elif sort_order == SortOrder.ZA:
            self._query['sort'] = [{field: {"order": "desc"}}, "_score"]
        else:
            raise ValueError(f"Unexpected sort_order value: {sort_order}")

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

    def include_script_field(
            self,
            name: str,
            script: str,
            lang: Optional[str] = None,
            params: Optional[dict] = None
    ) -> ElasticsearchQueryBuilder:
        """
        Adds a script field to the query builder

        :param name: name of the field
        :param script: script
        :param lang: language of the script
        :param params: parameters of the script
        :return: self
        """
        if 'script_fields' not in self._query:
            self._query['script_fields'] = {}

        self._query['script_fields'][name] = {
            'script': {
                'source': script
            }
        }

        if lang is not None:
            self._query['script_fields'][name]['script']['lang'] = lang

        if params is not None:
            self._query['script_fields'][name]['script']['params'] = params

        return self

    def rescore(self, window_size: int, query: dict) -> ElasticsearchQueryBuilder:
        """
        Adds a rescore to the query builder

        :param window_size: window size
        :param query: query
        :return: self
        """
        self._query['rescore'] = {
            'window_size': window_size,
            'query': query
        }
        return self

    def rescore_with_learning_to_rank(
            self,
            query: str,
            window_size: int,
            model_name: str,
            feature_set: str,
            feature_store: str,
            query_weight: float = 0.0,
            rescore_query_weight: float = 1.0,
    ) -> ElasticsearchQueryBuilder:
        """
        Adds a learning to rank rescore to the query builder

        :param query: query
        :param window_size: window size
        :param model_name: model name
        :param feature_set: feature set
        :param feature_store: feature store
        :param query_weight: query weight
        :param rescore_query_weight: rescore query weight
        :return: self
        """

        query = {
            "rescore_query": {
                "sltr": {
                    "_name":"logged_featureset",
                    "store": feature_store,
                    "featureset": feature_set,
                    "model": model_name,
                    "params": {
                        "keywords": query
                    }
                }
            },
            "query_weight": query_weight,
            "rescore_query_weight": rescore_query_weight
        }

        return self.rescore(window_size, query)

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
