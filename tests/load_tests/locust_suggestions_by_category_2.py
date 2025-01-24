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

input_names = ['cat', 'zeus']

CAT = set(
    ['mainecoon.eth', 'ragdoll.eth', 'ragdollcat.eth', 'siamesecat.eth', 'persiancat.eth', 'lambkin.eth', 'manxcat.eth', 'birman.eth', 'birmancat.eth', 'bombaycat.eth', 'aba.eth', 'abb.eth', 'abe.eth', 'abi.eth', 'abt.eth', 'abu.eth', 'aby.eth', 'ace.eth', 'acy.eth', 'ada.eth', 'spacejam.eth', 'tweetiepie.eth', 'kingtweety.eth', 'scaredycat.eth', 'canaryrow.eth', 'popimpop.eth', 'tweetyssos.eth', 'cannedfeud.eth', 'carrotblanca.eth', 'dogpounded.eth', 'maniac.eth', 'theblackcat.eth', 'twoevileyes.eth', 'talesofterror.eth', 'unheimlichegeschichten.eth', 'yourviceisalockedroomandonlyihavethekey.eth', 'adult.eth', 'porn.eth', 'sex.eth', 'xxx.eth', 'com.eth', 'icmregistry.eth', 'net.eth', 'onion.eth', 'org.eth', 'melbourne.eth', 'bengalcat.eth', 'sphynxcat.eth', 'tabbycat.eth', 'calicocat.eth', 'larry.eth', 'cremepuff.eth', 'blackcat.eth', 'kitten.eth', 'feralcat.eth', 'streetcat.eth', 'dog.eth', 'rabbit.eth', 'guy.eth', 'cats.eth', 'hombre.eth', 'kitty.eth', 'rat.eth', 'housemouse.eth', 'mouse.eth', 'bozo.eth', 'cat🐈.eth', 'cat🐈\u200d⬛.eth', 'cat🇺🇸.eth', 'cat🐱.eth', 'cat🐯.eth', 'cat💩.eth', 'cat😸.eth', 'cat😺.eth', '🇺🇸cat.eth', 'i❤cat.eth', 'dedicated.eth', 'incat.eth', 'notcat.eth', 'certification.eth', 'indicate.eth', 'indicates.eth', 'catalogue.eth', 'catservice.eth', 'bestcat.eth', 'catholic.eth', 'cats.eth', '$cat.eth', 'catgatt.eth', 'thecat.eth', '_cat.eth', 'ξcat.eth', 'cater.eth', 'catautocad.eth', '0xcat.eth', 'cat22.eth', 'c47.eth', 'tac.eth', 'ca7.eth'])
ZEUS = set(
    ['abaddon.eth', 'alchemist.eth', 'ancientapparition.eth', 'antimage.eth', 'arcwarden.eth', 'axe.eth', 'bane.eth', 'batrider.eth', 'beastmaster.eth', 'bloodseeker.eth', 'spiderman.eth', 'ironman.eth', 'thanos.eth', 'hulk.eth', 'wolverine.eth', 'doctordoom.eth', 'venom.eth', 'galactus.eth', 'janefoster.eth', 'titania.eth', 'rihanna.eth', 'willsmith.eth', 'kanyewest.eth', 'eminem.eth', 'miakhalifa.eth', 'beyonce.eth', 'snoopdogg.eth', 'johncena.eth', 'badbunny.eth', 'coolio.eth', 'aaba.eth', 'aal.eth', 'aame.eth', 'aaoi.eth', 'aaon.eth', 'aapl.eth', 'aaww.eth', 'aaxj.eth', 'aaxn.eth', 'abac.eth', 'cthulhu.eth', 'vecna.eth', 'thor.eth', 'azathoth.eth', 'aslan.eth', 'raiden.eth', 'beerus.eth', 'odin.eth', 'ares.eth', 'tiamat.eth', 'aphrodite.eth', 'apollo.eth', 'artemis.eth', 'tauropolia.eth', 'prometheus.eth', 'athena.eth', 'heracles.eth', 'hermes.eth', 'hades.eth', 'cronus.eth', 'hera.eth', 'hades.eth', 'poseidon.eth', 'odin.eth', 'cronus.eth', 'heracles.eth', 'persephone.eth', 'thor.eth', 'asgard.eth', 'darth.eth', 'zeus🇺🇸.eth', 'zeus💩.eth', '🆉🅴🆄🆂.eth', '🇺🇸zeus.eth', 'zeus💲.eth', 'zeus🐋.eth', 'zeus🐉.eth', '💎zeus.eth', '•zeus.eth', 'godzeus.eth', 'thezeus.eth', 'notzeus.eth', 'zeusfactory.eth', 'sonofzeus.eth', 'statueofzeus.eth', 'gameoverzeus.eth', 'zeusor.eth', 't1zeus.eth', 'hazeus.eth', '_zeus.eth', 'drzeus.eth', 'zeuser.eth', '$zeus.eth', 'zeusmorpheus.eth', 'realzeus.eth', 'thezeus.eth', 'mrzeus.eth', 'zeus-.eth', 'zeusamadeus.eth', '23v5.eth', 'suez.eth', '2ev5.eth'])

class WebsiteUser(HttpUser):
    wait_time = lambda x: 0.0  # between(1, 5)

    URL = "/suggestions_by_category"

    @task(5)
    def suggestions_by_category(self):
        json = copy.deepcopy(request_data)
        json['label'] = random.choice(input_names) # + ' ' + str(random.randint(0, 1000000))
        r = self.client.post(self.URL, name='suggestions_by_category', json=json)
        # print(r.json())
        response = r.json()
        names = []
        for category in response['categories']:
            for suggestion in category['suggestions']:
                # print(suggestion['name'])
                names.append(suggestion['name'])
        # print(json['label'], names)
        if json['label'] == 'cat' and set(names) & ZEUS:
            print(json['label'], names)
        elif json['label'] == 'zeus' and set(names) & CAT:
            print(json['label'], names)

        # if json['label'] == 'cat' and set(names) != CAT:
        #     print(json['label'], names)
        # elif json['label'] == 'zeus' and set(names) != ZEUS:
        #     print(json['label'], names)
