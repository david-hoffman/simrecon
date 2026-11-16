"""UNEXECUTED fixed five-case payload; only a root-released private init runtime."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path('/workspace/work/issue-113')


def identity():
    text = Path('/proc/self/stat').read_text(encoding='ascii')
    fields = text[text.rindex(')') + 2:].split()
    return {'pid': os.getpid(), 'ppid': os.getppid(), 'start_ticks': int(fields[19])}


def write_once(path, data):
    raw = json.dumps(data, sort_keys=True).encode()
    assert len(raw) <= 4096
    temporary = path.with_suffix(path.suffix + '.pending')
    assert not path.exists()
    with temporary.open('xb') as stream:
        stream.write(raw)
    os.replace(temporary, path)


def main():
    assert __debug__
    assert len(sys.argv) == 5 and sys.argv[1] == '--case' and sys.argv[3] == '--case-dir'
    case, directory = sys.argv[2], Path(sys.argv[4])
    assert str(directory).startswith('/workspace/work/campaign/evidence/113/init-case-')
    assert directory.is_dir()
    signal.alarm(20)  # Finite stdlib backstop; not a product/runtime budget.
    if case in ('exit0', 'exit7'):
        print('SP113_' + case.upper(), flush=True)
        return 0 if case == 'exit0' else 7
    if case == 'adoption-leaf':
        first = identity()
        write_once(directory / 'leaf-ready.json', first)
        deadline = time.monotonic() + 5
        while os.getppid() != 1:
            assert time.monotonic() < deadline, 'verified init did not adopt leaf'
            time.sleep(0.02)
        adopted = identity()
        assert adopted['pid'] == first['pid'] and adopted['start_ticks'] == first['start_ticks']
        write_once(directory / 'leaf-adopted.json', adopted)
        time.sleep(1)
        write_once(directory / 'leaf-complete.json', adopted)
        return 0
    if case == 'adoption':
        child = subprocess.Popen(
            [sys.executable, '-B', __file__, '--case', 'adoption-leaf', '--case-dir', str(directory)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        deadline = time.monotonic() + 3
        ready = directory / 'leaf-ready.json'
        while not ready.exists():
            assert child.poll() is None, 'leaf failed before acknowledgement'
            assert time.monotonic() < deadline, 'leaf acknowledgement absent'
            time.sleep(0.02)
        raw = ready.read_bytes()
        assert len(raw) <= 4096
        record = json.loads(raw)
        assert record['pid'] == child.pid and record['ppid'] == os.getpid()
        print(json.dumps({'case': 'adoption', 'acknowledged_leaf': record}, sort_keys=True), flush=True)
        # Explicitly root-released finite adoption control ONLY after init verified.
        # No use under old PID1sleep. Leaf alarm/backstop is installed before ACK.
        return 0
    assert case in ('typing-valid', 'typing-invalid')
    caller = directory / 'literal_caller.py'
    source = (
        'from typing import assert_type\n\ndef check(value: int) -> int:\n'
        '    assert_type(value, int)\n    return value\n'
        if case == 'typing-valid' else 'value: int = "SP113_INVALID_ASSIGNMENT"\n'
    )
    with caller.open('x', encoding='utf-8') as stream:
        stream.write(source)
    signal.alarm(0)  # The root-owned outer controller supplies the tool deadline.
    argv = [sys.executable, str(ROOT / 'scripts/source_free_check.py'), 'python',
            '-m', 'pyright', '--outputjson', '--pythonpath', sys.executable, str(caller)]
    os.execv(sys.executable, argv)  # Same compiler argv as the reviewed test.
    raise AssertionError('exec unexpectedly returned')


if __name__ == '__main__':
    raise SystemExit(main())
