# TASK:
# Looking at the places this function is called, it is quite typical to call
# it multiple times with the same data and a varying mode. We'd like to add
# a new API that can be used in these cases to avoid repeating work unnecessarily,
# while keeping the existing one around (for now)

# (unstated?) When data is 2D, the non-'fit' modes should apply to the second element (the 'y's)

# Solution 2 ("soln2"): a more advanced, nearly production-ready answer than
# ex3-soln.py. get_stats() is the new API: it computes several statistics of
# the same data, doing the work they share (sums, means, squared deviations)
# only once. summarize() stays for existing callers. Both apply every
# statistic but "fit" to the y values of (x, y) points. Like 02/ex2.py's
# soln2, it also settles everything the 2026-10-20 code quality review raised:
# - every statistic is defined once, in the Stat enum;
# - data is checked up front, so bad or too-short input raises a clear error
#   instead of returning a wrong answer or failing deep inside a formula;
# - the linear fit is numerically stable, and tuple results have named fields;
# - the argument is called stat; its old name, mode, still works but is
#   deprecated.

import math
import warnings
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from typing import NamedTuple, Self

__all__ = ["LinearFit", "MostCommon", "Range", "Stat", "get_stats", "summarize"]


class Range(NamedTuple):
    low: float
    high: float


class MostCommon(NamedTuple):
    value: float
    frequency: int


class LinearFit(NamedTuple):
    intercept: float
    slope: float


Result = float | Range | MostCommon | LinearFit


class Series:
    """Numbers checked once; the values their statistics share are computed once."""

    def __init__(self, values: Iterable[object], name: str = "data") -> None:
        checked: list[float] = []
        for i, value in enumerate(values):
            if not isinstance(value, (int, float)):
                raise TypeError(f"{name}[{i}] is {value!r}; expected a number")
            checked.append(value)
        self.values = tuple(checked)
        self.n = len(self.values)
        self.total = sum(self.values)

    @cached_property
    def mean(self) -> float:
        return self.total / self.n

    @cached_property
    def sum_of_squares(self) -> float:
        """Sum of the squared deviations from the mean."""
        mean = self.mean
        return sum((value - mean) ** 2 for value in self.values)


def _sum(series: Series) -> float:
    return series.total


def _mean(series: Series) -> float:
    return series.mean


def _median(series: Series) -> float:
    ordered = sorted(series.values)
    half = series.n // 2
    if series.n % 2 == 1:
        return ordered[half]
    return (ordered[half] + ordered[half - 1]) / 2


def _most_common(series: Series) -> MostCommon:
    return MostCommon(*Counter(series.values).most_common(1)[0])


def _range(series: Series) -> Range:
    return Range(min(series.values), max(series.values))


def _variance(series: Series) -> float:
    return series.sum_of_squares / series.n


def _sample_variance(series: Series) -> float:
    return series.sum_of_squares / (series.n - 1)


def _stdev(series: Series) -> float:
    return math.sqrt(_variance(series))


def _sample_stdev(series: Series) -> float:
    return math.sqrt(_sample_variance(series))


def _linear_fit(x: Series, y: Series) -> LinearFit:
    x_mean, y_mean = x.mean, y.mean
    # += rather than sum(): sum() of floats is compensated since Python 3.12
    slope_numerator: float = 0
    for xi, yi in zip(x.values, y.values):
        slope_numerator += (yi - y_mean) * (xi - x_mean)
    slope = slope_numerator / x.sum_of_squares
    # from the means, not from raw sums, which lose precision far from x = 0
    return LinearFit(intercept=y_mean - slope * x_mean, slope=slope)


def _looks_like_points(data: Sequence[object]) -> bool:
    return bool(data) and isinstance(data[0], Sequence) and not isinstance(data[0], str)


def _split_points(data: Sequence[object]) -> tuple[Series, Series]:
    xs: list[object] = []
    ys: list[object] = []
    for i, point in enumerate(data):
        if isinstance(point, str) or not isinstance(point, Sequence) or len(point) != 2:
            raise TypeError(f"data[{i}] is {point!r}; expected an (x, y) pair")
        xs.append(point[0])
        ys.append(point[1])
    return Series(xs, "x"), Series(ys, "y")


