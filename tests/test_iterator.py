from generator.xgenerator import by_one_iterator


def test_iterator1():
    lists = [['a1', 'a2', 'a3'], ['b1'], ['c1', 'c2', 'c3']]
    combined = by_one_iterator(lists)
    assert combined == ['a1', 'b1', 'c1', 'a2', 'c2', 'a3', 'c3']
