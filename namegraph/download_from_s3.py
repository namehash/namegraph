import os
import sys
from pathlib import Path

import tarfile
import boto3
import botocore
import hydra

from omegaconf import DictConfig


class S3Downloader:
    def __init__(self):
        self.s3_client = None
        self.region_name = 'us-east-1'
        self.bucket = 'prod-name-generator-namegeneratori-inputss3bucket-c26jqo3twfxy'

    def get_client(self):
        if self.s3_client is None:
            self.s3_client = boto3.client(
                's3', region_name=self.region_name, config=botocore.config.Config(signature_version=botocore.UNSIGNED)
            )
        return self.s3_client

    def download_file(self, url, path, override=True):
        print('Downloading?', url, path, file=sys.stderr)
        if not Path(path).exists() or override:
            print('Downloading', url, path, file=sys.stderr)
            self.get_client().download_file(self.bucket, url, path)


def download_embeddings(s3_downloader, url, path):
    s3_downloader.download_file(url, path, override=False)
    vectors = '.vectors.npy'
    s3_downloader.download_file(url + vectors, path + vectors, override=False)

def download_embeddings_extract(s3_downloader, url, path, override=False):
    if not Path(path).exists() or override:
        s3_downloader.download_file(url, '/tmp/embeddings.tgz', override=False)
        file = tarfile.open('/tmp/embeddings.tgz')
        file.extractall(path)
        file.close()
        os.remove('/tmp/embeddings.tgz')

@hydra.main(version_base=None, config_path="../conf", config_name="prod_config_new")
def init(config: DictConfig):
    s3_downloader = S3Downloader()
    # download_embeddings(s3_downloader, config.generation.word2vec_url, config.generation.word2vec_path)
    # download_embeddings(s3_downloader, config.generation.wikipedia2vec_url, config.generation.wikipedia2vec_path)

    s3_downloader.download_file(config.person_names.firstnames_url, config.person_names.firstnames_path, override=True)
    s3_downloader.download_file(config.person_names.lastnames_url, config.person_names.lastnames_path, override=True)
    s3_downloader.download_file(config.person_names.other_url, config.person_names.other_path, override=True)
    s3_downloader.download_file(config.person_names.country_stats_url, config.person_names.country_stats_path,
                                override=True)

    download_embeddings_extract(s3_downloader, config.generation.word2vec_rocks_url, config.generation.word2vec_rocks_path)
    download_embeddings_extract(s3_downloader, config.generation.wikipedia2vec_rocks_url, config.generation.wikipedia2vec_rocks_path)



if __name__ == "__main__":
    init()
