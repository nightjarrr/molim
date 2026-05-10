import argparse
import pathlib

from . import check, commands, processing, shell


class VideoFfmpegCommand(commands.Command):
    EXTENSION = ".mp4"
    GREATER_THAN = "30M"
    NO_SKIP_PROCESSED = False
    ORIGINALS = "move"
    VIDEO_PROCESSED_SUFFIX = ".min"
    VIDEO_PROCESSED_EXTENSION = ".mp4"
    VIDEO_FFMPEG_CODEC = "libx265"
    VIDEO_FFMPEG_RATE = 26
    VIDEO_FFMPEG_ADDITIONAL = None
    VIDEO_FFMPEG_REPORT = False

    def _add_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser.add_argument(
            "--ffmpeg-codec",
            default=VideoFfmpegCommand.VIDEO_FFMPEG_CODEC,
            help="FFMpeg codec to use for processing.",
        )
        parser.add_argument(
            "--ffmpeg-rate",
            default=VideoFfmpegCommand.VIDEO_FFMPEG_RATE,
            type=int,
            help="FFMpeg processing compression rate.",
        )
        parser.add_argument(
            "--ffmpeg-additional",
            default=VideoFfmpegCommand.VIDEO_FFMPEG_ADDITIONAL,
            help="Additional parameters for FFMpeg processing.",
        )
        parser.add_argument(
            "--ffmpeg-report",
            default=VideoFfmpegCommand.VIDEO_FFMPEG_REPORT,
            action="store_true",
            help="Write FFMpeg report with extended conversion information.",
        )
        return parser

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
        return (
            VideoFfmpegCommand.EXTENSION,
            VideoFfmpegCommand.GREATER_THAN,
            VideoFfmpegCommand.NO_SKIP_PROCESSED,
            VideoFfmpegCommand.ORIGINALS,
        )

    def _get_output_file_path_strategy(self, args: argparse.Namespace) -> processing.OutputFilePathStrategy:
        output_namer = processing.MultiOutputFilePathStrategy(
            [
                processing.SuffixOutputFilePathStrategy(VideoFfmpegCommand.VIDEO_PROCESSED_SUFFIX),
                processing.ChangeExtOutputFilePathStrategy(
                    # Force output extension.
                    VideoFfmpegCommand.VIDEO_PROCESSED_EXTENSION
                ),
            ]
        )
        return output_namer

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        file_processor = FfmpegFileProcessor(
            args.ffmpeg_codec,
            args.ffmpeg_rate,
            args.ffmpeg_additional,
            args.ffmpeg_report,
            output_namer,
            post_processor,
        )
        return file_processor

    def _get_file_skip_strategy(self, args: argparse.Namespace) -> processing.FileSkipStrategy:
        skips = []
        if not args.no_skip_processed:
            skips.append(processing.BySuffixFileSkipStrategy(VideoFfmpegCommand.VIDEO_PROCESSED_SUFFIX))
        if args.greater_than:
            skips.append(processing.BySizeFileSkipStrategy(args.greater_than))
        skipper = processing.MultiFileSkipStrategy(skips)
        return skipper

    @property
    def name(self) -> str:
        return "video"

    @property
    def help(self) -> str:
        return "Process and optimize video files using FFMpeg."


class FfmpegFileProcessor(shell.ShellCommandFileProcessor):
    VERSION_ARGS = ["-version"]

    def __init__(
        self,
        ffmpeg_codec: str,
        ffmpeg_rate: int,
        ffmpeg_additional: str,
        ffmpeg_report: bool,
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> None:
        check.ensure_type(ffmpeg_codec, str)
        check.ensure_int_between(ffmpeg_rate, 0, 51)
        check.ensure_type_or_none(ffmpeg_additional, str)
        check.ensure_type(ffmpeg_report, bool)

        args = [
            "-vcodec",
            ffmpeg_codec,  # Codec
            "-crf",
            str(ffmpeg_rate),
        ]
        if ffmpeg_additional:
            addl = ffmpeg_additional.split(" ")
            args += addl
        if ffmpeg_report:
            args.append("-report")
        super().__init__(
            "FFMpeg",
            "ffmpeg",
            *args,
            output_strategy=output_strategy,
            post_processor=post_processor,
        )

    def _get_verify_args(self) -> list[str]:
        return FfmpegFileProcessor.VERSION_ARGS

    def _finalize_args(
        self,
        initial_args: list[str],
        file_path: pathlib.Path,
        output_file_path: pathlib.Path,
    ) -> list[str]:
        args = ["-y", "-i", str(file_path)]
        args += initial_args
        args.append(str(output_file_path))  # Output
        # ffmpeg -i "$fullpath" -vcodec libx265 -crf 26 "$newpath"
        return args
