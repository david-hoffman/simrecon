"""Owned public-command fixtures; never inspect runtime implementation bytes."""

from __future__ import annotations

import hashlib
import http.client
import http.server
import ipaddress
import json
import os
import shutil
import ssl
import subprocess
import sys
import textwrap
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/source_free_check.py"
PYTHON = Path(sys.executable)
JAVA = os.environ.get("SIMRECON_JAVA", "java")
EVIDENCE = ROOT / "artifacts/infrastructure-supplement-A07/evidence"
PHASES = (
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
)
PINS = {
    "c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9": 70_000_000,
    "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20": 10_000_000,
}


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def run_public(
    cwd: Path, *args: str, timeout: float = 60, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """All product invocations retain the inherited source-free diagnostic aid."""
    result = subprocess.run(
        [str(PYTHON), str(HARNESS), "--timeout", str(timeout), "python", *args],
        cwd=cwd,
        env=os.environ.copy() | (env or {}),
        text=True,
        capture_output=True,
        timeout=timeout + 10,
        check=False,
    )
    invocation = EVIDENCE / ("public-" + str(uuid.uuid4()))
    invocation.mkdir(parents=True)
    (invocation / "stdout.txt").write_text(result.stdout)
    (invocation / "stderr.txt").write_text(result.stderr)
    (invocation / "command.json").write_text(
        json.dumps({"command": result.args, "returncode": result.returncode, "cwd": str(cwd)})
    )
    for relative in (
        "artifacts/verification",
        "artifacts/coverage",
        "artifacts/trace.jsonl",
        "ordinary-receipt.json",
        "ordinary-failed-receipt.json",
        "artifacts/imagej-reader/inputs.json",
        "artifacts/audit-events.json",
        ".coverage",
    ):
        source = cwd / relative
        destination = invocation / relative
        if source.is_dir():
            shutil.copytree(
                source, destination, symlinks=True, ignore=shutil.ignore_patterns("harmless-fifo")
            )
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    return result


def reader_repo(path: Path) -> tuple[Path, dict[str, Path]]:
    (path / "scripts").mkdir(parents=True)
    shutil.copyfile(
        ROOT / "scripts/prepare_imagej_reader.py",
        path / "scripts/prepare_imagej_reader.py",
    )
    cache = path / "artifacts/imagej-reader"
    cache.mkdir(parents=True)
    jars: dict[str, Path] = {}
    for source in (ROOT / "artifacts/imagej-reader").glob("*.jar"):
        destination = cache / source.name
        shutil.copyfile(source, destination)
        jars[digest(destination)] = destination
    assert set(jars) == set(PINS)
    (cache / "inputs.json").write_text('{"stale_identity": true}\n')
    return cache, jars


def run_reader(path: Path, java: str = JAVA) -> subprocess.CompletedProcess[str]:
    return run_public(
        path,
        "scripts/prepare_imagej_reader.py",
        timeout=45,
        env={"SIMRECON_JAVA": java},
    )


def write_program(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")


def executable(path: Path, body: str) -> None:
    write_program(path, f"#!{PYTHON}\n" + textwrap.dedent(body).lstrip())
    path.chmod(0o755)


def verifier_repo(path: Path, *, change: str = "", fail: str = "") -> Path:
    """Real Git/coverage/wheel evidence, with caller-owned Make command fixture.

    The phase fixture is not a full project check and makes no readiness claim.
    Native data/JSON/HTML are emitted by Coverage.py on two owned tiny modules.
    All mutations happen to public native report fields after authentic emission.
    """
    path.mkdir(parents=True)
    for folder in ("src/simrecon", "scripts", "artifacts", "dist"):
        (path / folder).mkdir(parents=True)
    (path / ".gitignore").write_text("artifacts/\ndist/\n.coverage*\n__pycache__/\n")
    (path / "src/simrecon/__init__.py").write_text("ANSWER = 42\n")
    (path / "scripts/owned.py").write_text("ANSWER = 42\n")
    (path / "marker.txt").write_bytes(b"A07 tracked preservation marker\n")
    (path / ".coveragerc").write_text("[run]\nbranch = True\nsource = src/simrecon, scripts\n")
    make = path / "phase-command"
    executable(
        make,
        """
        import base64
        import csv
        import hashlib
        import io
        import json
        import os
        from pathlib import Path
        import runpy
        import subprocess
        import sys
        import zipfile
        import coverage

        if "--version" in sys.argv:
            print("A07 disposable Make caller 1")
            raise SystemExit(0)
        phase = next(item for item in sys.argv[1:]
                     if not item.startswith(("-", "UV=")))
        with Path("artifacts/trace.jsonl").open("a") as output:
            output.write(json.dumps(sys.argv[1:]) + "\\n")
        print("authentic A07 phase output: " + phase, flush=True)
        change = os.environ.get("A07_CHANGE", "")
        failure = os.environ.get("A07_FAIL", "")
        if phase == failure:
            raise SystemExit(23)
        if phase == "coverage-clean":
            coverage.Coverage().erase()
        elif phase == "tests":
            cov = coverage.Coverage()
            cov.start()
            runpy.run_path("src/simrecon/__init__.py")
            runpy.run_path("scripts/owned.py")
            cov.stop()
            cov.save()
        elif phase == "coverage-json":
            cov = coverage.Coverage()
            cov.load()
            Path("artifacts/coverage").mkdir(exist_ok=True)
            cov.json_report(outfile="artifacts/coverage/coverage.json")
            report_path = Path("artifacts/coverage/coverage.json")
            report = json.loads(report_path.read_text())
            native = report["files"]["scripts/owned.py"]
            if change == "missing-destinations":
                native["executed_branches"] = {}
            elif change == "bad-destination":
                native["executed_branches"] = [[1, "destination"]]
            elif change == "exclusion-counter":
                native["summary"]["excluded_lines"] = 1
            elif change == "excluded-list":
                native["excluded_lines"] = [1]
            elif change == "global-exclusion-counter":
                report["totals"]["excluded_lines"] = 1
            report_path.write_text(json.dumps(report))
        elif phase == "coverage-html":
            cov = coverage.Coverage()
            cov.load()
            cov.html_report(directory="artifacts/coverage/html")
            html = Path("artifacts/coverage/html")
            if change == "directory-alias":
                (html / "harmless-alias").symlink_to(html.resolve(), target_is_directory=True)
            elif change == "directory-cycle":
                (html / "harmless-cycle").symlink_to(".", target_is_directory=True)
            elif change == "fifo-neighbor":
                os.mkfifo(html / "harmless-fifo")
        elif phase == "coverage-report":
            cov = coverage.Coverage()
            cov.load()
            cov.report()
        elif phase == "wheel":
            files = {
                "simrecon/__init__.py": b"ANSWER = 42\\n",
                "simrecon-1.0.dist-info/METADATA":
                    b"Metadata-Version: 2.1\\nName: simrecon\\nVersion: 1.0\\n",
                "simrecon-1.0.dist-info/WHEEL":
                    (b"Wheel-Version: 1.0\\nGenerator: A07\\n"
                     b"Root-Is-Purelib: true\\nTag: py3-none-any\\n"),
            }
            record = io.StringIO(newline="")
            writer = csv.writer(record)
            for name, content in files.items():
                digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
                writer.writerow((name, "sha256=" + digest.decode(), len(content)))
            writer.writerow(("simrecon-1.0.dist-info/RECORD", "", ""))
            files["simrecon-1.0.dist-info/RECORD"] = record.getvalue().encode()
            with zipfile.ZipFile("dist/simrecon-1.0-py3-none-any.whl", "w") as wheel:
                for name, content in files.items():
                    wheel.writestr(name, content)
        elif phase == "wheel-import":
            result = subprocess.run(
                [sys.executable, "-c",
                 "import sys; sys.path.insert(0, 'dist/simrecon-1.0-py3-none-any.whl'); "
                 "import simrecon; assert simrecon.ANSWER == 42"],
                timeout=15,
            )
            raise SystemExit(result.returncode)
        """,
    )
    for args in (
        ("init", "-q"),
        ("add", "."),
        (
            "-c",
            "user.name=A07 Fixture",
            "-c",
            "user.email=a07@example.invalid",
            "commit",
            "-qm",
            "public fixture",
        ),
    ):
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, timeout=15)
    # Parameters are passed through the fixture's explicit environment in verify().
    assert change in {
        "",
        "missing-destinations",
        "bad-destination",
        "exclusion-counter",
        "excluded-list",
        "global-exclusion-counter",
        "directory-alias",
        "directory-cycle",
        "fifo-neighbor",
    }
    assert fail == "" or fail in PHASES
    return make


def verify(
    path: Path,
    make: Path,
    *,
    receipt: str = "artifacts/verification/receipt.json",
    change: str = "",
    fail: str = "",
) -> subprocess.CompletedProcess[str]:
    return run_public(
        path,
        str(ROOT / "scripts/verify.py"),
        "--make",
        str(make),
        "--uv",
        str(PYTHON),
        "--receipt",
        receipt,
        "--contract",
        "BASELINE-INFRASTRUCTURE-SUPPLEMENT-01",
        "--reviewed-tests",
        "A07-authored-not-yet-reviewed",
        "--base",
        "fixture",
        timeout=90,
        env={"A07_CHANGE": change, "A07_FAIL": fail},
    )


def protected_bytes(path: Path) -> dict[str, bytes]:
    """Owned fixture marker and actual Git metadata; no project source reads."""
    return {
        "marker.txt": (path / "marker.txt").read_bytes(),
        ".git/HEAD": (path / ".git/HEAD").read_bytes(),
        ".git/index": (path / ".git/index").read_bytes(),
    }


def receipt_at(path: Path, relative: str = "artifacts/verification/receipt.json") -> dict:
    return json.loads((path / relative).read_text())


def trace_at(path: Path) -> list[list[str]]:
    return [json.loads(line) for line in (path / "artifacts/trace.jsonl").read_text().splitlines()]


def attempted_phases(path: Path) -> list[str]:
    return [next(item for item in entry if item in PHASES) for entry in trace_at(path)]


def record_case(label: str, observation: dict) -> None:
    """Record public observations separately from product expectations."""
    destination = EVIDENCE / ("r01-case-" + str(uuid.uuid4()))
    destination.mkdir(parents=True)
    (destination / "observation.json").write_text(
        json.dumps({"label": label, **observation}, indent=2) + "\n"
    )
    print("A07-R01 case evidence: " + str(destination.relative_to(ROOT)))


class ReaderTransport:
    """Scoped HTTPS proxy: actual public URLs, authentic independent jar bytes.

    Constructing/importing this fixture does not bind a socket. Only __enter__
    starts the host-only bounded server. The proxy never contacts upstream.
    Its disposable CA is trusted only by the child environment. No product
    dependency is patched, and a selected URL/backend is not an oracle constant.
    """

    def __init__(self, path: Path, payload: Path, maximum: int, mode: str) -> None:
        self.path = path
        self.payload = payload
        self.maximum = maximum
        self.mode = mode
        self.requests: list[dict] = []
        self.stop = threading.Event()
        self.certificate_lock = threading.Lock()
        self.server: http.server.ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.trust = path / "trust"
        self.environ: dict[str, str] = {}

    def openssl(self, *args: str) -> None:
        result = subprocess.run(
            ["/usr/bin/openssl", *args], text=True, capture_output=True, timeout=15, check=False
        )
        assert result.returncode == 0, result.stderr

    def tls_context(self, host: str) -> ssl.SSLContext:
        # Hash is merely a safe owned filename, never a product path oracle.
        token = hashlib.sha256(host.encode()).hexdigest()
        certificate = self.trust / (token + ".crt")
        key = self.trust / (token + ".key")
        with self.certificate_lock:
            if not certificate.exists():
                try:
                    ipaddress.ip_address(host)
                    alternative = "IP:" + host
                except ValueError:
                    alternative = "DNS:" + host
                assert not any(character in host for character in "\n\r")
                config = self.trust / (token + ".conf")
                config.write_text(
                    "[req]\nprompt=no\ndistinguished_name=dn\n"
                    "[dn]\nCN=A07 scoped transport\n"
                    "[leaf]\nbasicConstraints=critical,CA:FALSE\n"
                    "keyUsage=critical,digitalSignature,keyEncipherment\n"
                    "subjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid:always\n"
                    "extendedKeyUsage=serverAuth\nsubjectAltName=" + alternative + "\n"
                )
                csr = self.trust / (token + ".csr")
                self.openssl(
                    "req",
                    "-new",
                    "-sha256",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(key),
                    "-out",
                    str(csr),
                    "-config",
                    str(config),
                )
                self.openssl(
                    "x509",
                    "-req",
                    "-sha256",
                    "-in",
                    str(csr),
                    "-CA",
                    str(self.trust / "ca.crt"),
                    "-CAkey",
                    str(self.trust / "ca.key"),
                    "-CAcreateserial",
                    "-out",
                    str(certificate),
                    "-days",
                    "1",
                    "-extfile",
                    str(config),
                    "-extensions",
                    "leaf",
                )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certificate, key)
        return context

    def prepare_trust(self) -> None:
        """Create scoped issuer material without starting the transport server."""
        self.trust.mkdir(parents=True)
        config = self.trust / "ca.conf"
        config.write_text(
            "[req]\nprompt=no\ndistinguished_name=dn\nx509_extensions=ca\n"
            "[dn]\nCN=A07 disposable transport CA\n"
            "[ca]\nbasicConstraints=critical,CA:TRUE\n"
            "keyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\n"
            "authorityKeyIdentifier=keyid:always\n"
        )
        self.openssl(
            "req",
            "-new",
            "-x509",
            "-sha256",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-keyout",
            str(self.trust / "ca.key"),
            "-out",
            str(self.trust / "ca.crt"),
            "-config",
            str(config),
        )

    def __enter__(self) -> ReaderTransport:
        """Start only the scoped host-run transport server."""
        self.prepare_trust()
        transport = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_CONNECT(self) -> None:
                authority = urlsplit("//" + self.path)
                host = authority.hostname
                assert host is not None
                self.connection.settimeout(20)
                self.send_response(200, "Connection established")
                self.end_headers()
                observation: dict = {"connect_authority": self.path}
                try:
                    with transport.tls_context(host).wrap_socket(
                        self.connection, server_side=True
                    ) as connection:
                        connection.settimeout(20)
                        with connection.makefile("rb") as reader:
                            line = reader.readline(65_536).decode("iso-8859-1").strip()
                            method, target, _version = line.split(" ", 2)
                            headers = http.client.parse_headers(reader)
                        public_host = headers.get("Host", self.path)
                        if public_host.endswith(":443"):
                            public_host = public_host[:-4]
                        url = (
                            target
                            if target.startswith("https://")
                            else "https://" + public_host + target
                        )
                        observation.update({"method": method, "url": url, "request_target": target})
                        transport.requests.append(observation)
                        assert method in {"GET", "HEAD"}
                        mode = transport.mode
                        if (
                            mode == "redirect"
                            and urlsplit(url).path != "/a07-authentic-redirect-target"
                        ):
                            redirected = "https://" + public_host + "/a07-authentic-redirect-target"
                            response = (
                                "HTTP/1.1 302 Found\r\nLocation: "
                                + redirected
                                + "\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                            )
                            observation.update({"response": 302, "location": redirected})
                            connection.sendall(response.encode("ascii"))
                            return
                        observation["response"] = 200
                        size = transport.payload.stat().st_size
                        extra = ""
                        if mode == "advertised-oversize":
                            extra = "Content-Length: " + str(transport.maximum + 1) + "\r\n"
                        elif mode in {"valid-length", "redirect"}:
                            extra = "Content-Length: " + str(size) + "\r\n"
                        connection.sendall(
                            ("HTTP/1.1 200 OK\r\n" + extra + "Connection: close\r\n\r\n").encode(
                                "ascii"
                            )
                        )
                        if method == "HEAD":
                            return
                        if mode == "timeout":
                            # Cancellation closes this owned handler on context exit;
                            # no sleeping daemon survives a failed product command.
                            transport.stop.wait(60)
                            return
                        if mode == "actual-oversize":
                            remaining = transport.maximum + 1
                            while remaining and not transport.stop.is_set():
                                block = b"\0" * min(65_536, remaining)
                                connection.sendall(block)
                                remaining -= len(block)
                        elif mode == "digest-failure":
                            connection.sendall(b"A07 independently wrong jar digest\n")
                        else:
                            with transport.payload.open("rb") as source:
                                while not transport.stop.is_set():
                                    block = source.read(65_536)
                                    if not block:
                                        break
                                    connection.sendall(block)
                        observation["delivery_completed"] = True
                except (OSError, ssl.SSLError) as error:
                    observation["delivery_error"] = type(error).__name__ + ": " + str(error)
                    if observation not in transport.requests:
                        transport.requests.append(observation)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = False
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.1}
        )
        self.thread.start()
        port = self.server.server_port
        proxy = f"http://127.0.0.1:{port}"
        self.environ = {
            "https_proxy": proxy,
            "HTTPS_PROXY": proxy,
            "http_proxy": proxy,
            "HTTP_PROXY": proxy,
            "ALL_PROXY": proxy,
            "all_proxy": proxy,
            "no_proxy": "",
            "NO_PROXY": "",
            "SSL_CERT_FILE": str(self.trust / "ca.crt"),
            "REQUESTS_CA_BUNDLE": str(self.trust / "ca.crt"),
            "CURL_CA_BUNDLE": str(self.trust / "ca.crt"),
        }
        return self

    def __exit__(self, *_exception: object) -> None:
        """Stop and join the owned server, then remove its disposable trust files."""
        self.stop.set()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)
            assert not self.thread.is_alive(), "owned proxy did not terminate"
        shutil.rmtree(self.trust)


