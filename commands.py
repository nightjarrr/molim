import argparse
import check
import enum
import pathlib
import processing
import show
import stats


class HumanReadableSizeType(object):
    SIZE_NAME = {"K": 1, "M": 2, "G": 3}

    def __call__(self, value: str) -> int:
        check.ensure_type(value, str)
        result = None
        for s in HumanReadableSizeType.SIZE_NAME:
            if value.endswith(s):
                num = float(value[:-1])
                idx = HumanReadableSizeType.SIZE_NAME[s]
                factor = 1024**idx
                result = int(num * factor)
        if result is None:
            # Did not match any suffix, try to convert to regular int. Corresponds to size in bytes.
            result = int(value)
        if result < 0:
            raise ValueError(
                f"Expected non-negative value to be specified. {value} was converted to {result}."
            )
        return result


class OriginalsHandlingEnum(enum.Enum):
    LEAVE = 0
    MOVE = 1
    DELETE = 2


class OriginalsHandlingArgType(object):
    ORIGINALS_HANDLING_OPTIONS = ("leave", "move", "delete")

    def __call__(self, value: str) -> OriginalsHandlingEnum:
        check.ensure_type(value, str)
        i = 0
        for option in OriginalsHandlingArgType.ORIGINALS_HANDLING_OPTIONS:
            if value == option:
                return OriginalsHandlingEnum(i)
            i += 1
        raise ValueError(
            f"{value} is not supported. Choose from {OriginalsHandlingArgType.ORIGINALS_HANDLING_OPTIONS}"
        )


class Command(object):
    """
    Base class for defining command-line interface (CLI) commands.
    This class provides a structure for creating CLI commands with common
    argument parsing and execution logic. Subclasses should implement the
    abstract methods to define specific command behavior.
    Methods:
        _add_common_arguments(parser, default_extension, default_greater_than, default_originals):
            Adds common arguments to the argument parser.
        configure_parser(parser):
            Configures the argument parser with common and command-specific arguments.
        _add_arguments(parser):
            Abstract method to add command-specific arguments to the parser.
        _get_common_arguments_defaults():
            Abstract method to get default values for common arguments.
        _execute(args):
            Abstract method to execute the command with the given arguments.
        name:
            Abstract property to get the name of the command.
        __call__(args):
            Executes the command with the given arguments.
    """

    # Private methods

    def _add_common_arguments(
        self,
        parser: argparse.ArgumentParser,
        default_extension: str,
        default_greater_than: str,
        default_no_skip_processed: bool,
        default_originals: str,
    ) -> argparse.ArgumentParser:
        """
        Add common arguments to the given argparse parser.

        Args:
            parser (argparse.ArgumentParser): The argument parser to which the arguments will be added.
            default_extension (str): The default file extension to process.
            default_greater_than (str): The default size threshold for processing files.
                                        None can be passed to suppress this parameter.
            default_no_skip_processed (bool): The default flag to indicate whether to skip previously processed files.
                                              None can be passed to suppress this parameter.
            default_originals (str): The default handling method for original files after processing.
                                     None can be passed to suppress this parameter.

        Returns:
            argparse.ArgumentParser: The parser with the added arguments.
        """

        parser.add_argument("FOLDER", help="Process files in this folder.")
        parser.add_argument(
            "--dry-run",
            default=False,
            action="store_true",
            help="Execute everything but do not run actual processing commands or modify filesystem.",
        )
        parser.add_argument(
            "--verbose",
            default=False,
            action="store_true",
            help="Enable verbose output.",
        )
        parser.add_argument(
            "--extension",
            default=default_extension,
            help="Process files with this extension.",
        )
        if default_greater_than is not None:
            parser.add_argument(
                "--greater-than",
                default=default_greater_than,
                type=HumanReadableSizeType(),
                help="Process only files greater than this value. Value should be int or float number with size suffix (K, M, G), or without any suffix for bytes.",
            )
        if default_no_skip_processed is not None:
            parser.add_argument(
                "--no-skip-processed",
                default=False,
                action="store_true",
                help="Do not skip previously processed files (detect by suffix) and re-process them again.",
            )
        if default_originals is not None:
            parser.add_argument(
                "--originals",
                default=default_originals,
                type=OriginalsHandlingArgType(),
                help=f"How to handle original files after processing. Available choices: {OriginalsHandlingArgType.ORIGINALS_HANDLING_OPTIONS}",
            )
        return parser

    @property
    def _move_to_subfolder_name(self):
        return "_orig"

    def _get_post_processing_strategy(
        self, originals: OriginalsHandlingEnum, move_to: pathlib.Path, dry_run: bool
    ) -> processing.PostProcessingStrategy:
        if originals == OriginalsHandlingEnum.LEAVE:
            return processing.NoopPostProcessingStrategy()
        elif originals == OriginalsHandlingEnum.MOVE:
            return processing.MoveOriginalPostProcessingStrategy(move_to, dry_run)
        elif originals == OriginalsHandlingEnum.DELETE:
            return processing.DeleteOriginalPostProcessingStrategy()
        raise ValueError(originals)

    def _get_file_match_strategy(self, args: argparse.Namespace):
        return processing.ByExtensionFileMatchStrategy(args.extension)

    def _execute(self, args: argparse.Namespace) -> stats.FolderStats:
        folder_path = pathlib.Path(args.FOLDER)
        check.ensure_folder(folder_path)
        folder_path = folder_path.absolute()

        show.important(
            f"Processing {show.ext(args.extension)} files in folder {folder_path}."
        )

        if args.dry_run:
            show.normal("Dry run mode, no real modifications will be made.")

        output_namer = self._get_output_file_path_strategy(args)

        move_to = folder_path / self._move_to_subfolder_name
        post_processor = self._get_post_processing_strategy(
            args.originals, move_to, args.dry_run
        )

        file_processor = self._get_file_processor(args, output_namer, post_processor)

        matcher = self._get_file_match_strategy(args)
        skipper = self._get_file_skip_strategy(args)

        processor = processing.FolderProcessor(
            folder_path, matcher, skipper, file_processor
        )

        show.rule()
        s = processor.process(dry_run=args.dry_run)
        show.rule()
        show.folder_stats(s)

        return s

    # Public methods

    def configure_parser(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        ext, gt_than, no_skip_processed, originals = (
            self._get_common_arguments_defaults()
        )
        self._add_common_arguments(parser, ext, gt_than, no_skip_processed, originals)
        self._add_arguments(parser)
        # Set the command as a value to be available in the resulting args object
        parser.set_defaults(command=self)
        return parser

    # Abstract methods

    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        raise NotImplementedError()

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
        """
        Abstract methods that descendent classes must implement to provide the default values
        for common parameters or suppress them. The returned tuple consists of the following values:

        default_extension (str): The default file extension to process.
        default_greater_than (str): The default size threshold for processing files.
                                    None can be passed to suppress this parameter.
        default_no_skip_processed (bool): The default flag to indicate whether to skip previously processed files.
                                          None can be passed to suppress this parameter.
        default_originals (str): The default handling method for original files after processing.
        """
        raise NotImplementedError()

    def _get_output_file_path_strategy(
        self, args: argparse.Namespace
    ) -> processing.OutputFilePathStrategy:
        raise NotImplementedError()

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        raise NotImplementedError()

    def _get_file_skip_strategy(
        self, args: argparse.Namespace
    ) -> processing.FileSkipStrategy:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return f"<Command: {self.name}>"

    # Callable

    def __call__(self, args: argparse.Namespace) -> stats.FolderStats:
        check.ensure_type(args, argparse.Namespace)
        return self._execute(args)
