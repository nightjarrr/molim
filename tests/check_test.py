import pytest

from molim import check


def test_ensure_type_or_none_none_input():
    check.ensure_type_or_none(None, str)


def test_ensure_type_or_none_correct_type():
    check.ensure_type_or_none("hello", str)


def test_ensure_type_or_none_wrong_type():
    with pytest.raises(TypeError):
        check.ensure_type_or_none(42, str)
