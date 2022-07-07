import logging
from typing import List, Dict, Union

from fastapi import FastAPI
from hydra import initialize, compose
from pydantic import BaseModel, Field
from pydantic import BaseSettings

from generator.xgenerator import Generator
from inspector.name_inspector import Inspector

logger = logging.getLogger('generator')


class Settings(BaseSettings):
    config_name: str = "test_config"
    # config_name: str = "prod_config"


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

        return Inspector(config)


generator = init()
inspector = init_inspector()


class Name(BaseModel):
    name: str


class Result(BaseModel):
    advertised: List[str] = []
    secondary: List[str] = []
    primary: List[str] = []


@app.get("/", response_model=Result)
async def root(name: str):
    return generator.generate_names(name)


@app.post("/", response_model=Result)
async def root(name: Name):
    return generator.generate_names(name.name)


class InspectorConfusableCharResult(BaseModel):
    char: str = Field(title="confusable character")
    script: Union[str, None] = Field(title="script name of the character",
                                     description="can be null if script is not assigned for a character")
    name: Union[str, None] = Field(title="name assigned to the character",
                                   description="can be null if script is not assigned for a character")
    codepoint: str = Field(title="codepoint of the character as hex with 0x prefix")
    link: str = Field(title="link to external page with information about the character")
    classes: List[str] = \
        Field(title="list of classes in which the character is",
              description='* letter - a letter in any script; LC class http://www.unicode.org/reports/tr44/#GC_Values_Table'
                          '* number - a digit in any script; N class http://www.unicode.org/reports/tr44/#GC_Values_Table'  # TODO: check - not working, in unicode.link is numeric field 
                          '* hyphen - a hyphen'
                          '* emoji - an emoji'
                          '* basic - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')


class InspectorTokenResult(BaseModel):
    token: str = Field(title="the token")
    length: int = Field(title="number of Unicode characters")
    all_classes: List[str] = \
        Field(title="list of classes in which all characters are",
              description='* letter - a letter in any script; LC class http://www.unicode.org/reports/tr44/#GC_Values_Table'
                          '* number - a digit in any script; N class http://www.unicode.org/reports/tr44/#GC_Values_Table'  # TODO: check
                          '* hyphen - a hyphen'
                          '* emoji - an emoji'
                          '* basic - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')
    all_script: Union[str, None] = \
        Field(title="script name of all characters",
              description="can be null if characters are in different scripts or script is not assigned for a character")
    in_dictionary: bool = Field(title="if the token is in dictionary")
    pos: str = Field(title="part of speech of the token")
    lemma: str = Field(title="lemma of the word")


class InspectorCharResult(BaseModel):
    char: str = Field(title="character being inspected")
    script: Union[str, None] = Field(title="script name of the character",
                                     description="can be null if script is not assigned for a character")
    name: Union[str, None] = Field(title="name assigned to the character",
                                   description="can be null if script is not assigned for a character")
    codepoint: str = Field(title="codepoint of the character as hex with 0x prefix")
    link: str = Field(title="link to external page with information about the character")
    classes: List[str] = \
        Field(title="list of classes in which the character is",
              description='* letter - a letter in any script; LC class http://www.unicode.org/reports/tr44/#GC_Values_Table'
                          '* number - a digit in any script; N class http://www.unicode.org/reports/tr44/#GC_Values_Table'  # TODO: check
                          '* hyphen - a hyphen'
                          '* emoji - an emoji'
                          '* basic - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')
    unicodedata_category: str = Field(
        title="general category assigned to the character: http://www.unicode.org/reports/tr44/#GC_Values_Table")
    unicodedata_bidirectional: str = Field(title="bidirectional class assigned to the character or empty string")
    unicodedata_combining: int = Field(title="canonical combining class assigned to the character")
    unicodedata_mirrored: int = Field(title="mirrored property assigned to the character")
    unicodedata_decomposition: str = Field(
        title="character decomposition mapping assigned to the character or empty string")
    unicodeblock: Union[str, None] = Field(title="name of Unicode block in which the character is or null")
    unidecode: str = Field(
        title="https://pypi.org/project/Unidecode/ Tries to represent name in ASCII characters.",
        description="e.g. it converts 'ł' to 'l', 'ω' (omega) to 'o'.")
    NFKD_ascii: str = Field(title="string after decomposition in compatible mode with removed non-ascii chars")
    NFD_ascii: str = Field(title="string after decomposition with removed non-ascii chars")
    NFKD: str = Field(title="string after decomposition in compatible mode")
    NFD: str = Field(title="string after decomposition")
    # confusable: bool = Field(title="if the character is confusable")  # TODO: remove?
    confusable_with: List[List[InspectorConfusableCharResult]] = \
        Field(title="set of confusable characters",
              description='If the character is not confusable then empty list is returned. '
                          'The list also includes the original character. '
                          'The first element is usually a canonical form.')


class InspectorResult(BaseModel):
    name: str = Field(title="input string")
    length: int = Field(title="number of Unicode characters")
    all_classes: List[str] = \
        Field(title="list of classes in which all characters are",
              description='* letter - a letter in any script; LC class http://www.unicode.org/reports/tr44/#GC_Values_Table'
                          '* number - a digit in any script; N class http://www.unicode.org/reports/tr44/#GC_Values_Table'  # TODO: check
                          '* hyphen - a hyphen'
                          '* emoji - an emoji'
                          '* basic - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')
    all_script: Union[str, None] = Field(title="script name of all characters",
                                         description="can be null if characters are in different scripts or script is not assigned for a character")
    # all_letter: bool
    # all_number: bool
    # all_emoji: bool
    # all_basic: bool
    chars: List[InspectorCharResult]
    tokens: List[List[InspectorTokenResult]]
    aggregated: Dict
    ens_is_valid_name: bool = Field()
    ens_nameprep: Union[str, None] = Field()
    uts46_remap: Union[str, None] = Field()
    idna_encode: Union[str, None] = Field()
    version: str = Field(default='0.0.1', title="version of the name inspector",
                         description="version can be used for updating cache")


@app.get("/inspector/", response_model=InspectorResult)
async def root(name: str):
    return inspector.analyse_name(name)
