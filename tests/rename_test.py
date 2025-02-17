import argparse
import pathlib
import pytest
import random

from . import common

from molim import commands
from molim import processing
from molim import rename


# Fixtures

UNMATCHED_FILES_COUNT = 10
PROCESSED_FILES_COUNT = 23
SKIPPED_FILES_COUNT = 7


def create_file(dir: pathlib.Path, index: int, ext: str) -> pathlib.Path:
    f = dir / f"file_{index}.{ext}"
    f.write_bytes(random.randbytes(random.randint(100, 200)))
    return f


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


# RenameFileProcessor tests


def test_RenameFileProcessor_core_logic(tmp_path):
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()

    r = rename.RenameFileProcessor(o, p)

    i = tmp_path / "data_file.txt"
    i.touch()
    r.process(i)

    assert not i.exists()
    assert (tmp_path / "data_file.min.txt").exists()


# SuffixCommand tests


def test_SuffixCommand_name():
    cmd = rename.SuffixCommand()
    assert cmd.name == "suffix"


def test_SuffixCommand_get_common_arguments_defaults():
    cmd = rename.SuffixCommand()
    a, b, c, d = cmd._get_common_arguments_defaults()

    assert a == commands.ANY_MATCH_EXTENSION
    assert b is None
    assert c is None
    assert d is None


def test_SuffixCommand_create_parser():
    parser = argparse.ArgumentParser()
    cmd = rename.SuffixCommand()
    cmd.configure_parser(parser)
    args = parser.parse_args(["--dry-run", ".w1600", "."])

    assert args.FOLDER == "."
    assert args.SUFFIX == ".w1600"
    assert args.dry_run
    assert not args.verbose

    # Ensure some common args are suppressed
    with pytest.raises(AttributeError):
        args.originals
    with pytest.raises(AttributeError):
        args.no_skip_processed
    with pytest.raises(AttributeError):
        args.greater_than


def test_ResizeCommand_core_logic(prepared_folder):
    cmd = rename.SuffixCommand()
    s = cmd(
        argparse.Namespace(
            FOLDER=str(prepared_folder),
            SUFFIX=".min",
            extension=".mp4",
            dry_run=False,
            config=str(common.EMPTY_CONFIG),
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == PROCESSED_FILES_COUNT
    for f in s.processed_files_stats:
        assert f.processed_file.stem.endswith(".min")
    assert s.skipped_files_count == SKIPPED_FILES_COUNT
