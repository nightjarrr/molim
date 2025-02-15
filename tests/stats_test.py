import pytest

from molim import stats


def test_Stats():
    instance = stats.Stats()
    instance.start()
    assert not instance.finished
    instance.finish()

    assert instance.finished
    assert instance.start_timestamp is not None
    assert instance.end_timestamp is not None
    assert instance.elapsed > 0


def test_Stats_with():
    with stats.Stats() as instance:
        assert not instance.finished
    assert instance.finished
    assert instance.start_timestamp is not None
    assert instance.end_timestamp is not None
    assert instance.elapsed > 0


def test_Stats_unfinished_stats_throws():
    instance = stats.Stats()
    instance.start()
    with pytest.raises(stats.StatsNotFinishedError):
        instance.start_timestamp
    with pytest.raises(stats.StatsNotFinishedError):
        instance.end_timestamp
    with pytest.raises(stats.StatsNotFinishedError):
        instance.elapsed


def test_Stats_double_finish_throws():
    with stats.Stats() as instance:
        pass
    with pytest.raises(stats.StatsAlreadyFinishedError):
        instance.start()
    with pytest.raises(stats.StatsAlreadyFinishedError):
        instance.finish()
