# TASK:
# The following routine has grown unruly over time. We'd like to
# both make it more interpretable and add support for an additional
# mode, "stdev", which computes standard deviations

import warnings
from collections import Counter
from collections.abc import Callable
from enum import StrEnum
from typing import Self, cast

Result = float | tuple[float, float] | tuple[float | None, int]


def _mean(x: list[float]) -> float:
    return sum(x) / len(x)


def _median(x: list[float]) -> float:
    x = sorted(x)
    half = len(x) // 2
    if len(x) % 2 == 1:
        return x[half]
    return (x[half] + x[half - 1]) / 2


def _mode(x: list[float]) -> tuple[float | None, int]:
    if not x:
        return (None, 0)
    return Counter(x).most_common(1)[0]


def _range(x: list[float]) -> tuple[float, float]:
    return (min(x), max(x))


def _sum_of_squares(x: list[float]) -> float:
    mean = sum(x) / len(x)
    return sum((item - mean) ** 2 for item in x)


def _variance(x: list[float]) -> float:
    return _sum_of_squares(x) / len(x)


def _sample_variance(x: list[float]) -> float:
    return _sum_of_squares(x) / (len(x) - 1)


class Stat(StrEnum):
    """Every statistic of a series that summarize() computes.

    To add one, add a member: its name, the function that computes it, and
    optionally the function to use instead when is_sample is true.
    """

    compute: Callable[[list[float]], Result]
    sample_compute: Callable[[list[float]], Result] | None

    def __new__(
        cls,
        value: str,
        compute: Callable[[list[float]], Result],
        sample_compute: Callable[[list[float]], Result] | None = None,
    ) -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        member.compute = compute
        member.sample_compute = sample_compute
        return member

    SUM = "sum", sum
    MEAN = "mean", _mean
    MEDIAN = "median", _median
    MODE = "mode", _mode
    VARIANCE = "variance", _variance, _sample_variance
    RANGE = "range", _range


_BY_NAME = {stat.value: stat for stat in Stat}
FIT = "fit"  # the one statistic of points rather than of a series


def summarize(
    data: list[float] | list[list[float]],
    stat: Stat | str | None = None,
    is_sample: bool = True,
    *,
    mode: Stat | str | None = None,
) -> Result | None:
    """Compute one statistic of data. `mode` is the deprecated old name of `stat`."""
    stat = _renamed_stat(stat, mode)
    if stat == FIT:
        return _linear_fit(cast(list[list[float]], data))

    x = cast(list[float], data)
    sum(x)  # raises TypeError for non-numeric or 2-d data, as summarize always has
    chosen = _BY_NAME.get(stat)
    if chosen is None:
        return None  # unknown names have always returned None
    if is_sample and chosen.sample_compute is not None:
        return chosen.sample_compute(x)
    return chosen.compute(x)


def _renamed_stat(stat: Stat | str | None, mode: Stat | str | None) -> Stat | str:
    if mode is None:
        if stat is None:
            raise TypeError("summarize() missing required argument: 'stat'")
        return stat
    if stat is not None:
        raise TypeError("summarize() got both 'stat' and its old name 'mode'")
    warnings.warn(
        "summarize()'s 'mode' argument is deprecated; use 'stat' instead",
        DeprecationWarning,
        stacklevel=3,
    )
    return mode


def _linear_fit(points: list[list[float]]) -> tuple[float, float]:
    x = [point[0] for point in points]
    y = [point[1] for point in points]
    n = len(points)
    sum_x = sum(x)
    sum_y = sum(y)
    x_mean = sum_x / n
    y_mean = sum_y / n

    x_dev = [item - x_mean for item in x]
    y_dev = [item - y_mean for item in y]
    sum_sq = sum(d**2 for d in x_dev)
    # += rather than sum(): sum() of floats is compensated since Python 3.12
    slope_numerator: float = 0
    for dx, dy in zip(x_dev, y_dev):
        slope_numerator += dy * dx
    slope = slope_numerator / sum_sq

    sum_x_sq = sum(item**2 for item in x)
    sum_xy: float = 0
    for xi, yi in zip(x, y):
        sum_xy += xi * yi
    intercept = (sum_y * sum_x_sq - sum_x * sum_xy) / (n * sum_x_sq - sum_x**2)
    return (intercept, slope)
