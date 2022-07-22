def _load_data():
    class UnicodeData:
        def __init__(self):
            self.name = {}
            self.category = {}
            self.combining = {}

        def push(self, line: str):
            fields = line.split(';')

            code = int(fields[0], base=16)
            name = fields[1]
            category = fields[2]
            combining = int(fields[3])

            self.name[code] = name
            self.category[code] = category
            self.combining[code] = combining

    data = UnicodeData()

    with open('data/myunicode/UnicodeData.txt', 'r') as f:
        for line in f:
            data.push(line)

    return data


UNICODE_DATA = _load_data()
