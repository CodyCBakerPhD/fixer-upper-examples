# TASK:
# The following routine has grown unruly over time. We'd like to
# both make it more interpretable and add support for an additional
# mode, "stdev", which computes standard deviations

from collections import Counter


def summarize(
    data: list[float] | list[list[float]],
    mode,
    is_sample: bool = True,
) -> float | tuple[float, float]:
    if mode == 'fit':
        x = [point[0] for point in data]
        y = [point[1] for point in data]
    else:
        x = data

    if mode == 'mode':
        counts = Counter(x)

    n = len(data)
    total = sum(x)

    if mode in ('mean', 'variance', 'fit'):
        mean = total / n

    if mode == 'median':
        x = sorted(x)
        half = n // 2
        if n % 2 == 1:
            median = x[half]
        else:
            median = (x[half] + x[half - 1]) / 2

    if mode == 'variance' or mode == 'fit':
        x_xi_diff = [(item - mean) for item in x]
        sum_sq = sum(item ** 2 for item in x_xi_diff)

    if mode == 'fit':
        sum_y = sum(y)
        y_mean = sum_y / n
        y_yi_diff = [(item - y_mean) for item in y]
        # += rather than sum(): sum() of floats is compensated since Python 3.12
        slope_numerator = 0
        for dx, dy in zip(x_xi_diff, y_yi_diff):
            slope_numerator += dy * dx
        slope = slope_numerator / sum_sq

        sum_x_sq = sum(item ** 2 for item in x)
        sum_xy = 0
        for xi, yi in zip(x, y):
            sum_xy += xi * yi
        intercept = (sum_y * sum_x_sq - total * sum_xy) / (n * sum_x_sq - (total)**2)

    if mode == 'range':
        max = x[0]
        min = x[0]
        for i in range(len(x)):
            if x[i] > max:
                max = x[i]
            if x[i] < min:
                min = x[i]

    if mode == 'sum':
        return total
    if mode == 'mean':
        return mean
    if mode == 'median':
        return median
    if mode == 'mode':
        if not counts:
            return (None, 0)    # type: ignore
        return counts.most_common(1)[0]
    if mode == 'variance':
        if is_sample:
            return sum_sq / (n - 1)
        return sum_sq / n
    if mode == 'fit':
        return (intercept, slope)
    if mode == 'range':
        return (min, max)

    return None
