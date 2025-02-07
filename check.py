import pathlib


def ensure_not_none(obj):
    if obj is None:
        raise ValueError("Value cannot be None.")


def ensure_type(obj, type):
    ensure_not_none(obj)
    ensure_not_none(type)
    if not isinstance(obj, type):
        raise TypeError(f"A {type} object is required.")


def ensure_str_startswith(obj, start):
    ensure_type(obj, str)
    if not obj.startswith(start):
        raise ValueError(f"A string value that starts with '{start}' is required.")


def ensure_int_positive(obj):
    ensure_type(obj, int)
    if obj < 1:
        raise ValueError("A positive integer value is required.")


def ensure_list_non_empty(obj):
    ensure_type(obj, list)
    if len(obj) == 0:
        raise ValueError("A non-empty list is required.")


def ensure_path(obj):
    ensure_type(obj, pathlib.Path)


def ensure_file(obj):
    ensure_path(obj)
    if not obj.is_file():
        raise ValueError("A file is required.")


def ensure_folder(obj):
    ensure_path(obj)
    if not obj.is_dir():
        raise ValueError("A folder is required.")
