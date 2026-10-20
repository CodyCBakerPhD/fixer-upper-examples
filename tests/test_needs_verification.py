"""The "Needs verification" items of the 2026-10-20 code quality review, as tests.

See docs/code-reviews/2026-10-20-code-quality-review.md. NV-1 is fixed and is
tested as such. NV-2 has an unambiguous right answer, so it is a strict xfail
that fails once the intercept is fixed. NV-3 to NV-5 wait on a maintainer's
decision, so these tests pin today's behavior: changing it should be deliberate.
"""

import importlib.util
from pathlib import Path
from statistics import StatisticsError
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ex2 = _load("ex2", "02/ex2.py")
ex3 = _load("ex3", "03/ex3.py")
both = pytest.mark.parametrize("module", [ex2, ex3], ids=["ex2", "ex3"])

POINTS = [[1.0, 2.0], [2.0, 4.1], [3.0, 5.9], [4.0, 8.2]]
ONE_D_STATS = ["sum", "mean", "median", "mode", "variance", "range"]


def _line(offset: float) -> list[list[float]]:
    """Ten points on y = 3 + 2 * (x - offset)."""
    return [[offset + i, 3.0 + 2.0 * i] for i in range(10)]


# NV-1: fit used to raise UnboundLocalError in 02/ex2.py (fixed in e88941e)


@both
def test_nv1_fit_returns_intercept_and_slope(module):
    intercept, slope = module.summarize(POINTS, "fit")
    assert intercept == pytest.approx(-0.05)
    assert slope == pytest.approx(2.04)


# NV-2: the closed-form intercept loses precision when x is far from 0


@both
@pytest.mark.parametrize("offset", [0.0, 1e4, 1e6])
def test_nv2_fit_is_exact_near_zero(module, offset):
    intercept, slope = module.summarize(_line(offset), "fit")
    assert intercept == pytest.approx(3.0 - 2.0 * offset)
    assert slope == pytest.approx(2.0)


@both
def test_nv2_slope_is_exact_far_from_zero(module):
    _, slope = module.summarize(_line(1e8), "fit")
    assert slope == pytest.approx(2.0)


@both
@pytest.mark.xfail(
    strict=True, reason="NV-2: intercept is 7.4% off at x ~ 1e8; decision pending"
)
def test_nv2_intercept_is_exact_far_from_zero(module):
    intercept, _ = module.summarize(_line(1e8), "fit")
    assert intercept == pytest.approx(3.0 - 2.0 * 1e8)


# NV-3: malformed input is rejected by accident, or not at all


@pytest.mark.parametrize("stat", ONE_D_STATS)
@pytest.mark.parametrize("data", [["a", "b"], POINTS], ids=["strings", "points"])
def test_nv3_ex2_rejects_bad_data_only_because_it_sums_it(stat, data):
    with pytest.raises(TypeError, match="unsupported operand"):
        ex2.summarize(data, stat)


@pytest.mark.parametrize("stat", ["stdev", "bogus"])
def test_nv3_ex2_returns_none_for_unknown_stats(stat):
    # "stdev" is the statistic exercise 2 asks participants to add
    assert ex2.summarize([1.0, 2.0], stat) is None


@pytest.mark.parametrize("stat", ONE_D_STATS)
def test_nv3_ex3_rejects_list_points(stat):
    with pytest.raises(ValueError, match="2-d data supplied to 1-d statistic"):
        ex3.summarize(POINTS, stat)


def test_nv3_ex3_lets_tuple_points_through():
    points = [(1.0, 2.0), (2.0, 4.0)]
    assert ex3.summarize(points, "range") == ((1.0, 2.0), (2.0, 4.0))
    assert ex3.summarize(points, "mode") == ((1.0, 2.0), 1)
    with pytest.raises(TypeError):
        ex3.summarize(points, "mean")


def test_nv3_ex3_raises_key_error_for_unknown_stats():
    with pytest.raises(KeyError):
        ex3.summarize([1.0, 2.0], "bogus")


# NV-4: empty and one-element inputs fail differently in each mode.
# 02/ex2.py's empty "range" raised IndexError before b3c403c switched to min()/max().

TOO_SHORT = {
    (ex2, "empty"): {
        "sum": 0,
        "mean": ZeroDivisionError,
        "median": IndexError,
        "mode": (None, 0),
        "variance": ZeroDivisionError,
        "range": ValueError,
    },
    (ex3, "empty"): {
        "sum": 0,
        "mean": StatisticsError,
        "median": StatisticsError,
        "mode": IndexError,
        "variance": StatisticsError,
        "range": ValueError,
    },
    (ex2, "one"): {
        "sum": 7.0,
        "mean": 7.0,
        "median": 7.0,
        "mode": (7.0, 1),
        "variance": ZeroDivisionError,
        "range": (7.0, 7.0),
    },
    (ex3, "one"): {
        "sum": 7.0,
        "mean": 7.0,
        "median": 7.0,
        "mode": (7.0, 1),
        "variance": StatisticsError,
        "range": (7.0, 7.0),
    },
}


@pytest.mark.parametrize(
    ("module", "size", "stat", "expected"),
    [
        pytest.param(
            module, size, stat, expected, id=f"{module.__name__}-{size}-{stat}"
        )
        for (module, size), outcomes in TOO_SHORT.items()
        for stat, expected in outcomes.items()
    ],
)
def test_nv4_too_short_input(module, size, stat, expected):
    data = [] if size == "empty" else [7.0]
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            module.summarize(data, stat)
    else:
        assert module.summarize(data, stat) == expected


@both
def test_nv4_fit_of_one_point_divides_by_zero(module):
    with pytest.raises(ZeroDivisionError):
        module.summarize([[5.0, 1.0]], "fit")


# NV-5: the return shape depends on the statistic, and is_sample only sometimes matters


@both
def test_nv5_return_shape_depends_on_the_stat(module):
    data = [1.0, 2.0, 2.0, 5.0]
    assert isinstance(module.summarize(data, "mean"), float)
    assert module.summarize(data, "range") == (1.0, 5.0)  # (low, high)
    assert module.summarize(data, "mode") == (2.0, 2)  # (value, count)
    assert len(module.summarize(POINTS, "fit")) == 2  # (intercept, slope)


@both
@pytest.mark.parametrize("stat", ["sum", "mean", "median", "mode", "range"])
def test_nv5_is_sample_is_ignored_except_for_variance(module, stat):
    data = [1.0, 2.0, 2.0, 5.0]
    assert module.summarize(data, stat, True) == module.summarize(data, stat, False)


@both
def test_nv5_is_sample_changes_variance(module):
    data = [1.0, 2.0, 2.0, 5.0]
    assert module.summarize(data, "variance", True) == pytest.approx(3.0)
    assert module.summarize(data, "variance", False) == pytest.approx(2.25)
