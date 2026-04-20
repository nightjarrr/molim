import pathlib

from . import check, show, stats


class OutputFilePathStrategy:
    def get_output_path(input_path: pathlib.Path):
        raise NotImplementedError()


class SuffixOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, suffix: str):
        check.ensure_str_startswith(suffix, ".")
        self.__suffix = suffix
        show.normal(f"Processed files will get suffix '{suffix}'.")

    def get_output_path(self, input_path: pathlib.Path) -> pathlib.Path:
        check.ensure_path(input_path)
        output_stem = f"{input_path.stem}{self.__suffix}"
        return input_path.with_stem(output_stem)


class ChangeExtOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, ext: str):
        check.ensure_str_startswith(ext, ".")
        self.__ext = ext
        show.normal(f"Processed files will have extension '{ext}'.")

    def get_output_path(self, input_path: pathlib.Path) -> pathlib.Path:
        check.ensure_path(input_path)
        return input_path.with_suffix(self.__ext)


class FolderOutputFilePathStrategy(OutputFilePathStrategy):
    """
    Output strategy to put processed files into a different folder, not into the original folder.
    """

    def __init__(self, target_folder: pathlib.Path, dry_run: bool):
        check.ensure_path(target_folder)
        if target_folder.exists():
            check.ensure_folder(target_folder)
        else:
            if not dry_run:
                target_folder.mkdir(parents=True)
            show.verbose(f"Creating folder {target_folder}.")
        show.normal(f"Processed files will be created in folder {target_folder}.")
        self.__target_folder = target_folder

    def get_output_path(self, input_path: pathlib.Path) -> pathlib.Path:
        check.ensure_path(input_path)
        return self.__target_folder / input_path.name


class MultiOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, output_strategies: list[OutputFilePathStrategy]):
        check.ensure_list_non_empty(output_strategies)
        self.__output_strategies = output_strategies

    def get_output_path(self, input_path: pathlib.Path) -> pathlib.Path:
        check.ensure_path(input_path)
        output_path = input_path
        for s in self.__output_strategies:
            output_path = s.get_output_path(output_path)
        return output_path


class PostProcessingStrategy:
    def process(self, input_filepath: pathlib.Path, output_filepath: pathlib.Path, dry_run: bool) -> None:
        raise NotImplementedError()


class NoopPostProcessingStrategy(PostProcessingStrategy):
    def process(self, input_filepath: pathlib.Path, output_filepath: pathlib.Path, dry_run: bool) -> None:
        pass


class MoveOriginalPostProcessingStrategy(PostProcessingStrategy):
    def __init__(self, move_to: pathlib.Path, dry_run: bool):
        check.ensure_path(move_to)
        if move_to.exists():
            check.ensure_folder(move_to)
        else:
            if not dry_run:
                move_to.mkdir(parents=True)
            show.verbose(f"Creating folder {move_to}.")
        show.normal(f"Original files will be moved to folder {move_to}.")
        self.__move_to = move_to

    def process(self, input_filepath: pathlib.Path, output_filepath: pathlib.Path, dry_run: bool) -> None:
        check.ensure_file(input_filepath)
        if not dry_run:
            check.ensure_file(output_filepath)
        show.verbose(f"Moving original file {input_filepath.name} to folder {self.__move_to}.")
        if not dry_run:
            target = self.__move_to / input_filepath.name
            input_filepath.rename(target)


class DeleteOriginalPostProcessingStrategy(PostProcessingStrategy):
    def __init__(self):
        show.normal("Original files will be deleted.")

    def process(self, input_filepath: pathlib.Path, output_filepath: pathlib.Path, dry_run: bool) -> None:
        check.ensure_file(input_filepath)
        if not dry_run:
            check.ensure_file(output_filepath)
        show.verbose(f"Deleting original file {input_filepath.name}, only processed file {output_filepath.name} will remain.")
        if not dry_run:
            input_filepath.unlink()


class ReplaceOriginalPostProcessignStrategy(PostProcessingStrategy):
    """
    Post-processing strategy that will replace the original file with the processed file.
    It accepts a post-processing strategy instance that must handle the original file:
    delete it or move to another location, or anything else.
    """

    def __init__(self, originals_post_processor: PostProcessingStrategy):
        check.ensure_type(originals_post_processor, PostProcessingStrategy)
        self.__originals_post_processor = originals_post_processor
        show.normal("Processed files will be renamed to the original file name.")

    def process(self, input_filepath: pathlib.Path, output_filepath: pathlib.Path, dry_run: bool) -> None:
        check.ensure_file(input_filepath)
        if not dry_run:
            check.ensure_file(output_filepath)
        # Handle the original file.
        self.__originals_post_processor.process(input_filepath, output_filepath, dry_run)
        show.verbose(f"Renaming processed file {output_filepath.name} to original file name {input_filepath.name}.")
        if not dry_run:
            output_filepath.rename(input_filepath)


