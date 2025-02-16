import argparse
import pathlib

from .. import check
from .. import processing
from .. import shell

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


class ImageMagickFileProcessor(shell.ShellCommandFileProcessor):
    VERSION_ARGS = ["-version"]

    def __init__(
        self,
        *imagemagick_args: str,  # All args except for input and output file.
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(
            "ImageMagick",
            "convert",
            *imagemagick_args,
            output_strategy=output_strategy,
            post_processor=post_processor,
        )

    def _get_verify_args(self) -> list[str]:
        return ImageMagickFileProcessor.VERSION_ARGS

    def _finalize_args(
        self,
        initial_args: list[str],
        file_path: pathlib.Path,
        output_file_path: pathlib.Path,
    ) -> list[str]:
        args = [str(file_path)]
        args += initial_args
        args.append(str(output_file_path))  # Output
        return args
