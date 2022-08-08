import regex

VERSION_REGEX = regex.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
SPECIAL_CHAR_REGEX = regex.compile(r'[^a-zA-Z0-9.-]')


def check_generator_response(json):
    assert sorted(json.keys()) == sorted([
        'advertised',
        'secondary',
        'primary',
    ])

    assert type(json['advertised']) == list
    assert type(json['secondary']) == list
    assert type(json['primary']) == list

    for arr in json.values():
        assert all(type(item) == str for item in arr)


def generate_example_names(count, input_filename='data/primary.csv'):
    with open(input_filename, 'r') as f:
        num_lines = sum(1 for _ in f)
        f.seek(0)

        # ensure uniform sampling of lines
        # from the input file
        stride = max(1, num_lines // count)

        i = 0
        for line in f:
            # strip \n
            name = line[:-1]

            # skip simple names
            if SPECIAL_CHAR_REGEX.search(name) is None:
                continue

            if i % stride == 0:
                yield name

            i += 1
