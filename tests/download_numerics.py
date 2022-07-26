import requests

from tests.test_inspector import INSPECTOR_NUMERICS_FAILING


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
            numeric_value = fields[8].strip()

            is_numeric = len(numeric_value) > 0
            
            if is_numeric:
                if code in INSPECTOR_NUMERICS_FAILING:
                    f.write(f'# {code}\n')
                else:
                    f.write(f'{code}\n')


if __name__ == '__main__':
    print('Downloading data...')
    download_data()
    print('Done')
