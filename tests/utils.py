from typing import List


def assert_applied_strategies_are_equal(real: List[List[str]], expected: List[List[str]]) -> None:
    assert len(real) == len(expected)

    for r in real:
        assert r in expected

    # if there are duplicates in real, then there might be an element in expected, which won't get matched
    for e in expected:
        assert e in real
