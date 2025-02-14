import argparse
import commands
import images
import os.path
import pathlib
import processing
import pytest
import show
import stats

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
        images.ImageMagickFileProcessor(
            None, "None", output_strategy=o, post_processor=p
        )
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor("78", output_strategy=None, post_processor=p)
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor("90", output_strategy=o, post_processor=None)
    # Type checks
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor(90, output_strategy=o, post_processor=p)
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor("90", True, output_strategy=o, post_processor=p)
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor("90", output_strategy=87, post_processor=p)
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor("90", output_strategy=o, post_processor=o)
    # Method checks
    i = images.ImageMagickFileProcessor("92", output_strategy=o, post_processor=p)
    with pytest.raises(TypeError):
        i.process("/tmp/video.mp4")
    with pytest.raises(ValueError):
        i.process(None)


def test_ImageMagickFileProcessor_dry_run():
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()
    i = images.ImageMagickFileProcessor(
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
    i = images.ImageMagickFileProcessor(*cmdln, output_strategy=o, post_processor=p)

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
    with pytest.raises(images.ImageMagickRuntimeError):
        real_run("file_example_PNG_1MB.png", "---non -existent ARGUMENT!!!")


# JpegifyCommand tests


def test_JpegifyCommand_name():
    j = images.JpegifyCommand()
    assert j.name == "jpegify"


def test_JpegifyCommand_get_common_arguments_defaults():
    j = images.JpegifyCommand()
    a, b, c, d = j._get_common_arguments_defaults()

    assert a == images.JpegifyCommand.JPEGIFY_EXTENSION
    assert b is None
    assert c is None
    assert d == images.JpegifyCommand.JPEGIFY_ORIGINALS


def test_JpegifyCommand_create_parser():
    parser = argparse.ArgumentParser()
    j = images.JpegifyCommand()
    j.configure_parser(parser)
    args = parser.parse_args(["--dry-run", "."])

    assert args.FOLDER == "."
    assert args.dry_run
    assert args.extension == images.JpegifyCommand.JPEGIFY_EXTENSION

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
        c = images.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(JPEGIFY_FOLDER),
                dry_run=True,
                extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=-5,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = images.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(JPEGIFY_FOLDER),
                dry_run=True,
                extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=120,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(TypeError):
        c = images.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(JPEGIFY_FOLDER),
                dry_run=True,
                extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=90,
                imagemagick_additional=True,
                verbose=True,
            )
        )


def test_JpegifyCommand_dry_run():
    c = images.JpegifyCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(JPEGIFY_FOLDER),
            dry_run=True,
            extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    assert s.skipped_files_count == 0
    assert s.total_delta_size == 0


def test_JpegifyCommand_core_logic():
    c = images.JpegifyCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(JPEGIFY_FOLDER),
            dry_run=False,
            extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JPEG_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    assert s.skipped_files_count == 0

    cleanup_processed_files(s)


# ResizeCommand tests


def test_ResizeCommand_name():
    cmd = images.ResizeCommand()
    assert cmd.name == "resize"


def test_ResizeCommand_get_common_arguments_defaults():
    cmd = images.ResizeCommand()
    a, b, c, d = cmd._get_common_arguments_defaults()

    assert a == images.JPEG_EXTENSION
    assert b is None
    assert c is None
    assert d == images.ResizeCommand.RESIZE_ORIGINALS


def test_ResizeCommand_create_parser():
    parser = argparse.ArgumentParser()
    cmd = images.ResizeCommand()
    cmd.configure_parser(parser)
    args = parser.parse_args(["--dry-run", "1600", "."])

    assert args.FOLDER == "."
    assert args.SIZE == "1600"
    assert args.dry_run
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
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=57,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE=None,
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(TypeError):
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE=1280,
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=90,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="half",
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="-1800",
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="5%%",
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )
    with pytest.raises(ValueError):
        c = images.ResizeCommand()
        c(
            argparse.Namespace(
                FOLDER=str(RESIZE_FOLDER),
                SIZE="-5%",
                dry_run=True,
                extension=images.JPEG_EXTENSION,
                originals=commands.OriginalsHandlingEnum.LEAVE,
                imagemagick_quality=80,
                imagemagick_additional=None,
                verbose=True,
            )
        )


def test_ResizeCommand_dry_run():
    c = images.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="50%",
            dry_run=True,
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
    c = images.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="900",
            dry_run=False,
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
        assert fs.original_file.stem == fs.processed_file.stem
        assert fs.processed_file.parent == target_folder

    cleanup_processed_folder(target_folder)
    assert not target_folder.exists()


def test_ResizeCommand_core_logic_size_percent():
    c = images.ResizeCommand()
    s = c(
        argparse.Namespace(
            FOLDER=str(RESIZE_FOLDER),
            SIZE="70%",
            dry_run=False,
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
