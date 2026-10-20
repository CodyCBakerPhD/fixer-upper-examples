# TASK:
# Looking at the places this function is called, it is quite typical to call
# it multiple times with the same data and a varying mode. We'd like to add
# a new API that can be used in these cases to avoid repeating work unnecessarily,
# while keeping the existing one around (for now)

# (unstated?) When data is 2D, the non-'fit' modes should apply to the second element (the 'y's)

# Below is our solution to exercise 2, but we recommend you continue from _your_ solution!

import statistics
import warnings
from collections import Counter
from collections.abc import Callable, Mapping
from enum import StrEnum
from typing import Self, cast

Result = float | tuple[float, float]


def _mode(data: list[float]) -> tuple[float, int]:
    return Counter(data).most_common(1)[0]


def _range(data: list[float]) -> tuple[float, float]:
    return (min(data), max(data))


class Stat(StrEnum):
    """Every 1-d statistic this module computes.

    To add one, add a member: its name, the function that computes it, and
    optionally the name of the member that summarize() uses instead when
    is_sample is true.
    """

    compute: Callable[[list[float]], Result]
    sample: str | None

    def __new__(
        cls,
        value: str,
        compute: Callable[[list[float]], Result],
        sample: str | None = None,
    ) -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        member.compute = compute
        member.sample = sample
        return member

    MODE = "mode", _mode
    RANGE = "range", _range
    MEAN = "mean", statistics.mean
    MEDIAN = "median", statistics.median
    VARIANCE = "variance", statistics.pvariance, "sample_variance"
    SAMPLE_VARIANCE = "sample_variance", statistics.variance
    STDEV = "stdev", statistics.pstdev, "sample_stdev"
    SAMPLE_STDEV = "sample_stdev", statistics.stdev
    SUM = "sum", sum


STATS: Mapping[str, Callable[[list[float]], Result]] = {
    stat.value: stat.compute for stat in Stat
}
_SAMPLE_NAMES = {stat.value: stat.sample for stat in Stat if stat.sample is not None}
FIT = "fit"  # the one legacy statistic of points rather than of a series


def compute_1d_stat(data: list[float], stat: str) -> Result:
    return STATS[stat](data)


def map_legacy_stat_name(stat: str, is_sample: bool) -> str:
    if is_sample:
        return _SAMPLE_NAMES.get(stat, stat)
    return stat


def linear_fit(data: list[list[float]]) -> tuple[float, float]:
    x = [point[0] for point in data]
    y = [point[1] for point in data]

    x_mean = statistics.mean(x)
    y_mean = statistics.mean(y)
    x_xi_diff = [(item - x_mean) for item in x]
    x_xi_diff_sq = [item**2 for item in x_xi_diff]
    sum_sq = sum(x_xi_diff_sq)
    y_yi_diff = [(item - y_mean) for item in y]
    slope_numerator = sum(x_val * y_val for (x_val, y_val) in zip(x_xi_diff, y_yi_diff))

    slope = slope_numerator / sum_sq

    sum_x_sq = sum(item**2 for item in x)
    sum_xy = sum(x_val * y_val for (x_val, y_val) in zip(x, y))
    sum_y = sum(y)
    sum_x = sum(x)
    n = len(x)

    intercept = (sum_y * sum_x_sq - sum_x * sum_xy) / (n * sum_x_sq - (sum_x) ** 2)

    return (intercept, slope)


def summarize(
    data: list[float] | list[list[float]],
    stat: Stat | str | None = None,
    is_sample: bool = True,
    *,
    mode: Stat | str | None = None,
) -> Result:
    """Compute one statistic of data. `mode` is the deprecated old name of `stat`."""
    stat = _renamed_stat(stat, mode)
    if stat == FIT:
        return linear_fit(cast(list[list[float]], data))

    if data and isinstance(data[0], list):
        raise ValueError("2-d data supplied to 1-d statistic")
    name = map_legacy_stat_name(stat, is_sample)
    return compute_1d_stat(cast(list[float], data), name)


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
