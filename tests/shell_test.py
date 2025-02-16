import pytest

from molim import processing
from molim import shell

# ShellCommandFileProcessor tests


def test_ShellCommandFileProcessor_command_not_found():
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()

    with pytest.raises(shell.ShellCommandNotFoundError):
        shell.ShellCommandFileProcessor(
            "Super Duper Program",
            "but-it-does-not-exist.exe",
            output_strategy=o,
            post_processor=p,
        )


def test_ShellCommandFileProcessor_command_failed_verification():
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()

    with pytest.raises(shell.ShellCommandRuntimeError):
        # mv will fail with exis code 1 when launched without arguments
        # which is the default verification args for ShellCommandFileProcessor
        shell.ShellCommandFileProcessor(
            "Move",
            "mv",
            output_strategy=o,
            post_processor=p,
        )


def test_ShellCommandFileProcessor_command_successfully_initialized():
    o = processing.SuffixOutputFilePathStrategy(".min")
    p = processing.NoopPostProcessingStrategy()

    c = shell.ShellCommandFileProcessor(
        "Echo",
        "echo",
        output_strategy=o,
        post_processor=p,
    )
    assert c is not None
