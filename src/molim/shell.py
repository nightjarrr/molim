import pathlib
import sh

from . import check
from . import processing
from . import show


class ShellCommandNotFoundError(Exception):
    MESSAGE = (
        "Could not run '{cmdline}' command. "
        "Check whether {name} is installed on your system and is available on PATH."
    )

    def __init__(self, cmdline: str, name: str):
        self.message = ShellCommandNotFoundError.MESSAGE.format(
            cmdline=cmdline, name=name
        )
        super().__init__(self.message)


class ShellCommandRuntimeError(Exception):
    MESSAGE = (
        "An error occurred during {name} execution. "
        "Exit code: {exit_code}. Command line: '{args}'"
    )

    def __init__(self, name: str, e: sh.ErrorReturnCode):
        self.message = ShellCommandRuntimeError.MESSAGE.format(
            name=name, exit_code=e.exit_code, args=e.full_cmd
        )
        super().__init__(self.message)


class ShellCommandFileProcessor(processing.FileProcessor):
    def __init__(
        self,
        name: str,
        command: str,
        *command_args: str,  # All args except for input and output file.
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        super().__init__(output_strategy, post_processor)
        check.ensure_not_none(command_args)
        for a in command_args:
            check.ensure_type(a, str)
        self.__command_args = command_args
        try:
            # This will fail if there's no such command available.
            self.__command = sh.Command(command)
            self.__command_line = command
            self.__command_name = name
        except sh.CommandNotFound as e:
            raise ShellCommandNotFoundError(command, name) from e
        try:
            # Run test command (usually a -v or -version) to ensure that it is able to launch successfully.
            a = self._get_verify_args()
            self.__command(*a)
        except sh.ErrorReturnCode as e:
            raise ShellCommandRuntimeError(name, e) from e
        self.__args = []

    # Private methods

    def _get_verify_args(self) -> list[str]:
        return []

    def _prepare_execution(
        self, file_path: pathlib.Path, output_file_path: pathlib.Path
    ) -> None:
        self.__args = self._finalize_args(
            self.__command_args, file_path, output_file_path
        )
        cmdline = " ".join(self.__args)
        show.verbose(f"Running {self.__command_name}...")
        show.verbose(f"$ {self.__command_line} {cmdline}")

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        try:
            # convert
            self.__command(*self.__args)
        except sh.ErrorReturnCode as e:
            raise ShellCommandRuntimeError(self.__command_name, e) from e

    # Abstract methods

    def _finalize_args(
        self,
        initial_args: list[str],
        file_path: pathlib.Path,
        output_file_path: pathlib.Path,
    ) -> list[str]:
        raise NotImplementedError()
