"""Observe ordinary source file reads and mutate real files at guarded boundaries."""

from __future__ import annotations

import builtins
import io
import os
from pathlib import Path
from typing import Any

import numpy as np
import pytest


class SourceEvent:
    """One-shot filesystem event; never replace a product function or descriptor."""

    def __init__(self, source: Path, timing: str, extension_size: int = 0) -> None:
        self.source = source
        self.timing = timing
        self.payload_offset = 1024 + extension_size
        self.original_size = source.stat().st_size
        self.events: list[tuple[str, int]] = []
        self.header_observed = False

    def before(self, handle: Any) -> None:
        offset = handle.tell()
        if self.events:
            return
        if self.timing == "extension" and 1024 <= offset < self.payload_offset:
            assert self.header_observed, "extension mutation preceded identity-header read"
            self.shorten("extension", offset, offset)
        elif self.timing == "payload" and offset >= self.payload_offset:
            assert self.header_observed, "payload mutation preceded identity-header read"
            self.shorten("payload", offset, self.payload_offset)

    def after(self, handle: Any) -> None:
        if handle.tell() == 1024:
            self.header_observed = True
        if self.events or self.timing != "completion":
            return
        if handle.tell() == self.original_size:
            assert self.header_observed, "completion mutation preceded identity-header read"
            previous = self.source.stat()
            # Same-length identity mutation, after the final pixel operation returns.
            os.utime(self.source, ns=(previous.st_atime_ns, previous.st_mtime_ns + 1_000_000_000))
            assert self.source.stat().st_mtime_ns != previous.st_mtime_ns
            self.events.append(("completion", handle.tell()))

    def shorten(self, name: str, offset: int, size: int) -> None:
        assert size < self.original_size
        with self.source.open("r+b") as mutation:
            mutation.truncate(size)
        assert self.source.stat().st_size == size
        self.events.append((name, offset))

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_builtin_open = builtins.open
        real_io_open = io.open
        real_fromfile = np.fromfile
        event = self

        class ObservedFile:
            def __init__(self, handle: Any) -> None:
                self.handle = handle

            def __getattr__(self, name: str) -> Any:
                return getattr(self.handle, name)

            def __enter__(self) -> Any:
                self.handle.__enter__()
                return self

            def __exit__(self, *args: Any) -> Any:
                return self.handle.__exit__(*args)

            def read(self, *args: Any) -> Any:
                event.before(self.handle)
                result = self.handle.read(*args)
                event.after(self.handle)
                return result

            def readinto(self, *args: Any) -> Any:
                event.before(self.handle)
                result = self.handle.readinto(*args)
                event.after(self.handle)
                return result

        def opened(real: Any, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            handle = real(file, mode, *args, **kwargs)
            if isinstance(file, (str, Path)) and Path(file) == event.source and mode == "rb":
                return ObservedFile(handle)
            return handle

        def builtin_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            return opened(real_builtin_open, file, mode, *args, **kwargs)

        def io_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            return opened(real_io_open, file, mode, *args, **kwargs)

        def fromfile(file: Any, *args: Any, **kwargs: Any) -> Any:
            # NumPy performs native reads rather than calling Python file.read.
            # Observe that filesystem operation, retaining the real native reader.
            if isinstance(file, ObservedFile):
                event.before(file.handle)
                result = real_fromfile(file.handle, *args, **kwargs)
                event.after(file.handle)
                return result
            return real_fromfile(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", builtin_open)
        monkeypatch.setattr(io, "open", io_open)
        monkeypatch.setattr(np, "fromfile", fromfile)

    def assert_occurred(self) -> None:
        assert self.header_observed
        assert len(self.events) == 1, f"requested {self.timing} filesystem event did not occur"
        name, offset = self.events[0]
        assert name == self.timing
        if name == "extension":
            assert 1024 <= offset < self.payload_offset
        elif name == "payload":
            assert offset >= self.payload_offset
        else:
            assert offset == self.original_size
