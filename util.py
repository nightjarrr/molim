import pathlib


class NotAFileError(Exception):
    DEFAULT_MESSAGE = "A file is required."

    def __init__(self, message=DEFAULT_MESSAGE):
        self.message = message
        super().__init__(self.message)


def ensure_file(obj):
    if not isinstance(obj, pathlib.Path) or not obj.is_file():
        raise NotAFileError()
