"""The "Needs verification" items of the 2026-10-20 code quality review, as resolved.

See docs/code-reviews/2026-10-20-code-quality-review.md. Each test states the
behavior the soln2 code in 02/ex2.py and 03/ex3.py settled on for one item.
"""

import pytest
from exercises import both, ex2, ex3

POINTS = [[1.0, 2.0], [2.0, 4.1], [3.0, 5.9], [4.0, 8.2]]
TUPLE_POINTS = [(1.0, 2.0), (2.0, 4.0), (4.0, 4.0)]
SERIES_STATS = ["sum", "mean", "median", "mode", "range", "variance", "stdev"]


def _line(offset: float) -> list[list[float]]:
    """Ten points on y = 3 + 2 * (x - offset)."""
    return [[offset + i, 3.0 + 2.0 * i] for i in range(10)]


# NV-1: fit used to raise UnboundLocalError in 02/ex2.py


@both
def test_nv1_fit_returns_intercept_and_slope(module):
    assert module.summarize(POINTS, "fit") == pytest.approx((-0.05, 2.04))


# NV-2: the intercept used to lose precision when x is far from 0


@both
@pytest.mark.parametrize("offset", [0.0, 1e4, 1e6, 1e8])
def test_nv2_fit_is_exact_at_any_offset(module, offset):
    intercept, slope = module.summarize(_line(offset), "fit")
    assert intercept == pytest.approx(3.0 - 2.0 * offset)
    assert slope == pytest.approx(2.0)


# NV-3: malformed input is rejected explicitly, never answered wrongly


@both
@pytest.mark.parametrize("stat", ["bogus", "STDEV", ""])
def test_nv3_unknown_stats_raise_value_error(module, stat):
    with pytest.raises(ValueError, match="unknown statistic .*expected one of"):
        module.summarize([1.0, 2.0], stat)


@both
@pytest.mark.parametrize("stat", SERIES_STATS)
@pytest.mark.parametrize("data", [["a", "b"], [1.0, "a"], [1.0, None]])
def test_nv3_non_numbers_raise_type_error(module, stat, data):
    with pytest.raises(TypeError, match="expected a number"):
        module.summarize(data, stat)


@pytest.mark.parametrize("stat", SERIES_STATS)
@pytest.mark.parametrize("points", [POINTS, TUPLE_POINTS], ids=["lists", "tuples"])
def test_nv3_ex2_rejects_points_for_series_stats(stat, points):
    with pytest.raises(TypeError, match=r"not \(x, y\) points"):
        ex2.summarize(points, stat)


@pytest.mark.parametrize("stat", SERIES_STATS)
@pytest.mark.parametrize("points", [POINTS, TUPLE_POINTS], ids=["lists", "tuples"])
def test_nv3_ex3_describes_the_y_values_of_points(stat, points):
    ys = [y for _, y in points]
    assert ex3.summarize(points, stat) == ex3.summarize(ys, stat)


@both
@pytest.mark.parametrize(
    "data",
    [[1.0, 2.0], ["ab", "cd"], [[1.0, 2.0, 3.0]], [[1.0, 2.0], 3.0]],
    ids=["series", "strings", "triple", "mixed"],
)
def test_nv3_fit_rejects_data_that_is_not_points(module, data):
    with pytest.raises(TypeError):
        module.summarize(data, "fit")


# NV-4: too-short input raises ValueError, the same way for every statistic


@both
@pytest.mark.parametrize(
    ("stat", "is_sample", "too_short"),
    [
        ("mean", True, []),
        ("median", True, []),
        ("mode", True, []),
        ("range", True, []),
        ("variance", False, []),
        ("variance", True, [7.0]),
        ("stdev", False, []),
        ("stdev", True, [7.0]),
    ],
)
def test_nv4_too_short_input_raises_value_error(module, stat, is_sample, too_short):
    with pytest.raises(ValueError, match="needs at least"):
        module.summarize(too_short, stat, is_sample)
    module.summarize([*too_short, 8.0], stat, is_sample)  # one more value is enough


@both
def test_nv4_sum_of_nothing_is_zero(module):
    assert module.summarize([], "sum") == 0


@both
@pytest.mark.parametrize(
    "points",
    [[], [[5.0, 1.0]], [[5.0, 1.0], [5.0, 2.0]]],
    ids=["none", "one", "same-x"],
)
def test_nv4_fit_needs_two_different_x_values(module, points):
    with pytest.raises(ValueError, match="different x values"):
        module.summarize(points, "fit")


# NV-5: results have named fields, and is_sample only affects variance and stdev


@both
def test_nv5_results_have_named_fields(module):
    data = [1.0, 2.0, 2.0, 5.0]
    assert module.summarize(data, "range") == module.Range(low=1.0, high=5.0)
    assert module.summarize(data, "mode") == module.MostCommon(value=2.0, frequency=2)
    fit = module.summarize(POINTS, "fit")
    assert isinstance(fit, module.LinearFit)
    assert (fit.intercept, fit.slope) == pytest.approx((-0.05, 2.04))
    assert isinstance(module.summarize(data, "mean"), float)


@both
@pytest.mark.parametrize("stat", ["sum", "mean", "median", "mode", "range"])
def test_nv5_is_sample_only_matters_for_variance_and_stdev(module, stat):
    data = [1.0, 2.0, 2.0, 5.0]
    assert module.summarize(data, stat, True) == module.summarize(data, stat, False)


@both
def test_nv5_is_sample_picks_the_sample_or_population_form(module):
    data = [1.0, 2.0, 2.0, 5.0]
    assert module.summarize(data, "variance", True) == pytest.approx(3.0)
    assert module.summarize(data, "variance", False) == pytest.approx(2.25)
    assert module.summarize(data, "stdev", True) == pytest.approx(3.0**0.5)
    assert module.summarize(data, "stdev", False) == pytest.approx(1.5)
