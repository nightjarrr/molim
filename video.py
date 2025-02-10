import argparse
import check
import commands
import pathlib
import processing
import sh
import show


VIDEO_EXTENSION = ".mp4"
VIDEO_GREATER_THAN = "30M"
VIDEO_ORIGINALS = "leave"
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
        return (VIDEO_EXTENSION, VIDEO_GREATER_THAN, VIDEO_ORIGINALS)

    @property
    def name(self) -> str:
        return "video"

    def _execute(self, args: argparse.Namespace) -> None:
        folder_path = pathlib.Path(args.FOLDER)
        check.ensure_folder(folder_path)
        folder_path = folder_path.absolute()

        show.important(f"Processing *{args.extension} files in folder {folder_path}.")

        if args.dry_run:
            show.normal("Dry run mode, no real modifications will be made.")

        output_namer = processing.MultiOutputFilePathStrategy(
            [
                processing.SuffixOutputFilePathStrategy(VIDEO_PROCESSED_SUFFIX),
                processing.ChangeExtOutputFilePathStrategy(
                    # Force output extension.
                    VIDEO_PROCESSED_EXTENSION
                ),
            ]
        )

        move_to = folder_path / "_orig"
        post_processor = self._get_post_processing_strategy(args.originals, move_to, args.dry_run)

        file_processor = FfmpegFileProcessor(
            args.ffmpeg_codec,
            args.ffmpeg_rate,
            args.ffmpeg_additional,
            args.ffmpeg_report,
            output_namer,
            post_processor,
        )

        matcher = processing.ByExtensionFileMatchStrategy(args.extension)

        skips = []
        if not args.no_skip_processed:
            skips.append(processing.BySuffixFileSkipStrategy(".min"))
        if args.greater_than:
            skips.append(processing.BySizeFileSkipStrategy(args.greater_than))
        skipper = processing.MultiFileSkipStrategy(skips)

        processor = processing.FolderProcessor(
            folder_path, matcher, skipper, file_processor
        )

        show.rule()
        s = processor.process(dry_run=args.dry_run)
        show.rule()

        if s.processed_files_stats:
            show.important(
                f"Processed {len(s.processed_files_stats)} files in {show.elapsed(s.elapsed)}"
            )
            show.important(
                f"{show.human_size(s.total_original_size)} \u2192 {show.human_size(s.total_processed_size)}, new size {show.percent(s.total_original_size, s.total_processed_size)} of original, saved {show.human_size(s.total_delta_size)}",
                new_line=True,
            )
        return s


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

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        try:
            # ffmpeg -i "$fullpath" -vcodec libx265 -crf 26 "$newpath"
            self.__ffmpeg(*self.__args)
        except sh.ErrorReturnCode as e:
            raise FfmpegRuntimeError(e) from e
