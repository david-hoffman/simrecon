"""Independent neutral file inputs and real ImageJ write-failure observer."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def priism_file(path: Path, pixels: NDArray[np.generic], *, extension: bytes = b"") -> bytes:
    """Build the permitted Priism subset from the public byte offsets."""
    sections, rows, columns = pixels.shape
    endian = ">" if pixels.dtype.byteorder == ">" else "<"
    mode = 6 if pixels.dtype.kind == "u" else 2
    header = bytearray(1024)
    for offset, value in (
        (0, columns),
        (4, rows),
        (8, sections),
        (12, mode),
        (28, columns),
        (32, rows),
        (36, sections),
        (64, 1),
        (68, 2),
        (72, 3),
        (92, len(extension)),
    ):
        struct.pack_into(endian + "i", header, offset, value)
    for offset, value in ((40, 0.25), (44, 0.5), (48, 1.0)):
        struct.pack_into(endian + "f", header, offset, value)
    for offset, value in ((96, -16224), (180, 1), (182, 0), (196, 1)):
        struct.pack_into(endian + "h", header, offset, value)
    encoded = bytes(header) + extension + pixels.tobytes(order="C")
    path.write_bytes(encoded)
    return encoded


def imagej_write_failure(source: Path, destination: Path, config: dict[str, object]) -> None:
    """Child-only real write failure; no source-handle or cleanup strategy oracle."""
    import errno
    import json
    import signal

    def incomplete(reason: str) -> None:
        print(json.dumps({"classification": "incomplete_fixture", "incomplete_reason": reason}))

    try:
        import resource
    except ImportError:
        incomplete("POSIX resource module unavailable")
        return
    if not hasattr(resource, "RLIMIT_FSIZE") or not hasattr(signal, "SIGXFSZ"):
        incomplete("file-size limit or signal unavailable")
        return

    import simrecon as sr

    original = source.read_bytes()
    info = sr.harmonize(sr.inspect(source), config=config)
    unrestricted = destination.with_name("unrestricted.tif")
    report = sr.export_imagej(unrestricted, info)
    unrestricted_bytes = unrestricted.stat().st_size
    assert report.planes_written == 2 and source.read_bytes() == original
    limit = 65536
    assert unrestricted_bytes > limit
    assert not destination.exists()
    try:
        previous_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
        previous_handler = signal.getsignal(signal.SIGXFSZ)
    except (OSError, ValueError) as failure:
        incomplete("cannot inspect resource settings: " + type(failure).__name__)
        return
    signal_count = 0

    def count_signal(number: int, frame: object) -> None:
        nonlocal signal_count
        signal_count += 1

    limit_verified = False
    setup_problem = None
    restoration_problem = None
    export_succeeded = False
    failure_name = None
    failure_is_os_error = False
    failure_errno = None
    try:
        try:
            signal.signal(signal.SIGXFSZ, count_signal)
            resource.setrlimit(resource.RLIMIT_FSIZE, (limit, previous_limit[1]))
            limit_verified = resource.getrlimit(resource.RLIMIT_FSIZE) == (limit, previous_limit[1])
        except (OSError, ValueError) as failure:
            setup_problem = type(failure).__name__
        if limit_verified:
            # Prearm only around the synchronous public operation. The handler
            # only counts real signals; no fixture files/reports are written here.
            try:
                sr.export_imagej(destination, info)
            except Exception as failure:
                failure_name = type(failure).__name__
                failure_is_os_error = isinstance(failure, OSError)
                failure_errno = failure.errno if isinstance(failure, OSError) else None
            else:
                export_succeeded = True
    finally:
        try:
            resource.setrlimit(resource.RLIMIT_FSIZE, previous_limit)
        except (OSError, ValueError) as failure:
            restoration_problem = "resource: " + type(failure).__name__
        finally:
            try:
                signal.signal(signal.SIGXFSZ, previous_handler)
            except (OSError, ValueError) as failure:
                restoration_problem = "signal: " + type(failure).__name__
    limits_restored = resource.getrlimit(resource.RLIMIT_FSIZE) == previous_limit
    handler_restored = signal.getsignal(signal.SIGXFSZ) == previous_handler
    source_preserved = source.read_bytes() == original
    incomplete_reason = None
    if setup_problem or not limit_verified:
        incomplete_reason = "resource intervention not verified"
    elif restoration_problem or not limits_restored or not handler_restored:
        incomplete_reason = "resource or signal restoration not verified"
    elif signal_count <= 0:
        # A valid early resource preflight can avoid the write. That leaves this
        # fixture unexercised; it is not a product failure or a passing witness.
        incomplete_reason = "no observed SIGXFSZ: operation-time write failure unexercised"
    if incomplete_reason:
        classification = "incomplete_fixture"
    elif (
        export_succeeded
        or not failure_is_os_error
        or failure_errno != errno.EFBIG
        or not source_preserved
    ):
        classification = "witnessed_outcome_failure"
    else:
        classification = "witnessed_expected_failure"
    # Emit only after finally. A partial destination may be retained or removed.
    print(
        json.dumps(
            {
                "classification": classification,
                "incomplete_reason": incomplete_reason,
                "unrestricted_planes": report.planes_written,
                "unrestricted_bytes": unrestricted_bytes,
                "limit_bytes": limit,
                "limit_verified": limit_verified,
                "sigxfsz_count": signal_count,
                "export_succeeded": export_succeeded,
                "failure": failure_name,
                "failure_is_os_error": failure_is_os_error,
                "errno_is_efbig": failure_errno == errno.EFBIG,
                "limits_restored": limits_restored,
                "signal_handler_restored": handler_restored,
                "setup_problem": setup_problem,
                "restoration_problem": restoration_problem,
                "source_preserved": source_preserved,
            }
        )
    )
