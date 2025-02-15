import argparse

from . import check
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


def run(cmdline: list[str]) -> None:
    check.ensure_type(cmdline, list)
    parser = create_parser(
        video.VideoFfmpegCommand(),
        images.JpegifyCommand(),
        images.ResizeCommand(),
        rename.SuffixCommand(),
    )
    args = parser.parse_args(cmdline)

    show.set_verbose(args.verbose)
    show.verbose("Launched with the following parameters:")
    show.verbose_args(args, new_line=True)

    args.command(args)
    show.important("FINISHED.")
