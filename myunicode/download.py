import urllib.request
import os


_PATH = 'data/myunicode'


def download():
    os.makedirs(_PATH, exist_ok=True)
    urllib.request.urlretrieve(
        'https://www.unicode.org/Public/UNIDATA/UnicodeData.txt',
        f'{_PATH}/UnicodeData.txt'
    )


if __name__ == "__main__":
    print(f'Downloading unicode files into {_PATH}\n...')
    download()
    print('Done')
