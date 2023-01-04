import collections
import copy
import json
import math
from typing import Optional, Dict, List

from omegaconf import DictConfig


class PersonNames:
    """
    For each interpretation (tokenization) calculates probability of a person existence with given name per country. 
    It is weighted by number of Internet users.
    We want also tokenizer - should it be the highest prob or sum of probs for given interpretation.
    """

    def __init__(self, config):
        self.firstnames = json.load(
            open(config.person_names.firstnames_path))  # json.load(open('s_firstnames_10k.json'))
        self.lastnames = json.load(open(config.person_names.lastnames_path))  # json.load(open('s_lastnames_10k.json'))
        other = json.load(open(config.person_names.other_path))  # json.load(open('s_other_10k.json'))
        self.countries: Dict[str, int] = other['all']
        self.firstname_initials: Dict[str, Dict[str, int]] = other['firstname_initials']
        self.lastname_initials: Dict[str, Dict[str, int]] = other['lastname_initials']

        self.country_stats = json.load(
            open(config.person_names.country_stats_path))  # json.load(open('country_stats.json'))
        self.all_internet_users: int = sum(x[0] for x in self.country_stats.values())
        self.all_population: int = sum(x[1] for x in self.country_stats.values())

        self.country_bonus = config.person_names.country_bonus  # if user country is provided then its score is multiplied by this value
        self.allow_cross_country = False

    def print_missing_countries(self):
        for country, stats in sorted(self.country_stats.items(), key=lambda x: x[1][0], reverse=True):
            if country not in self.countries:
                print('X', country, stats)
            else:
                print(country, stats)

    def get_population(self, country: str) -> Optional[int]:
        try:
            return self.country_stats[country][1]
        except:
            return None

    def get_internet_users(self, country: str) -> Optional[int]:
        try:
            return self.country_stats[country][0]
        except:
            return None

    def get_internet_users_weight(self, country: str) -> Optional[float]:
        try:
            return self.country_stats[country][0] / self.all_internet_users
        except:
            return None

    def single_name(self, name: str, name_stats: Dict[str, Dict[str, int]]) -> Dict:
        name_prob = {
            country: sum(gender_counts.values()) / self.countries[country] * self.get_internet_users_weight(country)
            for country, gender_counts in name_stats.items()}

        genders = {}
        for country, gender_counts in name_stats.items():
            m = gender_counts.get('M', 1)
            f = gender_counts.get('F', 1)
            genders[country] = {'M': m / (m + f), 'F': f / (m + f)}

        interpretation = {}
        interpretation['names'] = [name_stats]
        interpretation['prob'] = name_prob
        interpretation['tokenization'] = [name]
        interpretation['genders'] = genders
        return interpretation

    def name_with_initial(self, name: str, initial: str, name_stats: Dict[str, Dict[str, int]], initial_firstname: bool,
                          initial_first: bool) -> Dict:
        name_prob = {
            country: sum(gender_counts.values()) / self.countries[country] *
                     (self.firstname_initials[country].get(initial, 1) if initial_firstname else
                      self.lastname_initials[country].get(initial, 1)) /
                     self.countries[country] * self.get_internet_users_weight(country) for country, gender_counts in
            name_stats.items()}

        genders = {}
        for country, gender_counts in name_stats.items():
            m = gender_counts.get('M', 1)
            f = gender_counts.get('F', 1)
            genders[country] = {'M': m / (m + f), 'F': f / (m + f)}

        interpretation = {}
        if initial_first:
            interpretation['tokenization'] = [initial, name]
        else:
            interpretation['tokenization'] = [name, initial]

        interpretation['names'] = [name_stats]
        interpretation['prob'] = name_prob
        interpretation['genders'] = genders
        return interpretation

    def two_names(self, name1: str, name2: str, name1_stats: Dict[str, Dict[str, int]],
                  name2_stats: Dict[str, Dict[str, int]]) -> Dict:
        name1_prob = {country: sum(gender_counts.values()) / self.countries[country] for
                      country, gender_counts in name1_stats.items()}
        name2_prob = {country: sum(gender_counts.values()) / self.countries[country] for
                      country, gender_counts in name2_stats.items()}
        interpretation = {}
        interpretation['names'] = [name1_stats, name2_stats]
        interpretation['tokenization'] = [name1, name2]

        probs = collections.defaultdict(list)
        probs2 = {}
        genders = {}
        for name_prob in [name1_prob, name2_prob]:
            for country, prob in name_prob.items():
                probs[country].append(prob)
        for country, probs in probs.items():
            if len(probs) == 1:
                if not self.allow_cross_country: continue
                probs.append(1 / self.countries[country])
            probs2[country] = math.prod(probs)
            probs2[country] *= self.get_internet_users_weight(country)

            m = name1_stats.get(country, {}).get('M', 1) * name2_stats.get(country, {}).get('M', 1)
            f = name1_stats.get(country, {}).get('F', 1) * name2_stats.get(country, {}).get('F', 1)
            genders[country] = {'M': m / (m + f), 'F': f / (m + f)}
        interpretation['prob'] = probs2
        interpretation['genders'] = genders

        return interpretation

    def anal(self, input_name: str) -> List[Dict]:
        interpretations = []
        # only one name
        name_stats = copy.copy(self.firstnames.get(input_name, None))
        if name_stats:
            interpretation = self.single_name(input_name, name_stats)
            interpretation['type'] = 'first'
            interpretations.append(interpretation)

        name_stats = copy.copy(self.lastnames.get(input_name, None))
        if name_stats:
            interpretation = self.single_name(input_name, name_stats)
            interpretation['type'] = 'last'
            interpretations.append(interpretation)

        # one name with initial
        for name, initial, initial_first in [(input_name[1:], input_name[:1], True),
                                             (input_name[:-1], input_name[-1:], False)]:
            if not initial or not name: continue
            name_stats = copy.copy(self.firstnames.get(name, None))
            if name_stats:
                interpretation = self.name_with_initial(name, initial, name_stats, initial_firstname=False,
                                                        initial_first=initial_first)
                interpretation['type'] = 'first with initial'
                interpretations.append(interpretation)

            name_stats = copy.copy(self.lastnames.get(name, None))
            if name_stats:
                interpretation = self.name_with_initial(name, initial, name_stats, initial_firstname=True,
                                                        initial_first=initial_first)
                interpretation['type'] = 'last with initial'
                interpretations.append(interpretation)

        # two names
        for i in range(1, len(input_name)):
            name1 = input_name[:i]
            name2 = input_name[i:]
            # print(name1, name2)
            name1_result = copy.copy(self.firstnames.get(name1, None))
            name2_result = copy.copy(self.lastnames.get(name2, None))
            if name1_result and name2_result:
                interpretation = self.two_names(name1, name2, name1_result, name2_result)
                interpretation['type'] = 'first last'
                interpretations.append(interpretation)

            name1_result = copy.copy(self.lastnames.get(name1, None))
            name2_result = copy.copy(self.firstnames.get(name2, None))
            if name1_result and name2_result:
                interpretation = self.two_names(name1, name2, name1_result, name2_result)
                interpretation['type'] = 'last first'
                interpretations.append(interpretation)

        return interpretations

    def tokenize1(self, input_name: str, user_country: str = None, topn: int = 1) -> List[
        tuple[float, str, List[str], List[str], Dict[str, float]]]:
        """Return best country interpretation."""
        all_interpretations = self.score(input_name, user_country)

        return all_interpretations[:topn]

    def tokenize2(self, input_name: str, user_country: str = None, topn: int = 1) -> List[
        tuple[float, str, List[str], List[str], Dict[str, float]]]:
        """Return interpretation with the highest sum of country probs."""
        results = self.anal(input_name)

        interpretations = []
        for r in results:
            if user_country in r['prob']:
                r['prob'][user_country] = r['prob'][user_country] * self.country_bonus

            probs2 = sorted(r['prob'].items(), key=lambda x: x[1], reverse=True)
            if not probs2: continue
            best = probs2[0]
            interpretations.append(
                (sum(r['prob'].values()), best[0], r['tokenization'], r['type'], r['genders'].get(best[0], None)))

        return sorted(interpretations, reverse=True)[:topn]

    def score(self, input_name: str, user_country: str = None) -> List[
        tuple[float, str, List[str], List[str], Dict[str, float]]]:
        """Return best interpretation."""
        interpretations = self.anal(input_name)

        all_interpretations = []
        for r in interpretations:
            if user_country in r['prob']:
                r['prob'][user_country] = r['prob'][user_country] * self.country_bonus

            # probs2 = sorted(r['prob'].items(), key=lambda x: x[1], reverse=True)[0]
            # interpretations.append((probs2[1], probs2[0], [result['name'] for result in r['names']], [result['type'] for result in r['names']]))

            for country, prob in r['prob'].items():
                # print('x', prob)
                all_interpretations.append(
                    (prob, country, r['tokenization'], r['type'], r['genders'].get(country, None)))
        # print(sorted(interpretations, reverse=True))
        # for x in all_interpretations:
        #     print(x)
        return sorted(all_interpretations, reverse=True)

    def verbose(self, input_name):
        results = self.anal(input_name)

        for r in results:
            score = math.prod([sum(result['gender'].values()) for result in r['names']])
            print([result['name'] for result in r['names']], [result['type'] for result in r['names']])
            print(score, score ** (1 / len(r)), r['names'])

            for result in r['names']:
                best_probs = sorted(result['prob'].items(), key=lambda x: x[1], reverse=True)[:5]
                print(result['name'])
                print(best_probs)

            # wymnoz gendery i kraje
            countries = collections.defaultdict(lambda: 1)
            genders = collections.defaultdict(lambda: 1)
            probs = collections.defaultdict(lambda: 1)
            for result in r['names']:
                for country, count in result['country'].items():
                    countries[country] *= count
                for gender, count in result['gender'].items():
                    genders[gender] *= count
                for country, count in result['prob'].items():
                    probs[country] *= count
            # TODO srednia geometryczna
            country = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:1]
            print('Country', country)
            gender = sorted(genders.items(), key=lambda x: x[1], reverse=True)[:1]
            print('Gender', gender)
            probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:1]
            print('Prob', probs)
            probs2 = sorted(r['prob'].items(), key=lambda x: x[1], reverse=True)[:3]
            print('Prob2', probs2)
            print()


if __name__ == "__main__":
    pn = PersonNames(DictConfig({}))

    for name in ['the', 'kwrobel', 'krzysztofwrobel', 'wrobel', 'apohl', 'banana', 'john', 'james', 'david', 'thefirst',
                 'information']:
        # try:
        r1 = pn.tokenize1(name)
        r2 = pn.tokenize2(name)
        print(name, r1, r2)
        # print(pn.score(name))
        # pn.verbose(name)
        # except:
        #     print('NOT_NAME', name)
