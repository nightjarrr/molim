from datetime import timedelta

import rich.console
import rich.panel
import rich.progress
import rich.text
import rich.traceback

# Formatting helpers


def percent(old: int, new: int) -> str:
    if old == new:
        return "0%"
    p = 100 * float(new) / old
    return f"{p:.1f}%"


def elapsed(value: float) -> str:
    return f"{timedelta(seconds=int(value))}"


def human_size(size: int) -> str:
    if abs(size) < 1024:
        return str(int(size))
    size /= 1024.0
    for unit in ["K", "M", "G"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}T"


def ext(value: str) -> str:
    if value.isupper():
        return value.lower()
    ex = value.split(",")
    return ", ".join(f"*{e}" for e in ex)


def ellipsis(value: str) -> str:
    if len(value) > 41:
        ending = value[-10:]
        start = value[:26]
        return f"{start}(...){ending}"
    return value


# Output helpers

__CONSOLE__ = rich.console.Console()
__verbose = False


def set_verbose(val: bool) -> None:
    global __verbose
    __verbose = val


def important(message: str, new_line=False) -> None:
    __CONSOLE__.print(message, style="bold", highlight=False, markup=False)
    if new_line:
        __CONSOLE__.print()


def rule(message: str = "") -> None:
    __CONSOLE__.rule(message)


def normal(message: str, new_line=False) -> None:
    __CONSOLE__.print(" " + message, highlight=False, markup=False)
    if new_line:
        __CONSOLE__.print()


def __delta(delta: int) -> str:
    if delta < 0:
        return f"added {human_size(-delta)}"
    else:
        return f"saved {human_size(delta)}"


def file_stats(s, show_size: bool):
    t = rich.text.Text(f"{s.original_file.name}")
    if show_size:
        t.append(
            f"\n{human_size(s.original_file_size)} \u2192 {human_size(s.processed_file_size)}, {__delta(s.delta_size)}",
            style="grey50",
        )

    cols = rich.columns.Columns(
        [
            rich.text.Text(f" \u2713 {elapsed(s.elapsed)}"),
            t,
        ],
        expand=False,
    )
    __CONSOLE__.print(cols, highlight=False, markup=False)


def folder_stats(s, show_size: bool):
    if s.processed_files_stats:
        important(
            f"Processed {len(s.processed_files_stats)} files in {elapsed(s.elapsed)}",
            new_line=not show_size,
        )
        if show_size:
            tos = s.total_original_size
            tps = s.total_processed_size
            tds = s.total_delta_size
            important(
                f"{human_size(tos)} \u2192 {human_size(tps)}, new size {percent(tos, tps)} of original, {__delta(tds)}",
                new_line=True,
            )


def progress(total: int) -> object:
    p = rich.progress.Progress(
        rich.progress.TextColumn(""),
        rich.progress.SpinnerColumn(),
        rich.progress.TimeElapsedColumn(),
        rich.progress.TextColumn("{task.description}"),
        rich.progress.BarColumn(),
        rich.progress.MofNCompleteColumn(),
        rich.progress.TaskProgressColumn(),
        console=__CONSOLE__,
        expand=True,
    )
    p.add_task(total=total, description="")
    return p


def progress_update(progress: object, description: str) -> None:
    task = progress.task_ids[0]
    progress.update(task, description=ellipsis(description))


def progress_advance(progress: object) -> None:
    task = progress.task_ids[0]
    progress.advance(task)


def verbose(message: str) -> None:
    if __verbose:
        __CONSOLE__.print("   " + message, style="grey50", highlight=False, markup=False)


def verbose_args(args, new_line=False):
    if __verbose:
        for k in args.__dict__:
            verbose(f" - {k} = {args.__dict__[k]}")
        if new_line:
            __CONSOLE__.print()


def error(message: str, ex: Exception) -> None:
    __CONSOLE__.print(message)
    t = rich.traceback.Traceback.from_exception(type(ex), ex, ex.__traceback__)
    __CONSOLE__.print(t)
