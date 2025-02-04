import pathlib


def ensure_not_none(obj):
    if obj is None:
        raise ValueError("Value cannot be None.")


def ensure_type(obj, type):
    ensure_not_none(obj)
    ensure_not_none(type)
    if not isinstance(obj, type):
        raise TypeError(f"A {type} object is required.")


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

