import pytest
import random

from molim import processing
from molim import stats


# SuffixOutputFilePathStrategy tests


def test_SuffixOutputFilePathStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.SuffixOutputFilePathStrategy(None)

    with pytest.raises(TypeError):
        processing.SuffixOutputFilePathStrategy(12)

    with pytest.raises(ValueError):
        processing.SuffixOutputFilePathStrategy("min")

    s = processing.SuffixOutputFilePathStrategy(".min")
    with pytest.raises(TypeError):
        s.get_output_path("/tmp/path")
    with pytest.raises(ValueError):
        s.get_output_path(None)


def test_SuffixOutputFilePathStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    s = processing.SuffixOutputFilePathStrategy(".min")
    output_path = s.get_output_path(input_path)

    # Input and output in the same folder
    assert output_path.parent == input_path.parent
    # Output filename is input with .min name suffix added
    assert output_path.name == "data.min.txt"


# ChangeExtOutputFilePathStrategy tests


def test_ChangeExtOutputFilePathStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.ChangeExtOutputFilePathStrategy(None)

    s = processing.ChangeExtOutputFilePathStrategy(".zip")
    with pytest.raises(TypeError):
        s.get_output_path("/tmp/path")
    with pytest.raises(ValueError):
        s.get_output_path(None)


def test_ChangeExtOutputFilePathStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    s = processing.ChangeExtOutputFilePathStrategy(".zip")
    output_path = s.get_output_path(input_path)

    # Input and output in the same folder
    assert output_path.parent == input_path.parent
    # Output filename is input with a changed extension
    assert output_path.name == "data.zip"


# FolderOutputFilePathStrategy tests


def test_FolderOutputFilePathStrategy_input_validation(tmp_path):
    with pytest.raises(ValueError):
        processing.FolderOutputFilePathStrategy(None, False)
    with pytest.raises(TypeError):
        processing.FolderOutputFilePathStrategy("/tmp/folder", False)

    s = processing.FolderOutputFilePathStrategy(tmp_path, True)
    with pytest.raises(TypeError):
        s.get_output_path("/tmp/path")
    with pytest.raises(ValueError):
        s.get_output_path(None)


def test_FolderOutputFilePathStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    output_folder = tmp_path / "out"

    s = processing.FolderOutputFilePathStrategy(output_folder, False)
    output_path = s.get_output_path(input_path)

    # Input and output in the same folder
    assert output_path.parent == output_folder
    # Output filename is input with a changed extension
    assert output_path.name == input_path.name


# MultiOutputFilePathStrategy tests


def test_MultiOutputFilePathStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.MultiOutputFilePathStrategy(None)

    with pytest.raises(TypeError):
        processing.MultiOutputFilePathStrategy("12")

    with pytest.raises(TypeError):
        processing.MultiOutputFilePathStrategy(100)

    with pytest.raises(ValueError):
        processing.MultiOutputFilePathStrategy([])

    s = processing.MultiOutputFilePathStrategy(
        [processing.ChangeExtOutputFilePathStrategy(".jpg")]
    )
    with pytest.raises(TypeError):
        s.get_output_path("/tmp/path")
    with pytest.raises(ValueError):
        s.get_output_path(None)


def test_MultiOutputFilePathStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    s = processing.MultiOutputFilePathStrategy(
        [
            processing.ChangeExtOutputFilePathStrategy(".zip"),
            processing.SuffixOutputFilePathStrategy(".min"),
        ]
    )
    output_path = s.get_output_path(input_path)

    # Input and output in the same folder
    assert output_path.parent == input_path.parent
    # Output filename is input with a changed extension
    assert output_path.name == "data.min.zip"


# MoveOriginalPostProcessingStrategy tests


