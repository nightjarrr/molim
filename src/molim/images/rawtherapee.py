import argparse
import pathlib

from .. import check, commands, processing, shell, show
from . import JPEG_EXTENSION, JPEG_PROCESSED_EXTENSION, JPEG_QUALITY

RAWTHERAPEE_PROFILE_FOLDER = pathlib.Path("~/.config/RawTherapee/profiles")
RAWTHERAPEE_PROFILE_EXTENSION = ".pp3"
RAWTHERAPEE_DEFAULT_PROFILE = "molim"


class RawTherapeeCommand(commands.Command):
    GREATER_THAN = "2M"
    NO_SKIP_PROCESSED = False
    ORIGINALS = "move"
    PROCESSED_SUFFIX = ".m"
    JPEG_QUALITY_80 = 80
    JPEG_SUBSAMPLING_2 = 2

    def _get_quality_defaults(self) -> tuple[int, int]:
        return (
            RawTherapeeCommand.JPEG_QUALITY_80,
            RawTherapeeCommand.JPEG_SUBSAMPLING_2,
        )

    def _add_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        parser.add_argument(
            "--profile-folder",
            default=None,
            help=(
                "Location of RawTherapee profiles to use for processing. "
                "If not specified as an argument or in configuration file, "
                f"{RAWTHERAPEE_PROFILE_FOLDER} will be used."
            ),
        )
        parser.add_argument(
            "--profile",
            default=None,
            help=(
                "Name of RawTherapee profile to use for processing. "
                "Name does not have the file extension, i.e., default and not default.pp3"
                "If not specified as an argument or in configuration file, "
                f"'{RAWTHERAPEE_DEFAULT_PROFILE}' will be used."
            ),
        )

        j, js = self._get_quality_defaults()
        parser.add_argument(
            "--quality",
            default=j,
            type=int,
            help=(
                "Processed JPEG file quality parameter, can take values between 1 and 100 "
                "(corresponds to RawTherapee CLI -j<VALUE> option)."
            ),
        )
        parser.add_argument(
            "--subsampling",
            default=js,
            type=int,
            choices=(1, 2, 3),
            help=("Processed JPEG file chroma subsampling parameter (corresponds to RawTherapee CLI -js<VALUE> option)."),
        )
        parser.add_argument(
            "--processed-subfolder",
            default=None,
            help=(
                "Create processed files in subfolder with this name. "
                "If this parameter is not specified, processed files "
                "will be created in the original folder."
            ),
        )
        return parser

    def _get_common_arguments_defaults(self) -> tuple[str, str, bool, str]:
        return (
            JPEG_EXTENSION,
            RawTherapeeCommand.GREATER_THAN,
            RawTherapeeCommand.NO_SKIP_PROCESSED,
            RawTherapeeCommand.ORIGINALS,
        )

    def _get_output_file_path_strategy(self, args: argparse.Namespace) -> processing.OutputFilePathStrategy:
        ext = processing.ChangeExtOutputFilePathStrategy(JPEG_PROCESSED_EXTENSION)
        suffix = processing.SuffixOutputFilePathStrategy(RawTherapeeCommand.PROCESSED_SUFFIX)
        out = [ext, suffix]
        if args.processed_subfolder is not None:
            original_path = pathlib.Path(args.FOLDER).absolute()
            output_folder = original_path / args.processed_subfolder
            out.append(processing.FolderOutputFilePathStrategy(output_folder, args.dry_run))
        return processing.MultiOutputFilePathStrategy(out)

    def _get_file_processor(
        self,
        args: argparse.Namespace,
        output_namer: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ) -> processing.FileProcessor:
        # Getting RawTherapee profile
        profile_folder = (
            pathlib.Path(args.profile_folder or self._get_config_value("profile-folder") or RAWTHERAPEE_PROFILE_FOLDER)
            .expanduser()
            .absolute()
        )
        check.ensure_folder(profile_folder)

        profile = args.profile or self._get_config_value("profile") or RAWTHERAPEE_DEFAULT_PROFILE
        check.ensure_type(profile, str)
        profile_name = f"{profile}{RAWTHERAPEE_PROFILE_EXTENSION}"
        profile_path = profile_folder / profile_name
        show.normal(f"Using RawTherapee profile {profile_path}")
        check.ensure_file(profile_path)

        file_processor = RawTherapeeFileProcessor(
            profile_path,
            args.quality,
            args.subsampling,
            output_namer,
            post_processor,
        )
        return file_processor

    def _get_file_skip_strategy(self, args: argparse.Namespace) -> processing.FileSkipStrategy:
        skips = []
        if not args.no_skip_processed:
            skips.append(processing.BySuffixFileSkipStrategy(RawTherapeeCommand.PROCESSED_SUFFIX))
        if args.greater_than:
            skips.append(processing.BySizeFileSkipStrategy(args.greater_than))
        skipper = processing.MultiFileSkipStrategy(skips)
        return skipper

    @property
    def name(self) -> str:
        return "rawtherapee"

    @property
    def help(self) -> str:
        return "Process image files with RawTherapee profiles."


class RawTherapeeHQCommand(RawTherapeeCommand):
    JPEG_SUBSAMPLING_3 = 3

    def _get_quality_defaults(self) -> tuple[int, int]:
        return (
            JPEG_QUALITY,
            RawTherapeeHQCommand.JPEG_SUBSAMPLING_3,
        )

    @property
    def name(self) -> str:
        return "rawtherapee-hq"

    @property
    def help(self) -> str:
        return "Process image files with RawTherapee profiles (alias with high-quality JPEG processing parameters)."


class RawTherapeeFileProcessor(shell.ShellCommandFileProcessor):
    def __init__(
        self,
        profile_path: pathlib.Path,
        jpeg_quality: int,
        jpeg_subsampling: int,
        output_strategy: processing.OutputFilePathStrategy,
        post_processor: processing.PostProcessingStrategy,
    ):
        check.ensure_file(profile_path)
        check.ensure_int_between(jpeg_quality, 1, 100)
        check.ensure_int_between(jpeg_subsampling, 1, 3)
        args = ["-p", str(profile_path), f"-j{jpeg_quality}", f"-js{jpeg_subsampling}"]
        super().__init__(
            "RawTherapee",
            "rawtherapee-cli",
            *args,
            output_strategy=output_strategy,
            post_processor=post_processor,
        )

    def _finalize_args(
        self,
        initial_args: list[str],
        file_path: pathlib.Path,
        output_file_path: pathlib.Path,
    ) -> list[str]:
        # quick mode, default profile, overwrite output if needed
        args = ["-o", str(output_file_path), "-q", "-d", "-Y"]
        args += initial_args
        # input path MUST be the last parameter
        args += ["-c", str(file_path)]
        # rawtherapee-cli -o <output_path> -q -d -p <profile_path> -Y -j75 -js1 -c <input_path>
        return args
