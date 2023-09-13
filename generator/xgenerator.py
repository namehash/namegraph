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
                    max_suggestions = category_params.max_related_collections * category_params.max_names_per_related_collection

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
