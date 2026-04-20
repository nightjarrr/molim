import sys

from . import cli, show


def main() -> int:
    try:
        args = sys.argv[1:]
        cli.run(args)
        return 0
    except KeyboardInterrupt:
        show.important("")
        show.rule()
        show.important("Processing interrupted with Ctrl+C.")
        return 130  # Return code for keyboard interrupt
    except Exception as e:
        show.error("A fatal error occurred during execution.", e)
        return 1
