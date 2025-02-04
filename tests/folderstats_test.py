import pytest
import random
import stats


def test_FolderStats_expects_folder(tmp_path):
    with pytest.raises(ValueError):
        stats.FolderStats(None)
    with pytest.raises(TypeError):
        stats.FolderStats("/tmp/folder")
    with pytest.raises(ValueError):
        stats.FolderStats(tmp_path / "file.txt")
    stats.FolderStats(tmp_path)


def test_FolderStats_unfinished_stats_throws(tmp_path):
    instance = stats.FolderStats(tmp_path)
    instance.start()
    with pytest.raises(stats.StatsNotFinishedError):
        instance.folder_path
    with pytest.raises(stats.StatsNotFinishedError):
        instance.processed_files_stats
    with pytest.raises(stats.StatsNotFinishedError):
        instance.skipped_files_count
    with pytest.raises(stats.StatsNotFinishedError):
        instance.total_original_size
    with pytest.raises(stats.StatsNotFinishedError):
        instance.total_processed_size
    with pytest.raises(stats.StatsNotFinishedError):
        instance.total_delta_size


def test_FolderStats_processed_after_finish_throws(tmp_path):
    with stats.FolderStats(tmp_path) as s:
        pass
    with pytest.raises(stats.StatsAlreadyFinishedError):
        f = tmp_path / "file.txt"
        f.touch()
        s.add_processed_file_stats(stats.FileStats(f))
    with pytest.raises(stats.StatsAlreadyFinishedError):
        s.add_skipped_file()


def test_FolderStats_core_logic(tmp_path):
    # Arrange
    files_count = random.randint(10, 20)
    skipped_count = random.randint(3, 7)
    files = []
    for _ in range(files_count):
        src_size = random.randint(100, 200)
        src_data = random.randbytes(src_size)
        src = tmp_path / f"{_}.txt"
        src.write_bytes(src_data)
        dst_size = random.randint(70, 130)
        dst_data = random.randbytes(dst_size)
        dst = tmp_path / f"{_}.min.txt"
        dst.write_bytes(dst_data)
        files.append((src, src_size, dst, dst_size))

    # Act
    with stats.FolderStats(tmp_path) as s:
        for _ in range(skipped_count):
            s.add_skipped_file()
        for _ in files:
            src, src_size, dst, dst_size = _
            with stats.FileStats(src) as ss:
                ss.set_processed_file(dst)
            s.add_processed_file_stats(ss)

    # Assert
    assert s.finished
    assert s.elapsed > 0
    assert s.folder_path == tmp_path
    assert s.skipped_files_count == skipped_count
    assert len(s.processed_files_stats) == len(files)
    assert s.total_original_size == sum(_[1] for _ in files)
    assert s.total_processed_size == sum(_[3] for _ in files)
    assert s.total_delta_size == (s.total_original_size - s.total_processed_size)
