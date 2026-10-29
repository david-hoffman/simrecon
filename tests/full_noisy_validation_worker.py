"""Bounded validation worker; execute each request through the public module CLI."""

from __future__ import annotations

import contextlib
import json
import os
import runpy
import sys
import threading
import time
from pathlib import Path
from typing import Any


def fifo_witness(path: str, receipt: str, deadline: float) -> None:
    until = time.monotonic() + deadline
    while time.monotonic() < until:
        try:
            fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError:
            time.sleep(0.005)
            continue
        Path(receipt).write_text("actual FIFO reader reached; writer sends no bytes\n")
        try:
            time.sleep(max(0, until - time.monotonic()) + 5)
        finally:
            os.close(fd)
        return


def main() -> None:
    print(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)
    for line in sys.stdin:
        request: dict[str, Any] = json.loads(line)
        if "fifo_witness" in request:
            threading.Thread(
                target=fifo_witness,
                args=(
                    request["fifo_witness"],
                    request["witness_receipt"],
                    request["deadline_s"],
                ),
            ).start()
        with (
            Path(request["stdout"]).open("w") as stdout,
            Path(request["stderr"]).open("w") as stderr,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            argv = sys.argv
            sys.argv = ["scripts.full_noisy_study", *request["argv"]]
            try:
                try:
                    runpy.run_module(
                        "scripts.full_noisy_study", run_name="__main__", alter_sys=True
                    )
                    status = 0
                except SystemExit as stopped:
                    if stopped.code is None:
                        status = 0
                    elif type(stopped.code) is int:
                        status = stopped.code
                    else:
                        print(stopped.code, file=sys.stderr)
                        status = 1
                except BaseException as error:
                    sys.excepthook(type(error), error, error.__traceback__)
                    raise SystemExit(1) from None
            finally:
                sys.argv = argv
        print(
            json.dumps({"request": request["request"], "status": status, "pid": os.getpid()}),
            flush=True,
        )


if __name__ == "__main__":
    main()