class FileProcessor:
    def __init__(
        self,
        output_strategy: OutputFilePathStrategy,
        post_processor: PostProcessingStrategy,
    ):
        check.ensure_type(output_strategy, OutputFilePathStrategy)
        check.ensure_type(post_processor, PostProcessingStrategy)
        self.__output_strategy = output_strategy
        self.__post_processor = post_processor

    def process(self, file_path: pathlib.Path, dry_run=False) -> stats.FileStats:
        check.ensure_file(file_path)
        with stats.FileStats(file_path) as statistics:
            output_file_path = self.__output_strategy.get_output_path(file_path)
            output_file_size = None

            self._prepare_execution(file_path, output_file_path)
            if not dry_run:
                self._execute(file_path, output_file_path)
            else:
                # For dry run, emulate output size matching the input size.
                output_file_size = file_path.stat().st_size

            statistics.set_processed_file(output_file_path, output_file_size)

            self.__post_processor.process(file_path, output_file_path, dry_run)

        return statistics

    def _prepare_execution(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        pass

    # Abstract methods

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        raise NotImplementedError()


class FileMatchStrategy:
    def match(self, file_path: pathlib.Path) -> bool:
        raise NotImplementedError()


class AnyFileMatchStrategy(FileMatchStrategy):
    def match(self, file_path: pathlib.Path) -> bool:
        return True


class ByExtensionFileMatchStrategy(FileMatchStrategy):
    def __init__(self, ext: str):
        check.ensure_type(ext, str)
        ext_list = ext.split(",")
        for e in ext_list:
            check.ensure_str_startswith(e, ".")
        self.__ext = set(ext_list)

    def match(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        return file_path.suffix in self.__ext


class FileSkipStrategy:
    def skip(self, file_path: pathlib.Path) -> bool:
        raise NotImplementedError()


class NoFileSkipStrategy(FileSkipStrategy):
    """
    The corner-case skip strategy that does not skip any file.
    """

    def skip(self, file_path: pathlib.Path) -> bool:
        return False


class BySuffixFileSkipStrategy(FileSkipStrategy):
    def __init__(self, suffix: str):
        check.ensure_str_startswith(suffix, ".")
        self.__suffix = suffix

    def skip(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        res = file_path.stem.endswith(self.__suffix)
        if res:
            show.verbose(f" - {file_path.name} skipped as it has suffix {self.__suffix}.")
        return res


class BySizeFileSkipStrategy(FileSkipStrategy):
    def __init__(self, less_than: int):
        check.ensure_int_positive(less_than)
        self.__less_than = less_than

    def skip(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        size = file_path.stat().st_size
        res = size < self.__less_than
        if res:
            show.verbose(
                f" - {file_path.name} ({show.human_size(size)}) skipped - smaller than {show.human_size(self.__less_than)}."
            )
        return res


class GlobFileSkipStrategy(FileSkipStrategy):
    def __init__(self, glob_pattern: str):
        check.ensure_type(glob_pattern, str)
        self.__glob_pattern = glob_pattern

    def skip(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        res = file_path.match(self.__glob_pattern)
        if res:
            show.verbose(f" - {file_path.name} skipped as it is matches pattern '{self.__glob_pattern}'.")
        return res


class MultiFileSkipStrategy(FileSkipStrategy):
    def __init__(self, skip_strategies: list[FileSkipStrategy]):
        check.ensure_type(skip_strategies, list)
        self.__skip_strategies = skip_strategies

    def skip(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        for s in self.__skip_strategies:
            if s.skip(file_path):
                return True
        return False


class FolderProcessor:
    def __init__(
        self,
        folder_path: pathlib.Path,
        file_matcher: FileMatchStrategy,
        file_skiper: FileSkipStrategy,
        file_processor: FileProcessor,
    ):
        check.ensure_folder(folder_path)
        check.ensure_type(file_matcher, FileMatchStrategy)
        check.ensure_type(file_skiper, FileSkipStrategy)
        check.ensure_type(file_processor, FileProcessor)
        self.__folder_path = folder_path
        self.__file_matcher = file_matcher
        self.__file_skiper = file_skiper
        self.__file_processor = file_processor

    def process(self, dry_run=False, show_size=True) -> stats.FolderStats:
        with stats.FolderStats(self.__folder_path) as statistics:
            files_list = []
            for f in self.__folder_path.iterdir():
                if f.is_file() and self.__file_matcher.match(f):
                    files_list.append(f)
            if files_list:
                show.normal(f"Matched {len(files_list)} files.")
                show.normal("Checking whether some of them can be skipped...")
                files_to_process = []
                skipped = 0
                for f in files_list:
                    if self.__file_skiper.skip(f):
                        statistics.add_skipped_file()
                        skipped += 1
                    else:
                        files_to_process.append(f)
                if skipped > 0:
                    show.normal(f"Skipped {skipped} of {len(files_list)} files.")
                else:
                    show.normal("No files were skipped.")
                if files_to_process:
                    show.normal(f"Processing {len(files_to_process)} files...")
                    with show.progress(len(files_to_process)) as p:
                        i = 1
                        for f in files_to_process:
                            show.verbose(f"Starting to process {f.name}...")
                            show.progress_update(p, f.name)
                            s = self.__file_processor.process(f, dry_run)
                            show.progress_advance(p)
                            statistics.add_processed_file_stats(s)
                            show.file_stats(s, show_size)
                            i += 1
                            show.verbose("")
                        show.progress_update(p, "")
                else:
                    show.normal("No files to process, done here.", new_line=True)
            else:
                show.normal("No matching files here, nothing to do.", new_line=True)

        return statistics
