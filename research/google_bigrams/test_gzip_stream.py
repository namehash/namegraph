import requests
import gzip
from io import BufferedReader, BytesIO
from time import perf_counter


def download_full(url: str):  # 50-70s
    decompressed_content = gzip.GzipFile(fileobj=BytesIO(requests.get(url, stream=True).content))
    str_content = decompressed_content.read().decode('utf-8')
    for i, line in enumerate(str_content.splitlines()):
        print(line)
        if i == 30:
            break


def download_stream_gzip(url: str):  # 30-40s
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with gzip.open(BytesIO(response.content), 'rt') as file:
            for i, line in enumerate(file):
                print(line)
                if i == 30:
                    break


def download_stream_gzip_custom_chunks(url: str):  # 30-40s

    def stream_chunks(response, chunk_size=8192):
        for chunk in response.iter_content(chunk_size=chunk_size):
            yield chunk

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        buffered_reader = BufferedReader(BytesIO(b''.join(stream_chunks(response))))
        with gzip.GzipFile(fileobj=buffered_reader, mode='rb') as f:
            for i, line in enumerate(f):
                text_line = line.decode('utf-8')
                print(text_line)
                if i == 30:
                    break

def download_stream_gzip_on_the_fly(url: str):  # ~0.2s
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        for i, line in enumerate(gzip.open(response.raw)):
            text_line = line.decode('utf-8')
            print(text_line)
            if i == 30:
                break


if __name__ == '__main__':
    t1 = perf_counter()
    download_stream_gzip_on_the_fly(url='http://storage.googleapis.com/books/ngrams/books/20200217/eng/2-00401-of-00589.gz')
    t2 = perf_counter()
    print(f'{t2 - t1} s')
