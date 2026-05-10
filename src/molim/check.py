import pathlib


def ensure_not_none(obj: object) -> None:
    if obj is None:
        raise ValueError("Value cannot be None.")


def ensure_type(obj: object, type: type) -> None:
    ensure_not_none(obj)
    ensure_not_none(type)
    if not isinstance(obj, type):
        raise TypeError(f"A {type} object is required.")


def ensure_type_or_none(obj: object, type: type) -> None:
    if obj is not None:
        ensure_type(obj, type)


def ensure_str_startswith(obj: object, start: str) -> None:
    ensure_type(obj, str)
    if not obj.startswith(start):
        raise ValueError(f"A string value that starts with '{start}' is required (provided: {obj}).")


def ensure_int_positive(obj: object) -> None:
    ensure_type(obj, int)
    if obj < 1:
        raise ValueError(f"A positive integer value is required (provided: {obj}).")


def ensure_int_between(obj: object, min: int, max: int) -> None:
    ensure_type(obj, int)
    if obj < min or obj > max:
        raise ValueError(f"An integer value between {min} and {max} is required (provided: {obj}).")


def ensure_list_non_empty(obj: object) -> None:
    ensure_type(obj, list)
    if len(obj) == 0:
        raise ValueError("A non-empty list is required.")


def ensure_path(obj: object) -> None:
    ensure_type(obj, pathlib.Path)


def ensure_file(obj: object) -> None:
    ensure_path(obj)
    if not obj.is_file():
        raise ValueError("A file is required.")


def ensure_folder(obj: object) -> None:
    ensure_path(obj)
    if not obj.is_dir():
        raise ValueError("A folder is required.")
