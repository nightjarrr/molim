import argparse
import os.path
import pathlib
import pytest

from . import common

from molim import commands
from molim import processing
from molim import shell
from molim import show
from molim import stats
from molim import images
from molim.images import resize
from molim.images import jpegify
from molim.images import imagemagick


JPEGIFY_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/jpegify"
RESIZE_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/resize"


def get_input_file(name: str):
    result = JPEGIFY_FOLDER / name
    return result.absolute()


def cleanup_output_file(file_path: pathlib.Path):
    file_path.unlink(missing_ok=False)


def cleanup_processed_files(s: stats.FolderStats):
    for ss in s.processed_files_stats:
        ss.processed_file.unlink(missing_ok=True)


def cleanup_processed_folder(folder: pathlib.Path):
    for f in folder.iterdir():
        f.unlink()
    folder.rmdir()


# ImageMagickFileProcessor tests


def test_ImageMagickFileProcessor_input_validation():
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()

    # Null checks
    with pytest.raises(ValueError):
        imagemagick.ImageMagickFileProcessor(
            None, "None", output_strategy=o, post_processor=p
        )
    with pytest.raises(ValueError):
        imagemagick.ImageMagickFileProcessor("78", output_strategy=None, post_processor=p)
    with pytest.raises(ValueError):
        imagemagick.ImageMagickFileProcessor("90", output_strategy=o, post_processor=None)
    # Type checks
    with pytest.raises(TypeError):
        imagemagick.ImageMagickFileProcessor(90, output_strategy=o, post_processor=p)
    with pytest.raises(TypeError):
        imagemagick.ImageMagickFileProcessor("90", True, output_strategy=o, post_processor=p)
    with pytest.raises(TypeError):
        imagemagick.ImageMagickFileProcessor("90", output_strategy=87, post_processor=p)
    with pytest.raises(TypeError):
        imagemagick.ImageMagickFileProcessor("90", output_strategy=o, post_processor=o)
    # Method checks
    i = imagemagick.ImageMagickFileProcessor("92", output_strategy=o, post_processor=p)
    with pytest.raises(TypeError):
        i.process("/tmp/video.mp4")
    with pytest.raises(ValueError):
        i.process(None)


def test_ImageMagickFileProcessor_dry_run():
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()
    i = imagemagick.ImageMagickFileProcessor(
        "-quality", "92", output_strategy=o, post_processor=p
    )

    ii = get_input_file("file_example_PNG_1MB.png")
    assert ii.exists()

    s = i.process(ii, dry_run=True)
    print(s.elapsed)


def real_run(name: str, addl=None):
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()

    cmdln = ["-quality", "92"]
    if addl:
        cmdln.append(addl)
    i = imagemagick.ImageMagickFileProcessor(*cmdln, output_strategy=o, post_processor=p)

    ii = get_input_file(name)
    assert ii.exists()

    s = i.process(ii)

    out = s.processed_file
    assert out.exists()
    assert out.suffix == ".jpg"

    cleanup_output_file(out)


def test_ImageMagickFileProcessor_real_run():
    # Set verbose output
    show.set_verbose(True)
    real_run("file_example_PNG_1MB.png")
    real_run("file example WEBP_500kB.webp")  # Test name with spaces
    with pytest.raises(shell.ShellCommandRuntimeError):
        real_run("file_example_PNG_1MB.png", "---non -existent ARGUMENT!!!")


# JpegifyCommand tests


def test_JpegifyCommand_name():
    j = jpegify.JpegifyCommand()
    assert j.name == "jpegify"


def test_JpegifyCommand_get_common_arguments_defaults():
    j = jpegify.JpegifyCommand()
    a, b, c, d = j._get_common_arguments_defaults()

    assert a == jpegify.JpegifyCommand.JPEGIFY_EXTENSION
    assert b is None
    assert c is None
    assert d == jpegify.JpegifyCommand.JPEGIFY_ORIGINALS


