import pytest
import random
import stats


SOURCE_SIZE = 200
SOURCE_DATA = random.randbytes(SOURCE_SIZE)

DEST_SIZE = 120
DEST_DATA = random.randbytes(DEST_SIZE)


@pytest.fixture(scope="module")
def files_pair(tmp_path_factory):
    folder = tmp_path_factory.mktemp("filestats")
    src = folder / "source.bin"
    src.write_bytes(SOURCE_DATA)
    dest = folder / "dest.bin"
    dest.write_bytes(DEST_DATA)
    return (src, dest)


def test_FileStats_unfinished_stats_throws(files_pair):
    src, dest = files_pair
    instance = stats.FileStats(src)
    instance.start()
    with pytest.raises(stats.StatsNotFinishedError):
        instance.original_file
    with pytest.raises(stats.StatsNotFinishedError):
        instance.original_file_size
    with pytest.raises(stats.StatsNotFinishedError):
        instance.processed_file
    with pytest.raises(stats.StatsNotFinishedError):
        instance.processed_file_size
    with pytest.raises(stats.StatsNotFinishedError):
        instance.delta_size


def test_FileStats_processed_after_finish_throws(files_pair):
    src, dest = files_pair
    with stats.FileStats(src) as s:
        pass
    with pytest.raises(stats.StatsAlreadyFinishedError):
        s.set_processed_file(dest)


def test_FileStats_expects_file(files_pair, tmp_path):
    src, dest = files_pair
    with pytest.raises(ValueError):
        s = stats.FileStats(tmp_path)
    with stats.FileStats(src) as s:
        with pytest.raises(ValueError):
            s.set_processed_file(tmp_path)


def test_FileStats_double_processed_throws(files_pair, tmp_path):
    src, dest = files_pair
    with stats.FileStats(src) as s:
        s.set_processed_file(dest)
        with pytest.raises(stats.FileStatsAlreadyHaveProcessedFileError):
            s.set_processed_file(dest)


def test_FileStats_processed_correct_stats(files_pair):
    src, dest = files_pair
    with stats.FileStats(src) as s:
        s.set_processed_file(dest)
    assert s.original_file == src
    assert s.original_file_size == SOURCE_SIZE
    assert s.processed_file == dest
    assert s.processed_file_size == DEST_SIZE
    assert s.delta_size == (DEST_SIZE - SOURCE_SIZE)
