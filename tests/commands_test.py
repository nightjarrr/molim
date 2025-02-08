import os.path
import pathlib
import commands

VIDEO_FOLDER = pathlib.Path(os.path.dirname(__file__)) / "data/video"


def cleanup_processed_files():
    for f in VIDEO_FOLDER.glob("*.min.mp4"):
        f.unlink()


def test_video_ffmpeg_command():
    s = commands.video_ffmpeg_command(
        VIDEO_FOLDER,
        dry_run=False,
        video_ext=".mp4",
        skip_processed=True,
        skip_less_than=500 * 1024,
        originals_handling=commands.OriginalFilesHandlingEnum.LEAVE,
        ffmpeg_codec="libx265",
        ffmpeg_rate=27,
        ffmpeg_additional=None,
        ffmpeg_report=False,
        verbosity=4,
    )
    assert s is not None
    assert len(s.processed_files_stats) == 2
    assert s.skipped_files_count == 1
    assert s.total_delta_size > 0

    cleanup_processed_files()
