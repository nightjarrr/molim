from datetime import timedelta
import rich
import rich.traceback

# Formatting helpers


def percent(old: int, new: int):
    if old == new:
        return "0%"
    p = 100 * float(new) / old
    return f"{p:.1f}%"


def elapsed(value: float):
    return f"{timedelta(seconds=int(value))}"


def human_size(size: int):
    for unit in ["", "K", "M", "G"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}Yi"


# Output helpers


def important(message):
    rich.print(message)
    rich.print()


def verbose(message):
    rich.print(message)


def error(message: str, ex: Exception):
    rich.print(message)
    t = rich.traceback.Traceback.from_exception(type(ex), ex, ex.__traceback__)
    rich.print(t)
