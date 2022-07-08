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
                          '* simple - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')


class InspectorEmptyTokenResult(BaseModel):
    token: str = Field(default='', const=True, title="always empty string")


class InspectorTokenResult(BaseModel):
    token: str = Field(title="the token")
    length: int = Field(title="number of Unicode characters")
    all_classes: List[str] = \
        Field(title="list of classes in which all characters are",
              description='* letter - a letter in any script; LC class http://www.unicode.org/reports/tr44/#GC_Values_Table'
                          '* number - a digit in any script; N class http://www.unicode.org/reports/tr44/#GC_Values_Table'  # TODO: check
                          '* hyphen - a hyphen'
                          '* emoji - an emoji'
                          '* simple - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')
    all_script: Union[str, None] = \
        Field(title="script name of all characters",
              description="can be null if characters are in different scripts or script is not assigned for a character")
    in_dictionary: bool = Field(title="if the token is in dictionary")
    pos: str = Field(title="part of speech of the token")
    lemma: str = Field(title="lemma of the word")


class InspectorTokenizedResult(BaseModel):
    tokens: List[Union[InspectorTokenResult, InspectorEmptyTokenResult]]


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
                          '* simple - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')
    unicodedata_category: str = Field(
        title="general category assigned to the character: http://www.unicode.org/reports/tr44/#GC_Values_Table",
        description='unicodedata_* uses library https://docs.python.org/3/library/unicodedata.html and is compiled with specific version of Unicode depending on Python version')
    unicodedata_bidirectional: str = Field(
        title="bidirectional class assigned to the character or empty string")  # TODO document those files
    unicodedata_combining: int = Field(title="canonical combining class assigned to the character")
    unicodedata_mirrored: int = Field(title="mirrored property assigned to the character")
    unicodedata_decomposition: str = Field(
        title="character decomposition mapping assigned to the character or empty string")
    unicodeblock: Union[str, None] = \
        Field(title="name of Unicode block in which the character is or null",
              description='the unicodeblock library is not maintained, it uses some old Unicode version')
    unidecode: str = Field(
        title="https://pypi.org/project/Unidecode/ Tries to represent name in ASCII characters.",
        description="e.g. it converts 'ł' to 'l', 'ω' (omega) to 'o'.")
    # NFKD_ascii: str = Field(title="string after decomposition in compatible mode with removed non-ascii chars")
    # NFD_ascii: str = Field(title="string after decomposition with removed non-ascii chars")
    # NFKD: str = Field(title="string after decomposition in compatible mode")
    # NFD: str = Field(title="string after decomposition")
    # confusable: bool = Field(title="if the character is confusable")  # TODO: remove?
    confusables: List[List[InspectorConfusableCharResult]] = \
        Field(title="set of confusable strings, each string is represented as a list of its characters",
              description='If the character is not confusable then empty list is returned. '
                          'The list also includes the original character. '
                          'The first element is usually a canonical form.'
                          'E.g. `ą` is confusable with `a`, and for `ą` returned will be `ą` and `a`.'
                          'However [a-z0-9] are always not confusable.'
                          'E.g. `ω` is confusable with `ώ` and on the first place in the list will be `ω` (the same), because its the canonical form.')


class InspectorResult(BaseModel):
    name: str = Field(title="input string")
    length: int = Field(title="number of Unicode characters")
    all_classes: List[str] = \
        Field(title="list of classes in which all characters are",
              description='* letter - a letter in any script; LC class http://www.unicode.org/reports/tr44/#GC_Values_Table'
                          '* number - a digit in any script; N class http://www.unicode.org/reports/tr44/#GC_Values_Table'  # TODO: check
                          '* hyphen - a hyphen'
                          '* emoji - an emoji'
                          '* simple - [a-z0-9-]'
                          '* invisible - zero width joiner or non-joiner')
    all_script: Union[str, None] = Field(title="script name of all characters",
                                         description="can be null if characters are in different scripts or script is not assigned for a character")
    # all_letter: bool
    # all_number: bool
    # all_emoji: bool
    # all_simple: bool
    chars: List[InspectorCharResult]
    tokenizations: List[InspectorTokenizedResult]
    # aggregated: Dict
    any_emoji: bool = Field(title='true if the string contains any emoji')
    any_invisible: bool = Field(title='true if the string contains any invisible character')
    all_unicodeblock: Union[str, None] = Field(
        title="Unicode block of all characters",
        description="can be null if characters are in different blocks or block is not assigned for a character")
    any_confusable: bool = Field(title='true if the string contains any confusable character')
    ens_is_valid_name: bool = Field(title='true if idna.uts46_remap(name, std3_rules=True) not raise errors',
                                    description='ens.main.ENS.is_valid_name(name)')
    ens_nameprep: Union[str, None] = Field(title='should be the same as idna.uts46_remap(name, std3_rules=True)',
                                           description='ens.main.ENS.nameprep(name)')
    uts46_remap: Union[str, None] = \
        Field(titile='Re-map the characters in the string according to UTS46 processing.',
              description='https://docs.ens.domains/contract-api-reference/name-processing#normalising-names'
                          'idna.uts46_remap(name, std3_rules=True)')
    idna_encode: Union[str, None] = Field(
        title='it does the same as uts46_remap(name, std3_rules=True), but do additional cheks regarding doots (subdomains), length, punycode, NFC, hyphens, combining characters',
        description='idna.encode(name, uts46=True, std3_rules=True, transitional=False)')
    version: str = Field(default='0.0.1', title="version of the name inspector",
                         description="version can be used for updating cache")


@app.get("/inspector/", response_model=InspectorResult)
async def root(name: str):
    return inspector.analyse_name(name)
