import random
import re

from namegraph.domains import Domains
from namegraph.generation.categories_generator import load_categories
from hydra import initialize, compose

with initialize(version_base=None, config_path="../../conf/"):
    config = compose(config_name="prod_config")
    domains = Domains(config)
    categories = load_categories(config)
    registered = set(domains.taken) | set(domains.on_sale)
    result = []
    for category, names in categories.items():
        left = set(names) - registered
        result.append((len(left), len(names), category, len(left) / len(names)))

    print('[unregistered names in the club] / [all in the club] = [ratio] [club name]: [sample of names]')
    for left, all, category, percentage in sorted(result, reverse=True):
        category_name = re.sub('^data/categories/', '', category)
        names = categories[category]
        random.shuffle(names)
        print(f'{left} / {all} = {percentage:0.2f} {category_name}: {names[:5]}')
