import pytest

from molim import cli

def test_cli_input_validation():
    with pytest.raises(ValueError):
        cli.run(None)
    with pytest.raises(TypeError):
        cli.run("resize 1600 .")
    with pytest.raises(TypeError):
        cli.run([1, 2, 3])

def test_cli_dry_run():
    cli.run(["suffix", "--dry-run", "--verbose", ".anything", "."])
    assert True
