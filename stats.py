import time
import util


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
    def start(self):
        self.__startTs = time.time()

    @ensure_not_finished
    def finish(self):
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
    def finished(self):
        return self.__finished

    @property
    @ensure_finished
    def start_timestamp(self):
        return self.__startTs

    @property
    @ensure_finished
    def end_timestamp(self):
        return self.__endTs

    @property
    @ensure_finished
    def elapsed(self):
        return self.__elapsed


class FileStatsAlreadyHaveProcessedFileError(Exception):
    DEFAULT_MESSAGE = "The processed file was already provided."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


class FileStats(Stats):
    def __init__(self, original_file):
        super().__init__()
        util.ensure_file(original_file)
        self.__originalFile = original_file
        self.__originalFileSize = original_file.stat().st_size
        self.__processedFile = None
        self.__processedFileSize = None
        self.__deltaSize = None

    @ensure_not_finished
    def set_processed(self, processed_file):
        if self.__processedFile:
            raise FileStatsAlreadyHaveProcessedFileError()
        util.ensure_file(processed_file)
        self.__processedFile = processed_file
        self.__processedFileSize = processed_file.stat().st_size

    def finish(self):
        super().finish()
        if self.__processedFileSize:
            self.__deltaSize = self.__processedFileSize - self.__originalFileSize

    # Properties

    @property
    @ensure_finished
    def originalFile(self):
        return self.__originalFile

    @property
    @ensure_finished
    def originalFileSize(self):
        return self.__originalFileSize

    @property
    @ensure_finished
    def processedFile(self):
        return self.__processedFile

    @property
    @ensure_finished
    def processedFileSize(self):
        return self.__processedFileSize

    @property
    @ensure_finished
    def deltaSize(self):
        return self.__deltaSize


class FolderStats(Stats):
    pass


class TotalStats(Stats):
    pass
