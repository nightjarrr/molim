from importlib.metadata import PackageNotFoundError

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


# Version support tests


def test_version_when_package_installed(monkeypatch):
    monkeypatch.setattr(cli, "version", lambda _: "1.2.3")
    assert cli.__version() == "1.2.3"


def test_version_when_package_not_installed(monkeypatch):
    def raise_not_found(_):
        raise PackageNotFoundError

    monkeypatch.setattr(cli, "version", raise_not_found)
    assert cli.__version() == cli.UNKNOWN_VERSION


def test_cli_version_flag(monkeypatch, capsys):
    monkeypatch.setattr(cli, "version", lambda _: "1.2.3")
    with pytest.raises(SystemExit) as exc:
        cli.run(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "molim 1.2.3" == captured.out.strip()
