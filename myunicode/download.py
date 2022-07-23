import requests
import os
import regex


_PATH = 'data/myunicode'

# e.g. 11AB0..11ABF; Unified Canadian Aboriginal Syllabics Extended-A
_BLOCK_REGEX = regex.compile(r'(?<start>[0-9a-fA-F]*)..(?<stop>[0-9a-fA-F]*);(?<name>.*)')


def download():
    os.makedirs(_PATH, exist_ok=True)

    r = requests.get('https://www.unicode.org/Public/UNIDATA/UnicodeData.txt')
    with open(f'{_PATH}/UnicodeData.txt', 'w') as f:
        for line in r.text.splitlines():
            line = line.strip()

            if len(line) == 0:
                continue

            fields = line.split(';')
            code = fields[0]
            name = fields[1]
            category = fields[2]
            combining = fields[3]
            
            f.write(f'{code};{name};{category};{combining}\n')

    r = requests.get('https://www.unicode.org/Public/UNIDATA/Blocks.txt')
    with open(f'{_PATH}/Blocks.txt', 'w') as f:
        for line in r.text.splitlines():
            line = line.strip()
            
            # Skip comments and empty lines
            if len(line) == 0 or line[0] == '#':
                continue

            m = _BLOCK_REGEX.search(line)
            start = m.group('start')
            stop = m.group('stop')
            name = m.group('name').strip()

            f.write(f'{start};{stop};{name}\n')


if __name__ == "__main__":
    print(f'Downloading unicode files into {_PATH}\n...')
    download()
    print('Done')
