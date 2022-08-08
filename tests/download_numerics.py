import requests


_FILEPATH = 'tests/data/unicode_numerics.txt'


def download_data():
    r = requests.get('https://www.unicode.org/Public/UNIDATA/UnicodeData.txt')
    
    with open(_FILEPATH, 'w') as f:
        for line in r.text.splitlines():
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue

            fields = line.split(';')
            code = fields[0].strip()
            category = fields[2].strip()

            is_numeric = category[0] == 'N'
            
            if is_numeric:
                f.write(f'{code}\n')


if __name__ == '__main__':
    print('Downloading data...')
    download_data()
    print('Done')
