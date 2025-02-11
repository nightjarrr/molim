import argparse
import commands
import images
import os.path
import pathlib
import processing
import pytest
import show
import stats

IMAGE_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/jpegify"


def get_input_file(name: str):
    result = IMAGE_FOLDER / name
    return result.absolute()


def cleanup_output_file(file_path: pathlib.Path):
    file_path.unlink(missing_ok=False)


def cleanup_processed_files(s: stats.FolderStats):
    for ss in s.processed_files_stats:
        ss.processed_file.unlink(missing_ok=True)


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
    assert args.imagemagick_quality == images.JpegifyCommand.JPEGIFY_QUALITY
    assert args.imagemagick_additional is None
    assert not args.verbose


def test_JpegifyCommand_args_validation():
    with pytest.raises(ValueError):
        c = images.JpegifyCommand()
        c(
            argparse.Namespace(
                FOLDER=str(IMAGE_FOLDER),
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
                FOLDER=str(IMAGE_FOLDER),
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
                FOLDER=str(IMAGE_FOLDER),
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
            FOLDER=str(IMAGE_FOLDER),
            dry_run=True,
            extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JpegifyCommand.JPEGIFY_QUALITY,
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
            FOLDER=str(IMAGE_FOLDER),
            dry_run=False,
            extension=images.JpegifyCommand.JPEGIFY_EXTENSION,
            originals=commands.OriginalsHandlingEnum.LEAVE,
            imagemagick_quality=images.JpegifyCommand.JPEGIFY_QUALITY,
            imagemagick_additional=None,
            verbose=True,
        )
    )

    assert s is not None
    assert len(s.processed_files_stats) == 5
    assert s.skipped_files_count == 0

    cleanup_processed_files(s)
