from datetime import timedelta
import rich.console
import rich.panel
import rich.progress
import rich.text
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

__CONSOLE__ = rich.console.Console()


def important(message: str, new_line=False):
    __CONSOLE__.print(message, style="bold", highlight=False)
    if new_line:
        __CONSOLE__.print()


def rule(message: str = ""):
    __CONSOLE__.rule(message)


def normal(message: str, new_line=False):
    __CONSOLE__.print(message, highlight=False)
    if new_line:
        __CONSOLE__.print()


def status(message: str):
    return __CONSOLE__.status(message, refresh_per_second=5)


def verbose(message: str, new_line=False):
    __CONSOLE__.print(message, style="grey50", highlight=False)
    if new_line:
        __CONSOLE__.print()


def error(message: str, ex: Exception):
    __CONSOLE__.print(message)
    t = rich.traceback.Traceback.from_exception(type(ex), ex, ex.__traceback__)
    __CONSOLE__.print(t)
