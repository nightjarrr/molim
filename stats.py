import check
import pathlib
import show
import time


class StatsNotFinishedError(Exception):
    DEFAULT_MESSAGE = (
        "Statistics results should not be accessed before gathering is finished yet."
    )

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


class StatsAlreadyFinishedError(Exception):
    DEFAULT_MESSAGE = "Statistics gathering is already finished, cannot finish again."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


def ensure_finished(method):
    def wrapper(self, *args, **kwargs):
        if not self.finished:
            raise StatsNotFinishedError()
        return method(self, *args, **kwargs)

    return wrapper


def ensure_not_finished(method):
    def wrapper(self, *args, **kwargs):
        if self.finished:
            raise StatsAlreadyFinishedError()
        return method(self, *args, **kwargs)

    return wrapper


class Stats(object):
    def __init__(self):
        self.__start_ts = None
        self.__end_ts = None
        self.__elapsed = None
        self.__finished = False

    @ensure_not_finished
    def start(self) -> None:
        self.__startTs = time.time()

    @ensure_not_finished
    def finish(self) -> None:
        self.__endTs = time.time()
        self.__elapsed = self.__endTs - self.__startTs
        self.__finished = True

    # Support 'with' usage

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.finish()

    # Properties

    @property
    def finished(self) -> bool:
        return self.__finished

    @property
    @ensure_finished
    def start_timestamp(self) -> float:
        return self.__startTs

    @property
    @ensure_finished
    def end_timestamp(self) -> float:
        return self.__endTs

    @property
    @ensure_finished
    def elapsed(self) -> float:
        return self.__elapsed


class FileStatsAlreadyHaveProcessedFileError(Exception):
    DEFAULT_MESSAGE = "The processed file was already provided."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


class FileStats(Stats):
    def __init__(self, original_file: pathlib.Path):
        super().__init__()
        check.ensure_file(original_file)
        self.__original_file = original_file
        self.__original_file_size = original_file.stat().st_size
        self.__processed_file = None
        self.__processed_file_size = None
        self.__delta_size = None

    @ensure_not_finished
    def set_processed_file(
        self, processed_file: pathlib.Path, processed_file_size: int = None
    ):
        if self.__processed_file:
            raise FileStatsAlreadyHaveProcessedFileError()
        if processed_file_size is not None:
            self.__processed_file_size = processed_file_size
        else:
            check.ensure_file(processed_file)
            self.__processed_file_size = processed_file.stat().st_size
        self.__processed_file = processed_file

    def finish(self):
        super().finish()
        if self.__processed_file_size is not None:
            self.__delta_size = self.__original_file_size - self.__processed_file_size

    # Properties

    @property
    @ensure_finished
    def original_file(self) -> pathlib.Path:
        return self.__original_file

    @property
    @ensure_finished
    def original_file_size(self) -> int:
        return self.__original_file_size

    @property
    @ensure_finished
    def processed_file(self) -> pathlib.Path:
        return self.__processed_file

    @property
    @ensure_finished
    def processed_file_size(self) -> int:
        return self.__processed_file_size

    @property
    @ensure_finished
    def delta_size(self) -> int:
        return self.__delta_size

    # __repr__

    def __repr__(self):
        if self.finished:
            return (
                f"<FileStats(original_file={self.original_file}, "
                f"original_file_size={show.human_size(self.original_file_size)}, "
                f"processed_file={self.processed_file}, "
                f"processed_file_size={show.human_size(self.processed_file_size)}, "
                f"delta_size={show.human_size(self.delta_size)}, "
                f"elapsed={show.elapsed(self.elapsed)})>"
            )
        else:
            return f"<FileStats(original_file={self.__original_file}) - UNFINISHED>"


class FolderStats(Stats):
    def __init__(self, folder_path: pathlib.Path):
        super().__init__()
        check.ensure_folder(folder_path)
        self.__folder_path = folder_path
        self.__processed_files_stats = []
        self.__total_original_size = 0
        self.__total_processed_size = 0
        self.__skipped_files_count = 0

    @ensure_not_finished
    def add_processed_file_stats(self, file_stats: FileStats) -> None:
        check.ensure_type(file_stats, FileStats)
        if not file_stats.finished:
            raise ValueError("Cannot add non-finished file stats to folder stats.")
        self.__processed_files_stats.append(file_stats)
        self.__total_original_size += file_stats.original_file_size
        self.__total_processed_size += file_stats.processed_file_size

    @ensure_not_finished
    def add_skipped_file(self) -> None:
        self.__skipped_files_count += 1

    # Properties

    @property
    @ensure_finished
    def folder_path(self) -> pathlib.Path:
        return self.__folder_path

    @property
    @ensure_finished
    def processed_files_stats(self) -> list[FileStats]:
        return self.__processed_files_stats

    @property
    @ensure_finished
    def skipped_files_count(self) -> int:
        return self.__skipped_files_count

    @property
    @ensure_finished
    def total_original_size(self) -> int:
        return self.__total_original_size

    @property
    @ensure_finished
    def total_processed_size(self) -> int:
        return self.__total_processed_size

    @property
    @ensure_finished
    def total_delta_size(self) -> int:
        return self.__total_original_size - self.__total_processed_size

    # __repr__

    def __repr__(self):
        if self.finished:
            return (
                f"<FolderStats(folder_path={self.folder_path}, "
                f"processed_files_stats={self.processed_files_stats}, "
                f"skipped_files_count={self.skipped_files_count}, "
                f"total_original_size={show.human_size(self.total_original_size)}, "
                f"total_processed_size={show.human_size(self.total_processed_size)}, "
                f"total_delta_size={show.human_size(self.total_delta_size)}, "
                f"elapsed={show.elapsed(self.elapsed)})>"
            )
        else:
            return f"<FolderStats(folder_path={self.__folder_path}) - UNFINISHED>"