def reader_transport_case(path: Path, pin: str, mode: str) -> dict:
    cache, jars = reader_repo(path / "reader")
    repo = cache.parents[1]
    independent = path / "authentic-input.jar"
    shutil.copyfile(jars[pin], independent)
    assert digest(independent) == pin
    missing = jars[pin]
    missing.unlink()
    retained = {key: digest(value) for key, value in jars.items() if key != pin}
    temporary = path / "download-temporary"
    temporary.mkdir()
    transport = ReaderTransport(path / "transport", independent, PINS[pin], mode)
    try:
        with transport:
            started = time.monotonic()
            result = run_public(
                repo,
                "scripts/prepare_imagej_reader.py",
                timeout=45,
                env=transport.environ | {"TMPDIR": str(temporary), "SIMRECON_JAVA": JAVA},
            )
            duration = time.monotonic() - started
    finally:
        # Also clean trust material if setup failed before __enter__ completed.
        if transport.trust.exists():
            shutil.rmtree(transport.trust)
    identity_path = cache / "inputs.json"
    identity = json.loads(identity_path.read_text()) if identity_path.exists() else None
    observation = {
        "pin": pin,
        "mode": mode,
        "maximum_bytes": PINS[pin],
        "independent_input_sha256": digest(independent),
        "command": result.args,
        "status": result.returncode,
        "duration_s": duration,
        "requests": transport.requests,
        "identity": identity,
        "cache_files_after": sorted(item.name for item in cache.iterdir()),
        "temporary_files_after": sorted(
            str(item.relative_to(temporary))
            for item in temporary.rglob("*")
            if item.is_file() or item.is_symlink()
        ),
        "missing_path": str(missing.relative_to(repo)),
    }
    record_case("reader-transport", observation)
    return {
        "result": result,
        "requests": transport.requests,
        "duration": duration,
        "cache": cache,
        "missing": missing,
        "identity": identity,
        "retained": retained,
        "jars": jars,
        "temporary_files": observation["temporary_files_after"],
    }


