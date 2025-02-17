import pytest

from . import common

from molim import config



def test_config_no_file():
    with pytest.raises(ValueError):
        config.load(common.TEST_CONFIG.with_name("no-such-config.toml"))


def test_config_none_values():
    # Non-existent key in global section
    c = config.load(common.TEST_CONFIG)
    assert c("space-shuttle") is None

    # Non-existent key in non-global section
    c = config.load(common.TEST_CONFIG, "suffix")
    assert c("space-shuttle") is None

    # Non-existent section
    c = config.load(common.TEST_CONFIG,"outer-space")
    assert c("space-shuttle") is None


def test_config_global_values():
    # Global section
    g = config.load(common.TEST_CONFIG)
    assert g("meaning_of_life") == 42
    assert g("important_text") == "Attention to everyone"
    skip = g("skip")
    assert isinstance(skip, list)
    assert len(skip) == 3
    assert skip[0] == "*.pyc"
    assert skip[1] == "ignore.*"
    assert skip[2] == "why.me"


def test_config_non_global_values():
    vid = config.load(common.TEST_CONFIG, "video")

    # Non-global section values
    assert vid("command_line") == "ffmpeg"

    # Value inheritance
    assert vid("meaning_of_life") == 42

    # Value overrides
    skip = vid("skip")
    assert isinstance(skip, list)
    assert len(skip) == 1
    assert skip[0] == "*.webm"
