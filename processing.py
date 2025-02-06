import pathlib
import stats
import check


class OutputFilePathStrategy(object):
    def get_output_path(input_path):
        raise NotImplementedError()


class SuffixOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, suffix):
        check.ensure_not_none(suffix)
        self.__suffix = suffix

    def get_output_path(self, input_path):
        check.ensure_path(input_path)
        output_stem = f"{input_path.stem}.{self.__suffix}"
        return input_path.with_stem(output_stem)


class ChangeExtOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, ext):
        check.ensure_not_none(ext)
        self.__ext = ext

    def get_output_path(self, input_path):
        check.ensure_path(input_path)
        return input_path.with_suffix(self.__ext)


class PostProcessingStrategy(object):
    def process(self, input_filepath, output_filepath):
        raise NotImplementedError()


class NoopPostProcessingStrategy(PostProcessingStrategy):
    def process(self, input_filepath, output_filepath):
        pass


class FileProcessor(object):
    def __init__(self, output_strategy, post_processor):
        check.ensure_type(output_strategy, OutputFilePathStrategy)
        check.ensure_type(post_processor, PostProcessingStrategy)
        self.__output_strategy = output_strategy
        self.__post_processor = post_processor

    def process(self, file_path: pathlib.Path, dry_run=False) -> stats.FileStats:
        check.ensure_file(file_path)
        with stats.FileStats(file_path) as statistics:
            output_file_path = self.__output_strategy.get_output_path(file_path)
            output_file_size = None

            self._prepare_execution(output_file_path)
            if not dry_run:
                self._execute(output_file_path)
            else:
                # For dry run, emulate output size matching the input size.
                output_file_size = file_path.stat().st_size

            statistics.set_processed_file(output_file_path, output_file_size)

            self.__post_processor.process(file_path, output_file_path)

        return statistics

    def _prepare_execution(self, output_file_path: pathlib.Path):
        pass

    # Abstract methods

    def _execute(self, output_file_path: pathlib.Path):
        raise NotImplementedError()


class FileMatchStrategy(object):
    def match(self, file_path):
        raise NotImplementedError()


class AnyFileMatchStrategy(FileMatchStrategy):
    def match(self, file_path):
        return True


class ByExtensionFileMatchStrategy(FileMatchStrategy):
    def __init__(self, ext):
        check.ensure_type(ext, str)
        self.__ext = ext

    def match(self, file_path):
        check.ensure_file(file_path)
        return file_path.suffix == self.__ext


class FileSkipStrategy(object):
    def skip(self, file_path):
        raise NotImplementedError()


class BySuffixFileSkipStrategy(FileSkipStrategy):
    def __init__(self, suffix):
        check.ensure_type(suffix, str)
        self.__suffix = suffix

    def skip(self, file_path):
        check.ensure_file(file_path)
        return file_path.stem.endswith(self.__suffix)


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
                    if self.__file_skiper.skip(f):
                        statistics.add_skipped_file()
                    else:
                        files_list.append(f)
            if files_list:
                for f in files_list:
                    s = self.__file_processor.process(f, dry_run)
                    statistics.add_processed_file_stats(s)

        return statistics