def all_git_bytes(path: Path) -> dict[str, bytes]:
    return {
        str(item.relative_to(path)): item.read_bytes()
        for item in (path / ".git").rglob("*")
        if item.is_file()
    }


def audited_verify(path: Path, make: Path, mode: str, fail: str = "") -> dict:
    receipt_name = "artifacts/caller-selected-receipt/receipt.json"
    driver = path.parent / "audit-cli-driver.py"
    write_program(
        driver,
        """
        import hashlib
        import json
        import os
        from pathlib import Path
        import runpy
        import sys

        mode, tool, receipt_name, *arguments = sys.argv[1:]
        root = Path.cwd()
        receipt = root / receipt_name
        parent = receipt.parent
        target = root / (".git" if mode == "directory" else "marker.txt")
        events = []
        state = {"active": True, "busy": False, "witnessed": False}
        def target_hashes():
            paths = [target] if target.is_file() else sorted(
                item for item in target.rglob("*") if item.is_file())
            return {str(item.relative_to(root)): hashlib.sha256(item.read_bytes()).hexdigest()
                    for item in paths}
        expected = target_hashes()

        def observer(event, arguments):
            if not state["active"] or state["busy"] or state["witnessed"]:
                return
            if event not in {"os.mkdir", "open"} or not arguments:
                return
            raw = arguments[0]
            if not isinstance(raw, (str, bytes, os.PathLike)):
                return
            actual = Path(os.fsdecode(raw))
            if not actual.is_absolute():
                actual = root / actual
            # Lexical caller-owned path binding: do not resolve an attacker alias.
            actual = Path(os.path.abspath(actual))
            in_parent = actual.is_relative_to(parent)
            if not in_parent:
                return
            flags = arguments[2] if event == "open" else None
            directory_fd = arguments[2] if event == "os.mkdir" else None
            chosen = (
                mode == "directory" and event == "os.mkdir" and actual == parent
                and directory_fd in (None, -1)
            ) or (
                mode == "late" and event == "open" and isinstance(flags, int)
                and bool(flags & os.O_CREAT) and bool(flags & os.O_EXCL)
                and bool(flags & (os.O_WRONLY | os.O_RDWR))
            )
            record = {"event": event, "path": str(actual.relative_to(root)),
                      "mode": str(arguments[1]), "flags": flags,
                      "dir_fd": directory_fd, "selected": chosen,
                      "caller_receipt": receipt_name,
                      "relation": "same invocation, within caller-selected receipt parent"}
            events.append(record)
            if not chosen:
                return
            state["busy"] = True
            try:
                before = target_hashes()
                if mode == "directory":
                    parent.symlink_to(target, target_is_directory=True)
                else:
                    if receipt.exists() or receipt.is_symlink():
                        receipt.unlink()
                    receipt.symlink_to(target)
                after = target_hashes()
                record.update({"intervention": "owned output alias installed",
                               "target": str(target.relative_to(root)),
                               "target_before": before, "target_after_intervention": after,
                               "intervention_preserved_target": before == after == expected})
                state["witnessed"] = True
            finally:
                state["busy"] = False

        sys.addaudithook(observer)
        sys.argv = [tool, "--receipt", receipt_name, *arguments]
        try:
            runpy.run_path(tool, run_name="__main__")
        finally:
            state["active"] = False
            report = {"mode": mode, "caller_receipt": receipt_name,
                      "witnessed": state["witnessed"], "events": events,
                      "target_after_run": target_hashes(), "expected_target": expected}
            Path("artifacts/audit-events.json").write_text(json.dumps(report, indent=2))
        """,
    )
    result = run_public(
        path,
        str(driver),
        mode,
        str(ROOT / "scripts/verify.py"),
        receipt_name,
        "--make",
        str(make),
        "--uv",
        str(PYTHON),
        "--contract",
        "BASELINE-INFRASTRUCTURE-SUPPLEMENT-01",
        "--reviewed-tests",
        "A07-R01-unaccepted",
        "--base",
        "fixture",
        timeout=90,
        env={"A07_CHANGE": "", "A07_FAIL": fail},
    )
    observation = json.loads((path / "artifacts/audit-events.json").read_text())
    receipt_path = path / receipt_name
    receipt = None
    if (
        receipt_path.is_file()
        and not receipt_path.is_symlink()
        and not receipt_path.parent.is_symlink()
    ):
        receipt = json.loads(receipt_path.read_text())
    record_case(
        "audited-verifier",
        {
            "command": result.args,
            "status": result.returncode,
            "audit": observation,
            "actual_receipt": receipt,
            "fail_phase": fail,
            "observed_phases": attempted_phases(path)
            if (path / "artifacts/trace.jsonl").exists()
            else [],
        },
    )
    return {"result": result, "audit": observation, "receipt": receipt}
