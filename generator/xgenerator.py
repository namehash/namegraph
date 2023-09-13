import collections
import concurrent.futures
import logging
import random
import time
from itertools import islice
from typing import List, Any

import wordninja
from omegaconf import DictConfig

from generator.preprocessor import Preprocessor
from generator.domains import Domains
from generator.generated_name import GeneratedName
from generator.pipeline import Pipeline
from generator.meta_sampler import MetaSampler
from generator.input_name import InputName
from generator.utils import aggregate_duplicates

logger = logging.getLogger('generator')


class Result:
    def __init__(self, config: DictConfig):
        self.domains = Domains(config)
        self.suggestions: List[List[GeneratedName]] = []

    def add_pipeline_suggestions(self, pipeline_suggestions: List[GeneratedName]):
        self.suggestions.append(pipeline_suggestions)

    def assign_statuses(self) -> None:
        for pipeline_suggestions in self.suggestions:
            for suggestion in pipeline_suggestions:
                suggestion.status = self.domains.get_name_status(str(suggestion))

    def unique_suggestions(self) -> int:
        return len(set([
            str(suggestion)
            for pipeline_suggestions in self.suggestions
            for suggestion in pipeline_suggestions
        ]))

    def available_suggestions(self) -> int:
        return len([
            suggestion
            for pipeline_suggestions in self.suggestions
            for suggestion in pipeline_suggestions
            if suggestion.status == Domains.AVAILABLE
        ])


class RelatedSuggestions(collections.UserList):
    def __init__(self, collection_title: str, collection_id: str, collection_members_count: int):
        super().__init__()
        self.collection_title = collection_title
        self.collection_id = collection_id
        self.collection_members_count = collection_members_count
        self.related_collections: list = []


