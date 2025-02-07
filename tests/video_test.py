import os.path
import pathlib
import processing
import pytest
import video

VIDEO_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/video"


def get_input_file(name: str):
    result = VIDEO_FOLDER / name
    return result.absolute()


def cleanup_output_file(file_path: pathlib.Path):
    file_path.unlink(missing_ok=False)


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
    with pytest.raises(video.FfmpegRuntimeError):
        real_run("sample_720x480_1mb.mp4", "---non -existent ARGUMENT!!!")
