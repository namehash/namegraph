import hydra
from omegaconf import DictConfig
import gensim.downloader as api
import gensim
from generator.generation import W2VGenerator, WordnetSynonymsGenerator


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config")
def init(config: DictConfig):
    WordnetSynonymsGenerator(config)
    W2VGenerator(config)

    # convert embeddings to binary
    model = api.load(config.generation.word2vec_model)
    model.save('data/embeddings.pkl')
    del model

    # TODO download files from S3


if __name__ == "__main__":
    init()
