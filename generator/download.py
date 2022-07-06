import hydra
from omegaconf import DictConfig
import gensim.downloader as api

from generator.download_names import download_file
from generator.generation import WordnetSynonymsGenerator


def download_wordnet(config):
    WordnetSynonymsGenerator(config)


def download_convert_embeddings(model):
    model = api.load(model)
    model.save('data/embeddings.pkl')
    del model

def download_spacy(config):
    from spacy.cli.download import download
    download('en_core_web_sm')

def download_embeddings(url, path):
    download_file(url, path, override=False)
    vectors = '.vectors.npy'
    download_file(url + vectors, path + vectors, override=False)


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    download_wordnet(config)
    # download_convert_embeddings(config.generation.word2vec_model)
    download_embeddings(config.generation.word2vec_url, config.generation.word2vec_path)
    download_embeddings(config.generation.wikipedia2vec_url, config.generation.wikipedia2vec_path)
    download_spacy(config)


if __name__ == "__main__":
    init()
