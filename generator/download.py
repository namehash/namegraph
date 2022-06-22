import hydra
from omegaconf import DictConfig
import gensim.downloader as api
from generator.generation import WordnetSynonymsGenerator


def download_wordnet(config):
    WordnetSynonymsGenerator(config)


def download_convert_embeddings(model):
    model = api.load(model)
    model.save('data/embeddings.pkl')
    del model


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    download_wordnet(config)
    download_convert_embeddings(config.generation.word2vec_model)


if __name__ == "__main__":
    init()
