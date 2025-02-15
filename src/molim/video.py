import argparse
import pathlib
import sh

from . import check
from . import commands
from . import processing
from . import show


VIDEO_EXTENSION = ".mp4"
VIDEO_GREATER_THAN = "30M"
VIDEO_NO_SKIP_PROCESSED = False
VIDEO_ORIGINALS = "move"
VIDEO_PROCESSED_SUFFIX = ".min"
VIDEO_PROCESSED_EXTENSION = ".mp4"
VIDEO_FFMPEG_CODEC = "libx265"
VIDEO_FFMPEG_RATE = 26


class VideoFfmpegCommand(commands.Command):
    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        parser.add_argument(
            "--ffmpeg-codec",
            default=VIDEO_FFMPEG_CODEC,
            help="FFMpeg codec to use for processing.",
        )
        parser.add_argument(
            "--ffmpeg-rate",
            default=VIDEO_FFMPEG_RATE,
            type=int,
            help="FFMpeg processing compression rate.",
        )
        parser.add_argument(
            "--ffmpeg-additional",
            default=None,
            help="Additional parameters for FFMpeg processing.",
        )
        parser.add_argument(
            "--ffmpeg-report",
            default=False,
            action="store_true",
            help="Write FFMpeg report with extended conversion information.",
        )
        return parser

    def _get_common_arguments_defaults(self) -> tuple[str, str, str]:
        return (
            VIDEO_EXTENSION,
            VIDEO_GREATER_THAN,
            VIDEO_NO_SKIP_PROCESSED,
            VIDEO_ORIGINALS,
        )

    def _get_output_file_path_strategy(
        self, args: argparse.Namespace
    ) -> processing.OutputFilePathStrategy:
        output_namer = processing.MultiOutputFilePathStrategy(
            [
                processing.SuffixOutputFilePathStrategy(VIDEO_PROCESSED_SUFFIX),
                processing.ChangeExtOutputFilePathStrategy(
                    # Force output extension.
                    VIDEO_PROCESSED_EXTENSION
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

    def _get_file_skip_strategy(
        self, args: argparse.Namespace
    ) -> processing.FileSkipStrategy:
        skips = []
        if not args.no_skip_processed:
            skips.append(processing.BySuffixFileSkipStrategy(".min"))
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


class FfmpegNotFoundError(Exception):
    DEFAULT_MESSAGE = "Could not run ffmpeg command. Check whether FFMpeg is installed on your system and is available on PATH."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


class FfmpegRuntimeError(Exception):
    DEFAULT_MESSAGE = "An error occurred during FFMpeg execution. Exit code: {exit_code}. Command line: '{args}'"

    def __init__(self, e: sh.ErrorReturnCode):
        self.message = FfmpegRuntimeError.DEFAULT_MESSAGE.format(
            exit_code=e.exit_code, args=e.full_cmd
        )
        super().__init__(self.message)


class FfmpegFileProcessor(processing.FileProcessor):
    VERSION_ARGS = ["-version"]

    def __init__(
        self,
        ffmpeg_codec: str,
        ffmpeg_rate: int,
        ffmpeg_additional: str,
        ffmpeg_report: bool,
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(output_strategy, post_processor)
        check.ensure_type(ffmpeg_codec, str)
        check.ensure_int_between(ffmpeg_rate, 0, 51)
        if ffmpeg_additional is not None:
            check.ensure_type(ffmpeg_additional, str)
        check.ensure_type(ffmpeg_report, bool)
        self.__ffmpeg_codec = ffmpeg_codec
        self.__ffmpeg_rate = ffmpeg_rate
        self.__ffmpeg_additional = ffmpeg_additional
        self.__ffmpeg_report = ffmpeg_report
        try:
            # This will fail if there's no ffmpeg command available.
            self.__ffmpeg = sh.ffmpeg
        except sh.CommandNotFound as e:
            raise FfmpegNotFoundError() from e
        try:
            # Run 'ffmpeg -version' to ensure that it is able to launch successfully.
            self.__ffmpeg(*FfmpegFileProcessor.VERSION_ARGS)
        except sh.ErrorReturnCode as e:
            raise FfmpegRuntimeError(e) from e
        self.__args = []

    def _prepare_execution(
        self, file_path: pathlib.Path, output_file_path: pathlib.Path
    ) -> None:
        self.__args = [
            "-y",
            "-i",
            str(file_path),  # Input
            "-vcodec",
            self.__ffmpeg_codec,  # Codec
            "-crf",
            str(self.__ffmpeg_rate),
        ]
        if self.__ffmpeg_additional:
            addl = self.__ffmpeg_additional.split(" ")
            self.__args += addl
        self.__args.append(f"{output_file_path}")  # Output
        if self.__ffmpeg_report:
            self.__args.append("-report")
        cmdline = " ".join(self.__args)
        show.verbose("Running ffmpeg...")
        show.verbose(f"$ ffmpeg {cmdline}")

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        try:
            # ffmpeg -i "$fullpath" -vcodec libx265 -crf 26 "$newpath"
            self.__ffmpeg(*self.__args)
        except sh.ErrorReturnCode as e:
            raise FfmpegRuntimeError(e) from e
