import regex

VERSION_REGEX = regex.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
SPECIAL_CHAR_REGEX = regex.compile(r'[^a-zA-Z0-9.-]')


def check_inspector_response(name, resp):
    """
    Checks that the response from the inspector is valid.
    Verifies only field names and types without exact values.
    Nullable fields:
    - word_length
    - all_class
    - all_script
    - tokenizations
    - probability
    - all_unicodeblock
    - ens_nameprep
    - idna_encode
    - score
    - chars.script
    - chars.name
    - chars.unicodeblock
    """
    assert sorted(resp.keys()) == sorted([
        'name',
        'length',
        'word_length',
        'all_class',
        'all_script',
        'any_scripts',
        'chars',
        'tokenizations',
        'probability',
        'any_classes',
        'all_unicodeblock',
        'ens_is_valid_name',
        'ens_nameprep',
        'idna_encode',
        'version',
        'score',
    ])

    assert resp['name'] == name
    assert resp['length'] == len(name)
    assert resp['word_length'] is None or 0 <= resp['word_length']
    assert resp['all_class'] is None or type(resp['all_class']) == str
    assert resp['all_script'] is None or type(resp['all_script']) == str
    assert type(resp['any_scripts']) == list
    assert type(resp['chars']) == list
    assert resp['tokenizations'] is None or type(resp['tokenizations']) == list
    assert resp['probability'] is None or 0 <= resp['probability'] <= 1
    # all_unicodeblock can be null
    assert resp['all_unicodeblock'] is None or type(resp['all_unicodeblock']) == str
    assert type(resp['ens_is_valid_name']) == bool
    assert resp['ens_nameprep'] is None or type(resp['ens_nameprep']) == str
    assert resp['idna_encode'] is None or type(resp['idna_encode']) == str
    assert VERSION_REGEX.match(resp['version'])
    assert resp['score'] is None or 0 <= resp['score'] <= 1

    # check returned characters
    # the order of the characters must match the input name
    for char, name_char in zip(resp['chars'], name):
        assert sorted(char.keys()) == sorted([
            'char',
            'script',
            'name',
            'codepoint',
            'link',
            'char_class',
            'unicodedata_category',
            'unicodeblock',
            'confusables',
        ])

        assert char['char'] == name_char
        assert char['script'] is None or type(char['script']) == str
        assert char['name'] is None or type(char['name']) == str
        # extract codepoint to create link
        assert char['codepoint'].startswith('0x')
        assert char['link'] == f'https://unicode.link/codepoint/{char["codepoint"][2:]}'
        assert type(char['char_class']) == str
        assert type(char['unicodedata_category']) == str
        assert char['unicodeblock'] is None or type(char['unicodeblock']) == str
        for conf_list in char['confusables']:
            for conf in conf_list:
                assert sorted(conf.keys()) == sorted([
                    'char',
                    'script',
                    'name',
                    'codepoint',
                    'link',
                    'char_class',
                ])
                # extract codepoint to create link
                assert char['codepoint'].startswith('0x')
                assert char['link'] == f'https://unicode.link/codepoint/{char["codepoint"][2:]}'

    # check returned tokenizations
    if resp['tokenizations'] is not None:
        for tokenization in resp['tokenizations']:
            assert sorted(tokenization.keys()) == sorted([
                'tokens',
                'probability',
                'entities',
            ])
            assert 0 <= tokenization['probability'] <= 1
            # TODO check entities
            for token in tokenization['tokens']:
                # token can be empty
                if list(token.keys()) == ['token']:
                    assert token['token'] == ''
                else:
                    assert sorted(token.keys()) == sorted([
                        'token',
                        'length',
                        'probability',
                        'pos',
                        'lemma',
                    ])
                    assert type(token['token']) == str
                    assert 0 <= token['length']
                    assert 0 <= token['probability'] <= 1
                    assert type(token['pos']) == str
                    assert type(token['lemma']) == str


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