def test_JpegifyCommand_create_parser():
    parser = argparse.ArgumentParser()
    j = jpegify.JpegifyCommand()
    j.configure_parser(parser)
    args = parser.parse_args(["--dry-run", "."])

    assert args.FOLDER == "."
    assert args.dry_run
    assert args.extension == jpegify.JpegifyCommand.JPEGIFY_EXTENSION

    # Ensure some common args are suppressed
    with pytest.raises(AttributeError):
        args.no_skip_processed
    with pytest.raises(AttributeError):
        args.greater_than

    assert args.originals == commands.OriginalsHandlingEnum.DELETE
    assert args.imagemagick_quality == images.JPEG_QUALITY
    assert args.imagemagick_additional is None
    assert not args.verbose


def test_JpegifyCommand_args_validation():
    with pytest.raises(ValueError):
        c = jpegify.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(JPEGIFY_FOLDER),
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                extension=jpegify.JpegifyCommand.JPEGIFY_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=-5,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = jpegify.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(JPEGIFY_FOLDER),
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                extension=jpegify.JpegifyCommand.JPEGIFY_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=120,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(TypeError):
        c = jpegify.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(JPEGIFY_FOLDER),
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                extension=jpegify.JpegifyCommand.JPEGIFY_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=90,
                imagemagick_additional=True,
                verbose=True,
            )
        )


def test_JpegifyCommand_dry_run():
    c = jpegify.JpegifyCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(JPEGIFY_FOLDER),
            dry_run=True,
            config=str(common.EMPTY_CONFIG),
            extension=jpegify.JpegifyCommand.JPEGIFY_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 11
    assert s.skipped_files_count == 0
    assert s.total_delta_size == 0


def test_JpegifyCommand_core_logic():
    c = jpegify.JpegifyCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(JPEGIFY_FOLDER),
            dry_run=False,
            config=str(common.EMPTY_CONFIG),
            extension=jpegify.JpegifyCommand.JPEGIFY_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 11
    assert s.skipped_files_count == 0

    cleanup_processed_files(s)


# ResizeCommand tests


def test_ResizeCommand_name():
    cmd = resize.ResizeCommand()
    assert cmd.name == "resize"


def test_ResizeCommand_get_common_arguments_defaults():
    cmd = resize.ResizeCommand()
    a, b, c, d = cmd._get_common_arguments_defaults()

    assert a == images.JPEG_EXTENSION
    assert b is None
    assert c is None
    assert d == resize.ResizeCommand.RESIZE_ORIGINALS


def test_ResizeCommand_get_post_processing_strategy(tmp_path):
    cmd = resize.ResizeCommand()
    args = argparse.Namespace(
        originals=commands.OriginalsHandlingEnum.LEAVE, suffix=False, dry_run=False
    )

    # No suffix verification

    p = cmd._get_post_processing_strategy(tmp_path, args)
    assert isinstance(p, processing.NoopPostProcessingStrategy)

    args.originals = commands.OriginalsHandlingEnum.DELETE
    p = cmd._get_post_processing_strategy(tmp_path, args)
    assert isinstance(p, processing.ReplaceOriginalPostProcessignStrategy)

    args.originals = commands.OriginalsHandlingEnum.MOVE
    p = cmd._get_post_processing_strategy(tmp_path, args)
    assert isinstance(p, processing.ReplaceOriginalPostProcessignStrategy)

    # Suffix verification
    args.suffix = True

    args.originals = commands.OriginalsHandlingEnum.LEAVE
    p = cmd._get_post_processing_strategy(tmp_path, args)
    assert isinstance(p, processing.NoopPostProcessingStrategy)

    args.originals = commands.OriginalsHandlingEnum.DELETE
    p = cmd._get_post_processing_strategy(tmp_path, args)
    assert isinstance(p, processing.DeleteOriginalPostProcessingStrategy)

    args.originals = commands.OriginalsHandlingEnum.MOVE
    p = cmd._get_post_processing_strategy(tmp_path, args)
    assert isinstance(p, processing.MoveOriginalPostProcessingStrategy)


