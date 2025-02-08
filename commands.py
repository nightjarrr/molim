import check
import enum
import pathlib
import processing
import show
import stats
import video


class OriginalFilesHandlingEnum(enum.Enum):
    LEAVE = 0
    MOVE = 1
    DELETE = 2


def get_post_processor(
    originals_handling: OriginalFilesHandlingEnum,
) -> processing.PostProcessingStrategy:
    check.ensure_type(originals_handling, OriginalFilesHandlingEnum)
    return processing.NoopPostProcessingStrategy()


def video_ffmpeg_command(
    folder_path: pathlib.Path,
    dry_run: bool,
    video_ext: str,
    skip_processed: bool,
    skip_less_than: int,
    originals_handling: OriginalFilesHandlingEnum,
    ffmpeg_codec: str,
    ffmpeg_rate: int,
    ffmpeg_additional: str,
    ffmpeg_report: bool,
    verbosity: int,
) -> stats.FolderStats:
    check.ensure_folder(folder_path)

    show.important(f"Processing *{video_ext} files in folder {folder_path}.")
    show.rule()

    PROCESSED_SUFFIX = ".min"
    PROCESSED_EXT = ".mp4"
    output_namer = processing.MultiOutputFilePathStrategy(
        [
            processing.SuffixOutputFilePathStrategy(PROCESSED_SUFFIX),
            processing.ChangeExtOutputFilePathStrategy(
                # Force output extension.
                PROCESSED_EXT
            ),
        ]
    )
    post_processor = get_post_processor(originals_handling)

    file_processor = video.FfmpegFileProcessor(
        ffmpeg_codec,
        ffmpeg_rate,
        ffmpeg_additional,
        ffmpeg_report,
        output_namer,
        post_processor,
    )

    matcher = processing.ByExtensionFileMatchStrategy(video_ext)

    skips = []
    if skip_processed:
        skips.append(processing.BySuffixFileSkipStrategy(".min"))
    if skip_less_than:
        skips.append(processing.BySizeFileSkipStrategy(skip_less_than))
    skipper = processing.MultiFileSkipStrategy(skips)

    processor = processing.FolderProcessor(
        folder_path, matcher, skipper, file_processor
    )
    s = processor.process(dry_run=dry_run)
    show.rule()

    if s.processed_files_stats:
        show.important(
            f"Processed {len(s.processed_files_stats)} files ({show.human_size(s.total_original_size)} in total) in {show.elapsed(s.elapsed)}"
        )
        show.important(
            f"New total size: {show.human_size(s.total_processed_size)}, ({show.percent(s.total_original_size, s.total_processed_size)} of original, saved {show.human_size(s.total_delta_size)})",
            new_line=True,
        )

    return s
