import stats
import util


class OutputFilePathStrategy(object):
    def get_output_path(input_path):
        raise NotImplementedError()


class SuffixOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, suffix):
        util.ensure_not_none(suffix)
        self.__suffix = suffix

    def get_output_path(self, input_path):
        util.ensure_path(input_path)
        output_stem = f"{input_path.stem}.{self.__suffix}"
        return input_path.with_stem(output_stem)


class ChangeExtOutputFilePathStrategy(OutputFilePathStrategy):
    def __init__(self, ext):
        util.ensure_not_none(ext)
        self.__ext = ext

    def get_output_path(self, input_path):
        util.ensure_path(input_path)
        return input_path.with_suffix(self.__ext)


class PostProcessingStrategy(object):
    pass


class FileProcessor(object):
    def __init__(self, filepath, output_strategy, post_processor):
        util.ensure_file(filepath)
        util.ensure_type(output_strategy, OutputFilePathStrategy)
        util.ensure_type(post_processor, PostProcessingStrategy)
        self.__filepath = filepath
        self.__output_strategy = output_strategy
        self.__post_processor = post_processor

    def process(self, dry_run=False):
        with stats.FileStats(self.__filepath) as statistics:
            output_filepath = self.__output_strategy.get_output_path(self.__filepath)

            if not dry_run:
                self._execute(self, output_filepath)
                statistics.set_processed(output_filepath)
            else:
                statistics.set_processed(self.__filepath)

            self.__post_processor.process(self.__filepath, output_filepath)

        return statistics

    # Abstract methods

    def _execute(self, output_filepath):
        raise NotImplementedError()
