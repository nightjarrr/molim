import argparse
import commands
import pathlib
import show
import sys

ORIGINAL_HANDLING_OPTIONS = ("leave", "move", "delete")


class HumanReadableSizeType(object):
    def __call__(self, string):
        size_name = {"K": 1, "M": 2, "G": 3}
        for s in size_name:
            if string.endswith(s):
                num = int(string[:-1])
                idx = size_name[s]
                factor = 1024**idx
                return num * factor
        raise ValueError(string)


def add_common_arguments(
    parser: argparse.ArgumentParser,
    default_extension: str,
    default_greater_than: int,
    default_originals: str,
) -> argparse.ArgumentParser:
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
    parser.add_argument(
        "--greater-than",
        default=default_greater_than,
        type=HumanReadableSizeType(),
        help="Process only files greater than this valye. Value shoult be int number with size suffix (K, M, G).",
    )
    parser.add_argument(
        "--no-skip-processed",
        default=False,
        action="store_true",
        help="Do not skip previously processed files (detect by suffix) and re-process them again.",
    )
    parser.add_argument(
        "--originals",
        choices=ORIGINAL_HANDLING_OPTIONS,
        default="leave",
        help="How to handle original files after processing.",
    )
    return parser


VIDEO_EXTENSION = ".mp4"
VIDEO_GREATER_THAN = "30M"
VIDEO_ORIGINALS = "leave"
VIDEO_FFMPEG_CODEC = "libx265"
VIDEO_FFMPEG_RATE = 26


def create_video_arguments(parser: argparse.ArgumentParser):
    parser = add_common_arguments(
        parser, VIDEO_EXTENSION, VIDEO_GREATER_THAN, VIDEO_ORIGINALS
    )
    parser.add_argument(
        "--ffmpeg-codec",
        default=VIDEO_FFMPEG_CODEC,
        help="FFMpeg codec to use for processing.",
    )
    parser.add_argument(
        "--ffmpeg-rate",
        default=VIDEO_FFMPEG_RATE,
        type=int,
        help="FFMpeg processing compression rate.",
    )
    parser.add_argument(
        "--ffmpeg-additional",
        default=None,
        help="Additional parameters for FFMpeg processing.",
    )
    parser.add_argument(
        "--ffmpeg-report",
        default=False,
        action="store_true",
        help="Write FFMpeg report with extended conversion information.",
    )
    return parser


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="do",
        description="Processing of files for different use cases.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    s = parser.add_subparsers(title="Commands", required=True, dest="command")
    v = s.add_parser("video", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    create_video_arguments(v)

    return parser


if __name__ == "__main__":
    try:
        parser = create_parser()
        args = parser.parse_args()

        show.set_verbose(args.verbose)
        show.verbose("Launched with the following parameters:")
        show.verbose_args(args, new_line=True)

        folder = pathlib.Path(args.FOLDER)
        folder = folder.absolute()

        if args.command == "video":
            commands.video_ffmpeg_command(
                folder,
                dry_run=args.dry_run,
                video_ext=args.extension,
                skip_processed=not args.no_skip_processed,
                skip_less_than=args.greater_than,
                originals_handling=commands.OriginalFilesHandlingEnum.LEAVE,
                ffmpeg_codec=args.ffmpeg_codec,
                ffmpeg_rate=args.ffmpeg_rate,
                ffmpeg_additional=args.ffmpeg_additional,
                ffmpeg_report=args.ffmpeg_report,
                verbose=args.verbose,
            )
        else:
            show.important(f"Command {args.command} not supported yet.", new_line=True)

        show.important("FINISHED.")
    except Exception as e:
        show.error("A fatal error occurred during execution.", e)
        sys.exit(1)
