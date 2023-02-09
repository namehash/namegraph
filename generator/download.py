import hydra
import nltk

from omegaconf import DictConfig


def download_wordnet(config):
    nltk.download("wordnet")
    nltk.download("omw-1.4")


def download_embeddings(s3_downloader, url, path):
    s3_downloader.download_file(url, path, override=False)
    vectors = '.vectors.npy'
    s3_downloader.download_file(url + vectors, path + vectors, override=False)


@hydra.main(version_base=None, config_path="../conf", config_name="prod_config_new")
def init(config: DictConfig):
    download_wordnet(config)


if __name__ == "__main__":
    init()
