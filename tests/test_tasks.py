"""The exercises' own tasks, as solved by the soln2 code in 02/ex2.py and 03/ex3.py."""

import functools
import statistics
import warnings

import pytest
from exercises import both, ex3

DATA = [3.5, 1.25, 2.0, 2.0, 9.75]
POINTS = [[1.0, 2.0], [2.0, 4.1], [3.0, 5.9], [4.0, 8.2]]


# Exercise 2: a readable summarize() that also computes "stdev"


@both
def test_stdev_matches_the_statistics_module(module):
    assert module.summarize(DATA, "stdev") == pytest.approx(statistics.stdev(DATA))
    assert module.summarize(DATA, "stdev", False) == pytest.approx(
        statistics.pstdev(DATA)
    )


@both
def test_every_stat_is_accepted_by_name_and_by_member(module):
    for stat in module.Stat:
        data = POINTS if stat is module.Stat.FIT else DATA
        assert module.summarize(data, stat) == module.summarize(data, stat.value)


@both
def test_mode_is_the_deprecated_name_of_stat(module):
    with pytest.warns(DeprecationWarning, match="'mode' argument is deprecated"):
        assert module.summarize(DATA, mode="mean") == module.summarize(DATA, "mean")
    with pytest.raises(TypeError, match="both 'stat' and its old name 'mode'"):
        module.summarize(DATA, stat="mean", mode="mean")
    with pytest.raises(TypeError, match="missing required argument: 'stat'"):
        module.summarize(DATA)


# Exercise 3: get_stats() computes several statistics without repeating work


@pytest.mark.parametrize("data", [DATA, POINTS], ids=["series", "points"])
def test_get_stats_agrees_with_summarize(data):
    names = [stat.value for stat in ex3.Stat]
    if data is DATA:
        names.remove("fit")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        results = ex3.get_stats(data, names, is_sample=False)
    assert results == {name: ex3.summarize(data, name, False) for name in names}


def test_get_stats_does_shared_work_once(monkeypatch):
    calls = []
    original = ex3.Series.mean.func

    def counted_mean(series):
        calls.append(series)
        return original(series)

    mean = functools.cached_property(counted_mean)
    mean.__set_name__(ex3.Series, "mean")
    monkeypatch.setattr(ex3.Series, "mean", mean)
    ex3.get_stats(DATA, ["mean", "variance", "stdev"])
    assert len(calls) == 1


def test_get_stats_checks_every_name_before_computing():
    with pytest.raises(ValueError, match="unknown statistic 'bogus'"):
        ex3.get_stats(["not", "numbers"], ["mean", "bogus"])
