import pytest
import stats


def test_stats():
    instance = stats.Stats()
    instance.start()
    assert not instance.finished
    instance.finish()

    assert instance.finished
    assert instance.startTimestamp is not None
    assert instance.endTimestamp is not None
    assert instance.elapsed > 0

def test_stats_with():
    with stats.Stats() as instance:
        assert not instance.finished
    assert instance.finished
    assert instance.startTimestamp is not None
    assert instance.endTimestamp is not None
    assert instance.elapsed > 0

def test_unfinished_stats_throws():
    instance = stats.Stats()
    instance.start()
    with pytest.raises(stats.StatsNotFinishedError):
        instance.startTimestamp
    with pytest.raises(stats.StatsNotFinishedError):
        instance.endTimestamp
    with pytest.raises(stats.StatsNotFinishedError):
        instance.elapsed

def test_double_finish_throws():
    with stats.Stats() as instance:
        pass
    with pytest.raises(stats.StatsAlreadyFinishedError):
        instance.start()
    with pytest.raises(stats.StatsAlreadyFinishedError):
        instance.finish()