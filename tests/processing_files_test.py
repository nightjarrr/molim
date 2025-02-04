import pytest
import processing
import random
import stats


# SuffixOutputFilePathStrategy tests


def test_SuffixOutputFilePathStrategy_input_validation():
    with pytest.raises(ValueError):
        processing.SuffixOutputFilePathStrategy(None)

    s = processing.SuffixOutputFilePathStrategy("min")
    with pytest.raises(TypeError):
        s.get_output_path("/tmp/path")
    with pytest.raises(ValueError):
        s.get_output_path(None)


def test_SuffixOutputFilePathStrategy_core_logic(tmp_path):
    input_path = tmp_path / "data.txt"
    s = processing.SuffixOutputFilePathStrategy("min")
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
