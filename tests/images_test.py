import images
import os.path
import pathlib
import processing
import pytest
import show

IMAGE_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/jpegify"


def get_input_file(name: str):
    result = IMAGE_FOLDER / name
    return result.absolute()


def cleanup_output_file(file_path: pathlib.Path):
    file_path.unlink(missing_ok=False)


def cleanup_processed_files():
    for f in IMAGE_FOLDER.glob("*.jpg"):
        f.unlink()


# ImageMagickFileProcessor tests


def test_ImageMagickFileProcessor_input_validation():
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()

    # Null checks
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor(None, None, o, p)
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor(78, None, None, p)
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor(90, None, o, None)
    # Type checks
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor("90", None, o, p)
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor(90, True, o, p)
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor("90", None, 87, p)
    with pytest.raises(TypeError):
        images.ImageMagickFileProcessor("90", None, o, o)
    # Value checks
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor(-10, None, o, p)
    with pytest.raises(ValueError):
        images.ImageMagickFileProcessor(101, None, o, p)
    # Method checks
    i = images.ImageMagickFileProcessor(92, None, o, p)
    with pytest.raises(TypeError):
        i.process("/tmp/video.mp4")
    with pytest.raises(ValueError):
        i.process(None)


def test_ImageMagickFileProcessor_dry_run():
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()
    i = images.ImageMagickFileProcessor(92, None, o, p)

    ii = get_input_file("file_example_PNG_1MB.png")
    assert ii.exists()

    s = i.process(ii, dry_run=True)
    print(s.elapsed)


def real_run(name: str, addl=None):
    o = processing.ChangeExtOutputFilePathStrategy(".jpg")
    p = processing.NoopPostProcessingStrategy()
    i = images.ImageMagickFileProcessor(92, addl, o, p)

    ii = get_input_file(name)
    assert ii.exists()

    s = i.process(ii)

    out = s.processed_file
    assert out.exists()
    assert out.suffix == ".jpg"

    cleanup_output_file(out)


def test_FfmpegFileProcessor_real_run():
    # Set verbose output
    show.set_verbose(True)
    real_run("file_example_PNG_1MB.png")
    real_run("file example WEBP_500kB.webp")  # Test name with spaces
    with pytest.raises(images.ImageMagickRuntimeError):
        real_run("file_example_PNG_1MB.png", "---non -existent ARGUMENT!!!")
