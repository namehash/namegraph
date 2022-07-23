import requests
import os


_PATH = 'data/myunicode'


def download():
    os.makedirs(_PATH, exist_ok=True)
    r = requests.get('https://www.unicode.org/Public/UNIDATA/UnicodeData.txt')
    with open(f'{_PATH}/UnicodeData.txt', 'w') as f:
        for line in r.text.splitlines():
            fields = line.split(';')
            code = fields[0]
            name = fields[1]
            category = fields[2]
            combining = fields[3]
            f.write(f'{code};{name};{category};{combining}\n')


if __name__ == "__main__":
    print(f'Downloading unicode files into {_PATH}\n...')
    download()
    print('Done')
