import argparse

from . import check
from . import commands
from . import images
from . import rename
from . import show
from . import video


def _create_parser(*cmds: commands.Command) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molim",
        description="Processing of files for different use cases by commands.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sorted_cmds = sorted(cmds, key=lambda c: c.name)
    metavar = "[ " + " | ".join([c.name for c in sorted_cmds]) + " ]"
    s = parser.add_subparsers(
        title="Supported commands", required=True, dest="command", metavar=metavar
    )
    for cmd in sorted_cmds:
        p = s.add_parser(
            cmd.name,
            help=cmd.help,
            description=cmd.help,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        cmd.configure_parser(parser=p)

    return parser


def run(cmdline: list[str]) -> None:
    check.ensure_type(cmdline, list)
    parser = _create_parser(
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
