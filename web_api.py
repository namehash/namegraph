import logging, random, hashlib, json
from typing import List, Optional

import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from hydra import initialize, compose
from pydantic import BaseSettings

from generator.generated_name import GeneratedName
from generator.utils.log import LogEntry
from generator.xgenerator import Generator

logger = logging.getLogger('generator')


class Settings(BaseSettings):
    # config_name: str = "test_config"
    config_name: str = "prod_config_new"
    config_overrides: Optional[str] = None


settings = Settings()
app = FastAPI()


def init():
    with initialize(version_base=None, config_path="conf/"):
        overrides = json.loads(settings.config_overrides) if settings.config_overrides is not None else []
        config = compose(config_name=settings.config_name, overrides=overrides)
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


def seed_all(seed: int | str):
    if isinstance(seed, str):
        hashed = hashlib.md5(seed.encode('utf-8')).digest()
        seed = int.from_bytes(hashed, 'big') & 0xff_ff_ff_ff

    logger.info(f'Setting all seeds to {seed}')
    random.seed(seed)
    np.random.seed(seed)


generator = init()
inspector = init_inspector()

from models import (
    Name,
    Suggestion,
)


def convert_to_suggestion_format(names: List[GeneratedName], include_metadata: bool = True) -> list[dict[str, str]]:
    response = [{
        'name': str(name) + '.eth',
        # TODO this should be done using Domains (with or without duplicates if multiple suffixes available for one label?)
    } for name in names]

    if include_metadata:
        for name, name_json in zip(names, response):
            name_json['metadata'] = {
                'applied_strategies': name.applied_strategies,
                'interpretation': name.interpretation,
                'category': name.category,
                'pipeline_name': name.pipeline_name,
            }

    return response


@app.post("/", response_model=list[Suggestion])
async def root(name: Name):
    seed_all(name.name)
    log_entry = LogEntry(generator.domains)
    logger.debug(f'Request received: {name.name}')
    params = name.params.dict() if name.params is not None else dict()

    generator.clear_cache()
    result = generator.generate_names(name.name,
                                      sorter=name.sorter,
                                      min_suggestions=name.min_suggestions,
                                      max_suggestions=name.max_suggestions,
                                      min_available_fraction=name.min_primary_fraction,
                                      params=params)

    response = convert_to_suggestion_format(result, include_metadata=name.metadata)

    logger.info(json.dumps(log_entry.create_log_entry(name.dict(), result)))

    return JSONResponse(response)