class Sample:
    """Data checked once: a series of numbers, or (x, y) points.

    Statistics of a series describe the series itself or, for points, the y
    values, as the task asks.
    """

    def __init__(self, data: Iterable[object]) -> None:
        items = list(data)
        self.x: Series | None
        self.y: Series
        if _looks_like_points(items):
            self.x, self.y = _split_points(items)
        else:
            self.x, self.y = None, Series(items)


@dataclass(frozen=True)
class _OfSeries:
    """A statistic of a series of numbers.

    sample_compute, if given, is used when is_sample is true; such sample
    estimates divide by n - 1, so they need one value more than min_size.
    """

    compute: Callable[[Series], Result]
    min_size: int = 1
    sample_compute: Callable[[Series], Result] | None = None

    def __call__(self, stat: str, sample: Sample, is_sample: bool) -> Result:
        series = sample.y
        compute, min_size = self.compute, self.min_size
        if is_sample and self.sample_compute is not None:
            compute, min_size = self.sample_compute, min_size + 1
        if series.n < min_size:
            raise ValueError(
                f"{stat!r} needs at least {min_size} values; got {series.n}"
            )
        return compute(series)


@dataclass(frozen=True)
class _OfPoints:
    """A statistic of (x, y) points."""

    compute: Callable[[Series, Series], Result]

    def __call__(self, stat: str, sample: Sample, is_sample: bool) -> Result:
        x, y = sample.x, sample.y
        if x is None and y.n:
            raise TypeError(f"{stat!r} takes (x, y) points, not a series of numbers")
        if x is None or len(set(x.values)) < 2:
            raise ValueError(
                f"{stat!r} needs at least two points with different x values"
            )
        return self.compute(x, y)


class Stat(StrEnum):
    """Every statistic summarize() and get_stats() compute, each defined once.

    To add a statistic, add a member: its name, and how to compute it from a
    series of numbers (_OfSeries) or from (x, y) points (_OfPoints).
    """

    statistic: _OfSeries | _OfPoints

    def __new__(cls, value: str, statistic: _OfSeries | _OfPoints) -> Self:
        member = str.__new__(cls, value)
        member._value_ = value
        member.statistic = statistic
        return member

    @classmethod
    def parse(cls, name: object) -> Self:
        for stat in cls:
            if stat == name:
                return stat
        choices = ", ".join(cls)
        raise ValueError(f"unknown statistic {name!r}; expected one of: {choices}")

    SUM = "sum", _OfSeries(_sum, min_size=0)
    MEAN = "mean", _OfSeries(_mean)
    MEDIAN = "median", _OfSeries(_median)
    MODE = "mode", _OfSeries(_most_common)
    RANGE = "range", _OfSeries(_range)
    VARIANCE = "variance", _OfSeries(_variance, sample_compute=_sample_variance)
    STDEV = "stdev", _OfSeries(_stdev, sample_compute=_sample_stdev)
    FIT = "fit", _OfPoints(_linear_fit)


def get_stats(
    data: Iterable[float] | Iterable[Sequence[float]],
    stats: Iterable[Stat | str],
    is_sample: bool = True,
) -> dict[Stat, Result]:
    """Compute several statistics of the same data, doing shared work once.

    The data is checked once, and values the statistics share, such as the
    mean, are computed once, so asking for "mean", "variance" and "stdev"
    together costs little more than asking for one. Arguments and errors are
    as for summarize(); every name is checked before anything is computed.
    """
    chosen = [Stat.parse(name) for name in stats]
    sample = Sample(data)
    return {stat: stat.statistic(stat.value, sample, is_sample) for stat in chosen}


def summarize(
    data: Iterable[float] | Iterable[Sequence[float]],
    stat: Stat | str | None = None,
    is_sample: bool = True,
    *,
    mode: Stat | str | None = None,
) -> Result:
    """Compute one statistic of data.

    data is a series of numbers, or (x, y) points; for points, every statistic
    but "fit" describes the y values. is_sample picks the sample form
    (dividing by n - 1) of "variance" and "stdev" over the population form;
    the other statistics ignore it. Data of the wrong type raises TypeError;
    data too short for the statistic, or an unknown statistic, raises
    ValueError. `mode` is the deprecated old name of `stat`.
    """
    chosen = Stat.parse(_renamed_stat(stat, mode))
    return chosen.statistic(chosen.value, Sample(data), is_sample)


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
