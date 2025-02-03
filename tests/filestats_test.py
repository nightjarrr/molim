import pytest
import random
import stats
import util

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
        instance.originalFile
    with pytest.raises(stats.StatsNotFinishedError):
        instance.originalFileSize
    with pytest.raises(stats.StatsNotFinishedError):
        instance.processedFile
    with pytest.raises(stats.StatsNotFinishedError):
        instance.processedFileSize
    with pytest.raises(stats.StatsNotFinishedError):
        instance.deltaSize


def test_FileStats_processed_after_finish_throws(files_pair):
    src, dest = files_pair
    with stats.FileStats(src) as s:
        pass
    with pytest.raises(stats.StatsAlreadyFinishedError):
        s.set_processed(dest)


def test_FileStats_expects_file(files_pair, tmp_path):
    src, dest = files_pair
    with pytest.raises(util.NotAFileError):
        s = stats.FileStats(tmp_path)
    with stats.FileStats(src) as s:
        with pytest.raises(util.NotAFileError):
            s.set_processed(tmp_path)


def test_FileStats_double_processed_throws(files_pair, tmp_path):
    src, dest = files_pair
    with stats.FileStats(src) as s:
        s.set_processed(dest)
        with pytest.raises(stats.FileStatsAlreadyHaveProcessedFileError):
            s.set_processed(dest)


def test_FileStats_processed_correct_stats(files_pair):
    src, dest = files_pair
    with stats.FileStats(src) as s:
        s.set_processed(dest)
    assert s.originalFile == src
    assert s.originalFileSize == SOURCE_SIZE
    assert s.processedFile == dest
    assert s.processedFileSize == DEST_SIZE
    assert s.deltaSize == (DEST_SIZE - SOURCE_SIZE)
