import argparse
import pathlib

from . import commands
from . import processing
from . import show


class SuffixCommand(commands.Command):
    def _add_arguments(
        self, parser: argparse.ArgumentParser
    ) -> argparse.ArgumentParser:
        parser.add_argument(
            "SUFFIX",
            help="Add this suffix to all matched files.",
        )
        return parser

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
        return (
            commands.ANY_MATCH_EXTENSION,
            None,  # Suppress greater-than parameter
            None,  # Suppress no-skip-processed parameter
            None,  # Suppress originals parameter
        )

    def _get_post_processing_strategy(
        self, folder_path: pathlib.Path, args: argparse.Namespace
    ) -> processing.PostProcessingStrategy:
        return processing.NoopPostProcessingStrategy()

    def _get_output_file_path_strategy(
        self, args: argparse.Namespace
    ) -> processing.OutputFilePathStrategy:
        return processing.SuffixOutputFilePathStrategy(args.SUFFIX)

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        return RenameFileProcessor(
            output_strategy=output_namer, post_processor=post_processor
        )

    def _get_file_skip_strategy(
        self, args: argparse.Namespace
    ) -> processing.FileSkipStrategy:
        return processing.BySuffixFileSkipStrategy(args.SUFFIX)

    @property
    def _show_size(self):
        return False

    @property
    def name(self) -> str:
        return "suffix"

    @property
    def help(self) -> str:
        return "Add a suffix to file names."


class RenameFileProcessor(processing.FileProcessor):
    def __init__(
        self,
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(output_strategy, post_processor)

    def _prepare_execution(
        self, file_path: pathlib.Path, output_file_path: pathlib.Path
    ) -> None:
        show.verbose(f"Renaming {file_path.name} to {output_file_path.name}.")

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        file_path.rename(output_file_path)
