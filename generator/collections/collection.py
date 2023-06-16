from __future__ import annotations

from typing import Optional


class Collection:
    def __init__(
            self,
            title: str,
            names: list[str],
            namehashes: list[str],
            tokenized_names: Optional[list[tuple[str]]],
            name_types: list[str],
            rank: float,
            score: float,
            owner: str,
            number_of_names: int,
            collection_id: str,
            # TODO do we need those above? and do we need anything else?
    ):
        self.title = title
        self.names = names
        self.namehashes = namehashes
        self.tokenized_names = tokenized_names
        self.name_types = name_types
        self.rank = rank
        self.score = score
        self.owner = owner
        self.number_of_names = number_of_names
        self.collection_id = collection_id

    @classmethod
    def from_elasticsearch_hit(cls, hit: dict[str, Any]) -> Collection:
        return cls(
            title=hit['fields']['data.collection_name'][0],
            names=hit['fields']['normalized_names'],
            namehashes=hit['fields']['namehashes'],
            tokenized_names=[tuple(tokens) for tokens in hit['fields']['tokenized_names']] \
                if 'tokenized_names' in hit['fields'] else None,
            name_types=hit['fields']['collection_types'],
            rank=hit['fields']['template.collection_rank'][0],
            score=hit['_score'],
            owner=hit['fields']['metadata.owner'][0],
            number_of_names=hit['fields']['metadata.members_count'][0],
            collection_id=hit['fields']['metadata.id'][0],
        )
