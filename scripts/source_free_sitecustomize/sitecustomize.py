"""Render Python warnings and uncaught exceptions without source snippets."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import traceback
import warnings
from collections.abc import Generator
from copy import copy
from types import TracebackType
from typing import Any, TextIO

ORIGINAL_FRAME_FORMATTER: Any = traceback.StackSummary.format_frame_summary
ORIGINAL_EXCEPTION_ONLY_FORMATTER: Any = traceback.TracebackException.format_exception_only
ORIGINAL_TIMEOUT_MESSAGE: Any = subprocess.TimeoutExpired.__str__
ORIGINAL_PROCESS_MESSAGE: Any = subprocess.CalledProcessError.__str__


def executable_label(command: Any) -> str:
    """Retain an argv executable without rendering its command arguments."""
    if isinstance(command, (list, tuple)) and command:
        executable = command[0]
        if isinstance(executable, (str, bytes, os.PathLike)):
            return os.fsdecode(executable)
    return "<command executable not recorded>"


def timeout_message(self: subprocess.TimeoutExpired) -> str:
    """Preserve the standard timeout meaning with source-free command identity."""
    safe_exception = copy(self)
    safe_exception.cmd = executable_label(self.cmd)
    return ORIGINAL_TIMEOUT_MESSAGE(safe_exception)


def process_message(self: subprocess.CalledProcessError) -> str:
    """Preserve standard child exit or signal meaning without command arguments."""
    safe_exception = copy(self)
    safe_exception.cmd = executable_label(self.cmd)
    return ORIGINAL_PROCESS_MESSAGE(safe_exception)


def format_warning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    line: str | None = None,
) -> str:
    """Retain warning identity and location without consulting source lines."""
    return f"{filename}:{lineno}: {category.__name__}: {message}\n"


def render_exception(
    exception: BaseException,
    trace: TracebackType | None,
    stream: TextIO,
    seen: set[int] | None = None,
) -> None:
    """Preserve exception chains, groups and stack locations without locals."""
    if seen is None:
        seen = set()
    if id(exception) in seen:
        return
    seen.add(id(exception))
    if exception.__cause__ is not None:
        render_exception(exception.__cause__, exception.__cause__.__traceback__, stream, seen)
        stream.write("The above exception was the direct cause of the following exception:\n")
    elif exception.__context__ is not None and not exception.__suppress_context__:
        render_exception(exception.__context__, exception.__context__.__traceback__, stream, seen)
        stream.write("During handling of the above exception, another exception occurred:\n")
    if trace is not None:
        stream.write("Traceback (most recent call last):\n")
        for frame, lineno in traceback.walk_tb(trace):
            stream.write(
                f'  File "{frame.f_code.co_filename}", line {lineno}, in {frame.f_code.co_name}\n'
            )
    if isinstance(exception, SyntaxError):
        stream.write(f'  File "{exception.filename}", line {exception.lineno}\n')
        message = exception.msg
    else:
        message = str(exception)
    stream.write(f"{type(exception).__name__}: {message}\n")
    for note in getattr(exception, "__notes__", ()):
        stream.write(f"{note}\n")
    if isinstance(exception, BaseExceptionGroup):
        for index, child in enumerate(exception.exceptions, start=1):
            stream.write(f"Exception group child {index}:\n")
            render_exception(child, child.__traceback__, stream, seen)


def exception_hook(
    category: type[BaseException], exception: BaseException, trace: TracebackType | None
) -> None:
    """Handle an uncaught Python exception using source-free output."""
    render_exception(exception, trace, sys.stderr)


def thread_hook(arguments: threading.ExceptHookArgs) -> None:
    """Retain uncaught thread exceptions through the same renderer."""
    if arguments.exc_value is not None:
        exception_hook(arguments.exc_type, arguments.exc_value, arguments.exc_traceback)


def clean_snapshot(snapshot: traceback.TracebackException) -> None:
    """Remove lazy source lookups from a standard traceback snapshot."""
    snapshot.stack = traceback.StackSummary.from_list(
        [
            traceback.FrameSummary(
                frame.filename, frame.lineno, frame.name, lookup_line=False, line=""
            )
            for frame in snapshot.stack
        ]
    )
    if hasattr(snapshot, "text"):
        snapshot.text = ""
    for linked in (snapshot.__cause__, snapshot.__context__):
        if linked is not None:
            clean_snapshot(linked)
    for child in snapshot.exceptions or ():
        clean_snapshot(child)


def format_frame_summary(
    self: traceback.StackSummary, frame_summary: traceback.FrameSummary, **kwargs: Any
) -> str:
    """Render a standard stack frame with location but no source or locals."""
    safe_frame = traceback.FrameSummary(
        frame_summary.filename,
        frame_summary.lineno,
        frame_summary.name,
        lookup_line=False,
        line="",
    )
    return ORIGINAL_FRAME_FORMATTER(self, safe_frame, **kwargs)


def format_snapshot_exception_only(
    self: traceback.TracebackException,
    *,
    show_group: bool = False,
    _depth: int = 0,
    **kwargs: Any,
) -> Generator[str]:
    """Suppress SyntaxError source in every standard exception-only renderer."""
    safe_snapshot = copy(self)
    if hasattr(safe_snapshot, "text"):
        safe_snapshot.text = ""
    yield from ORIGINAL_EXCEPTION_ONLY_FORMATTER(
        safe_snapshot, show_group=show_group, _depth=_depth, **kwargs
    )


def format_exception(
    exc: BaseException | type[BaseException],
    value: BaseException | None = None,
    tb: TracebackType | None = None,
    limit: int | None = None,
    *,
    chain: bool = True,
) -> list[str]:
    """Support standard modern and legacy traceback formatting calls."""
    exception = exc if isinstance(exc, BaseException) else value
    if exception is None:
        return ["NoneType: None\n"]
    snapshot = traceback.TracebackException(
        type(exception),
        exception,
        exception.__traceback__ if isinstance(exc, BaseException) else tb,
        limit=limit,
        lookup_lines=False,
        capture_locals=False,
    )
    clean_snapshot(snapshot)
    return list(snapshot.format(chain=chain))


def print_exception(
    exc: BaseException | type[BaseException],
    value: BaseException | None = None,
    tb: TracebackType | None = None,
    limit: int | None = None,
    file: TextIO | None = None,
    chain: bool = True,
) -> None:
    """Print standard traceback diagnostics through source-free snapshots."""
    stream = sys.stderr if file is None else file
    stream.writelines(format_exception(exc, value, tb, limit, chain=chain))


def format_exc(limit: int | None = None, chain: bool = True) -> str:
    """Format the currently handled exception without source or locals."""
    exception = sys.exception()
    return (
        "NoneType: None\n"
        if exception is None
        else "".join(format_exception(exception, limit=limit, chain=chain))
    )


def print_exc(limit: int | None = None, file: TextIO | None = None, chain: bool = True) -> None:
    """Print the currently handled exception through the standard API."""
    stream = sys.stderr if file is None else file
    stream.write(format_exc(limit=limit, chain=chain))


def install() -> None:
    """Install diagnostic renderers without changing warning filters."""
    warnings.formatwarning = format_warning
    sys.excepthook = exception_hook
    threading.excepthook = thread_hook
    traceback.format_exception = format_exception
    traceback.print_exception = print_exception
    traceback.format_exc = format_exc
    traceback.print_exc = print_exc
    traceback.StackSummary.format_frame_summary = format_frame_summary
    traceback.TracebackException.format_exception_only = format_snapshot_exception_only
    subprocess.TimeoutExpired.__str__ = timeout_message
    subprocess.CalledProcessError.__str__ = process_message


install()
