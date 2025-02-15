from . import cli
from . import show


def main() -> int:
    try:
        cli.run()
        return 0
    except KeyboardInterrupt:
        show.important("")
        show.rule()
        show.important("Processing interrupted with Ctrl+C, exiting.")
        return 130  # Return code for keyboard interrupt
    except Exception as e:
        show.error("A fatal error occurred during execution.", e)
        return 1
