def _load_data():
    from typing import Iterable, Tuple
    from .utils import get_data_lines

    def parse_line(line: str) -> Tuple[int, Tuple[str, str, int]]:
        fields = line.split(';')

        code = int(fields[0], base=16)
        name = fields[1]
        category = fields[2]
        combining = int(fields[3])

        return code, (name, category, combining)

    class UnicodeData:
        def __init__(self, lines: Iterable[str]):
            self.data = {e[0]: e[1] for e in map(parse_line, lines)}

        def name(self, code: int) -> str:
            return self.data[code][0]

        def category(self, code: int) -> str:
            return self.data[code][1]

        def combining(self, code: int) -> int:
            return self.data[code][2]

    with open('data/myunicode/UnicodeData.txt', 'r') as f:
        return UnicodeData(get_data_lines(f))


UNICODE_DATA = _load_data()
