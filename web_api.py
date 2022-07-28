import logging
from typing import List, Dict, Union, Tuple, Optional

from fastapi import FastAPI
from hydra import initialize, compose
from pydantic import BaseModel, Field
from pydantic import BaseSettings

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


class Name(BaseModel):
    name: str = Field(title='input name')


class Result(BaseModel):
    """
    Input name might be truncated if is too long.
    """
    advertised: List[str] = []
    secondary: List[str] = []
    primary: List[str] = []


@app.get("/", response_model=Result)
async def root(name: str):
    return generator.generate_names(name)


@app.post("/", response_model=Result)
async def root(name: Name):
    logger.debug(f'Request received: {name.name}')
    return generator.generate_names(name.name)

# 
# @app.get("/inspector/", response_model=InspectorResult)
# async def root(name: str):
#     return inspector.analyse_name(name)
# 
# 
# @app.post("/inspector/", response_model=InspectorResult)
# async def root(name: InspectorName):
#     return inspector.analyse_name(name.label,
#                                   tokenization=name.tokenization,
#                                   entities=name.entities,
#                                   limit_confusables=name.limit_confusables,
#                                   truncate_chars_output=name.truncate_chars_output,
#                                   disable_char_analysis=name.disable_char_analysis,
#                                   pos_lemma=name.pos_lemma)
