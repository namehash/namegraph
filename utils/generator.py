import hydra
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
import os
import nltk
import collections
import itertools

from timeit import default_timer as timer
from datetime import timedelta


from nltk.corpus import wordnet as wn


def read_domains(path):
    domains = set()
    with open(path) as domains_file:
        for line in domains_file:
            domains.add(line.strip()[:-4])
    return domains

def get_lemmas_for_word(word):
    synsets = wn.synsets(word)

    return get_lemmas(synsets)

def get_lemmas(synsets):
    lemmas = []
    for synset in synsets:
        lemmas.extend([str(lemma.name()) for lemma in synset.lemmas()])
    lemmas = [l for l in lemmas if '_' not in l]

    stats = collections.defaultdict(int)
    for l in lemmas:
        stats[l] += 1

    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

def find_words(name):
    result=[]

    for i in range(1,len(name)):
        prefix_synsets = wn.synsets(name[:i])
        suffix_synsets = wn.synsets(name[i:])

        if prefix_synsets and suffix_synsets:
            result.append([prefix_synsets,suffix_synsets])

    return result

def generate_names(name, count):
    synsets = find_words(name)
    result = []

    for prefix_synsets, suffix_synsets in synsets:
        prefix_lemmas = get_lemmas(prefix_synsets)
        suffix_lemmas = get_lemmas(suffix_synsets)

        for prefix_count, suffix_count in itertools.product(prefix_lemmas.items(),suffix_lemmas.items()):
            prefix, prefix_count = prefix_count
            suffix, suffix_count = suffix_count

            result.append([prefix + suffix, prefix_count + suffix_count])

    names = [x[0] for x in sorted(result, key=lambda x: x[1], reverse=True)]
    return names[:count]


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def generate(config : DictConfig) -> None:
    nltk.download("wordnet")
    nltk.download("omw-1.4")
    wn.synsets('dog') # init wordnet

    root = Path(os.path.abspath(__file__)).parents[1]
    domains = read_domains(root / config.generator.domains)
    start = timer()
    suggestions = generate_names(config.generator.query, config.generator.suggestions)
    end = timer()
    print(f"Generation time (s): {timedelta(seconds=end-start)}")

    print(suggestions)
    #suggestions = [s for s in suggestions if not s in domains]


if __name__ == "__main__":
    generate()