def test_MoveOriginalPostProcessingStrategy_input_validation(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    with pytest.raises(ValueError):
        processing.MoveOriginalPostProcessingStrategy(None, False)
    with pytest.raises(TypeError):
        processing.MoveOriginalPostProcessingStrategy(str(tmp_path), False)
    with pytest.raises(ValueError):
        processing.MoveOriginalPostProcessingStrategy(input_path, False)

    move_to = tmp_path / "_orig"
    m = processing.MoveOriginalPostProcessingStrategy(move_to, True)
    with pytest.raises(ValueError):
        m.process(None, input_path, True)
    with pytest.raises(ValueError):
        m.process(input_path, None, False)


def test_MoveOriginalPostProcessingStrategy_dry_run(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    move_to = tmp_path / "_orig"
    m = processing.MoveOriginalPostProcessingStrategy(move_to, True)
    m.process(input_path, tmp_path / "data.zip", True)

    assert not move_to.exists()
    assert input_path.exists()
    assert input_path == (tmp_path / "data.txt")


def test_MoveOriginalPostProcessingStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    output_path = tmp_path / "data.zip"
    output_path.touch()

    move_to = tmp_path / "_orig"
    m = processing.MoveOriginalPostProcessingStrategy(move_to, False)
    m.process(input_path, output_path, False)

    assert move_to.exists()
    assert not input_path.exists()
    assert (move_to / "data.txt").exists()


# DeleteOriginalPostProcessingStrategy tests


def test_DeleteOriginalPostProcessingStrategy_input_validation(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    m = processing.DeleteOriginalPostProcessingStrategy()
    with pytest.raises(ValueError):
        m.process(None, input_path, True)
    with pytest.raises(ValueError):
        m.process(input_path, None, False)


def test_DeleteOriginalPostProcessingStrategy_dry_run(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    m = processing.DeleteOriginalPostProcessingStrategy()
    m.process(input_path, tmp_path / "data.zip", True)

    assert input_path.exists()
    assert input_path == (tmp_path / "data.txt")


def test_DeleteOriginalPostProcessingStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    output_path = tmp_path / "data.zip"
    output_path.touch()

    m = processing.DeleteOriginalPostProcessingStrategy()
    m.process(input_path, output_path, False)

    assert not input_path.exists()


# ReplaceOriginalPostProcessignStrategy tests


def test_ReplaceOriginalPostProcessignStrategy_input_validation(tmp_path):
    with pytest.raises(ValueError):
        processing.ReplaceOriginalPostProcessignStrategy(None)
    with pytest.raises(TypeError):
        processing.ReplaceOriginalPostProcessignStrategy(17)

    input_path = tmp_path / "data.txt"
    input_path.touch()

    m = processing.ReplaceOriginalPostProcessignStrategy(
        processing.DeleteOriginalPostProcessingStrategy()
    )
    with pytest.raises(ValueError):
        m.process(None, input_path, True)
    with pytest.raises(ValueError):
        m.process(input_path, None, False)


def test_ReplaceOriginalPostProcessignStrategy_dry_run(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    m = processing.ReplaceOriginalPostProcessignStrategy(
        processing.DeleteOriginalPostProcessingStrategy()
    )
    m.process(input_path, tmp_path / "data.zip", True)

    assert input_path.exists()
    assert input_path == (tmp_path / "data.txt")


def test_ReplaceOriginalPostProcessignStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    input_path.touch()

    output_path = tmp_path / "data.zip"
    output_path.touch()

    orig_folder = tmp_path / "_orig"

    m = processing.ReplaceOriginalPostProcessignStrategy(
        processing.MoveOriginalPostProcessingStrategy(orig_folder, False)
    )
    m.process(input_path, output_path, False)

    assert orig_folder.exists()
    assert (orig_folder / input_path.name).exists()  # Moved original file
    assert (
        not output_path.exists()
    )  # Output original name does not exist because it was renamed
    assert (
        input_path.exists()
    )  # Input original name exists because output was renamed to this name


# FileProcessor tests


def test_FileProcessor_input_validation(tmp_path):
    input_path = tmp_path / "data.txt"
    s = processing.ChangeExtOutputFilePathStrategy(".zip")
    pp = processing.NoopPostProcessingStrategy()

    with pytest.raises(ValueError):
        processing.FileProcessor(None, pp)

    with pytest.raises(ValueError):
        processing.FileProcessor(s, None)

    # Type checks
    with pytest.raises(TypeError):
        processing.FileProcessor(s, s)

    with pytest.raises(TypeError):
        processing.FileProcessor(pp, pp)

    # File check
    p = processing.FileProcessor(s, pp)
    with pytest.raises(ValueError):
        p.process(input_path)
    input_path.touch()

    with pytest.raises(TypeError):
        p.process("/tmp/path")


def test_FileProcessor_dry_run(tmp_path):
    input_path = tmp_path / "data.bin"
    input_size = random.randint(100, 200)
    input_data = random.randbytes(input_size)
    input_path.write_bytes(input_data)
    s = processing.ChangeExtOutputFilePathStrategy(".zip")
    pp = processing.NoopPostProcessingStrategy()

    p = processing.FileProcessor(s, pp)
    # Verify that non-dry run fails on abstract class.
    with pytest.raises(NotImplementedError):
        p.process(input_path)

    stat = p.process(input_path, dry_run=True)

    assert stat is not None
    assert isinstance(stat, stats.FileStats)
    assert stat.finished
    assert stat.original_file == input_path
    assert stat.original_file_size == input_size
    assert stat.processed_file.name == "data.zip"
    assert stat.processed_file_size == input_size
    assert stat.delta_size == 0
    assert stat.elapsed > 0