def test_ResizeCommand_create_parser():
    parser = argparse.ArgumentParser()
    cmd = resize.ResizeCommand()
    cmd.configure_parser(parser)
    args = parser.parse_args(["--dry-run", "--suffix", "1600", "."])

    assert args.FOLDER == "."
    assert args.SIZE == "1600"
    assert args.dry_run
    assert args.suffix
    assert args.extension == images.JPEG_EXTENSION

    # Ensure some common args are suppressed
    with pytest.raises(AttributeError):
        args.no_skip_processed
    with pytest.raises(AttributeError):
        args.greater_than

    assert args.originals == commands.OriginalsHandlingEnum.DELETE
    assert args.imagemagick_quality == images.JPEG_QUALITY
    assert args.imagemagick_additional is None
    assert not args.verbose


def test_ResizeCommand_args_validation():
    with pytest.raises(AttributeError):
        # SIZE not set
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                suffix=False,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=57,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE=None,
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                suffix=False,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(TypeError):
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE=1280,
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                suffix=False,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=90,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="half",
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                suffix=False,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="-1800",
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                extension=images.JPEG_EXTENSION,
                suffix=False,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="5%%",
                suffix=False,
                config=str(common.EMPTY_CONFIG),
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = resize.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="-5%",
                dry_run=True,
                config=str(common.EMPTY_CONFIG),
                suffix=False,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )


def test_ResizeCommand_dry_run_suffix():
    c = resize.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="50%",
            dry_run=True,
            config=str(common.EMPTY_CONFIG),
            suffix=True,
            extension=images.JPEG_EXTENSION,
            originals=commands.OriginalsHandlingEnum.MOVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    for f in s.processed_files_stats:
        assert f.processed_file.name.endswith(".w50percent.jpg")
    assert s.skipped_files_count == 0
    assert s.total_delta_size == 0


def test_ResizeCommand_dry_run_nosuffix():
    c = resize.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="50%",
            dry_run=True,
            config=str(common.EMPTY_CONFIG),
            suffix=False,
            extension=images.JPEG_EXTENSION,
            originals=commands.OriginalsHandlingEnum.MOVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    for f in s.processed_files_stats:
        assert f.processed_file.name.endswith(".temp.jpg")
    assert s.skipped_files_count == 0
    assert s.total_delta_size == 0


def test_ResizeCommand_core_logic_size_value():
    c = resize.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="900",
            suffix=True,
            dry_run=False,
            config=str(common.EMPTY_CONFIG),
            extension=images.JPEG_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    assert s.skipped_files_count == 0

    target_folder = RESIZE_FOLDER / "w900"
    assert target_folder.exists()
    assert len([f for f in target_folder.iterdir()]) == 5
    for fs in s.processed_files_stats:
        assert fs.processed_file.stem == fs.original_file.stem + ".w900"
        assert fs.processed_file.parent == target_folder

    cleanup_processed_folder(target_folder)
    assert not target_folder.exists()


def test_ResizeCommand_core_logic_size_percent():
    c = resize.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="70%",
            dry_run=False,
            config=str(common.EMPTY_CONFIG),
            suffix=False,
            extension=images.JPEG_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    assert s.skipped_files_count == 0
    assert s.total_delta_size > 0  # With % resize, every file should get smaller.

    target_folder = RESIZE_FOLDER / "w70percent"
    assert target_folder.exists()
    assert len([f for f in target_folder.iterdir()]) == 5
    for fs in s.processed_files_stats:
        assert fs.original_file.stem == fs.processed_file.stem
        assert fs.processed_file.parent == target_folder

    cleanup_processed_folder(target_folder)
    assert not target_folder.exists()
