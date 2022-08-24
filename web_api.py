import logging
from typing import List, Dict

from fastapi import FastAPI
from hydra import initialize, compose
from pydantic import BaseSettings

from generator.generated_name import GeneratedName
from generator.xgenerator import Generator


logger = logging.getLogger('generator')


class Settings(BaseSettings):
    # config_name: str = "test_config"
    config_name: str = "prod_config"


settings = Settings()
app = FastAPI()


def init():
    with initialize(version_base=None, config_path="conf/"):
        config = compose(config_name=settings.config_name)
        logger.setLevel(config.app.logging_level)
        for handler in logger.handlers:
            handler.setLevel(config.app.logging_level)

        return Generator(config)


def init_inspector():
    with initialize(version_base=None, config_path="conf/"):
        config = compose(config_name=settings.config_name)
        logger.setLevel(config.app.logging_level)
        for handler in logger.handlers:
            handler.setLevel(config.app.logging_level)

        # return Inspector(config)


generator = init()
inspector = init_inspector()


from models import (
    Name,
    Result,
    ResultWithMetadata,
    Suggestion
)


def convert_to_str(result: List[GeneratedName]):
    return [str(gn) + '.eth' for gn in result]


@app.post("/only_names", response_model=list[str])
async def only_names(name: Name):
    logger.debug(f'Request received: {name.name}')
    result = generator.generate_names(name.name,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions)
    return convert_to_str(result)


def convert_to_suggestion_format(names: List[GeneratedName]) -> List[Suggestion]:
    return [{
        'name': str(name) + '.eth',  # TODO this should be done using Domains (with or without duplicates if multiple suffixes available for one label?)
        'nameguard_rating': 'green',  # TODO add some logic to GeneratedName depending on the generator
        'metadata': {
            'applied_strategies': name.applied_strategies
        }
    } for name in names]


@app.post("/", response_model=list[Suggestion])
async def metadata(name: Name):
    logger.debug(f'Request received: {name.name}')
    result = generator.generate_names(name.name,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions)
    return convert_to_suggestion_format(result)
