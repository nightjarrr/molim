import stats
import util


class FileProcessor(object):
    def __init__(self, filepath):
        util.ensure_file(filepath)
        self.__filepath = filepath
        self.__stats = stats.FileStats(filepath)

    def process(self):
        pass
