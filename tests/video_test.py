import argparse
import os.path
import pathlib
import pytest

from molim import commands
from molim import processing
from molim import shell
from molim import show
from molim import video


# Set verbose output
show.set_verbose(True)

VIDEO_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/video"


def get_input_file(name: str):
    result = VIDEO_FOLDER / name
    return result.absolute()


def cleanup_output_file(file_path: pathlib.Path):
    file_path.unlink(missing_ok=False)


def cleanup_processed_files():
    for f in VIDEO_FOLDER.glob("*.min.mp4"):
        f.unlink()


# FfmpegFileProcessor tests


def test_FfmpegFileProcessor_input_validation():
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()

    # Null checks
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor(None, 27, None, False, o, p)
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor("co", None, None, False, o, p)
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor("co", 27, None, None, o, p)
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor("co", 27, None, False, None, p)
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor("co", 27, None, False, o, None)

    # Type checks
    with pytest.raises(TypeError):
        video.FfmpegFileProcessor(True, 27, None, False, o, p)
    with pytest.raises(TypeError):
        video.FfmpegFileProcessor("co", "op", None, False, o, p)
    with pytest.raises(TypeError):
        video.FfmpegFileProcessor("co", 27, 3.14, None, o, p)
    with pytest.raises(TypeError):
        video.FfmpegFileProcessor("co", 27, None, "False", o, p)
    with pytest.raises(TypeError):
        video.FfmpegFileProcessor("co", 27, None, False, p, p)
    with pytest.raises(TypeError):
        video.FfmpegFileProcessor("co", 27, None, False, p, [p])

    # Value checks
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor("libx265", -1, None, False, o, p)
    with pytest.raises(ValueError):
        video.FfmpegFileProcessor("libx265", 52, None, False, o, p)

    # Method checks
    v = video.FfmpegFileProcessor("libx265", 27, "", False, o, p)
    with pytest.raises(TypeError):
        v.process("/tmp/video.mp4")
    with pytest.raises(ValueError):
        v.process(None)


def test_FfmpegFileProcessor_dry_run():
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()
    v = video.FfmpegFileProcessor("libx265", 27, None, True, o, p)

    i = get_input_file("sample_720x480_1mb.mp4")
    assert i.exists()

    s = v.process(i, dry_run=True)
    print(s.elapsed)


def real_run(name: str, addl=None):
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()
    v = video.FfmpegFileProcessor("libx265", 27, addl, False, o, p)

    i = get_input_file(name)
    assert i.exists()

    s = v.process(i)

    out = s.processed_file
    assert out.exists()
    assert s.processed_file_size < s.original_file_size
    assert s.delta_size > 0

    cleanup_output_file(out)


def test_FfmpegFileProcessor_real_run():
    real_run("sample_720x480_1mb.mp4")
    real_run("Sample Video 1280x720 1mb.mp4")  # Test name with spaces
    with pytest.raises(shell.ShellCommandRuntimeError):
        real_run("sample_720x480_1mb.mp4", "---non -existent ARGUMENT!!!")


# VideoFfmpegCommand tests


def test_VideoFfmpegCommand_name():
    v = video.VideoFfmpegCommand()
    assert v.name == "video"


def test_VideoFfmpegCommand_get_common_arguments_defaults():
    v = video.VideoFfmpegCommand()
    a, b, c, d = v._get_common_arguments_defaults()

    assert a == video.VIDEO_EXTENSION
    assert b == video.VIDEO_GREATER_THAN
    assert c == video.VIDEO_NO_SKIP_PROCESSED
    assert d == video.VIDEO_ORIGINALS


def test_VideoFfmpegCommand_create_parser():
    parser = argparse.ArgumentParser()
    v = video.VideoFfmpegCommand()
    v.configure_parser(parser)
    args = parser.parse_args(["--dry-run", "."])

    assert args.FOLDER == "."
    assert args.dry_run
    assert args.extension == video.VIDEO_EXTENSION
    assert not args.no_skip_processed
    assert args.greater_than == commands.HumanReadableSizeType()(
        video.VIDEO_GREATER_THAN
    )
    assert args.originals == commands.OriginalsHandlingEnum.MOVE
    assert args.ffmpeg_codec == video.VIDEO_FFMPEG_CODEC
    assert args.ffmpeg_rate == video.VIDEO_FFMPEG_RATE
    assert args.ffmpeg_additional is None
    assert not args.ffmpeg_report
    assert not args.verbose


def test_VideoFfmpegCommand_core_logic():
    # Cleanup any previous leftover results.
    cleanup_processed_files()

    c = video.VideoFfmpegCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(VIDEO_FOLDER),
            dry_run=False,
            extension=".mp4",
            no_skip_processed=False,
            greater_than=500 * 1024,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            ffmpeg_codec="libx265",
            ffmpeg_rate=27,
            ffmpeg_additional=None,
            ffmpeg_report=False,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 2
    assert s.skipped_files_count == 1
    assert s.total_delta_size > 0

    cleanup_processed_files()
