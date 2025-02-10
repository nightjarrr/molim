import commands
import processing
import pytest

# HumanReadableSizeType tests


def test_HumanReadableSizeType_input_validation():
    h = commands.HumanReadableSizeType()
    with pytest.raises(TypeError):
        h()  # No required parameter passed
    with pytest.raises(ValueError):
        h(None)
    with pytest.raises(TypeError):
        h(800)
    with pytest.raises(ValueError):
        h("some random string of text")  # Incorrect value and incorrect suffix
    with pytest.raises(ValueError):
        h("12-and-a-half-G")  # Correct suffix, incorrect value
    with pytest.raises(ValueError):
        h("-2G")  # Correct suffix, negative value


def test_HumanReadableSizeType_core_logic():
    h = commands.HumanReadableSizeType()
    assert 200 == h("200")
    assert 450 * 1024 == h("450K")
    assert 7 * 1024 * 1024 == h("7M")
    assert int(12.5 * 1024 * 1024) == h("12.5M")
    assert int(1.2 * 1024 * 1024 * 1024) == h("1.2G")


# OriginalsHandlingArgType tests


def test_OriginalsHandlingArgType_input_validation():
    o = commands.OriginalsHandlingArgType()
    with pytest.raises(TypeError):
        o()  # No required parameter passed
    with pytest.raises(ValueError):
        o(None)
    with pytest.raises(TypeError):
        o(800)
    with pytest.raises(ValueError):
        o("some random string of text")  # Incorrect value
    with pytest.raises(ValueError):
        o("LEAVE")  # Correct value but not lowercase


# Command tests


def test_Command_get_post_processing_strategy(tmp_path):
    c = commands.Command()

    p = c._get_post_processing_strategy(
        commands.OriginalsHandlingEnum.LEAVE, tmp_path, False
    )
    assert isinstance(p, processing.NoopPostProcessingStrategy)

    p = c._get_post_processing_strategy(
        commands.OriginalsHandlingEnum.DELETE, tmp_path, False
    )
    assert isinstance(p, processing.DeleteOriginalPostProcessingStrategy)

    p = c._get_post_processing_strategy(
        commands.OriginalsHandlingEnum.MOVE, tmp_path, False
    )
    assert isinstance(p, processing.MoveOriginalPostProcessingStrategy)
