import pathlib
import random

import pytest

from molim import processing

# Fixtures


UNMATCHED_FILES_COUNT = 10
PROCESSED_FILES_COUNT = 23
SKIPPED_FILES_COUNT = 7


def create_file(dir: pathlib.Path, index: int, ext: str) -> pathlib.Path:
    f = dir / f"file_{index}.{ext}"
    f.write_bytes(random.randbytes(random.randint(100, 200)))
    return f


def f(tmp_path: pathlib.Path, name: str) -> pathlib.Path:
    _ = tmp_path / name
    _.touch()
    return _


@pytest.fixture(scope="module")
def prepared_folder(tmp_path_factory):
    dir = tmp_path_factory.mktemp("prep")
    for i in range(UNMATCHED_FILES_COUNT):
        create_file(dir, i, "mov")
    for i in range(PROCESSED_FILES_COUNT):
        create_file(dir, i, "mp4")
    for i in range(SKIPPED_FILES_COUNT):
        create_file(dir, i, "min.mp4")
    return dir


# ByExtensionFileMatchStrategy tests


def test_ByExtensionFileMatchStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.ByExtensionFileMatchStrategy(None)
    with pytest.raises(TypeError):
        processing.ByExtensionFileMatchStrategy(12)
    with pytest.raises(ValueError):
        processing.ByExtensionFileMatchStrategy("jpg")
    with pytest.raises(ValueError):
        processing.ByExtensionFileMatchStrategy(".jpg,png")
    with pytest.raises(ValueError):
        processing.ByExtensionFileMatchStrategy(".jpg, some other .png")


def test_ByExtensionFileMatchStrategy_core_logic(tmp_path):
    m = processing.ByExtensionFileMatchStrategy(".cpp")

    assert m.match(f(tmp_path, "data.min.cpp"))
    assert m.match(f(tmp_path, "data_.cpp"))
    assert not m.match(f(tmp_path, "data.jpg"))
    assert not m.match(f(tmp_path, "data.cpp.txt"))
    assert not m.match(f(tmp_path, "data.cppp"))


def test_ByExtensionFileMatchStrategy_core_logic_multiple(tmp_path):
    m = processing.ByExtensionFileMatchStrategy(".docx,.pdf,.ppt")

    assert m.match(f(tmp_path, "data.min.docx"))
    assert m.match(f(tmp_path, "data.pdf.ppt"))
    assert m.match(f(tmp_path, "data.pdf"))
    assert not m.match(f(tmp_path, "data.jpg"))
    assert not m.match(f(tmp_path, "data.pdf.txt"))
    assert not m.match(f(tmp_path, "data,pdf"))


# BySuffixFileSkipStrategy tests


def test_BySuffixFileSkipStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.BySuffixFileSkipStrategy(None)

    with pytest.raises(TypeError):
        processing.BySuffixFileSkipStrategy(12)

    with pytest.raises(ValueError):
        processing.BySuffixFileSkipStrategy("min")

    s = processing.BySuffixFileSkipStrategy(".min")
    with pytest.raises(TypeError):
        s.skip("/tmp/path")
    with pytest.raises(ValueError):
        s.skip(None)


def test_BySuffixFileSkipStrategy_core_logic(tmp_path):
    s = processing.BySuffixFileSkipStrategy(".min")

    path = tmp_path / "data.txt"
    path.touch()
    assert not s.skip(path)

    path = tmp_path / "data.min.txt"
    path.touch()
    assert s.skip(path)


# BySizeFileSkipStrategy tests


def test_BySizeFileSkipStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.BySizeFileSkipStrategy(None)

    with pytest.raises(TypeError):
        processing.BySizeFileSkipStrategy("12")

    with pytest.raises(ValueError):
        processing.BySizeFileSkipStrategy(0)

    with pytest.raises(ValueError):
        processing.BySizeFileSkipStrategy(-100)

    s = processing.BySizeFileSkipStrategy(100)
    with pytest.raises(TypeError):
        s.skip("/tmp/path")
    with pytest.raises(ValueError):
        s.skip(None)


def test_BySizeFileSkipStrategy_core_logic(tmp_path):
    s = processing.BySizeFileSkipStrategy(120)

    path = tmp_path / "data.txt"
    path.write_bytes(random.randbytes(150))
    assert not s.skip(path)

    path.write_bytes(random.randbytes(100))
    assert s.skip(path)


# GlobFileSkipStrategy tests


def test_GlobFileSkipStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.GlobFileSkipStrategy(None)

    with pytest.raises(TypeError):
        processing.GlobFileSkipStrategy(12)

    s = processing.GlobFileSkipStrategy("*.txt")
    with pytest.raises(TypeError):
        s.skip("/tmp/path")
    with pytest.raises(ValueError):
        s.skip(None)


