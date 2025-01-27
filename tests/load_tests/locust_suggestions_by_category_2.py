import copy
import random

from locust import HttpUser, between, task

request_data = {
    "label": '',
    "params": {
        "user_info": {
            "user_wallet_addr": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "user_ip_addr": "192.168.0.1",
            "session_id": "d6374908-94c3-420f-b2aa-6dd41989baef",
            "user_ip_country": "us"
        },
        "mode": "full",
        "metadata": True
    },
    "categories": {
        "related": {
            "enable_learning_to_rank": True,
            "max_labels_per_related_collection": 10,
            "max_per_type": 2,
            "max_recursive_related_collections": 3,
            "max_related_collections": 6,
            "label_diversity_ratio": 0.5
        },
        "wordplay": {
            "max_suggestions": 10,
            "min_suggestions": 2
        },
        "alternates": {
            "max_suggestions": 10,
            "min_suggestions": 2
        },
        "emojify": {
            "max_suggestions": 10,
            "min_suggestions": 2
        },
        "community": {
            "max_suggestions": 10,
            "min_suggestions": 2
        },
        "expand": {
            "max_suggestions": 10,
            "min_suggestions": 2
        },
        "gowild": {
            "max_suggestions": 10,
            "min_suggestions": 2
        },
        "other": {
            "max_suggestions": 10,
            "min_suggestions": 6,
            "min_total_suggestions": 50
        }
    }
}

input_labels = ['cat', 'zeus']

CAT = set(
    ['mainecoon', 'ragdoll', 'ragdollcat', 'siamesecat', 'persiancat', 'lambkin', 'manxcat', 'birman', 'birmancat', 'bombaycat', 'aba', 'abb', 'abe', 'abi', 'abt', 'abu', 'aby', 'ace', 'acy', 'ada', 'spacejam', 'tweetiepie', 'kingtweety', 'scaredycat', 'canaryrow', 'popimpop', 'tweetyssos', 'cannedfeud', 'carrotblanca', 'dogpounded', 'maniac', 'theblackcat', 'twoevileyes', 'talesofterror', 'unheimlichegeschichten', 'yourviceisalockedroomandonlyihavethekey', 'adult', 'porn', 'sex', 'xxx', 'com', 'icmregistry', 'net', 'onion', 'org', 'melbourne', 'bengalcat', 'sphynxcat', 'tabbycat', 'calicocat', 'larry', 'cremepuff', 'blackcat', 'kitten', 'feralcat', 'streetcat', 'dog', 'rabbit', 'guy', 'cats', 'hombre', 'kitty', 'rat', 'housemouse', 'mouse', 'bozo', 'cat🐈', 'cat🐈\u200d⬛', 'cat🇺🇸', 'cat🐱', 'cat🐯', 'cat💩', 'cat😸', 'cat😺', '🇺🇸cat', 'i❤cat', 'dedicated', 'incat', 'notcat', 'certification', 'indicate', 'indicates', 'catalogue', 'catservice', 'bestcat', 'catholic', 'cats', '$cat', 'catgatt', 'thecat', '_cat', 'ξcat', 'cater', 'catautocad', '0xcat', 'cat22', 'c47', 'tac', 'ca7'])
ZEUS = set(
    ['abaddon', 'alchemist', 'ancientapparition', 'antimage', 'arcwarden', 'axe', 'bane', 'batrider', 'beastmaster', 'bloodseeker', 'spiderman', 'ironman', 'thanos', 'hulk', 'wolverine', 'doctordoom', 'venom', 'galactus', 'janefoster', 'titania', 'rihanna', 'willsmith', 'kanyewest', 'eminem', 'miakhalifa', 'beyonce', 'snoopdogg', 'johncena', 'badbunny', 'coolio', 'aaba', 'aal', 'aame', 'aaoi', 'aaon', 'aapl', 'aaww', 'aaxj', 'aaxn', 'abac', 'cthulhu', 'vecna', 'thor', 'azathoth', 'aslan', 'raiden', 'beerus', 'odin', 'ares', 'tiamat', 'aphrodite', 'apollo', 'artemis', 'tauropolia', 'prometheus', 'athena', 'heracles', 'hermes', 'hades', 'cronus', 'hera', 'hades', 'poseidon', 'odin', 'cronus', 'heracles', 'persephone', 'thor', 'asgard', 'darth', 'zeus🇺🇸', 'zeus💩', '🆉🅴🆄🆂', '🇺🇸zeus', 'zeus💲', 'zeus🐋', 'zeus🐉', '💎zeus', '•zeus', 'godzeus', 'thezeus', 'notzeus', 'zeusfactory', 'sonofzeus', 'statueofzeus', 'gameoverzeus', 'zeusor', 't1zeus', 'hazeus', '_zeus', 'drzeus', 'zeuser', '$zeus', 'zeusmorpheus', 'realzeus', 'thezeus', 'mrzeus', 'zeus-', 'zeusamadeus', '23v5', 'suez', '2ev5'])

class WebsiteUser(HttpUser):
    wait_time = lambda x: 0.0  # between(1, 5)

    URL = "/suggestions_by_category"

    @task(5)
    def suggestions_by_category(self):
        json = copy.deepcopy(request_data)
        json['label'] = random.choice(input_labels) # + ' ' + str(random.randint(0, 1000000))
        r = self.client.post(self.URL, name='suggestions_by_category', json=json)
        # print(r.json())
        response = r.json()
        labels = []
        for category in response['categories']:
            for suggestion in category['suggestions']:
                # print(suggestion['name'])
                labels.append(suggestion['name'])
        # print(json['label'], names)
        if json['label'] == 'cat' and set(labels) & ZEUS:
            print(json['label'], labels)
        elif json['label'] == 'zeus' and set(labels) & CAT:
            print(json['label'], labels)

        # if json['label'] == 'cat' and set(names) != CAT:
        #     print(json['label'], names)
        # elif json['label'] == 'zeus' and set(names) != ZEUS:
        #     print(json['label'], names)
