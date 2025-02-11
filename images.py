import argparse
import check
import commands
import pathlib
import processing
import sh
import show


class JpegifyCommand(commands.Command):
    JPEGIFY_EXTENSION = ".png,.webp"
    JPEGIFY_ORIGINALS = "delete"
    JPEGIFY_PROCESSED_EXTENSION = ".jpg"
    JPEGIFY_QUALITY = 95

    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        parser.add_argument(
            "--imagemagick-quality",
            default=JpegifyCommand.JPEGIFY_QUALITY,
            type=int,
            help="ImageMagick quality for output JPEG image.",
        )
        parser.add_argument(
            "--imagemagick-additional",
            default=None,
            help="Additional parameters for ImageMagick processing.",
        )
        return parser

    def _get_common_arguments_defaults(self) -> tuple[str, str, str]:
        return (
            JpegifyCommand.JPEGIFY_EXTENSION,
            None,  # Suppress greater-than parameter
            None,  # Suppress no-skip-processed parameter
            JpegifyCommand.JPEGIFY_ORIGINALS,
        )

    def _get_output_file_path_strategy(
        self, args: argparse.Namespace
    ) -> processing.OutputFilePathStrategy:
        output_namer = processing.ChangeExtOutputFilePathStrategy(
            # Force output extension.
            JpegifyCommand.JPEGIFY_PROCESSED_EXTENSION
        )
        return output_namer

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        file_processor = ImageMagickFileProcessor(
            args.imagemagick_quality,
            args.imagemagick_additional,
            output_namer,
            post_processor,
        )
        return file_processor

    def _get_file_skip_strategy(
        self, args: argparse.Namespace
    ) -> processing.FileSkipStrategy:
        # Skipping is not applicable for image conversion.
        return processing.NoFileSkipStrategy()

    @property
    def name(self) -> str:
        return "jpegify"


class ImageMagickNotFoundError(Exception):
    DEFAULT_MESSAGE = "Could not run convert command. Check whether ImageMagick is installed on your system and is available on PATH."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


class ImageMagickRuntimeError(Exception):
    DEFAULT_MESSAGE = "An error occurred during ImageMagick execution. Exit code: {exit_code}. Command line: '{args}'"

    def __init__(self, e: sh.ErrorReturnCode):
        self.message = ImageMagickRuntimeError.DEFAULT_MESSAGE.format(
            exit_code=e.exit_code, args=e.full_cmd
        )
        super().__init__(self.message)


class ImageMagickFileProcessor(processing.FileProcessor):
    VERSION_ARGS = ["-version"]

    def __init__(
        self,
        imagemagick_quality: int,
        imagemagick_additional: str,
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(output_strategy, post_processor)
        check.ensure_int_between(imagemagick_quality, 1, 100)
        if imagemagick_additional is not None:
            check.ensure_type(imagemagick_additional, str)
        self.__imagemagick_quality = imagemagick_quality
        self.__imagemagick_additional = imagemagick_additional
        try:
            # This will fail if there's no convert command available.
            self.__convert = sh.convert
        except sh.CommandNotFound as e:
            raise ImageMagickNotFoundError() from e
        try:
            # Run 'convert -version' to ensure that it is able to launch successfully.
            self.__convert(*ImageMagickFileProcessor.VERSION_ARGS)
        except sh.ErrorReturnCode as e:
            raise ImageMagickRuntimeError(e) from e
        self.__args = []

    def _prepare_execution(
        self, file_path: pathlib.Path, output_file_path: pathlib.Path
    ) -> None:
        self.__args = [
            str(file_path),  # Input
            "-quality",
            str(self.__imagemagick_quality),
        ]
        if self.__imagemagick_additional:
            addl = self.__imagemagick_additional.split(" ")
            self.__args += addl
        self.__args.append(f"{output_file_path}")  # Output
        cmdline = " ".join(self.__args)
        show.verbose("Running ImageMagick...")
        show.verbose(f"$ convert {cmdline}")

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        try:
            # convert
            self.__convert(*self.__args)
        except sh.ErrorReturnCode as e:
            raise ImageMagickRuntimeError(e) from e
