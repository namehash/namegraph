from namegraph.generation.combination_limiter import CombinationLimiter, prod


def test_limiter():
    limiter = CombinationLimiter(10000)
    result = limiter.compute_limits([1000, 1000, 1000, 1000])
    assert result == [10, 10, 10, 10]


def test_limiter2():
    limiter = CombinationLimiter(10000)
    result = limiter.compute_limits([1, 1, 1000000, 1])
    assert result == [1, 1, 10000, 1]


def test_limiter3():
    limiter = CombinationLimiter(10000)
    result = limiter.compute_limits([1, 1, 100, 10, 10, 10])
    assert result == [1, 1, 10, 10, 10, 10]


def test_limiter4():
    limiter = CombinationLimiter(10000)
    result = limiter.compute_limits([1, 2, 4, 8, 16, 32, 64])
    assert result == [1, 2, 4, 5, 6, 6, 6]  # prod(result)==8640
    assert prod(result) <= 10000
