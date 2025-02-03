import os.path
import time

class StatsNotFinishedError(Exception):
    DEFAULT_MESSAGE = "Statistics results should not be accessed before gathering is finished yet."

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

class Stats(object):
    def __init__(self):
        self.__startTs = None
        self.__endTs = None
        self.__elapsed = None
        self.__finished = False

    def start(self):
        if self.__finished:
            raise StatsAlreadyFinishedError()
        self.__startTs = time.time()

    def finish(self):
        if self.__finished:
            raise StatsAlreadyFinishedError()
        self.__endTs = time.time()
        self.__elapsed = self.__endTs - self.__startTs
        self.__finished = True

    # Abstract methods


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
    def startTimestamp(self):
        return self.__startTs

    @property
    @ensure_finished
    def endTimestamp(self):
        return self.__endTs

    @property
    @ensure_finished
    def elapsed(self):
        return self.__elapsed


class FileStats(Stats):
    def __init__(self, print, originalFile):
        super().__init__(print)
        self.__originalFile = originalFile
        self.__originalFileSize = os.path.getsize(originalFile)
        self.__processedFile = None
        self.__processedFileSize = None
        self.__deltaSize = None

    def set_processed(self, processedFile):
        self.__processedFile = processedFile
        self.__processedFileSize = os.path.getsize(processedFile)

    def finish(self):
        super().finish()
        if self.__processedFileSize:
            self.__deltaSize = self.__processedFileSize - self.__originalFileSize

    # Properties

    @property
    def originalFile(self):
        return self.__originalFile

    @property
    def originalFileSize(self):
        return self.__originalFileSize

    @property
    def processedFile(self):
        return self.__processedFile

    @property
    def processedFileSize(self):
        return self.__processedFileSize

    @property
    def deltaSize(self):
        return self.__deltaSize


class FolderStats(Stats):
    pass


class TotalStats(Stats):
    pass