RANDOM_COLLECTIONS = [{
    "collection_id": "Rn4TS0G7h04u",
    "collection_title": "Obsolete occupations",
    "collection_members_count": 10
}, {
    "collection_id": "kzlXjF0nokTC",
    "collection_title": "DC Comics characters",
    "collection_members_count": 10
}, {
    "collection_id": "5CdmAuHfxLra",
    "collection_title": "Cold War spies",
    "collection_members_count": 10
}, {
    "collection_id": "0XvELSuR7y_h",
    "collection_title": "21st-century American male actors",
    "collection_members_count": 10
}, {
    "collection_id": "cNy9n4Tv5tFm",
    "collection_title": "20th-century professional wrestlers",
    "collection_members_count": 10
}, {
    "collection_id": "n0yp8UgYdMss",
    "collection_title": "British comedy films",
    "collection_members_count": 10
}, {
    "collection_id": "rUci33FP3OwS",
    "collection_title": "Dance styles",
    "collection_members_count": 10
}, {
    "collection_id": "UepWlJCTZln1",
    "collection_title": "Musical instruments",
    "collection_members_count": 10
}, {
    "collection_id": "nCyUuy6rQiAP",
    "collection_title": "Marvel Comics aliens",
    "collection_members_count": 10
}, {
    "collection_id": "KIE6K9Jg7vgv",
    "collection_title": "Films based on comic strips",
    "collection_members_count": 10
}, {
    "collection_id": "c8RGzTnqZCiD",
    "collection_title": "Censored books",
    "collection_members_count": 10
}, {
    "collection_id": "5qRqZPd_KeRO",
    "collection_title": "Archie Comics characters",
    "collection_members_count": 10
}, {
    "collection_id": "BmjZ5T2bWFpk",
    "collection_title": "Marvel Comics characters",
    "collection_members_count": 10
}, {
    "collection_id": "xzNaDygkWMVo",
    "collection_title": "Explorers",
    "collection_members_count": 10
}, {
    "collection_id": "EA43gP3uI5NL",
    "collection_title": "Hellboy comics",
    "collection_members_count": 10
}, {
    "collection_id": "0hVnr8sRkukr",
    "collection_title": "French comedy films",
    "collection_members_count": 10
}, {
    "collection_id": "Emc7u4WtaNtp",
    "collection_title": "Foods named after places",
    "collection_members_count": 10
}, {
    "collection_id": "0WCTzrYMNoG1",
    "collection_title": "Beef dishes",
    "collection_members_count": 10
}, {
    "collection_id": "UpGCVBdMTpts",
    "collection_title": "Jazz standards",
    "collection_members_count": 10
}, {
    "collection_id": "jeJsHmpXAfk0",
    "collection_title": "Video game developers",
    "collection_members_count": 10
}, {
    "collection_id": "Rg36ar39wfFU",
    "collection_title": "Christmas films",
    "collection_members_count": 10
}, {
    "collection_id": "CtoU6z6v7wy8",
    "collection_title": "Bands from Canada",
    "collection_members_count": 10
}, {
    "collection_id": "KhEIfPSsD9FV",
    "collection_title": "Shortest-reigning monarchs",
    "collection_members_count": 10
}, {
    "collection_id": "1hXgVdZASbRd",
    "collection_title": "Paintings by Claude Monet",
    "collection_members_count": 10
}, {
    "collection_id": "Y8VJ5n116apI",
    "collection_title": "Stage names",
    "collection_members_count": 10
}, {
    "collection_id": "rscWddX5gdY0",
    "collection_title": "20th-century American singers",
    "collection_members_count": 10
}, {
    "collection_id": "ZWvYFmQ82Ffy",
    "collection_title": "Nobel laureates in Literature",
    "collection_members_count": 10
}, {
    "collection_id": "T9ok9ofLDeRD",
    "collection_title": "Fictional universes in literature",
    "collection_members_count": 10
}, {
    "collection_id": "Gatf71h41k7h",
    "collection_title": "Muscle cars",
    "collection_members_count": 10
}, {
    "collection_id": "26FTReK7esbE",
    "collection_title": "Women of the Victorian era",
    "collection_members_count": 10
}, {
    "collection_id": "SqfYnJR2_gym",
    "collection_title": "Prohibition-era gangsters",
    "collection_members_count": 10
}, {
    "collection_id": "66UpRRj5QCcj",
    "collection_title": "Classical-era composers",
    "collection_members_count": 10
}, {
    "collection_id": "B9LhWs9SAlGI",
    "collection_title": "19th-century inventors",
    "collection_members_count": 10
}, {
    "collection_id": "muYT3ivX12I2",
    "collection_title": "Polish inventors",
    "collection_members_count": 10
}, {
    "collection_id": "jWav3c4dxj1F",
    "collection_title": "Italian inventors",
    "collection_members_count": 10
}, {
    "collection_id": "vPXFy3hSl40y",
    "collection_title": "English inventors",
    "collection_members_count": 10
}, {
    "collection_id": "wA57LVyPZvmi",
    "collection_title": "Russian inventors",
    "collection_members_count": 10
}, {
    "collection_id": "sfrIjsTCGcFO",
    "collection_title": "Prolific inventors",
    "collection_members_count": 10
}, {
    "collection_id": "aaxILPm5TdCj",
    "collection_title": "Richest Americans in history",
    "collection_members_count": 10
}, {
    "collection_id": "_knZzsUAekUG",
    "collection_title": "Star Wars weapons",
    "collection_members_count": 10
}, {
    "collection_id": "EhQ49Ozw3K0m",
    "collection_title": "Star Wars spacecraft",
    "collection_members_count": 10
}, {
    "collection_id": "dZ422ZnidxJR",
    "collection_title": "Most luminous stars",
    "collection_members_count": 10
}, {
    "collection_id": "rjisxn50I7Im",
    "collection_title": "Stars in Orion",
    "collection_members_count": 10
}, {
    "collection_id": "6Z771V6bf7tL",
    "collection_title": "Pornographic actors who appeared in mainstream films",
    "collection_members_count": 10
}, {
    "collection_id": "1ukka8oAfM0O",
    "collection_title": "Muslim writers and poets",
    "collection_members_count": 10
}, {
    "collection_id": "17qyaSyQimYH",
    "collection_title": "Ancient Greek writers",
    "collection_members_count": 10
}, {
    "collection_id": "4mHWqJIUCZVY",
    "collection_title": "Child characters in literature",
    "collection_members_count": 10
}, {
    "collection_id": "DEPfifLgFKgh",
    "collection_title": "19th-century paintings",
    "collection_members_count": 10
}, {
    "collection_id": "72vVPATqGYtQ",
    "collection_title": "American comedy films",
    "collection_members_count": 10
}, {
    "collection_id": "HSQMe2jPewDo",
    "collection_title": "Works by Salvador Dalí",
    "collection_members_count": 10
}, {
    "collection_id": "wBKV7zdAEJuk",
    "collection_title": "Works by Gian Lorenzo Bernini",
    "collection_members_count": 10
}, {
    "collection_id": "ZKLnjo_W2lhF",
    "collection_title": "Works by Henri Matisse",
    "collection_members_count": 10
}, {
    "collection_id": "zKtzooh5Yjmf",
    "collection_title": "Most expensive video games to develop",
    "collection_members_count": 10
}, {
    "collection_id": "Fb77Zojl7Jwy",
    "collection_title": "Most expensive animated films",
    "collection_members_count": 10
}, {
    "collection_id": "dAYrT9CDP2Zk",
    "collection_title": "Most expensive photographs",
    "collection_members_count": 10
}, {
    "collection_id": "0iC_8BQ0pNKL",
    "collection_title": "Most expensive films",
    "collection_members_count": 10
}, {
    "collection_id": "k9m_GNKecMXI",
    "collection_title": "Most expensive paintings",
    "collection_members_count": 10
}, {
    "collection_id": "RONmxbNvOqzw",
    "collection_title": "The New York Times Best Seller list",
    "collection_members_count": 10
}, {
    "collection_id": "YC6mjmAgE_xD",
    "collection_title": "The World's 50 Best Bars",
    "collection_members_count": 10
}, {
    "collection_id": "s3Kd1FDjzRrH",
    "collection_title": "Best Directing Academy Award winners",
    "collection_members_count": 10
}, {
    "collection_id": "goZlhqv7nhjy",
    "collection_title": "Best-selling films in the United States",
    "collection_members_count": 10
}, {
    "collection_id": "yxA8UUSpyEta",
    "collection_title": "Best-selling Nintendo Entertainment System video games",
    "collection_members_count": 10
}, {
    "collection_id": "CchbWfyn2Rql",
    "collection_title": "Cult films",
    "collection_members_count": 10
}, {
    "collection_id": "gIGHkbXQJgzS",
    "collection_title": "Walt Disney Studios films",
    "collection_members_count": 10
}, {
    "collection_id": "d6kMx2Zq3n2u",
    "collection_title": "Best-selling albums in the United States",
    "collection_members_count": 10
}, {
    "collection_id": "Te7dYo4n78l5",
    "collection_title": "Films set in New York City",
    "collection_members_count": 10
}, {
    "collection_id": "BzdUNUNW77cB",
    "collection_title": "Best-selling music artists",
    "collection_members_count": 10
}, {
    "collection_id": "n5ApBFzc8FIS",
    "collection_title": "Best-selling PC games",
    "collection_members_count": 10
}, {
    "collection_id": "wvDEXG71Hw6t",
    "collection_title": "Best-selling fiction authors",
    "collection_members_count": 10
}, {
    "collection_id": "YEqAyeqw5_8E",
    "collection_title": "Best-selling video games",
    "collection_members_count": 10
}, {
    "collection_id": "BxJSj2cUXRGp",
    "collection_title": "Films set on beaches",
    "collection_members_count": 10
}, {
    "collection_id": "RFdwh8N68bzC",
    "collection_title": "Works by John Singer Sargent",
    "collection_members_count": 10
}, {
    "collection_id": "zRjpr5tsasLH",
    "collection_title": "Most-visited museums",
    "collection_members_count": 10
}, {
    "collection_id": "dCw6FzMg9ZqO",
    "collection_title": "Baroque paintings",
    "collection_members_count": 10
}, {
    "collection_id": "9aTrdtcqd26t",
    "collection_title": "Most valuable brands",
    "collection_members_count": 10
}, {
    "collection_id": "bPwgtwmL1ScK",
    "collection_title": "Renaissance paintings",
    "collection_members_count": 10
}, {
    "collection_id": "RpLJVythw7er",
    "collection_title": "FBI Ten Most Wanted Fugitives, 1980s",
    "collection_members_count": 10
}, {
    "collection_id": "9BUtvOe1sZp8",
    "collection_title": "Golfers with most European Tour wins",
    "collection_members_count": 10
}, {
    "collection_id": "bBsOoiQw94bf",
    "collection_title": "FBI Ten Most Wanted Fugitives, 2000s",
    "collection_members_count": 10
}, {
    "collection_id": "sso2QwGMX7yE",
    "collection_title": "Paintings by Raphael",
    "collection_members_count": 10
}, {
    "collection_id": "AgYZzjohMOTo",
    "collection_title": "Paintings by Rembrandt",
    "collection_members_count": 10
}, {
    "collection_id": "bhD0YD60Az7W",
    "collection_title": "Mythological paintings",
    "collection_members_count": 10
}, {
    "collection_id": "w8k_K0488Mkv",
    "collection_title": "Golfers with most PGA Tour wins",
    "collection_members_count": 10
}, {
    "collection_id": "RufejBxGSt3j",
    "collection_title": "The most common surnames in Germany",
    "collection_members_count": 10
}, {
    "collection_id": "jK9pcmL39qt_",
    "collection_title": "Most-streamed songs on Spotify",
    "collection_members_count": 10
}, {
    "collection_id": "6hjz5WHssENL",
    "collection_title": "Football managers with most games",
    "collection_members_count": 10
}, {
    "collection_id": "8ySok7TjE13v",
    "collection_title": "Most-listened-to radio programs",
    "collection_members_count": 10
}, {
    "collection_id": "hdud6s9Wv6FH",
    "collection_title": "The most intense tropical cyclones",
    "collection_members_count": 10
}, {
    "collection_id": "wezgtOjcJTfU",
    "collection_title": "Most wanted fugitives in Italy",
    "collection_members_count": 10
}, {
    "collection_id": "CddzuA9u59wN",
    "collection_title": "Cities with the most skyscrapers",
    "collection_members_count": 10
}, {
    "collection_id": "Z3YN5Uez0MVU",
    "collection_title": "NBA players with most championships",
    "collection_members_count": 10
}, {
    "collection_id": "jLGcbcAA_klI",
    "collection_title": "Stolen paintings",
    "collection_members_count": 10
}, {
    "collection_id": "2a7qaCz26MRq",
    "collection_title": "Most popular dog breeds",
    "collection_members_count": 10
}, {
    "collection_id": "GQxwMlq9SDlt",
    "collection_title": "Most-visited art museums",
    "collection_members_count": 10
}, {
    "collection_id": "qlVLOp9YGwX8",
    "collection_title": "Most popular given names",
    "collection_members_count": 10
}, {
    "collection_id": "Dx7EDYecPGQ2",
    "collection_title": "Most-followed Twitch channels",
    "collection_members_count": 10
}, {
    "collection_id": "IgKizwjeLuO5",
    "collection_title": "Hellenistic-era philosophers",
    "collection_members_count": 10
}, {
    "collection_id": "l0ajAWNvf6Yr",
    "collection_title": "Maritime explorers",
    "collection_members_count": 10
}, {
    "collection_id": "ujSC7uk5IA_D",
    "collection_title": "Chess openings",
    "collection_members_count": 10
}, {
    "collection_id": "TmFOy31z3Cdr",
    "collection_title": "Energy resources",
    "collection_members_count": 10
}, {
    "collection_id": "4vaYiFMbwZAB",
    "collection_title": "Liqueurs",
    "collection_members_count": 10
}, {
    "collection_id": "zeE0CyJumwa8",
    "collection_title": "Board games",
    "collection_members_count": 10
}, {
    "collection_id": "iCXiiZoHh2ml",
    "collection_title": "Programming languages",
    "collection_members_count": 10
}, {
    "collection_id": "LpZKTtODovKs",
    "collection_title": "Hairstyles",
    "collection_members_count": 10
}, {
    "collection_id": "0iHNOsobou3f",
    "collection_title": "Candies",
    "collection_members_count": 10
}, {
    "collection_id": "nll65OOYz9T8",
    "collection_title": "Cocktails",
    "collection_members_count": 10
}, {
    "collection_id": "lPuLOu5HQpzT",
    "collection_title": "Musicals",
    "collection_members_count": 10
}, {
    "collection_id": "d11eBUhLqijD",
    "collection_title": "Entrepreneurs",
    "collection_members_count": 10
}, {
    "collection_id": "WUvdQ5MPcqpQ",
    "collection_title": "Sports",
    "collection_members_count": 10
}, {
    "collection_id": "eJtHOwTktJ1w",
    "collection_title": "Banned films",
    "collection_members_count": 10
}, {
    "collection_id": "q0frEa2zle1Y",
    "collection_title": "Science fiction characters",
    "collection_members_count": 10
}, {
    "collection_id": "87XDeSmBu0DW",
    "collection_title": "Banned political parties",
    "collection_members_count": 10
}, {
    "collection_id": "1sPckzCRx3HY",
    "collection_title": "Sportswomen",
    "collection_members_count": 10
}, {
    "collection_id": "fxfprvLrFFjG",
    "collection_title": "Athletes on Wheaties boxes",
    "collection_members_count": 10
}, {
    "collection_id": "isv7LAyTH5Ft",
    "collection_title": "Animated characters",
    "collection_members_count": 10
}, {
    "collection_id": "raUFSb1GdbJ_",
    "collection_title": "Pen names",
    "collection_members_count": 10
}, {
    "collection_id": "d1UbNz8pfV5Q",
    "collection_title": "Discontinued software",
    "collection_members_count": 10
}, {
    "collection_id": "ybv_9FpqYLbl",
    "collection_title": "1920s cars",
    "collection_members_count": 10
}, {
    "collection_id": "BUJFgijETBJA",
    "collection_title": "Exploration ships",
    "collection_members_count": 10
}, {
    "collection_id": "ovZAARoXEw60",
    "collection_title": "Cowboys",
    "collection_members_count": 10
}, {
    "collection_id": "tvBGcodKLstS",
    "collection_title": "Car brands",
    "collection_members_count": 10
}, {
    "collection_id": "BYJQfDxjpI9w",
    "collection_title": "Military tactics",
    "collection_members_count": 10
}, {
    "collection_id": "CpCD1CdRD06d",
    "collection_title": "Star Wars characters",
    "collection_members_count": 10
}, {
    "collection_id": "coC_eu9KvoCN",
    "collection_title": "Mythological places",
    "collection_members_count": 10
}, {
    "collection_id": "I14bpsrVpQqE",
    "collection_title": "Etruscan cities",
    "collection_members_count": 10
}, {
    "collection_id": "9NFG1WEBHo1a",
    "collection_title": "Fictional pirates",
    "collection_members_count": 10
}, {
    "collection_id": "5f3xUvXtouJr",
    "collection_title": "Drinking games",
    "collection_members_count": 10
}, {
    "collection_id": "QCgbqo5D35QY",
    "collection_title": "South Park characters",
    "collection_members_count": 10
}, {
    "collection_id": "pQ5br1AM8WS0",
    "collection_title": "Hip hop musicians",
    "collection_members_count": 10
}, {
    "collection_id": "Dd9jxVuuuAGk",
    "collection_title": "Glossary of chess",
    "collection_members_count": 10
}, {
    "collection_id": "OGOlCrPAEqTx",
    "collection_title": "Video game franchises",
    "collection_members_count": 10
}, {
    "collection_id": "GYYuvk3MQc9j",
    "collection_title": "The Simpsons characters",
    "collection_members_count": 10
}, {
    "collection_id": "ZARwGb97Klxe",
    "collection_title": "Star Trek characters",
    "collection_members_count": 10
}, {
    "collection_id": "UpveSTQBSyL2",
    "collection_title": "Apollo missions",
    "collection_members_count": 10
}, {
    "collection_id": "JT1kR0GHtvo0",
    "collection_title": "Cigar brands",
    "collection_members_count": 10
}, {
    "collection_id": "ZbiRjnJ1UVKQ",
    "collection_title": "National capitals",
    "collection_members_count": 10
}, {
    "collection_id": "qoNSe9Sae3by",
    "collection_title": "Restaurant chains",
    "collection_members_count": 10
}, {
    "collection_id": "3Z8U4tsobyPo",
    "collection_title": "Heavy metal bands",
    "collection_members_count": 10
}, {
    "collection_id": "dORVWe_XS9uH",
    "collection_title": "Fictional islands",
    "collection_members_count": 10
}, {
    "collection_id": "PXK0XidiGaq9",
    "collection_title": "Time travelers",
    "collection_members_count": 10
}, {
    "collection_id": "q2kkMM74A5mV",
    "collection_title": "Star Wars creatures",
    "collection_members_count": 10
}, {
    "collection_id": "QnkK23Gk8jPM",
    "collection_title": "Cyberpunk films",
    "collection_members_count": 10
}, {
    "collection_id": "4DN1YsrDgvQz",
    "collection_title": "Planets in science fiction",
    "collection_members_count": 10
}, {
    "collection_id": "kB_LYH9Cm8G9",
    "collection_title": "1980 singles",
    "collection_members_count": 10
}, {
    "collection_id": "nDTcwrPMJV4r",
    "collection_title": "Fictional spacecraft",
    "collection_members_count": 10
}, {
    "collection_id": "LVH632ccYneC",
    "collection_title": "Fictional hackers",
    "collection_members_count": 10
}, {
    "collection_id": "1fuDavdSb219",
    "collection_title": "S&P 500 companies",
    "collection_members_count": 10
}, {
    "collection_id": "o5joEHqwxILQ",
    "collection_title": "Fictional countries",
    "collection_members_count": 10
}, {
    "collection_id": "PIA_aCFoMZul",
    "collection_title": "Cryptographers",
    "collection_members_count": 10
}, {
    "collection_id": "CkOz4FMOKtvr",
    "collection_title": "Outline of academic disciplines",
    "collection_members_count": 10
}, {
    "collection_id": "HgRv0SRx0Ox6",
    "collection_title": "Films about mathematicians",
    "collection_members_count": 10
}, {
    "collection_id": "Zm_wPk1y5vvd",
    "collection_title": "Women mathematicians",
    "collection_members_count": 10
}, {
    "collection_id": "Yo6n6XRoo2l0",
    "collection_title": "Ancient Romans",
    "collection_members_count": 10
}, {
    "collection_id": "a93lHGFRzP31",
    "collection_title": "Ancient Greeks",
    "collection_members_count": 10
}, {
    "collection_id": "N8hOXdjVQjuZ",
    "collection_title": "Ancient Egyptians",
    "collection_members_count": 10
}, {
    "collection_id": "R5os_gRrhAR0",
    "collection_title": "Ultimate Fighting Championship male fighters",
    "collection_members_count": 10
}, {
    "collection_id": "TYH9rMt54U4P",
    "collection_title": "Current mixed martial arts champions",
    "collection_members_count": 10
}, {
    "collection_id": "USPyI8ZRDupc",
    "collection_title": "Street Fighter characters",
    "collection_members_count": 10
}, {
    "collection_id": "NJlLzYrhIvYi",
    "collection_title": "Male mixed martial artists",
    "collection_members_count": 10
}, {
    "collection_id": "Tkm6X2KhkCgg",
    "collection_title": "Bomber aircraft",
    "collection_members_count": 10
}, {
    "collection_id": "QgJAPZ80rXlm",
    "collection_title": "Latin phrases (full)",
    "collection_members_count": 10
}, {
    "collection_id": "A4oPQkViRRoS",
    "collection_title": "Historical currencies",
    "collection_members_count": 10
}, {
    "collection_id": "DKd5PiITYx4S",
    "collection_title": "Circulating currencies",
    "collection_members_count": 10
}, {
    "collection_id": "59vidPzkFOkx",
    "collection_title": "Currencies",
    "collection_members_count": 10
}, {
    "collection_id": "837dlXhajRUx",
    "collection_title": "Ancient Greek explorers",
    "collection_members_count": 10
}, {
    "collection_id": "6XwhccNWq1dH",
    "collection_title": "16th-century explorers",
    "collection_members_count": 10
}, {
    "collection_id": "nqMku1yqmOag",
    "collection_title": "Female explorers and travelers",
    "collection_members_count": 10
}, {
    "collection_id": "Wuv2eLY7BBm6",
    "collection_title": "Pre-computer cryptographers",
    "collection_members_count": 10
}, {
    "collection_id": "7GkyeC9IWZ_Y",
    "collection_title": "Modern cryptographers",
    "collection_members_count": 10
}, {
    "collection_id": "yce20ppJTPaR",
    "collection_title": "Hacker groups",
    "collection_members_count": 10
}, {
    "collection_id": "MP8wk872pYYL",
    "collection_title": "NASA aircraft",
    "collection_members_count": 10
}, {
    "collection_id": "zw2La_KTIzfl",
    "collection_title": "Fictional extraterrestrial characters",
    "collection_members_count": 10
}, {
    "collection_id": "3l5KcyaWNTYp",
    "collection_title": "Criminal duos",
    "collection_members_count": 10
}, {
    "collection_id": "DpVpG0nFIFtN",
    "collection_title": "Punk rock bands",
    "collection_members_count": 10
}, {
    "collection_id": "3vkCFOZ101p1",
    "collection_title": "Greek mythological figures",
    "collection_members_count": 10
}, {
    "collection_id": "JtCnUA0x_BD5",
    "collection_title": "Lunar deities",
    "collection_members_count": 10
}, {
    "collection_id": "oGOANxvfU8cX",
    "collection_title": "Footwear designers",
    "collection_members_count": 10
}, {
    "collection_id": "XqPQbwma51i1",
    "collection_title": "Films about computers",
    "collection_members_count": 10
}, {
    "collection_id": "XW4IILWegiXl",
    "collection_title": "Types of sword",
    "collection_members_count": 10
}, {
    "collection_id": "19DhHlGEa3Dr",
    "collection_title": "Historians of astronomy",
    "collection_members_count": 10
}, {
    "collection_id": "j0Wu2vwyVj7R",
    "collection_title": "Fashion designers",
    "collection_members_count": 10
}, {
    "collection_id": "qB8M4s9PgN1k",
    "collection_title": "Satellites orbiting Earth",
    "collection_members_count": 10
}, {
    "collection_id": "A5fXMo9LJYLG",
    "collection_title": "Women computer scientists",
    "collection_members_count": 10
}, {
    "collection_id": "cDy2E8g5tEvc",
    "collection_title": "Longest-running American television series",
    "collection_members_count": 10
}, {
    "collection_id": "vn8mUlr1UQ6J",
    "collection_title": "Atari games",
    "collection_members_count": 10
}, {
    "collection_id": "KLfU1xWB6TIi",
    "collection_title": "Pioneers in computer science",
    "collection_members_count": 10
}, {
    "collection_id": "nEjrCGdNtoRp",
    "collection_title": "Sega Genesis games",
    "collection_members_count": 10
}, {
    "collection_id": "3Ruz4H6s7iyQ",
    "collection_title": "Equations",
    "collection_members_count": 10
}, {
    "collection_id": "Sd0WHBpuWFW1",
    "collection_title": "Scientific laws named after people",
    "collection_members_count": 10
}, {
    "collection_id": "X6S0sgGBKPnO",
    "collection_title": "People considered father or mother of a scientific field",
    "collection_members_count": 10
}, {
    "collection_id": "yoWTPmmY9HNz",
    "collection_title": "Manga series",
    "collection_members_count": 10
}]


