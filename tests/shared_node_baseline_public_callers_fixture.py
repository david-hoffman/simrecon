"""Owned public callers and run-bound A09 evidence; no runtime source inspection."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import socketserver
import ssl
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/baseline-compatibility-20261013/A09"
RUN_ID = os.environ.get("SIMRECON_A09_RUN_ID") or "standalone-" + uuid.uuid4().hex
# Evidence placement must not change the shared reader-cache reservation lock.
RUN = Path(os.environ.get("SIMRECON_PROTOCOLS_EVIDENCE", str(EVIDENCE))) / "authored-runs" / RUN_ID
HARNESS = ROOT / "scripts/source_free_check.py"
READER = ROOT / "scripts/prepare_imagej_reader.py"
VERIFY = ROOT / "scripts/verify.py"
GENERATOR = ROOT / "scripts/generate_reference_fixtures.py"
CACHE = ROOT / "artifacts/imagej-reader"
ACTIVE: set[int] = set()
DECLARATIONS: dict[str, Any] = json.loads(
    (ROOT / "tests/data/reader-public-input-context.json").read_text()
)["artifact_declarations"]
PHASES = [
    "sync",
    "coverage-clean",
    "lint",
    "format",
    "types",
    "tests",
    "coverage-combine",
    "coverage-json",
    "coverage-html",
    "coverage-report",
    "wheel",
    "wheel-import",
    "audit",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(kind: str, data: dict[str, Any]) -> Path:
    directory = RUN / "observations"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{kind}-{uuid.uuid4().hex}.json"
    path.write_text(json.dumps({"run_id": RUN_ID, **data}, indent=2, sort_keys=True) + "\n")
    return path


def invoke(
    argv: list[str | Path],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: float = 60,
    kind: str = "command",
    observation: dict[str, Any] | None = None,
    before_rescue_observer: Callable[[], dict[str, Any]] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Bound waits; retain source-free output and exact actual public argv."""
    command = [str(item) for item in argv]
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    ACTIVE.add(process.pid)
    children: set[int] = set()
    monitor_stop = threading.Event()

    def process_table() -> dict[int, tuple[int, str]]:
        table = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,stat="],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return {
            int(parts[0]): (int(parts[1]), parts[2])
            for line in table.stdout.splitlines()
            if len(parts := line.split()) == 3
        }

    def watch_children() -> None:
        while not monitor_stop.is_set():
            table = process_table()
            descendants = {process.pid, *children}
            while True:
                found = {pid for pid, (parent, _) in table.items() if parent in descendants}
                if found <= descendants:
                    break
                descendants.update(found)
            children.update(descendants - {process.pid})
            monitor_stop.wait(0.5)

    monitor = None
    if timeout >= 200 and kind == "actual-reader":
        monitor = threading.Thread(target=watch_children, daemon=True)
    timed_out = False
    stdout = stderr = ""
    failure: BaseException | None = None
    cleanup_events: list[dict[str, Any]] = []
    before_rescue = None

    def owned_processes() -> dict[int, tuple[int, str]]:
        owned = {}
        for pid, entry in process_table().items():
            try:
                if os.getsid(pid) == process.pid:
                    owned[pid] = entry
            except ProcessLookupError:
                continue
        return owned

    def stop_owned_session() -> tuple[str, str]:
        # A descendant may change group while remaining in our new session.
        # Keep waiting parents alive so they can reap terminated children.
        for sig, bound in ((signal.SIGTERM, 3), (signal.SIGKILL, 7)):
            deadline = time.monotonic() + bound
            signalled: set[int] = set()
            while time.monotonic() < deadline:
                process.poll()
                owned = owned_processes()
                if not owned:
                    try:
                        output = process.communicate(timeout=max(0.01, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        break
                    if not owned_processes():
                        ACTIVE.discard(process.pid)
                        return output
                parents = {parent for parent, _ in owned.values()}
                leaves = set(owned) - parents
                for pid in leaves - signalled:
                    if "Z" in owned[pid][1]:
                        continue
                    with contextlib.suppress(ProcessLookupError):
                        # Recheck session ownership immediately before signalling.
                        if os.getsid(pid) == process.pid:
                            os.kill(pid, sig)
                            cleanup_events.append(
                                {"signal": sig.name, "bound_s": bound, "pid": pid}
                            )
                    signalled.add(pid)
                time.sleep(0.05)
        raise AssertionError(
            "Tooling blocker: owned session cleanup unproven; cache restore blocked"
        )

    try:
        if monitor is not None:
            monitor.start()
        stdout, stderr = process.communicate(timeout=timeout)
        if observation is not None:
            # Read-only observation before the existing unconditional safety cleanup.
            before_rescue = {
                "at_s": time.monotonic() - started,
                "owned_process_states": {
                    str(pid): list(state) for pid, state in owned_processes().items()
                },
                "limitation": "Session snapshot; zombies present; no PID birth-time identity",
            }
            if before_rescue_observer is not None:
                before_rescue["state"] = before_rescue_observer()
    except subprocess.TimeoutExpired:
        timed_out = True
        stdout, stderr = stop_owned_session()
    except BaseException as error:
        failure = error
        try:
            stdout, stderr = stop_owned_session()
        except BaseException as cleanup_error:
            record(
                "cleanup-blocked",
                {
                    "pid": process.pid,
                    "category": type(error).__name__,
                    "cleanup_category": type(cleanup_error).__name__,
                    "restore_blocked": True,
                },
            )
        record(
            kind,
            {
                "argv": command,
                "cwd": str(cwd),
                "status": process.returncode,
                "duration_s": time.monotonic() - started,
                "exception_category": type(error).__name__,
                "stdout": stdout,
                "stderr": stderr,
                "pid": process.pid,
            },
        )
        raise
    finally:
        monitor_stop.set()
        if monitor is not None and monitor.ident is not None:
            monitor.join(timeout=6)
            if monitor.is_alive():
                record("cleanup-blocked", {"pid": process.pid, "monitor_stopped": False})
                if failure is None:
                    raise AssertionError("Tooling blocker: child observer did not stop")
        if failure is None:
            if owned_processes():
                stdout, stderr = stop_owned_session()
            else:
                ACTIVE.discard(process.pid)
        record(
            "owned-process-cleanup",
            {
                "pid": process.pid,
                "stopped": process.pid not in ACTIVE,
                "exception_category": type(failure).__name__ if failure else None,
                "events": cleanup_events,
                "limitation": "Ordinary unwinding only; no recovery guarantee after author SIGKILL",
            },
        )
    elapsed = time.monotonic() - started
    cleanup = None
    if monitor is not None:
        table = process_table()
        cleanup = {
            "observed_child_pids": sorted(children),
            "remaining_child_states": {str(pid): table[pid][1] for pid in children if pid in table},
        }
    if observation is not None:
        observation.update(
            {
                "duration_s": elapsed,
                "child_cleanup": cleanup,
                "before_rescue": before_rescue,
                "outer_timeout": timed_out,
                "status": process.returncode,
            }
        )
    record(
        kind,
        {
            "argv": command,
            "cwd": str(cwd),
            "status": process.returncode,
            "duration_s": elapsed,
            "outer_timeout": timed_out,
            "pid": process.pid,
            "stdout": stdout,
            "stderr": stderr,
            "child_cleanup": cleanup,
            "before_rescue": before_rescue,
            "measurement_namespace": {
                key: (env or os.environ).get(key)
                for key in (
                    "COVERAGE_FILE",
                    "COVERAGE_RCFILE",
                    "COVERAGE_PROCESS_START",
                    "COVERAGE_PROCESS_CONFIG",
                )
            },
        },
    )
    if timed_out:
        raise AssertionError("Tooling nonwitness: supported outer wait expired")
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def python(
    script: Path,
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    args: tuple[str, ...] = (),
    timeout: float = 60,
    kind: str = "python",
    observation: dict[str, Any] | None = None,
    before_rescue_observer: Callable[[], dict[str, Any]] | None = None,
) -> subprocess.CompletedProcess[str]:
    return invoke(
        [sys.executable, HARNESS, "--timeout", str(timeout - 5), "python", script, *args],
        cwd=cwd,
        env=env,
        timeout=timeout,
        kind=kind,
        observation=observation,
        before_rescue_observer=before_rescue_observer,
    )


def inventory(directory: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise AssertionError("Tooling blocker: cache contains foreign symlink")
        stat = path.stat()
        result[str(path.relative_to(directory))] = {
            "directory": path.is_dir(),
            "mode": stat.st_mode,
            "inode": stat.st_ino,
            "size": stat.st_size,
            "sha256": digest(path) if path.is_file() else None,
        }
    return result


class ReaderReservation:
    """Rename the authentic directory intact; only mutate new owned copies."""

    def __init__(self) -> None:
        self.backup = CACHE.with_name(f"imagej-reader-A09-backup-{uuid.uuid4().hex}")
        RUN.mkdir(parents=True, exist_ok=True)
        self.journal = RUN / f"recovery-{uuid.uuid4().hex}.json"
        self.lock = EVIDENCE / "reader-reservation.lock"
        self.before: dict[str, Any] = {}
        self.original_inode: int | None = None
        self.original_mode: int | None = None
        self.fixture_inode: int | None = None

    def journal_write(self, stage: str) -> None:
        self.journal.write_text(
            json.dumps(
                {
                    "stage": stage,
                    "run_id": RUN_ID,
                    "original": str(CACHE),
                    "backup": str(self.backup),
                    "original_inode": self.original_inode,
                    "original_mode": self.original_mode,
                    "fixture_inode": self.fixture_inode,
                    "before": self.before,
                    "limitation": "Normal unwinding only; journal permits SIGKILL recovery",
                },
                indent=2,
            )
            + "\n"
        )

    def __enter__(self) -> ReaderReservation:
        """Preserve the entire original cache and journal partial preparation."""
        self.lock.mkdir()  # Exclusive A09 reservation; an existing lock is a blocker.
        self.before = inventory(CACHE)
        self.original_inode = CACHE.stat().st_ino
        self.original_mode = CACHE.stat().st_mode
        self.journal_write("before-rename")
        CACHE.rename(self.backup)
        try:
            self.journal_write("original-backed-up")
            CACHE.mkdir()
            self.fixture_inode = CACHE.stat().st_ino
            self.journal_write("fixture-owned")
        except BaseException:
            if self.fixture_inode is not None:
                self.__exit__()
            elif not CACHE.exists() and not CACHE.is_symlink():
                self.backup.rename(CACHE)
                self.journal_write("restored-after-enter-failure")
                self.lock.rmdir()
            else:
                self.journal_write("BLOCKED-enter-resource-conflict")
            raise
        return self

    def seed(self, *, omit: str | None = None) -> None:
        for name, expected in DECLARATIONS.items():
            original = self.backup / name
            assert original.stat().st_size == expected["size_bytes"]
            assert digest(original) == expected["sha256"]
            if name != omit:
                shutil.copyfile(original, CACHE / name)
                assert (CACHE / name).stat().st_ino != original.stat().st_ino
        (CACHE / "inputs.json").write_text('{"stale_A08_identity":true}\n')

    def __exit__(self, *_: object) -> None:
        """Restore only this owned fixture; retain backup on resource conflict."""
        if ACTIVE:
            self.journal_write("BLOCKED-owned-processes-active")
            raise AssertionError(
                "Tooling blocker: owned process cleanup incomplete; backup retained"
            )
        if not CACHE.is_dir() or CACHE.is_symlink() or CACHE.stat().st_ino != self.fixture_inode:
            self.journal_write("BLOCKED-unexpected-cache-replacement")
            raise AssertionError("Tooling blocker: unexpected cache replacement; backup retained")
        if inventory(self.backup) != self.before:
            self.journal_write("BLOCKED-backup-changed")
            raise AssertionError("Tooling blocker: authentic backup changed")
        shutil.rmtree(CACHE)
        self.backup.rename(CACHE)
        after = inventory(CACHE)
        restored = (
            after == self.before
            and CACHE.stat().st_ino == self.original_inode
            and CACHE.stat().st_mode == self.original_mode
        )
        record(
            "cache-restoration",
            {
                "before": self.before,
                "after": after,
                "restored": restored,
                "journal": str(self.journal),
                "original_inode": self.original_inode,
                "restored_inode": CACHE.stat().st_ino,
                "original_mode": self.original_mode,
                "restored_mode": CACHE.stat().st_mode,
            },
        )
        self.journal_write("restored" if restored else "BLOCKED-restoration-mismatch")
        assert restored
        self.lock.rmdir()


def selected_java() -> str:
    java = os.environ.get("SIMRECON_JAVA")
    assert java and Path(java).is_file(), "Tooling blocker: selected actual JDK missing"
    return java


def java_wrapper(tmp: Path, variant: str) -> Path:
    """Transparent selected executable; delegate actual source launching to the JDK."""
    wrapper = tmp / "selected-java"
    property_lines = [
        f"    java.version = {'20.0.1' if variant == 'wrong-version' else '21.0.7'}",
        "    java.vendor = A08-disposable-vendor",
        "    os.name = A08-disposable-platform",
        "    os.arch = A08-disposable-architecture",
    ]
    if variant == "missing-vendor":
        property_lines = [line for line in property_lines if "java.vendor" not in line]
    if variant == "missing-platform":
        property_lines = [
            line for line in property_lines if "os.name" not in line and "os.arch" not in line
        ]
    wrapper.write_text(
        f"#!{sys.executable}\n"
        "import os,sys\n"
        f"variant={variant!r}\n"
        "if variant == 'failure': sys.exit(37)\n"
        "if any(a.endswith('.java') for a in sys.argv[1:]):\n"
        "    if variant == 'launcher-failure': sys.exit(38)\n"
        f"    os.execv({selected_java()!r}, [{selected_java()!r}, *sys.argv[1:]])\n"
        f"print({chr(10).join(property_lines)!r}, file=sys.stderr)\n"
    )
    wrapper.chmod(0o700)
    return wrapper


def reader(
    env: dict[str, str] | None = None,
    *,
    driver: Path | None = None,
    timeout: float = 60,
    observation: dict[str, Any] | None = None,
    before_rescue_observer: Callable[[], dict[str, Any]] | None = None,
) -> subprocess.CompletedProcess[str]:
    return python(
        driver or READER,
        env=env,
        timeout=timeout,
        kind="actual-reader",
        observation=observation,
        before_rescue_observer=before_rescue_observer,
    )


def dictionaries(value: Any) -> Iterator[dict[str, Any]]:
    """Find records without prescribing their enclosing field organization."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from dictionaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from dictionaries(child)


def assert_identity(
    java: str,
    tmp: Path,
    env: dict[str, str] | None = None,
    observed_urls: dict[str, str] | None = None,
) -> None:
    """Bind semantic input records to independent public Java/host observations.

    The decoder recognizes the supplied public manifest's descriptive vocabulary,
    not a mandatory schema. An unrecognized association is a material meaning gap.
    Cached URL provenance is uncorroborated; reached transport URLs are bound exactly.
    """
    executable = shutil.which(java, path=(env or os.environ).get("PATH"))
    assert executable, "Tooling blocker: independent selected Java resolution failed"
    properties = invoke(
        [executable, "-XshowSettings:properties", "-version"],
        env=env,
        kind="independent-java-properties",
    )
    assert properties.returncode == 0, "Environment failure: independent Java properties"
    observed = dict(
        re.findall(
            r"^\s*(java.version|java.vendor|os.name|os.arch)\s*=\s*(.+?)\s*$",
            properties.stderr,
            re.MULTILINE,
        )
    )
    assert set(observed) == {"java.version", "java.vendor", "os.name", "os.arch"}
    launcher = tmp / "A09PublicLauncher.java"
    launcher.write_text(
        "class A09PublicLauncher { public static void main(String[] args) { "
        'System.out.println("A09-independent-launcher"); } }\n'
    )
    launch = invoke([executable, launcher], env=env, kind="independent-java-source-launcher")
    assert launch.returncode == 0 and launch.stdout.strip() == "A09-independent-launcher"
    document = json.loads((CACHE / "inputs.json").read_text())
    records = list(dictionaries(document))
    record(
        "reader-identity",
        {
            "manifest": document,
            "sha256": digest(CACHE / "inputs.json"),
            "independent": {
                "selected": java,
                "resolved": executable,
                "properties": observed,
                "source_launcher_status": launch.returncode,
                "host": platform.platform(),
            },
            "observed_urls": observed_urls,
            "cached_url_limit": "No current fetch witness",
        },
    )
    for name, expected in DECLARATIONS.items():
        matching = [
            item
            for item in records
            if isinstance(item.get("path"), str)
            and Path(item["path"]).resolve() == (CACHE / name).resolve()
        ]
        assert matching, f"Material identity meaning gap: jar path record for {name}"
        for item in matching:
            assert item.get("sha256") == expected["sha256"]
            assert type(item.get("size_bytes")) is int
            assert item["size_bytes"] == expected["size_bytes"]
            url = item.get("url")
            assert isinstance(url, str), f"Material identity meaning gap: jar URL for {name}"
            parsed = urlsplit(url)
            assert parsed.scheme and (parsed.netloc or parsed.path)
            if observed_urls and name in observed_urls:
                assert url == observed_urls[name]
        assert digest(CACHE / name) == expected["sha256"]
    selected = [
        item
        for item in records
        if isinstance(item.get("executable"), str)
        and Path(item["executable"]).resolve() == Path(executable).resolve()
    ]
    assert selected, "Material identity meaning gap: selected Java executable record"
    for item in selected:
        assert item.get("version") == observed["java.version"] == "21.0.7"
        assert item.get("vendor") == observed["java.vendor"]
        recorded_platform = item.get("platform")
        assert isinstance(recorded_platform, dict), "Material identity meaning gap: Java platform"
        assert recorded_platform.get("os_name") == observed["os.name"]
        assert recorded_platform.get("os_arch") == observed["os.arch"]
        assert "source_launcher_checked" in item, (
            "Material identity meaning gap: launcher observation"
        )
        assert item["source_launcher_checked"] is True
    hosts = [item["host_platform"] for item in records if "host_platform" in item]
    assert hosts, "Material identity meaning gap: host platform association"
    assert all(value == platform.platform() for value in hosts)


class Transport:
    """Real scoped HTTPS proxy. TLS trust exists only in the tested invocation."""

    def __init__(self, tmp: Path, authentic: Path, mode: str) -> None:
        self.tmp, self.authentic, self.mode = tmp, authentic, mode
        self.stop = threading.Event()
        self.events: list[dict[str, Any]] = []
        self.started = time.monotonic()
        self.server: socketserver.ThreadingTCPServer | None = None
        self.thread: threading.Thread | None = None

    def __enter__(self) -> Transport:
        """Start genuine controlled TLS transport after bounded prerequisites."""
        openssl = shutil.which("openssl")
        assert openssl, "Tooling blocker: openssl prerequisite missing"
        cert, key = self.tmp / "cert.pem", self.tmp / "key.pem"
        certificate = invoke(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                key,
                "-out",
                cert,
                "-days",
                "1",
                "-subj",
                "/CN=A08-owned-transport",
                "-addext",
                "subjectAltName=DNS:downloads.openmicroscopy.org,DNS:sites.imagej.net",
            ],
            timeout=30,
            kind="transport-certificate",
        )
        assert certificate.returncode == 0
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        owner = self

        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                self.connection.settimeout(20)
                first = self.rfile.readline().decode("ascii").strip()
                while self.rfile.readline().strip():
                    pass
                owner.events.append(
                    {"event": "proxy", "request": first, "at_s": time.monotonic() - owner.started}
                )
                assert first.startswith("CONNECT "), "Tooling nonwitness: unsupported proxy request"
                self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
                self.wfile.flush()
                with context.wrap_socket(self.connection, server_side=True) as connection:
                    stream = connection.makefile("rb")
                    request = stream.readline().decode("ascii").strip()
                    while stream.readline().strip():
                        pass
                    owner.events.append(
                        {
                            "event": "request",
                            "request": request,
                            "at_s": time.monotonic() - owner.started,
                        }
                    )
                    if owner.mode == "redirect" and "/A08-redirect" not in request:
                        connection.sendall(
                            b"HTTP/1.1 302 Found\r\n"
                            b"Location: https://sites.imagej.net/A08-redirect\r\n"
                            b"Content-Length: 0\r\nConnection: close\r\n\r\n"
                        )
                        return
                    if owner.mode == "advertised-oversize":
                        connection.sendall(
                            b"HTTP/1.1 200 OK\r\nContent-Length: 10000001\r\n"
                            b"Connection: close\r\n\r\n"
                        )
                        return
                    payload = owner.authentic.read_bytes()
                    if owner.mode == "digest":
                        payload = b"A08-genuine-invalid-download"
                    if owner.mode == "actual-oversize":
                        payload = b"x" * 10000001
                    length = (
                        b""
                        if owner.mode in {"eof", "actual-oversize"}
                        else f"Content-Length: {len(payload)}\r\n".encode()
                    )
                    connection.sendall(
                        b"HTTP/1.1 200 OK\r\n" + length + b"Connection: close\r\n\r\n"
                    )
                    if owner.mode == "socket-timeout":
                        # Authentic incomplete progress, then no EOF before client failure.
                        connection.sendall(payload[:262144])
                        owner.events.append(
                            {
                                "event": "socket-stall-start",
                                "count": min(262144, len(payload)),
                                "scheduled_s": 60,
                                "at_s": time.monotonic() - owner.started,
                            }
                        )
                        cancelled = owner.stop.wait(60)
                        owner.events.append(
                            {
                                "event": "socket-stall-ended",
                                "cancelled": cancelled,
                                "at_s": time.monotonic() - owner.started,
                            }
                        )
                        return
                    try:
                        for offset in range(0, len(payload), 65536):
                            if owner.stop.is_set():
                                break
                            connection.sendall(payload[offset : offset + 65536])
                            owner.events.append(
                                {
                                    "event": "bytes",
                                    "count": min(65536, len(payload) - offset),
                                    "at_s": time.monotonic() - owner.started,
                                }
                            )
                            if owner.mode == "parent-deadline" and owner.stop.wait(5.0):
                                break
                            if owner.mode == "adapted-parent" and owner.stop.wait(0.5):
                                break
                    except (BrokenPipeError, ConnectionResetError, ssl.SSLError) as error:
                        owner.events.append(
                            {
                                "event": "peer-closed",
                                "category": type(error).__name__,
                                "at_s": time.monotonic() - owner.started,
                            }
                        )

        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = False

        self.server = Server(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=False)
        self.thread.start()
        return self

    def environment(self) -> dict[str, str]:
        assert self.server is not None
        env = dict(os.environ)
        proxy = f"http://127.0.0.1:{self.server.server_address[1]}"
        for name in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
            env[name] = proxy
        env["NO_PROXY"] = env["no_proxy"] = ""
        env["SSL_CERT_FILE"] = str(self.tmp / "cert.pem")
        return env

    def observed_url(self) -> str:
        """Bind the actual TLS request authority/path, allowing lawful endpoints."""
        proxy = next(event["request"] for event in self.events if event["event"] == "proxy")
        request = next(event["request"] for event in self.events if event["event"] == "request")
        authority = proxy.split()[1]
        host = authority.removesuffix(":443")
        target = request.split()[1]
        return target if target.startswith("https://") else "https://" + host + target

    def __exit__(self, *_: object) -> None:
        """Stop and join owned transport before restoring the reader cache."""
        self.stop.set()
        assert self.server is not None and self.thread is not None
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        assert not self.thread.is_alive(), "Tooling blocker: owned transport did not terminate"
        record(
            "transport",
            {
                "mode": self.mode,
                "events": self.events,
                "server_thread_stopped": not self.thread.is_alive(),
                "duration_s": time.monotonic() - self.started,
            },
        )


@contextlib.contextmanager
def reserved() -> Iterator[ReaderReservation]:
    with ReaderReservation() as reservation:
        yield reservation


class VerificationFixture:
    """Disposable public CLI repository with genuinely measured native evidence."""

    def __init__(self, directory: Path) -> None:
        self.root = directory / "repository"
        self.root.mkdir()
        (self.root / "src/simrecon").mkdir(parents=True)
        (self.root / "scripts").mkdir()
        # Actual public script, executed with the documented caller repository cwd.
        (self.root / "public-bin").mkdir()
        self.verifier = VERIFY
        (self.root / "src/simrecon/owned.py").write_text("value = 1\n")
        (self.root / "scripts/owned.py").write_text("value = 2\n")
        (self.root / "external.py").write_text(
            "def external(flag):\n    if flag:\n        return 1\n    return 0\n"
            "def excluded(): # pragma: no cover\n    return 3\n"
            "external(True)\nexternal(False)\n"
        )
        (self.root / "control-marker.txt").write_bytes(b"A08-INDEPENDENT-PROTECTED-MARKER\n")
        (self.root / ".gitignore").write_text(
            "artifacts/\ndist/\n.coverage*\npublic-bin/\nphase-driver.py\n"
            "fixture-make\ncontrols.json\nphase-trace.jsonl\nphase-trace.argv\nobserver.json\n"
        )
        self.controls = self.root / "controls.json"
        self.controls.write_text("{}\n")
        driver = self.root / "phase-driver.py"
        driver.write_text(
            f"import sys\nsys.path.insert(0, {str(ROOT / 'tests')!r})\n" + PHASE_DRIVER
        )
        self.make = self.root / "fixture-make"
        self.configure({})
        for args in (
            ["init", "-q"],
            ["config", "--local", "maintenance.auto", "false"],
            ["add", "."],
            [
                "-c",
                "user.name=A08 disposable fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-qm",
                "Independent disposable public evidence fixture",
            ],
        ):
            result = invoke(["git", *args], cwd=self.root, timeout=30, kind="fixture-git")
            assert result.returncode == 0

    def configure(self, controls: dict[str, Any]) -> None:
        from verification_fixture_dispatch import install_native_dispatch

        self.controls.write_text(json.dumps(controls) + "\n")
        dynamic = {
            "coverage-clean",
            "tests",
            "coverage-json",
            "coverage-html",
            "coverage-report",
            "wheel",
            "wheel-import",
        }
        dynamic.update(controls[key] for key in ("fail_phase", "redirect_phase") if key in controls)
        install_native_dispatch(
            self.make, self.root / "phase-driver.py", dynamic_phases=tuple(sorted(dynamic))
        )

    def run(
        self,
        *,
        receipt: str = "artifacts/verification/receipt.json",
        observer: str | None = None,
        load: bool = False,
        make: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
        argv = [
            str(self.verifier),
            "--make",
            make or str(self.make),
            "--uv",
            sys.executable,
            "--receipt",
            receipt,
        ]
        entry = self.verifier
        if observer or load:
            entry = self.root / "public-bin/public-caller.py"
            entry.write_text(
                "import json,os,pathlib,runpy,sys\n"
                f"argv={argv!r}\nroot=pathlib.Path({str(self.root)!r})\n"
                f"selected=root / {receipt!r}\nmode={observer!r}\nload={load!r}\n"
                "busy=False\nfired=False\nevents=[]\n"
                "def hook(event,args):\n"
                "    global busy,fired\n"
                "    if busy or fired or mode is None: return\n"
                "    busy=True\n"
                "    try:\n"
                "        if event not in ('os.mkdir','open'): return\n"
                "        if not isinstance(args[0],(str,bytes,os.PathLike)): return\n"
                "        path=pathlib.Path(os.fsdecode(args[0]))\n"
                "        if not path.is_absolute(): path=root/path\n"
                "        match=(mode=='mkdir' and event=='os.mkdir' and path==selected.parent)\n"
                "        if mode=='late-open' and event=='open' and path.parent==selected.parent:\n"
                "            flags=args[2]\n"
                "            write_flags=os.O_WRONLY|os.O_RDWR|os.O_CREAT\n"
                "            match=isinstance(flags,int) and bool(flags & write_flags)\n"
                "        if not match: return\n"
                "        fired=True\n"
                "        target=root/'.git' if mode=='mkdir' else root/'control-marker.txt'\n"
                "        if mode=='mkdir':\n"
                "            selected.parent.symlink_to(target,target_is_directory=True)\n"
                "        else:\n"
                "            if selected.exists() or selected.is_symlink(): selected.unlink()\n"
                "            selected.symlink_to(target)\n"
                "        events.append({'event':event,'path':str(path),\n"
                "                       'selected':str(selected),'target':str(target),\n"
                "                       'intervened':True})\n"
                "    finally:\n"
                "        busy=False\n"
                "sys.addaudithook(hook)\n"
                "try:\n"
                "    if load:\n"
                "        sys.argv=argv\n"
                "        try: runpy.run_path(argv[0],run_name='A08_operational_preflight')\n"
                "        except SystemExit as error:\n"
                "            if error.code not in (0,None): raise\n"
                "    sys.argv=argv\n"
                "    runpy.run_path(argv[0],run_name='__main__')\n"
                "finally:\n"
                "    result={'witness':fired,'events':events}\n"
                "    (root/'observer.json').write_text(json.dumps(result))\n"
            )
            args: tuple[str, ...] = ()
        else:
            args = tuple(argv[1:])
        marker = self.root / "control-marker.txt"
        before = digest(marker) if marker.is_file() else None
        result = python(entry, cwd=self.root, args=args, timeout=90, kind="actual-verifier")
        from verification_fixture_dispatch import read_records

        trace = [
            {"phase": fields[0], "argv": fields[1:]}
            for fields in read_records(self.root / "phase-trace.argv")
        ]
        if trace:
            (self.root / "phase-trace.jsonl").write_text(
                "".join(json.dumps(item) + "\n" for item in trace)
            )
        observer_path = self.root / "observer.json"
        observation = json.loads(observer_path.read_text()) if observer_path.exists() else None
        target = self.root / receipt
        document = None
        if target.is_file() and not target.is_symlink():
            try:
                candidate = json.loads(target.read_text())
                if isinstance(candidate, dict):
                    document = candidate
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
        retained: dict[str, Any] = {
            "receipt": document,
            "observer": observation,
            "marker_before": before,
            "marker_after": digest(marker) if marker.is_file() else None,
            "fixture_root": str(self.root),
            "public_cli_argv": argv,
            "public_execution": "standard-loading-then-CLI" if observer or load else "CLI",
            "controls": json.loads(self.controls.read_text()),
            "opaque_verifier_sha256": digest(self.verifier),
            "phase_trace": (
                (self.root / "phase-trace.jsonl").read_text()
                if (self.root / "phase-trace.jsonl").exists()
                else None
            ),
        }
        native = self.root / "artifacts/coverage/coverage.json"
        if native.exists():
            retained["native"] = json.loads(native.read_text())
            retained["native_sha256"] = digest(native)
        retained["evidence_files"] = {
            str(path.relative_to(self.root)): {
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
            }
            for parent in (self.root / "artifacts", self.root / "dist")
            if parent.is_dir()
            for path in parent.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        # Preserve complete genuinely emitted native database/HTML/wheel/log bytes.
        archive = RUN / "fixture-evidence" / uuid.uuid4().hex
        archive.mkdir(parents=True)
        for name in ("artifacts", "dist"):
            if (self.root / name).is_dir():
                shutil.copytree(self.root / name, archive / name, symlinks=True)
        if (self.root / ".coverage").is_file():
            shutil.copyfile(self.root / ".coverage", archive / ".coverage")
        retained["archive"] = str(archive)
        record("verifier-evidence", retained)
        return result, document


PHASE_DRIVER = r"""
import base64,csv,hashlib,io,json,pathlib,runpy,shutil,sys,zipfile
root=pathlib.Path.cwd()
phase=next(arg for arg in sys.argv[1:] if not arg.startswith('-') and '=' not in arg)
controls=json.loads((root/'controls.json').read_text())
from verification_fixture_dispatch import append_record
append_record(root/'phase-trace.argv', [phase, *sys.argv[1:]])
print('A08 actual disposable phase '+phase,flush=True)
if phase==controls.get('fail_phase'): sys.exit(controls.get('status',19))
if phase==controls.get('redirect_phase'):
    output=root/controls['redirect_output']
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists() or output.is_symlink(): output.unlink()
    output.symlink_to(root/controls['redirect_target'])
if phase=='coverage-clean':
    for name in ('artifacts/coverage','dist'):
        shutil.rmtree(root/name,ignore_errors=True)
    (root/'.coverage').unlink(missing_ok=True)
if phase=='tests':
    import coverage
    cov=coverage.Coverage(branch=True,config_file=False,data_file=str(root/'.coverage'),
        include=[str(root/'src/simrecon/*'),str(root/'scripts/*'),str(root/'external.py')])
    cov.start()
    for name in ('src/simrecon/owned.py','scripts/owned.py','external.py'):
        runpy.run_path(str(root/name),run_name='__main__')
    cov.stop(); cov.save()
    original=root/'artifacts/coverage/A08-original-native.database'
    original.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(root/'.coverage',original)
if phase in ('coverage-json','coverage-html','coverage-report'):
    import coverage
    cov=coverage.Coverage(branch=True,config_file=False,data_file=str(root/'.coverage'))
    cov.load()
    if phase=='coverage-json':
        path=root/'artifacts/coverage/coverage.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        cov.json_report(outfile=str(path))
        if 'native_change' in controls:
            shutil.copyfile(path,path.with_name('A08-original-native.json'))
            change=controls['native_change']
            doc=json.loads(path.read_text())
            if change['scope']=='totals': summary=doc['totals']
            else: summary=doc['files']['external.py']['summary']
            if change.get('increment'): summary[change['field']]+=1
            else: summary[change['field']]=change['value']
            path.write_text(json.dumps(doc))
    elif phase=='coverage-html': cov.html_report(directory=str(root/'artifacts/coverage/html'))
    else: cov.report()
if phase=='wheel':
    dist=root/'dist'; dist.mkdir(exist_ok=True)
    members={
        'simrecon/__init__.py':b'__version__ = "0.1.0"\n',
        'simrecon-0.1.0.dist-info/METADATA':(
            b'Metadata-Version: 2.1\nName: simrecon\nVersion: 0.1.0\n'),
        'simrecon-0.1.0.dist-info/WHEEL':(
            b'Wheel-Version: 1.0\nGenerator: A08-independent-fixture\n'
            b'Root-Is-Purelib: true\nTag: py3-none-any\n'),
    }
    record_name='simrecon-0.1.0.dist-info/RECORD'
    rows=[]
    for name,data in members.items():
        digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        rows.append([name,'sha256='+digest,str(len(data))])
    rows.append([record_name,'',''])
    text=io.StringIO(); csv.writer(text,lineterminator='\n').writerows(rows)
    members[record_name]=text.getvalue().encode()
    with zipfile.ZipFile(dist/'simrecon-0.1.0-py3-none-any.whl','w') as wheel:
        for name,data in members.items(): wheel.writestr(name,data)
if phase=='wheel-import':
    sys.path.insert(0,str(root/'dist/simrecon-0.1.0-py3-none-any.whl'))
    import simrecon
    assert simrecon.__version__=='0.1.0'
"""
