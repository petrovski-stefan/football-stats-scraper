"""Test data shared by the `domain/` tests."""

from itertools import product

import pytest


@pytest.fixture
def score_grid() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Every reachable HT -> FT pair with up to 4 goals per side.

    A side never has fewer goals at full time than at half time.
    """
    return [
        ((ht_home, ht_away), (ft_home, ft_away))
        for ht_home, ht_away, ft_home, ft_away in product(range(5), repeat=4)
        if ft_home >= ht_home and ft_away >= ht_away
    ]
