"""`modelling/experiment.py`: the scoring and interval arithmetic, on textbook inputs.

Only the general-purpose helpers are tested. The walk-forward and the screen are study
procedures, not mechanics.
"""

import math

import numpy as np
import pytest

from modelling.experiment import brier, holm, log_loss, wilson_ci


def test_brier() -> None:
    assert brier(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 0.0
    assert brier(np.array([0.5, 0.5]), np.array([0.0, 1.0])) == 0.25


def test_log_loss() -> None:
    assert log_loss(np.array([0.5]), np.array([1.0])) == pytest.approx(math.log(2))
    # A certain, wrong prediction is clipped to a large finite loss instead of infinity.
    assert math.isfinite(log_loss(np.array([1.0]), np.array([0.0])))


def test_wilson_ci_known_value() -> None:
    lo, hi = wilson_ci(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-4)
    assert hi == pytest.approx(0.7634, abs=1e-4)


@pytest.mark.parametrize(("successes", "n"), [(0, 10), (3, 10), (10, 10), (1, 1000)])
def test_wilson_ci_brackets_the_rate(successes: int, n: int) -> None:
    lo, hi = wilson_ci(successes, n)
    assert -1e-12 <= lo <= successes / n <= hi <= 1.0 + 1e-12


def test_wilson_ci_of_nothing() -> None:
    assert wilson_ci(0, 0) == (0.0, 0.0)


@pytest.mark.parametrize(
    ("name", "p_adjusted", "significant"),
    [
        ("a", 0.03, True),  # 3 x 0.01
        ("c", 0.06, False),  # 2 x 0.03
        # 1 x 0.04 would be 0.04, but an adjusted p may not drop below an earlier one.
        ("b", 0.06, False),
    ],
)
def test_holm_steps_down_and_stays_monotone(
    name: str, p_adjusted: float, significant: bool
) -> None:
    p, flag = holm({"a": 0.01, "b": 0.04, "c": 0.03})[name]
    assert p == pytest.approx(p_adjusted)
    assert flag is significant


def test_holm_caps_at_one() -> None:
    assert holm({"a": 0.6, "b": 0.7}) == {"a": (1.0, False), "b": (1.0, False)}
