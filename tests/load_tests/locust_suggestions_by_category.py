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
            "max_names_per_related_collection": 10,
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

input_names = ['fire', 'funny', 'funnyshit', 'funnyshitass', 'funnyshitshit', 'lightwalker', 'josiahadams',
               'kwrobel', 'krzysztofwrobel', 'pikachu', 'mickey', 'adoreyoureyes', 'face', 'theman', 'goog',
               'billycorgan', '[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91]', 'a' * 101,
               'dogcat', 'firepower', 'tubeyou', 'fireworks', 'hacker', 'firecar', '😊😊😊', 'anarchy',
               'prayforukraine', 'krakowdragon', 'fiftysix', 'あかまい', '💛', 'asd', 'bartek', 'hongkong', 'hongkonger',
               'tyler', 'asdfasdfasdf3453212345', 'nineinchnails', 'krakow', 'joebiden', 'europeanunion',
               'rogerfederer', 'suzuki', 'pirates', 'doge', 'ethcorner', 'google', 'apple', '001',
               'stop-doing-fake-bids-its-honestly-lame-my-guy', 'kfcsogood', 'wallet', 'الأبيض', 'porno', 'sex',
               'slutwife', 'god', 'imexpensive', 'htaccess', 'nike', '€80000', 'starbucks', 'ukraine', '٠٠٩',
               'sony', 'kevin', 'discord', 'monaco', 'market', 'sportsbet', 'volodymyrzelensky', 'coffee', 'gold',
               'hodl', 'yeezy', 'brantly', 'jeezy', 'vitalik', 'exampleregistration', 'pyme', 'avalanche', 'messy',
               'messi', 'kingmessi', 'abc', 'testing', 'superman', 'facebook', 'test', 'namehash', 'testb',
               'happypeople', 'muscle', 'billybob', 'quo', 'circleci', 'bitcoinmine', 'poweroutage',
               'shootingarrowatthesky', 'pinkfloyd', 'kiwi']


class WebsiteUser(HttpUser):
    wait_time = lambda x: 0.0 #between(1, 5)

    URL = "/suggestions_by_category"

    @task(5)
    def suggestions_by_category(self):
        json = copy.deepcopy(request_data)
        json['label'] = random.choice(input_names) + ' ' + str(random.randint(0, 1000000))
        self.client.post(self.URL, name='suggestions_by_category', json=json)
