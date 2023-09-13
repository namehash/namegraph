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

RANDOM_COLLECTIONS = [
    {
        "collection_id": "Q8691332",
        "collection_title": "Obsolete occupations",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6568325",
        "collection_title": "DC Comics characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8387102",
        "collection_title": "Cold War spies",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q14914955",
        "collection_title": "21st-century American male actors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q110607984",
        "collection_title": "20th-century professional wrestlers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6312531",
        "collection_title": "British comedy films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6710019",
        "collection_title": "Dance styles",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1033564",
        "collection_title": "Musical instruments",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6240182",
        "collection_title": "Marvel Comics aliens",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6619974",
        "collection_title": "Films based on comic strips",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q31964013",
        "collection_title": "Censored books",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6561958",
        "collection_title": "Archie Comics characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q371776",
        "collection_title": "Marvel Comics characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q176649",
        "collection_title": "Explorers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6573012",
        "collection_title": "Hellboy comics",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7786397",
        "collection_title": "French comedy films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6620587",
        "collection_title": "Foods named after places",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q17097513",
        "collection_title": "Beef dishes",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1553781",
        "collection_title": "Jazz standards",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3253626",
        "collection_title": "Video game developers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1580173",
        "collection_title": "Christmas films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6607083",
        "collection_title": "Bands from Canada",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6639464",
        "collection_title": "Shortest-reigning monarchs",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6645607",
        "collection_title": "Paintings by Claude Monet",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q11811782",
        "collection_title": "Stage names",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8205190",
        "collection_title": "20th-century American singers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6461210",
        "collection_title": "Nobel laureates in Literature",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6619794",
        "collection_title": "Fictional universes in literature",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q9057217",
        "collection_title": "Muscle cars",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6577120",
        "collection_title": "Women of the Victorian era",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8795685",
        "collection_title": "Prohibition-era gangsters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q5001943",
        "collection_title": "Classical-era composers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6262914",
        "collection_title": "19th-century inventors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7012162",
        "collection_title": "Polish inventors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6574909",
        "collection_title": "Italian inventors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7145684",
        "collection_title": "English inventors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6596077",
        "collection_title": "Russian inventors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6635433",
        "collection_title": "Prolific inventors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1322417",
        "collection_title": "Wealthiest historical figures",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6636580",
        "collection_title": "Richest Americans in history",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q4353132",
        "collection_title": "Star Wars weapons",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3255153",
        "collection_title": "Star Wars spacecraft",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1547772",
        "collection_title": "Stars for navigation",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1141760",
        "collection_title": "Most luminous stars",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1064642",
        "collection_title": "Stars in Orion",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3245641",
        "collection_title": "Pornographic actors who appeared in mainstream films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6590889",
        "collection_title": "Muslim writers and poets",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q5128290",
        "collection_title": "Ancient Greek writers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7905486",
        "collection_title": "Child characters in literature",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7136631",
        "collection_title": "19th-century paintings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6312512",
        "collection_title": "American comedy films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q391049",
        "collection_title": "Works by Salvador Dal\u00ed",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q25424983",
        "collection_title": "Works by Gian Lorenzo Bernini",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6645649",
        "collection_title": "Works by Henri Matisse",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q17042473",
        "collection_title": "Most expensive video games to develop",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q24904880",
        "collection_title": "Most expensive animated films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q477949",
        "collection_title": "Most expensive photographs",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2476255",
        "collection_title": "Most expensive films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1368268",
        "collection_title": "Most expensive paintings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q578913",
        "collection_title": "The New York Times Best Seller list",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q90723885",
        "collection_title": "The World's 50 Best Bars",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7146100",
        "collection_title": "Best Directing Academy Award winners",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q20649326",
        "collection_title": "Best-selling films in the United States",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q468543",
        "collection_title": "Best-selling Nintendo Entertainment System video games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6614871",
        "collection_title": "Cult films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q99919996",
        "collection_title": "Walt Disney Studios films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q468514",
        "collection_title": "Best-selling albums in the United States",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6620067",
        "collection_title": "Films set in New York City",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q859266",
        "collection_title": "Best-selling music artists",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8273483",
        "collection_title": "Best-selling PC games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q260894",
        "collection_title": "Best-selling fiction authors",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q468558",
        "collection_title": "Best-selling video games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q17096236",
        "collection_title": "Films set on beaches",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6645657",
        "collection_title": "Works by John Singer Sargent",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q40888113",
        "collection_title": "Most-visited museums",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q4399678",
        "collection_title": "Baroque paintings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q253427",
        "collection_title": "Most valuable brands",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6468877",
        "collection_title": "Renaissance paintings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q5424600",
        "collection_title": "FBI Ten Most Wanted Fugitives, 1980s",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3438063",
        "collection_title": "Golfers with most European Tour wins",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q5424608",
        "collection_title": "FBI Ten Most Wanted Fugitives, 2000s",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3116876",
        "collection_title": "Paintings by Raphael",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1935417",
        "collection_title": "Paintings by Rembrandt",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8709510",
        "collection_title": "Mythological paintings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6621761",
        "collection_title": "Golfers with most PGA Tour wins",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q16511139",
        "collection_title": "The most common surnames in Germany",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q27661711",
        "collection_title": "Most-streamed songs on Spotify",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6620885",
        "collection_title": "Football managers with most games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6629053",
        "collection_title": "Most-listened-to radio programs",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6643122",
        "collection_title": "The most intense tropical cyclones",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2644810",
        "collection_title": "Most wanted fugitives in Italy",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1575895",
        "collection_title": "Cities with the most skyscrapers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1607351",
        "collection_title": "NBA players with most championships",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6641487",
        "collection_title": "Stolen paintings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6629083",
        "collection_title": "Most popular dog breeds",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1771711",
        "collection_title": "Most-visited art museums",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6629080",
        "collection_title": "Most popular given names",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q46609563",
        "collection_title": "Most-followed Twitch channels",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8508264",
        "collection_title": "Hellenistic-era philosophers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1362208",
        "collection_title": "Maritime explorers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q374709",
        "collection_title": "Chess openings",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q17105506",
        "collection_title": "Energy resources",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6625475",
        "collection_title": "Liqueurs",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2600160",
        "collection_title": "Board games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q11707952",
        "collection_title": "Programming languages",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q450779",
        "collection_title": "Hairstyles",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2678215",
        "collection_title": "Candies",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2507328",
        "collection_title": "Cocktails",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7466917",
        "collection_title": "Musicals",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6618930",
        "collection_title": "Entrepreneurs",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q212664",
        "collection_title": "Sports",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q376479",
        "collection_title": "Banned films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7035212",
        "collection_title": "Science fiction characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6811469",
        "collection_title": "Banned political parties",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6640427",
        "collection_title": "Sportswomen",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6606342",
        "collection_title": "Athletes on Wheaties boxes",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7046061",
        "collection_title": "Animated characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6632123",
        "collection_title": "Pen names",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6938680",
        "collection_title": "Discontinued software",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6278608",
        "collection_title": "1920s cars",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6379792",
        "collection_title": "Exploration ships",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q9536594",
        "collection_title": "Cowboys",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q233327",
        "collection_title": "Car brands",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6628565",
        "collection_title": "Military tactics",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q51805",
        "collection_title": "Star Wars characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1053077",
        "collection_title": "Mythological places",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q248137",
        "collection_title": "Etruscan cities",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q16000160",
        "collection_title": "Fictional pirates",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q17088638",
        "collection_title": "Drinking games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q47226",
        "collection_title": "South Park characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1863553",
        "collection_title": "Hip hop musicians",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q571113",
        "collection_title": "Glossary of chess",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3511268",
        "collection_title": "Video game franchises",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q267149",
        "collection_title": "The Simpsons characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q16375",
        "collection_title": "Star Trek characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2708098",
        "collection_title": "Apollo missions",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6357667",
        "collection_title": "Cigar brands",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q35094",
        "collection_title": "National capitals",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6636523",
        "collection_title": "Restaurant chains",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2733646",
        "collection_title": "Heavy metal bands",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q20900298",
        "collection_title": "Fictional islands",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q13353395",
        "collection_title": "Time travelers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7498272",
        "collection_title": "Star Wars creatures",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7784185",
        "collection_title": "Cyberpunk films",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q108061205",
        "collection_title": "Planets in science fiction",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8163929",
        "collection_title": "1980 singles",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2750576",
        "collection_title": "Fictional spacecraft",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6619674",
        "collection_title": "Fictional hackers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6596115",
        "collection_title": "S&P 500 companies",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q24735548",
        "collection_title": "Fictional countries",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q779391",
        "collection_title": "Cryptographers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q221173",
        "collection_title": "Outline of academic disciplines",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6619927",
        "collection_title": "Films about mathematicians",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8723010",
        "collection_title": "Women mathematicians",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q875625",
        "collection_title": "Ancient Romans",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2268342",
        "collection_title": "Ancient Greeks",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q614554",
        "collection_title": "Ancient Egyptians",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q65626784",
        "collection_title": "Ultimate Fighting Championship male fighters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6615344",
        "collection_title": "Current mixed martial arts champions",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1188538",
        "collection_title": "Street Fighter characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q4432676",
        "collection_title": "Male mixed martial artists",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3082644",
        "collection_title": "Bomber aircraft",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3409821",
        "collection_title": "Latin phrases (full)",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q2042322",
        "collection_title": "Historical currencies",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q80167",
        "collection_title": "Circulating currencies",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q858338",
        "collection_title": "Currencies",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8250685",
        "collection_title": "Ancient Greek explorers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8100596",
        "collection_title": "16th-century explorers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6619420",
        "collection_title": "Female explorers and travelers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8789379",
        "collection_title": "Pre-computer cryptographers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8637205",
        "collection_title": "Modern cryptographers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3769423",
        "collection_title": "Hacker groups",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3247039",
        "collection_title": "NASA aircraft",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6148196",
        "collection_title": "Fictional extraterrestrial characters",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q8427931",
        "collection_title": "Criminal duos",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q289111",
        "collection_title": "Punk rock bands",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q516588",
        "collection_title": "Greek mythological figures",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q56351871",
        "collection_title": "Lunar deities",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6620952",
        "collection_title": "Footwear designers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6619920",
        "collection_title": "Films about computers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1514175",
        "collection_title": "Types of sword",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7777128",
        "collection_title": "Historians of astronomy",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q56926",
        "collection_title": "Fashion designers",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q5827867",
        "collection_title": "Satellites orbiting Earth",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q9651963",
        "collection_title": "Women computer scientists",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6626703",
        "collection_title": "Longest-running American television series",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6461577",
        "collection_title": "Atari games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q82529",
        "collection_title": "Pioneers in computer science",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q1369166",
        "collection_title": "Sega Genesis games",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q3243244",
        "collection_title": "Equations",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6638016",
        "collection_title": "Scientific laws named after people",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q6632170",
        "collection_title": "People considered father or mother of a scientific field",
        "collection_members_count": 10
    },
    {
        "collection_id": "Q7034480",
        "collection_title": "Manga series",
    }
]

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
            'related_collections': random.sample(RANDOM_COLLECTIONS, max_recursive_related_collections) #TODO get from ES
        }

        return result, es_response_metadata
