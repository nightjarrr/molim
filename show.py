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
__verbose = False


def set_verbose(val: bool) -> None:
    global __verbose
    __verbose = val


def important(message: str, new_line=False) -> None:
    __CONSOLE__.print(message, style="bold", highlight=False)
    if new_line:
        __CONSOLE__.print()


def rule(message: str = "") -> None:
    __CONSOLE__.rule(message)


def normal(message: str, new_line=False) -> None:
    __CONSOLE__.print(" " + message, highlight=False)
    if new_line:
        __CONSOLE__.print()


def file_stats(s):
    t = rich.text.Text(f"{s.original_file.name}\n")
    t.append(
        f"{human_size(s.original_file_size)} \u2192 {human_size(s.processed_file_size)}, saved {human_size(s.delta_size)}",
        style="grey50",
    )

    cols = rich.columns.Columns(
        [
            rich.text.Text(f" \u2713 {elapsed(s.elapsed)}"),
            t,
        ],
        expand=False,
    )
    __CONSOLE__.print(cols, highlight=False)


def folder_stats(s):
    if s.processed_files_stats:
        important(
            f"Processed {len(s.processed_files_stats)} files in {elapsed(s.elapsed)}"
        )
        important(
            f"{human_size(s.total_original_size)} \u2192 {human_size(s.total_processed_size)}, new size {percent(s.total_original_size, s.total_processed_size)} of original, saved {human_size(s.total_delta_size)}",
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
        console=__CONSOLE__,
    )
    p.add_task(total=total, description="")
    return p


def progress_update(progress: object, description: str) -> None:
    task = progress.task_ids[0]
    progress.update(task, description=description)


def progress_advance(progress: object) -> None:
    task = progress.task_ids[0]
    progress.advance(task)


def verbose(message: str, new_line=False) -> None:
    if __verbose:
        __CONSOLE__.print("   " + message, style="grey50", highlight=False)
        if new_line:
            __CONSOLE__.print()


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
