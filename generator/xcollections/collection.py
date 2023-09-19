from __future__ import annotations

from typing import Optional, Any


class Collection:
    def __init__(
            self,
            score: float,
            collection_id: str,
            title: str,
            rank: float,
            owner: str,
            number_of_names: int,
            names: list[str],
            namehashes: Optional[list[str]],
            tokenized_names: Optional[list[tuple[str]]],
            name_types: list[str],
            modified_timestamp: int,
            avatar_emoji: Optional[str],
            avatar_image: Optional[str],
            related_collections: Optional[list[dict[str, Any]]] = None,
            # TODO do we need those above? and do we need anything else?
    ):
        self.score = score
        self.collection_id = collection_id
        self.title = title
        self.rank = rank
        self.owner = owner
        self.number_of_names = number_of_names
        self.names = names
        self.namehashes = namehashes
        self.tokenized_names = tokenized_names
        self.name_types = name_types
        self.modified_timestamp = modified_timestamp
        self.avatar_emoji = avatar_emoji
        self.avatar_image = avatar_image
        self.related_collections = related_collections

    # FIXME make more universal or split into multiple methods
    # FIXME should we move limit_names somewhere else?
    @classmethod
    def from_elasticsearch_hit(cls, hit: dict[str, Any], limit_names: int = 10) -> Collection:
        fields = hit['fields']
        _source = hit.get('_source', {})

        normalized_names_key = 'template.top25_names.normalized_name' \
            if 'template.top25_names.normalized_name' in fields else 'template.top10_names.normalized_name'
        namehashes_key = 'template.top25_names.namehash' \
            if 'template.top25_names.namehash' in fields else 'template.top10_names.namehash'
        tokenized_names_key = 'top25_names' \
            if 'top25_names' in _source.get('template', dict()) else 'top10_names'

        try:
            tokenized_names = [
                tuple(name['tokenized_name'])
                for name in hit['_source']['template'][tokenized_names_key]
            ][:limit_names]
        except KeyError:
            tokenized_names = None

        return cls(
            score=hit['_score'],
            collection_id=hit['_id'],
            title=fields['data.collection_name'][0],
            rank=fields['template.collection_rank'][0],
            owner=fields['metadata.owner'][0],
            number_of_names=fields['metadata.members_count'][0],
            names=fields[normalized_names_key][:limit_names],
            namehashes=fields[namehashes_key][:limit_names] if namehashes_key in fields else None,
            tokenized_names=tokenized_names,
            name_types=fields['template.collection_types'][1::2],
            modified_timestamp=fields['metadata.modified'][0],
            avatar_emoji=fields['data.avatar_emoji'][0] if 'data.avatar_emoji' in fields else None,
            avatar_image=fields['data.avatar_image'][0] if 'data.avatar_image' in fields else None,
            related_collections=_source.get('name_generator', {}).get('related_collections', None),
        )

    @classmethod
    def from_elasticsearch_hit_script_names(cls, hit: dict[str, Any], limit_names: int = 100) -> Collection:
        fields = hit['fields']
        _source = hit.get('_source', {})

        tokenized_names_key = 'top25_names' \
            if 'top25_names' in _source.get('template', dict()) else 'top10_names'

        try:
            tokenized_names = [
                tuple(name['tokenized_name'])
                for name in hit['_source']['template'][tokenized_names_key]
            ][:limit_names]
        except KeyError:
            tokenized_names = None

        return cls(
            score=hit['_score'],
            collection_id=hit['_id'],
            title=fields['data.collection_name'][0],
            rank=fields['template.collection_rank'][0],
            owner=fields['metadata.owner'][0],
            number_of_names=fields['metadata.members_count'][0],
            names=fields['script_names'][:limit_names],
            namehashes=fields['script_namehashes'][:limit_names]
                if 'script_namehashes' in fields else None,
            tokenized_names=tokenized_names,
            name_types=fields['template.collection_types'][1::2],
            modified_timestamp=fields['metadata.modified'][0],
            avatar_emoji=fields['data.avatar_emoji'],
            avatar_image=fields['data.avatar_image'][0] if 'data.avatar_image' in fields else None,
            related_collections=_source.get('name_generator', {}).get('related_collections', None),
        )
