import argparse

from .. import commands, processing
from . import JPEG_PROCESSED_EXTENSION
from .imagemagick import ImageMagickMixin


class JpegifyCommand(commands.Command, ImageMagickMixin):
    JPEGIFY_EXTENSION = ".png,.webp,.avif,.heic"
    JPEGIFY_ORIGINALS = "delete"

    def _add_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        return ImageMagickMixin._add_arguments(self, parser)

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
        return (
            JpegifyCommand.JPEGIFY_EXTENSION,
            None,  # Suppress greater-than parameter
            None,  # Suppress no-skip-processed parameter
            JpegifyCommand.JPEGIFY_ORIGINALS,
        )

    def _get_output_file_path_strategy(self, args: argparse.Namespace) -> processing.OutputFilePathStrategy:
        output_namer = processing.ChangeExtOutputFilePathStrategy(
            # Force output extension.
            JPEG_PROCESSED_EXTENSION
        )
        return output_namer

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        return ImageMagickMixin._get_file_processor(self, args, output_namer, post_processor)

    def _get_file_skip_strategy(self, args: argparse.Namespace) -> processing.FileSkipStrategy:
        # Skipping is not applicable for image conversion.
        return processing.NoFileSkipStrategy()

    @property
    def name(self) -> str:
        return "jpegify"

    @property
    def help(self) -> str:
        return "Convert images of other formats into JPEG using ImageMagick."
