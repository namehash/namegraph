import logging

from fastapi import FastAPI
from hydra import initialize, compose
from pydantic import BaseModel
from pydantic import BaseSettings

from generator.xgenerator import Generator

logger = logging.getLogger('generator')


class Settings(BaseSettings):
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


generator = init()


@app.get("/")
async def root(name: str):
    return generator.generate_names(name)


class Name(BaseModel):
    name: str


@app.post("/")
async def root(name: Name):
    return generator.generate_names(name.name)
