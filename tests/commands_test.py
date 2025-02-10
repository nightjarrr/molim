import commands
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

