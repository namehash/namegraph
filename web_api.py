import logging
from typing import List, Dict

from fastapi import FastAPI
from hydra import initialize, compose
from pydantic import BaseModel, Field
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


class Name(BaseModel):
    name: str = Field(title='input name')


class Result(BaseModel):
    """
    Input name might be truncated if is too long.
    """
    advertised: List[str] = []
    secondary: List[str] = []
    primary: List[str] = []


def convert_to_str(result: Dict[str, List[GeneratedName]]):
    for list_name, gns in result.items():
        result[list_name] = [str(gn) for gn in gns]


@app.get("/", response_model=Result)
async def root(name: str):
    result = generator.generate_names(name)
    convert_to_str(result)
    return result


@app.post("/", response_model=Result)
async def root(name: Name):
    logger.debug(f'Request received: {name.name}')
    result = generator.generate_names(name.name)
    convert_to_str(result)
    return result
