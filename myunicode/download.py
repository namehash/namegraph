import requests
import os
import regex


_PATH = 'data/myunicode'

# e.g. 11AB0..11ABF; Unified Canadian Aboriginal Syllabics Extended-A
_BLOCK_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)..(?<stop>[0-9a-fA-F]+)\s*;(?<name>.+)$')

# e.g. 0000..001F    ; Common # Cc  [32] <control-0000>..<control-001F>
# or   0020          ; Common # Zs       SPACE
_SCRIPT_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)(?:..(?<stop>[0-9a-fA-F]+))?\s*;(?<script>[^#]+)#.*$')

# e.g. 1FA74         ; Extended_Pictographic# E13.0  [1] (🩴)       thong sandal
# or   1FA75..1FA77  ; Extended_Pictographic# E0.0   [3] (🩵..🩷)    <reserved-1FA75>..<reserved-1FA77>
_EMOJI_REGEX = regex.compile(r'^(?<start>[0-9a-fA-F]+)(?:..(?<stop>[0-9a-fA-F]+))?\s*;.*$')


def download_data():
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


def download_blocks():
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


def download_scripts():
    r = requests.get('https://www.unicode.org/Public/UNIDATA/Scripts.txt')
    scripts = []
    for line in r.text.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if len(line) == 0 or line[0] == '#':
            continue

        m = _SCRIPT_REGEX.search(line)
        start = int(m.group('start'), base=16)
        stop = int(m.group('stop'), base=16) if m.group('stop') is not None else start
        script = m.group('script').strip()

        scripts.append((start, stop, script))

    scripts.sort(key=lambda x: x[0])

    # compress continuous script ranges
    compressed = []
    for s in scripts:
        # if current script range extends the previous one
        if len(compressed) > 0 and s[0] == compressed[-1][1] + 1 and s[2] == compressed[-1][2]:
            # extend last range
            compressed[-1] = (compressed[-1][0], s[1], compressed[-1][2])
        else:
            # add new range
            compressed.append(s)

    with open(f'{_PATH}/Scripts.txt', 'w') as f:
        for s in compressed:
            f.write(f'{s[0]:04X};{s[1]:04X};{s[2]}\n')


def download_emoji():
    r = requests.get('https://www.unicode.org/Public/UNIDATA/emoji/emoji-data.txt')
    emojis = set()
    for line in r.text.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if len(line) == 0 or line[0] == '#':
            continue

        m = _EMOJI_REGEX.search(line)
        start = int(m.group('start'), base=16)
        stop = int(m.group('stop'), base=16) if m.group('stop') is not None else start

        for e in range(start, stop + 1):
            emojis.add(e)

    ranges = []
    for e in sorted(emojis):
        # if there was a gap
        if len(ranges) == 0 or e > ranges[-1][1] + 1:
            # add new range
            ranges.append((e, e))
        else:
            # extend last range
            ranges[-1] = (ranges[-1][0], e)

    with open(f'{_PATH}/emoji-ranges.txt', 'w') as f:
        for start, stop in ranges:
            f.write(f'{start:04X};{stop:04X};\n')


def download():
    os.makedirs(_PATH, exist_ok=True)
    download_data()
    download_blocks()
    download_scripts()
    download_emoji()


if __name__ == "__main__":
    print(f'Downloading unicode files into {_PATH}\n...')
    download()
    print('Done')
