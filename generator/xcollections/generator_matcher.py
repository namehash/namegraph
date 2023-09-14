from copy import copy
import random
from typing import Optional, Literal
from time import perf_counter
from itertools import cycle
import concurrent.futures
import logging

import elasticsearch.exceptions
from fastapi import HTTPException

from generator.xcollections.matcher import CollectionMatcher
from generator.xcollections.collection import Collection
from generator.xcollections.query_builder import ElasticsearchQueryBuilder

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

logger = logging.getLogger('generator')


class CollectionMatcherForGenerator(CollectionMatcher):
    def _search_for_generator(
            self,
            tokens: tuple[str, ...],
            max_related_collections: int = 5,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
            enable_learning_to_rank: bool = True,
    ) -> tuple[list[Collection], dict]:

        if not self.active:
            return [], {}

        tokenized_query = ' '.join(tokens)
        if len(tokens) > 1:
            tokenized_query = ''.join(tokens) + ' ' + tokenized_query

        include_fields = [
            'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.collection_types', 'metadata.modified',
        ]

        query_fields = [
            'data.collection_name^3', 'data.collection_name.exact^3', 'data.collection_description',
            'data.collection_keywords^2', 'data.names.normalized_name', 'data.names.tokenized_name'
        ]

        apply_diversity = name_diversity_ratio is not None or max_per_type is not None
        query_builder = ElasticsearchQueryBuilder() \
            .add_limit(max_related_collections if not apply_diversity else max_related_collections * 3) \
            .set_source({'includes': ['data.names.tokenized_name']}) \
            .add_rank_feature('template.collection_rank', boost=100) \
            .include_fields(include_fields)

        if enable_learning_to_rank:
            query_params = query_builder \
                .add_query(tokenized_query, fields=query_fields, type_='most_fields') \
                .add_rank_feature('metadata.members_rank_mean', boost=1) \
                .add_rank_feature('metadata.members_rank_median', boost=1) \
                .add_rank_feature('template.members_system_interesting_score_mean', boost=1) \
                .add_rank_feature('template.members_system_interesting_score_median', boost=1) \
                .add_rank_feature('template.valid_members_count', boost=1) \
                .add_rank_feature('template.invalid_members_count', boost=1) \
                .add_rank_feature('template.valid_members_ratio', boost=1) \
                .add_rank_feature('template.nonavailable_members_count', boost=1) \
                .add_rank_feature('template.nonavailable_members_ratio', boost=1) \
                .rescore_with_learning_to_rank(tokenized_query,
                                               window_size=self.ltr_window_size.instant,
                                               model_name=self.ltr_model_name,
                                               feature_set=self.ltr_feature_set,
                                               feature_store=self.ltr_feature_store,
                                               query_weight=0.001,
                                               rescore_query_weight=1000) \
                .build_params()
        else:
            query_params = query_builder \
                .add_query(tokenized_query, fields=query_fields, type_='cross_fields') \
                .add_rank_feature('metadata.members_count', boost=1) \
                .build_params()

        try:
            collections, es_response_metadata = self._execute_query(query_params, limit_names)

            if not apply_diversity:
                return collections[:max_related_collections], es_response_metadata

            diversified = self._apply_diversity(
                collections,
                max_related_collections,
                name_diversity_ratio,
                max_per_type
            )
            return diversified, es_response_metadata
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [collections generator]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

    # FIXME duplicate of CollectionMatcherForAPI.get_collections_membership_list_for_name
    # FIXME either we remove this or move to a parent class
    def _search_by_membership(
            self,
            name_label: str,
            limit_names: int = 10,
            sort_order: Literal['A-Z', 'Z-A', 'AI'] = 'AI',
            max_results: int = 3,
            offset: int = 0
    ) -> tuple[list[Collection], dict]:

        fields = [
            'data.collection_name', 'template.collection_rank',
            'metadata.owner', 'metadata.members_count', 'template.top10_names.normalized_name',
            'template.collection_types', 'metadata.modified',
        ]

        if sort_order == 'AI':
            sort_order = 'AI-by-member'

        query_params = (ElasticsearchQueryBuilder()
                        .add_filter('term', {'data.names.normalized_name': name_label})
                        .add_filter('term', {'data.public': True})
                        .set_source({'includes': ['data.names.tokenized_name']})
                        .add_rank_feature('metadata.members_count')
                        .add_rank_feature('template.members_system_interesting_score_median')
                        .add_rank_feature('template.valid_members_ratio')
                        .add_rank_feature('template.nonavailable_members_ratio', boost=10)
                        .set_sort_order(sort_order=sort_order, field='data.collection_name.raw')
                        .include_fields(fields)
                        .add_limit(max_results)
                        .add_offset(offset)
                        .build_params())
        try:
            collections, es_response_metadata = self._execute_query(query_params, limit_names)
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [by-member]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        return collections, es_response_metadata

    def search_for_generator(
            self,
            tokens: tuple[str, ...],
            max_related_collections: int = 5,
            name_diversity_ratio: Optional[float] = 0.5,
            max_per_type: Optional[int] = 3,
            limit_names: int = 10,
            enable_learning_to_rank: bool = True,
    ) -> tuple[list[Collection], dict]:

        t_before = perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            related_future = executor.submit(
                self._search_for_generator,
                tokens=tokens,
                max_related_collections=max_related_collections,
                name_diversity_ratio=name_diversity_ratio,
                max_per_type=max_per_type,
                limit_names=limit_names,
                enable_learning_to_rank=enable_learning_to_rank
            )

            membership_future = executor.submit(
                self._search_by_membership,
                name_label=''.join(tokens),
                limit_names=limit_names,
                sort_order='AI',
                max_results=max_related_collections,
                offset=0
            )

            related, es_response_metadata1 = related_future.result()
            membership, es_response_metadata2 = membership_future.result()

        time_elapsed = (perf_counter() - t_before) * 1000

        related_iter = iter(related)
        membership_iter = iter(membership)
        common = []
        used_ids = set()
        for iterable, items_to_take in cycle([(related_iter, 2), (membership_iter, 1)]):
            try:
                while items_to_take:
                    item = next(iterable)
                    if item.collection_id not in used_ids:
                        common.append(item)
                        used_ids.add(item.collection_id)
                        items_to_take -= 1
            except StopIteration:
                break

        if len(common) < max_related_collections:
            common.extend(related_iter)
            common.extend(membership_iter)

        if es_response_metadata1['n_total_hits'] == '1000+' or es_response_metadata2['n_total_hits'] == '1000+':
            n_total_hits = '1000+'
        else:
            n_total_hits = es_response_metadata1['n_total_hits'] + es_response_metadata2['n_total_hits']
            n_total_hits = '1000+' if n_total_hits > 1000 else n_total_hits

        es_response_metadata = {
            'n_total_hits': n_total_hits,
            'took': es_response_metadata1['took'] + es_response_metadata2['took'],
            'elasticsearch_communication_time': time_elapsed,
        }

        return common[:max_related_collections], es_response_metadata

    def sample_members_from_collection(
            self,
            collection_id: str,
            seed: int,
            max_sample_size: int = 10,
    ) -> tuple[dict, dict]:

        fields = ['data.collection_name']

        sampling_script = """
            def number_of_names = params._source.data.names.size();
            def random = new Random(params.seed);

            if (number_of_names <= params.max_sample_size) {
                return params._source.data.names.stream()
                    .map(n -> n.normalized_name)
                    .collect(Collectors.toList())
            }

            if (number_of_names <= 100 || params.max_sample_size * 2 >= number_of_names) {
                Collections.shuffle(params._source.data.names, random);
                return params._source.data.names.stream()
                    .limit(params.max_sample_size)
                    .map(n -> n.normalized_name)
                    .collect(Collectors.toList());
            }

            def set = new HashSet();

            while (set.size() < params.max_sample_size) {
                def index = random.nextInt(number_of_names);
                set.add(index);
            }

            return set.stream().map(i -> params._source.data.names[i].normalized_name).collect(Collectors.toList());
        """

        query_params = ElasticsearchQueryBuilder() \
            .set_term('_id', collection_id) \
            .include_fields(fields) \
            .set_source(False) \
            .include_script_field(name='sampled_members',
                                  script=sampling_script,
                                  lang='painless',
                                  params={'seed': seed, 'max_sample_size': max_sample_size}) \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.search(index=self.index_name, **query_params)
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [collection members sampling]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        try:
            hit = response['hits']['hits'][0]
            es_response_metadata = {
                'n_total_hits': 1,
                'took': response['took'],
                'elasticsearch_communication_time': time_elapsed,
            }
        except IndexError as ex:
            raise HTTPException(status_code=404, detail=f'Collection with id={collection_id} not found') from ex

        result = {
            'collection_id': hit['_id'],
            'collection_title': hit['fields']['data.collection_name'][0],
            'sampled_members': hit['fields']['sampled_members']
        }

        return result, es_response_metadata

    def fetch_top10_members_from_collection(self, collection_id: str, max_recursive_related_collections: int) -> tuple[
        dict, dict]:
        fields = ['data.collection_name', 'template.top10_names.normalized_name', 'metadata.members_count']

        try:
            t_before = perf_counter()
            response = self.elastic.get(index=self.index_name, id=collection_id, _source_includes=fields)
            time_elapsed = (perf_counter() - t_before) * 1000
        except elasticsearch.exceptions.NotFoundError as ex:
            raise HTTPException(status_code=404, detail=f'Collection with id={collection_id} not found') from ex
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [fetch top10 collection members]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        es_response_metadata = {
            'n_total_hits': 1,
            'elasticsearch_communication_time': time_elapsed,
        }

        result = {
            'collection_id': response['_id'],
            'collection_title': response['_source']['data']['collection_name'],
            'collection_members_count': response['_source']['metadata']['members_count'],
            'top_members': [item['normalized_name'] for item in response['_source']['template']['top10_names']],
            'related_collections': random.sample(RANDOM_COLLECTIONS, max_recursive_related_collections)
            # TODO get from ES
        }

        return result, es_response_metadata


    def scramble_tokens_from_collection(
            self,
            collection_id: str,
            method: Literal['left-right-shuffle', 'left-right-shuffle-with-unigrams', 'full-shuffle'],
            n_top_members: int,
            n_suggestions: int
    ) -> tuple[dict, dict]:

        fields = ['data.collection_name']

        query_params = ElasticsearchQueryBuilder() \
            .set_term('_id', collection_id) \
            .include_fields(fields) \
            .include_script_field('names_with_tokens', script="params['_source'].data.names.stream()"
                                                              f".limit({n_top_members}).collect(Collectors.toList())") \
            .build_params()

        try:
            t_before = perf_counter()
            response = self.elastic.search(index=self.index_name, **query_params)
            time_elapsed = (perf_counter() - t_before) * 1000
        except Exception as ex:
            logger.error(f'Elasticsearch search failed [scramble tokens from collection]', exc_info=True)
            raise HTTPException(status_code=503, detail=str(ex)) from ex

        try:
            hit = response['hits']['hits'][0]
            es_response_metadata = {
                'n_total_hits': 1,
                'took': response['took'],
                'elasticsearch_communication_time': time_elapsed,
            }
        except IndexError as ex:
            raise HTTPException(status_code=404, detail=f'Collection with id={collection_id} not found') from ex

        name_tokens_tuples = [(r['normalized_name'], r['tokenized_name']) for r in hit['fields']['names_with_tokens']]
        token_scramble_suggestions = self._get_suggestions_by_scrambling_tokens(
            name_tokens_tuples, method, n_suggestions=n_suggestions
        )

        result = {
            'collection_id': hit['_id'],
            'collection_title': hit['fields']['data.collection_name'][0],
            'token_scramble_suggestions': token_scramble_suggestions
        }

        return result, es_response_metadata


    def _get_suggestions_by_scrambling_tokens(
            self,
            name_tokens_tuples: list[tuple[str, list[str]]],
            method: Literal['left-right-shuffle', 'left-right-shuffle-with-unigrams', 'full-shuffle'],
            n_suggestions: Optional[int] = None
    ) -> list[str]:

        # collect bigrams (left and right tokens) and unigrams (collection names that could not be tokenized)
        left_tokens = set()
        right_tokens = set()
        unigrams = set()
        for name, tokenized_name in name_tokens_tuples:
            if len(tokenized_name) == 1:
                further_tokenized_name = self.bigram_longest_tokenizer.get_tokenization(name)
                if further_tokenized_name is None or further_tokenized_name == (name, ''):
                    unigrams.add(name)
                else:
                    left_tokens.add(further_tokenized_name[0])
                    right_tokens.add(further_tokenized_name[1])
            elif len(tokenized_name) == 2:
                left_tokens.add(tokenized_name[0])
                right_tokens.add(tokenized_name[1])
            elif len(tokenized_name) > 2:
                left_tokens.add(tokenized_name[0])
                # todo: there might be a better approach (if more than 2 tokens, cut in the center?)
                right_tokens.add(''.join(tokenized_name[1:]))

        original_names = {t[0] for t in name_tokens_tuples}
        suggestions = []

        left_tokens_list = list(left_tokens)
        right_tokens_list = list(right_tokens)
        unigrams_list = list(unigrams)

        if method == 'left-right-shuffle' or method == 'left-right-shuffle-with-unigrams':
            if method == 'left-right-shuffle-with-unigrams':
                random.shuffle(unigrams_list)
                mid = len(unigrams_list) // 2
                left_tokens_list = list(left_tokens | set(unigrams_list[:mid]))
                right_tokens_list = list(right_tokens | set(unigrams_list[mid:]))
            random.shuffle(left_tokens_list)
            random.shuffle(right_tokens_list)

            # if not enough left/right tokens, repeat tokens
            if n_suggestions is None:
                pass
            elif (est_n_suggestions := min(len(left_tokens_list), len(right_tokens_list))) < n_suggestions:
                n_repeats = min(n_suggestions // est_n_suggestions + 1, est_n_suggestions)
                left_tokens_list *= n_repeats
                right_tokens_list *= n_repeats

            while left_tokens_list and (n_suggestions is None or len(suggestions) < n_suggestions):
                left = left_tokens_list.pop()
                for i, right in enumerate(right_tokens_list):
                    s = left + right
                    if s not in original_names and s not in suggestions:
                        suggestions.append(s)
                        del right_tokens_list[i]
                        break
        elif method == 'full-shuffle':
            all_unigrams = list(left_tokens | right_tokens | unigrams)
            random.shuffle(all_unigrams)

            # if not enough all_unigrams, repeat tokens
            if n_suggestions is None:
                pass
            elif (est_n_suggestions := len(all_unigrams) // 2) < n_suggestions:
                n_repeats = min(n_suggestions // est_n_suggestions + 1, est_n_suggestions)
                all_unigrams *= n_repeats

            while len(all_unigrams) >= 2 and (n_suggestions is None or len(suggestions) < n_suggestions):
                left = all_unigrams.pop()
                for i, right in enumerate(all_unigrams):
                    s = left + right
                    if s not in original_names and s not in suggestions:
                        suggestions.append(s)
                        del all_unigrams[i]
                        break
        else:
            raise ValueError(f'[get_suggestions_by_scrambling_tokens] no such method allowed: \'{method}\'')

        random.shuffle(suggestions)

        if n_suggestions is not None and len(suggestions) != n_suggestions:
            logger.warning(f'[get_suggestions_by_scrambling_tokens] number of suggestions ({len(suggestions)}) '
                           f'does not equal desired n_suggestions ({n_suggestions})')

        return suggestions
