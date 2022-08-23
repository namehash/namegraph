import logging
from typing import List, Dict

from fastapi import FastAPI
from hydra import initialize, compose
from pydantic import BaseSettings

from generator.generated_name import GeneratedName
from generator.xgenerator import Generator

from models import (
    Name,
    Result,
    ResultWithMetadata,
    Suggestion
)

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


def convert_to_str(result: Dict[str, List[GeneratedName]]):
    for list_name, gns in result.items():
        result[list_name] = [str(gn) for gn in gns]


@app.get("/", response_model=Result)
async def root(name: str, min_suggestions: int = None, max_suggestions: int = None):
    result = generator.generate_names(name, min_suggestions=min_suggestions, max_suggestions=max_suggestions)
    convert_to_str(result)
    return result


@app.post("/", response_model=Result)
async def root(name: Name):
    logger.debug(f'Request received: {name.name}')
    result = generator.generate_names(name.name,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions)
    convert_to_str(result)
    return result


def convert_to_suggestion_format(names: List[GeneratedName]) -> List[Suggestion]:
    return [{
        'name': str(name),
        'metadata': {
            'applied_strategies': name.applied_strategies
        }
    } for name in names]


@app.get("/metadata", response_model=ResultWithMetadata)
async def metadata(name: str, min_suggestions: int = None, max_suggestions: int = None):
    result = generator.generate_names(name, min_suggestions=min_suggestions, max_suggestions=max_suggestions)
    for list_name, gns in result.items():
        result[list_name] = convert_to_suggestion_format(gns)
    return result


@app.post("/metadata", response_model=ResultWithMetadata)
async def metadata(name: Name):
    logger.debug(f'Request received: {name.name}')
    result = generator.generate_names(name.name,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions)
    for list_name, gns in result.items():
        result[list_name] = convert_to_suggestion_format(gns)
    return result
