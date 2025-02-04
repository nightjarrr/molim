import pytest
import processing


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
