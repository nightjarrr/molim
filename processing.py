import check
import pathlib
import show
import stats


class OutputFilePathStrategy(object):
    def get_output_path(input_path: pathlib.Path):
        raise NotImplementedError()


class SuffixOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, suffix: str):
        check.ensure_str_startswith(suffix, ".")
        self.__suffix = suffix

    def get_output_path(self, input_path: pathlib.Path) -> pathlib.Path:
        check.ensure_path(input_path)
        output_stem = f"{input_path.stem}{self.__suffix}"
        return input_path.with_stem(output_stem)


class ChangeExtOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, ext: str):
        check.ensure_str_startswith(ext, ".")
        self.__ext = ext

    def get_output_path(self, input_path: pathlib.Path) -> pathlib.Path:
        check.ensure_path(input_path)
        return input_path.with_suffix(self.__ext)


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


class PostProcessingStrategy(object):
    def process(
        self, input_filepath: pathlib.Path, output_filepath: pathlib.Path
    ) -> None:
        raise NotImplementedError()


class NoopPostProcessingStrategy(PostProcessingStrategy):
    def process(
        self, input_filepath: pathlib.Path, output_filepath: pathlib.Path
    ) -> None:
        pass


class FileProcessor(object):
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

            self.__post_processor.process(file_path, output_file_path)

        return statistics

    def _prepare_execution(
        self, file_path: pathlib.Path, output_file_path: pathlib.Path
    ) -> None:
        pass

    # Abstract methods

    def _execute(self, file_path: pathlib.Path, output_file_path: pathlib.Path) -> None:
        raise NotImplementedError()


class FileMatchStrategy(object):
    def match(self, file_path: pathlib.Path) -> bool:
        raise NotImplementedError()


class AnyFileMatchStrategy(FileMatchStrategy):
    def match(self, file_path: pathlib.Path) -> bool:
        return True


class ByExtensionFileMatchStrategy(FileMatchStrategy):
    def __init__(self, ext: str):
        check.ensure_str_startswith(ext, ".")
        self.__ext = ext

    def match(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        return file_path.suffix == self.__ext


class FileSkipStrategy(object):
    def skip(self, file_path: pathlib.Path) -> bool:
        raise NotImplementedError()


class BySuffixFileSkipStrategy(FileSkipStrategy):
    def __init__(self, suffix: str):
        check.ensure_str_startswith(suffix, ".")
        self.__suffix = suffix

    def skip(self, file_path: pathlib.Path) -> bool:
        check.ensure_file(file_path)
        res = file_path.stem.endswith(self.__suffix)
        if res:
            show.verbose(
                f" - {file_path.name} skipped as it has suffix {self.__suffix}."
            )
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
                f" - {file_path.name} ({show.human_size(size)}) skipped as it is smaller than {show.human_size(self.__less_than)}."
            )
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


class FolderProcessor(object):
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

    def process(self, dry_run=False) -> stats.FolderStats:
        with stats.FolderStats(self.__folder_path) as statistics:
            files_list = []
            for f in self.__folder_path.iterdir():
                if f.is_file() and self.__file_matcher.match(f):
                    files_list.append(f)
            if files_list:
                show.normal(
                    f"Matched {len(files_list)} files. Checking whether some of them can be skipped..."
                )
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
                    i = 1
                    for f in files_to_process:
                        with show.status(
                            f" [{i}/{len(files_to_process)}] {f.name} ({show.human_size(f.stat().st_size)})"
                        ):
                            s = self.__file_processor.process(f, dry_run)
                            statistics.add_processed_file_stats(s)
                        show.normal(
                            f" \u2713 [{show.elapsed(s.elapsed)}] {f.name}, {show.human_size(s.original_file_size)} \u2192 {show.human_size(s.processed_file_size)} ({show.percent(s.original_file_size, s.processed_file_size)}), saved {show.human_size(s.delta_size)}"
                        )
                        i += 1
                else:
                    show.normal("No files to process, done here.", new_line=True)
            else:
                show.normal("No matching files here, nothing to do.", new_line=True)

        return statistics
