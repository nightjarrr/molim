import argparse
import check
import commands
import pathlib
import processing
import sh
import show


JPEG_EXTENSION = ".jpg,.jpeg,.JPG"
JPEG_QUALITY = 95
JPEG_PROCESSED_EXTENSION = ".jpg"


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


class JpegifyCommand(commands.Command, ImageMagickMixin):
    JPEGIFY_EXTENSION = ".png,.webp"
    JPEGIFY_ORIGINALS = "delete"

    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        return ImageMagickMixin._add_arguments(self, parser)

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
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
            JPEG_PROCESSED_EXTENSION
        )
        return output_namer

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        return ImageMagickMixin._get_file_processor(
            self, args, output_namer, post_processor
        )

    def _get_file_skip_strategy(
        self, args: argparse.Namespace
    ) -> processing.FileSkipStrategy:
        # Skipping is not applicable for image conversion.
        return processing.NoFileSkipStrategy()

    @property
    def name(self) -> str:
        return "jpegify"


class ResizeCommand(commands.Command, ImageMagickMixin):
    RESIZE_ORIGINALS = "delete"

    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        parser = ImageMagickMixin._add_arguments(self, parser)
        parser.add_argument(
            "SIZE",
            help="Resize images to this size. Size can be an integer value or a percent value. Only images larger than specified size will be resized.",
        )
        parser.add_argument(
            "--suffix",
            default=False,
            action="store_true",
            help="Add size-based suffix to processed files and skip files that already have this suffix.",
        )
        return parser

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
        return (
            JPEG_EXTENSION,
            None,  # Suppress greater-than parameter
            None,  # Suppress no-skip-processed parameter
            ResizeCommand.RESIZE_ORIGINALS,
        )

    def _get_post_processing_strategy(
        self, folder_path: pathlib.Path, args: argparse.Namespace
    ) -> processing.PostProcessingStrategy:
        originals_post_processor = super()._get_post_processing_strategy(
            folder_path, args
        )
        if (args.originals == commands.OriginalsHandlingEnum.LEAVE) or args.suffix:
            # If a suffix will be added, do not rename the processed file back to original name.
            return originals_post_processor
        else:
            return processing.ReplaceOriginalPostProcessignStrategy(
                originals_post_processor
            )

    def _get_size_name(self, size: str) -> str:
        check.ensure_type(size, str)
        if "%" in size:
            return "w" + size.replace("%", "percent")
        else:
            return f"w{size}"

    def _get_resized_subfolder(self, args: argparse.Namespace) -> pathlib.Path:
        original_path = pathlib.Path(args.FOLDER)
        original_path = original_path.absolute()
        subfolder = self._get_size_name(args.SIZE)
        return original_path / subfolder

    def _get_output_file_path_strategy(
        self, args: argparse.Namespace
    ) -> processing.OutputFilePathStrategy:
        out = [processing.ChangeExtOutputFilePathStrategy(JPEG_PROCESSED_EXTENSION)]
        if args.suffix:
            out.append(
                processing.SuffixOutputFilePathStrategy(
                    "." + self._get_size_name(args.SIZE)
                )
            )
        if args.originals == commands.OriginalsHandlingEnum.LEAVE:
            # If original files stay as is, the resized files must go to subfolder.
            resized_subfolder = self._get_resized_subfolder(args)
            out.append(
                processing.FolderOutputFilePathStrategy(resized_subfolder, args.dry_run)
            )
        else:
            if not args.suffix:
                # For MOVE and DELETE handling of original files, create a temp name for processed file.
                # At post-processing stage it will be renamed back to the original name by post-processing strategy.
                out.append(processing.SuffixOutputFilePathStrategy(".temp"))
        return processing.MultiOutputFilePathStrategy(out)

    def _get_imagemagick_args(self, args: argparse.Namespace) -> list[str]:
        imagemagick_args = ImageMagickMixin._get_imagemagick_args(self, args)

        s = args.SIZE
        check.ensure_type(s, str)

        imagemagick_args.append("-resize")
        if s.endswith("%"):
            # Basic validation of supplied % value.
            percent = int(s[:-1])
            check.ensure_int_positive(percent)
            # If the size value is % (e.g., '50%'), just pass it through to ImageMagick.
            imagemagick_args.append(s)
        else:
            size = int(s)  # Otherwise expecting a valid integer value.
            check.ensure_int_positive(size)
            # Set the width and height boundary equal to SIZE and use > modifier to only resize if the image is bigger.
            arg = f"{size}x{size}>"
            imagemagick_args.append(arg)
        return imagemagick_args

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        return ImageMagickMixin._get_file_processor(
            self, args, output_namer, post_processor
        )

    def _get_file_skip_strategy(
        self, args: argparse.Namespace
    ) -> processing.FileSkipStrategy:
        if args.suffix:
            return processing.BySuffixFileSkipStrategy(
                "." + self._get_size_name(args.SIZE)
            )
        # Skipping is not applicable for image conversion.
        return processing.NoFileSkipStrategy()

    @property
    def name(self):
        return "resize"


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
