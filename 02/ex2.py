# TASK:
# The following routine has grown unruly over time. We'd like to
# both make it more interpretable and add support for an additional
# mode, "stdev", which computes standard deviations

from collections import Counter
from typing import Literal, cast

Mode = Literal['sum', 'mean', 'median', 'mode', 'variance', 'range', 'fit']


def summarize(
    data: list[float] | list[list[float]],
    mode: Mode,
    is_sample: bool = True,
) -> float | tuple[float, float] | tuple[float | None, int] | None:
    if mode == 'fit':
        return _linear_fit(cast(list[list[float]], data))

    x = cast(list[float], data)
    n = len(x)
    total = sum(x)  # every 1-d mode starts here, so non-numeric data raises TypeError

    if mode == 'sum':
        return total
    if mode == 'mean':
        return total / n
    if mode == 'median':
        return _median(x)
    if mode == 'mode':
        return _mode(x)
    if mode == 'variance':
        mean = total / n
        sum_sq = sum((item - mean) ** 2 for item in x)
        if is_sample:
            return sum_sq / (n - 1)
        return sum_sq / n
    if mode == 'range':
        return (min(x), max(x))
    return None


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
    sum_sq = sum(d ** 2 for d in x_dev)
    # += rather than sum(): sum() of floats is compensated since Python 3.12
    slope_numerator: float = 0
    for dx, dy in zip(x_dev, y_dev):
        slope_numerator += dy * dx
    slope = slope_numerator / sum_sq

    sum_x_sq = sum(item ** 2 for item in x)
    sum_xy: float = 0
    for xi, yi in zip(x, y):
        sum_xy += xi * yi
    intercept = (sum_y * sum_x_sq - sum_x * sum_xy) / (n * sum_x_sq - sum_x ** 2)
    return (intercept, slope)
