import argparse
import time

from . import commands
from . import images
from . import rename
from . import show
from . import video


def create_parser(*cmds: commands.Command) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molim",
        description="Processing of files for different use cases by commands.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    s = parser.add_subparsers(title="Commands", required=True, dest="command")
    for cmd in cmds:
        p = s.add_parser(
            cmd.name, formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        cmd.configure_parser(parser=p)

    return parser


def run() -> int:
    try:
        parser = create_parser(
            video.VideoFfmpegCommand(),
            images.JpegifyCommand(),
            images.ResizeCommand(),
            rename.SuffixCommand(),
        )
        args = parser.parse_args()

        show.set_verbose(args.verbose)
        show.verbose("Launched with the following parameters:")
        show.verbose_args(args, new_line=True)

        args.command(args)
        time.sleep(20)
        show.important("FINISHED.")
        return 0

    except KeyboardInterrupt:
        show.important("")
        show.rule()
        show.important("Processing interrupted with Ctrl+C, exiting.")
        return 130  # Return code for keyboard interrupt
    except Exception as e:
        show.error("A fatal error occurred during execution.", e)
        return 1
