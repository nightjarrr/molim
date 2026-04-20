import argparse
import os.path
import pathlib

import pytest

from molim import commands, processing
from molim.images import rawtherapee

from . import common

FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/rawtherapee"


# RawTherapeeFileProcessor tests


def test_RawTherapeeFileProcessor_input_validation(tmp_path):
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()
    profile = tmp_path / "profile.pp3"
    profile.touch()

    # Null checks
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(None, 75, 1, o, p)
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(profile, None, 1, o, p)
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(profile, 75, None, o, p)

    # Type checks
    with pytest.raises(TypeError):
        rawtherapee.RawTherapeeFileProcessor(True, 75, 1, o, p)
    with pytest.raises(TypeError):
        rawtherapee.RawTherapeeFileProcessor(str(profile), 75, 1, o, p)
    with pytest.raises(TypeError):
        rawtherapee.RawTherapeeFileProcessor(profile, "75", 1, o, p)
    with pytest.raises(TypeError):
        rawtherapee.RawTherapeeFileProcessor(profile, 75, o, o, p)
    with pytest.raises(TypeError):
        rawtherapee.RawTherapeeFileProcessor(profile, 75, 1.6, o, p)

    # Range checks
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(profile, 0, 1, o, p)
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(profile, 102, 1, o, p)
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(profile, 90, -2, o, p)
    with pytest.raises(ValueError):
        rawtherapee.RawTherapeeFileProcessor(profile, 10, 5, o, p)


def test_RawTherapeeFileProcessor_core_logic():
    o = processing.SuffixOutputFilePathStrategy(".m")
    p = processing.NoopPostProcessingStrategy()
    profile = FOLDER / "profile.pp3"
    input = FOLDER / "file_example_JPG_100kB.jpg"
    output = FOLDER / "file_example_JPG_100kB.m.jpg"

    r = rawtherapee.RawTherapeeFileProcessor(profile, 75, 1, o, p)
    s = r.process(input)

    assert s is not None
    assert s.processed_file == output
    assert output.exists()
    # Input file not touched
    assert input.exists()
    # Output file must be smaller
    assert s.delta_size > 0

    # Cleanup
    output.unlink()


# RawTherapeeCommand tests


def test_RawTherapeeCommand_core_logic():
    cmd = rawtherapee.RawTherapeeCommand()
    s = cmd(
        argparse.Namespace(
            FOLDER=str(FOLDER),
            dry_run=False,
            config=str(common.EMPTY_CONFIG),
            extension=".jpg",
            no_skip_processed=False,
            greater_than=1024,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            profile_folder=str(FOLDER),
            profile="profile",
            quality=60,
            subsampling=1,
            processed_subfolder=None,
            verbose=True,
        )
    )

    assert s is not None
    assert s.total_delta_size > 0
    assert len(s.processed_files_stats) == 1
    for fs in s.processed_files_stats:
        assert fs.processed_file.exists()
        assert fs.original_file.exists()
        # Output file must be smaller
        assert fs.delta_size > 0
        # Cleanup
        fs.processed_file.unlink()


def test_RawTherapeeCommand_core_logic_subfolder():
    subfolder = "_out"
    subfolder_path = FOLDER / subfolder
    assert not subfolder_path.exists()

    cmd = rawtherapee.RawTherapeeCommand()
    s = cmd(
        argparse.Namespace(
            FOLDER=str(FOLDER),
            dry_run=False,
            config=str(common.EMPTY_CONFIG),
            extension=".jpg",
            no_skip_processed=False,
            greater_than=1024,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            profile_folder=str(FOLDER),
            profile="profile",
            quality=60,
            subsampling=1,
            processed_subfolder=subfolder,
            verbose=True,
        )
    )

    assert s is not None
    assert s.total_delta_size > 0
    assert len(s.processed_files_stats) == 1
    for fs in s.processed_files_stats:
        assert fs.processed_file.exists()
        assert fs.processed_file.parent == subfolder_path
        assert fs.original_file.exists()
        # Output file must be smaller
        assert fs.delta_size > 0
        # Cleanup
        fs.processed_file.unlink()
    assert subfolder_path.exists()
    assert len([f for f in subfolder_path.iterdir()]) == 0

    # Cleanup
    subfolder_path.rmdir()