def test_GlobFileSkipStrategy_core_logic(tmp_path):
    s = processing.GlobFileSkipStrategy("*.txt")

    path = tmp_path / "data.txt.pdf"
    path.touch()
    assert not s.skip(path)

    path = tmp_path / "data.min.txt"
    path.touch()
    assert s.skip(path)

    s = processing.GlobFileSkipStrategy("data.txt")
    path = tmp_path / "data.txt"
    path.touch()
    assert s.skip(path)


# MultiFileSkipStrategy tests


def test_MultiFileSkipStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.MultiFileSkipStrategy(None)

    with pytest.raises(TypeError):
        processing.MultiFileSkipStrategy("12")

    with pytest.raises(TypeError):
        processing.MultiFileSkipStrategy(100)

    s = processing.MultiFileSkipStrategy([])
    with pytest.raises(TypeError):
        s.skip("/tmp/path")
    with pytest.raises(ValueError):
        s.skip(None)


def test_MultiFileSkipStrategy_empty(tmp_path):
    s = processing.MultiFileSkipStrategy([])

    path = tmp_path / "data.min.txt"
    path.write_bytes(random.randbytes(150))
    assert not s.skip(path)

    path = tmp_path / "data.txt"
    path.write_bytes(random.randbytes(100))
    assert not s.skip(path)

    path.write_bytes(random.randbytes(150))
    assert not s.skip(path)


def test_MultiFileSkipStrategy_core_logic(tmp_path):
    s = processing.MultiFileSkipStrategy(
        [
            processing.BySuffixFileSkipStrategy(".min"),
            processing.BySizeFileSkipStrategy(120),
        ]
    )

    path = tmp_path / "data.min.txt"
    path.write_bytes(random.randbytes(150))
    assert s.skip(path)

    path = tmp_path / "data.txt"
    path.write_bytes(random.randbytes(100))
    assert s.skip(path)

    path.write_bytes(random.randbytes(150))
    assert not s.skip(path)


# FolderProcessor tests


def test_FolderProcessor_input_validation(tmp_path):
    m = processing.FileMatchStrategy()
    s = processing.FileSkipStrategy()
    p = processing.FileProcessor(
        processing.SuffixOutputFilePathStrategy(".min"),
        processing.NoopPostProcessingStrategy(),
    )

    # Null checks
    with pytest.raises(ValueError):
        processing.FolderProcessor(None, m, s, p)
    with pytest.raises(ValueError):
        processing.FolderProcessor(tmp_path, None, s, p)
    with pytest.raises(ValueError):
        processing.FolderProcessor(tmp_path, m, None, p)
    with pytest.raises(ValueError):
        processing.FolderProcessor(tmp_path, m, s, None)

    # Type checks
    with pytest.raises(TypeError):
        processing.FolderProcessor(p, m, s, p)
    with pytest.raises(TypeError):
        processing.FolderProcessor(tmp_path, tmp_path, s, p)
    with pytest.raises(TypeError):
        processing.FolderProcessor(tmp_path, m, m, p)
    with pytest.raises(TypeError):
        processing.FolderProcessor(tmp_path, m, s, s)


def test_FolderProcessor_empty_folder(tmp_path):
    m = processing.FileMatchStrategy()
    s = processing.FileSkipStrategy()
    p = processing.FileProcessor(
        processing.SuffixOutputFilePathStrategy(".min"),
        processing.NoopPostProcessingStrategy(),
    )

    dir = tmp_path / "empty"
    dir.mkdir()
    f = processing.FolderProcessor(dir, m, s, p)
    stat = f.process()

    assert stat is not None
    assert stat.finished
    assert stat.elapsed > 0
    assert stat.folder_path == dir
    assert len(stat.processed_files_stats) == 0
    assert stat.skipped_files_count == 0
    assert stat.total_original_size == 0
    assert stat.total_processed_size == 0
    assert stat.total_delta_size == 0


def test_FolderProcessor_dry_run(prepared_folder):
    m = processing.ByExtensionFileMatchStrategy(".mp4")
    s = processing.BySuffixFileSkipStrategy(".min")
    p = processing.FileProcessor(
        processing.SuffixOutputFilePathStrategy(".min"),
        processing.NoopPostProcessingStrategy(),
    )

    f = processing.FolderProcessor(prepared_folder, m, s, p)
    stat = f.process(dry_run=True)

    assert stat is not None
    assert stat.finished
    assert stat.elapsed > 0
    assert stat.folder_path == prepared_folder
    assert len(stat.processed_files_stats) == PROCESSED_FILES_COUNT
    assert stat.skipped_files_count == SKIPPED_FILES_COUNT
    assert stat.total_original_size > 0
    assert stat.total_original_size == sum(s.original_file_size for s in stat.processed_files_stats)
    assert stat.total_processed_size == stat.total_original_size
    assert stat.total_delta_size == 0
