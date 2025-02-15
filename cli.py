import argparse
import commands
import images
import rename
import show
import sys
import video


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


if __name__ == "__main__":
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
        show.important("FINISHED.")

    except Exception as e:
        show.error("A fatal error occurred during execution.", e)
        sys.exit(1)
