import argparse
import pathlib
import sh

from .. import check
from .. import processing
from .. import show

from . import JPEG_QUALITY


class ImageMagickMixin(object):
    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        parser.add_argument(
            "--imagemagick-quality",
            default=JPEG_QUALITY,
            type=int,
            help="ImageMagick quality for output JPEG image.",
        )
        parser.add_argument(
            "--imagemagick-additional",
            default=None,
            help="Additional parameters for ImageMagick processing.",
        )
        return parser

    def _get_imagemagick_args(self, args: argparse.Namespace) -> list[str]:
        check.ensure_int_between(args.imagemagick_quality, 1, 100)
        if args.imagemagick_additional is not None:
            check.ensure_type(args.imagemagick_additional, str)
        cmdline = ["-quality", str(args.imagemagick_quality)]
        if args.imagemagick_additional is not None:
            cmdline += args.imagemagick_additional.split(" ")
        return cmdline

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        cmdline = self._get_imagemagick_args(args)
        file_processor = ImageMagickFileProcessor(
            *cmdline,
            output_strategy=output_namer,
            post_processor=post_processor,
        )
        return file_processor


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
        *imagemagick_args: str,  # All args except for input and output file.
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(output_strategy, post_processor)
        check.ensure_not_none(imagemagick_args)
        for a in imagemagick_args:
            check.ensure_type(a, str)
        self.__imagemagick_args = imagemagick_args
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
        self.__args = [str(file_path)]
        self.__args += self.__imagemagick_args
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