class Generator:
    def __init__(self, config: DictConfig):
        self.domains = None
        self.config = config

        self.pipelines = []
        for definition in self.config.pipelines:
            # logger.info('start ' + str(definition.name))
            self.pipelines.append(Pipeline(definition, self.config))
            # logger.info('end ' + str(definition.name))

        self.random_available_name_pipeline = Pipeline(self.config.random_available_name_pipeline, self.config)

        self.init_objects()
        self.preprocessor = Preprocessor(config)
        self.metasampler = MetaSampler(config, self.pipelines)

        # self.weights = {}
        # for definition in self.config.pipelines:
        #     self.weights[definition.name] = definition.weights

        # new grouped endpoint
        # 1. split pipelines into categories
        generator_to_category = {}
        for category, generator_names in self.config.generation.grouping_categories.items():
            for generator_name in generator_names:
                generator_to_category[generator_name] = category

        self.pipelines_grouped = {}
        for pipeline in self.pipelines:
            if pipeline.definition.generator in generator_to_category:
                category = generator_to_category[pipeline.definition.generator]
                if category not in self.pipelines_grouped:
                    self.pipelines_grouped[category] = []
                self.pipelines_grouped[category].append(pipeline)

        # 2. Within each category: sample type and lang of interpretation, sample interpretaion with this type and lang. Sample pipeline (weights of pipelines depends on type and language. Do it in parallel?
        self.grouped_metasamplers = {}
        for category, pipelines in self.pipelines_grouped.items():
            self.grouped_metasamplers[category] = MetaSampler(config, pipelines)

        # 3. Sample `max number of suggestions per category`. How handle `min_available_fraction`?

    def init_objects(self):
        self.domains = Domains(self.config)
        wordninja.DEFAULT_LANGUAGE_MODEL = wordninja.LanguageModel(self.config.tokenization.wordninja_dictionary)

    def generate_names(
            self,
            name: str,
            sorter: str = 'weighted-sampling',
            min_suggestions: int = None,
            max_suggestions: int = None,
            min_available_fraction: float = 0.1,
            params: dict[str, Any] = None
    ) -> list[GeneratedName]:
        params = params or {}

        min_suggestions = min_suggestions or self.config.app.suggestions
        max_suggestions = max_suggestions or self.config.app.suggestions
        min_available_fraction = min_available_fraction or self.config.app.min_available_fraction

        params['min_suggestions'] = min_suggestions
        params['max_suggestions'] = max_suggestions
        params['min_available_fraction'] = min_available_fraction

        name = InputName(name, params)
        logger.info('Start normalize')
        self.preprocessor.normalize(name)
        logger.info('Start classify')
        self.preprocessor.classify(name)
        logger.info('End preprocessing')

        logger.info(str(name.types_probabilities))

        logger.info('Start sampling')
        all_suggestions = self.metasampler.sample(name, sorter, min_suggestions=name.params['min_suggestions'],
                                                  max_suggestions=name.params['max_suggestions'],
                                                  min_available_fraction=name.params['min_available_fraction'])

        logger.info(f'Generated suggestions: {len(all_suggestions)}')

        if len(all_suggestions) < min_suggestions:
            only_available_suggestions = self.random_available_name_pipeline.apply(name, None)
            all_suggestions.extend(only_available_suggestions)  # TODO dodawaj do osiągnięcia limitu
            logger.info(f'Generated suggestions after random: {len(all_suggestions)}')
            all_suggestions = aggregate_duplicates(all_suggestions)

        return all_suggestions[:max_suggestions]

    def generate_grouped_names(
            self,
            name: str,
            max_related_collections: int = 5,
            max_names_per_related_collection: int = 5,
            max_recursive_related_collections: int = 5,
            categories_params=None,
            min_total_suggestions: int = 50,
            params: dict[str, Any] = None
    ) -> tuple[dict[str, RelatedSuggestions], dict[str, list[GeneratedName]]]:
        params = params or {}
        categories_params = categories_params or {}

        params['max_related_collections'] = max_related_collections
        params['max_names_per_related_collection'] = max_names_per_related_collection
        params['max_recursive_related_collections'] = max_recursive_related_collections
        params['categories_params'] = categories_params
        params['min_total_suggestions'] = min_total_suggestions
        params['max_suggestions'] = 200  # TODO used to limit generators
        params['name_diversity_ratio'] = categories_params.related.name_diversity_ratio
        params['max_per_type'] = categories_params.related.max_per_type
        params['enable_learning_to_rank'] = categories_params.related.enable_learning_to_rank

        min_available_fraction = 0.0

        name = InputName(name, params)
        logger.info('Start normalize')
        self.preprocessor.normalize(name)
        logger.info('Start classify')
        self.preprocessor.classify(name)
        logger.info('End preprocessing')

        logger.info(str(name.types_probabilities))

        logger.info('Start sampling')

        multithreading = True
        grouped_suggestions = {}
        if not multithreading:
            for category, meta_sampler in self.grouped_metasamplers.items():
                start_time = time.time()

                category_params = getattr(categories_params, category)
                try:
                    min_suggestions = category_params.min_suggestions
                    max_suggestions = category_params.max_suggestions
                except AttributeError:  # RelatedCategoryParams
                    min_suggestions = 0
                    max_suggestions = 3 * category_params.max_related_collections * category_params.max_names_per_related_collection # 3 interpretations

                # TODO should they use the same set of suggestions (for deduplications)
                suggestions = meta_sampler.sample(name, 'weighted-sampling',
                                                  min_suggestions=min_suggestions,
                                                  max_suggestions=max_suggestions,
                                                  min_available_fraction=min_available_fraction,
                                                  category_endpoint=True)

                generator_time = 1000 * (time.time() - start_time)
                logger.info(
                    f'Generated suggestions in category {category}: {len(suggestions)} Time: {generator_time:.2f}')
                grouped_suggestions[category] = suggestions
        else:
            # multithreading using concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.grouped_metasamplers)) as executor:
                futures = {}
                for category, meta_sampler in self.grouped_metasamplers.items():
                    start_time = time.time()

                    category_params = getattr(categories_params, category)
                    try:
                        min_suggestions = category_params.min_suggestions
                        max_suggestions = category_params.max_suggestions
                    except AttributeError:  # RelatedCategoryParams
                        min_suggestions = 0
                        max_suggestions = category_params.max_related_collections * category_params.max_names_per_related_collection

                    futures[executor.submit(meta_sampler.sample, name, 'weighted-sampling',
                                            min_suggestions=min_suggestions, max_suggestions=max_suggestions,
                                            min_available_fraction=min_available_fraction,
                                            category_endpoint=True)] = category
                for future in concurrent.futures.as_completed(futures):
                    category = futures[future]
                    suggestions = future.result()
                    generator_time = 1000 * (time.time() - start_time)
                    logger.info(
                        f'Generated suggestions in category {category}: {len(suggestions)} Time: {generator_time:.2f}')
                    grouped_suggestions[category] = suggestions

        # split related

        all_related_suggestions: dict[str, RelatedSuggestions] = {}
        if 'related' in grouped_suggestions:
            for suggestion in grouped_suggestions['related']:
                if suggestion.collection_id not in all_related_suggestions:
                    all_related_suggestions[suggestion.collection_id] = RelatedSuggestions(suggestion.collection_title,
                                                                                           suggestion.collection_id,
                                                                                           suggestion.collection_members_count)
                    # TODO fix by taking related collections from ES
                    all_related_suggestions[suggestion.collection_id].related_collections = random.sample(
                        RANDOM_COLLECTIONS, max_recursive_related_collections)

                all_related_suggestions[suggestion.collection_id].append(suggestion)
            del grouped_suggestions['related']

        # TODO agregate duplicates
        # all_suggestions = aggregate_duplicates(all_suggestions)

        # remove categories with less than min_suggestions suggestions and cap to max_suggestions
        for category, suggestions in list(grouped_suggestions.items()):
            category_params = getattr(categories_params, category)
            min_suggestions = category_params.min_suggestions
            max_suggestions = category_params.max_suggestions
            if len(suggestions) < min_suggestions:
                del grouped_suggestions[category]
            else:
                grouped_suggestions[category] = suggestions[:max_suggestions]

        category_params = getattr(categories_params, 'related')
        for category, related_suggestions in all_related_suggestions.items():
            max_suggestions = category_params.max_names_per_related_collection
            related_suggestions.data = related_suggestions.data[:max_suggestions]

        # cap related collections to max_related_collections
        for category in list(all_related_suggestions.keys())[max_related_collections:]:
            del all_related_suggestions[category]

        count_real_suggestions = sum(
            [len(suggestions) for suggestions in grouped_suggestions.values()] + [len(suggestions) for suggestions in
                                                                                  all_related_suggestions.values()])

        logger.info(f'Generated suggestions: {count_real_suggestions}')

        if count_real_suggestions < min_total_suggestions:
            category_params = getattr(categories_params, 'other')
            other_suggestions_number = max(
                min((min_total_suggestions - count_real_suggestions), category_params.max_suggestions),
                category_params.min_suggestions)
            logger.info(f'Generated other suggestions: {other_suggestions_number}')
            only_available_suggestions = self.random_available_name_pipeline.apply(name, None)
            grouped_suggestions['other'] = list(islice(only_available_suggestions, other_suggestions_number))

        return all_related_suggestions, grouped_suggestions

    def clear_cache(self) -> None:
        for pipeline in self.pipelines:
            pipeline.clear_cache()
        self.random_available_name_pipeline.clear_cache()
