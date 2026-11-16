"""UNEXECUTED/DISABLED without exact ROOT activation; no Docker creation/kill.

One docker-exec proxy, bounded channels/deadline. On failure HOLD alive; ROOT
closes the exact container and supplies its separately observed closure receipt.
This is an outside finite qualification controller, never a product/gate helper.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import selectors
import subprocess
import sys
import time

BASE = Path('/workspace/work/campaign/evidence/113')
CASES = {'exit0': 0, 'exit7': 7, 'adoption': 0, 'typing-valid': 0, 'typing-invalid': 1}
PAYLOAD = BASE / 'typing-init-cases-2.py'
WORKTREE = '/workspace/work/issue-113'
BYTE_BUDGET = 16 * 1024
DEADLINE_SECONDS = 60


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    raw = path.read_bytes()
    assert len(raw) <= 16384
    return json.loads(raw)


def event(kind, **fields):
    raw = json.dumps({'event': kind, **fields}, sort_keys=True)
    assert len(raw.encode()) <= 8192
    print(raw, flush=True)


def main():
    assert __debug__
    assert len(sys.argv) == 4, 'ROOT activation path/SHA and fixed case required'
    activation_path, activation_sha, case = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    assert case in CASES and activation_path.parent == BASE
    assert re.fullmatch('[0-9a-f]{64}', activation_sha)
    assert sha(activation_path) == activation_sha
    activation = read_json(activation_path)
    assert activation['root_released'] is True  # No activation file is authored here.
    assert str(Path(sys.executable).resolve()) == activation['outer_python_executable']
    assert sha(sys.executable) == activation['outer_python_sha256']
    assert activation['controller_sha256'] == sha(__file__)
    assert activation['payload_sha256'] == sha(PAYLOAD)
    assert case in activation['released_cases']
    runtime = activation['runtime']
    cid = runtime['container_id']
    assert re.fullmatch('[0-9a-f]{64}', cid)
    assert runtime['private_pid_namespace_verified'] is True
    assert runtime['init_verified'] is True and runtime['no_other_workload'] is True
    assert runtime['linux_primary_sha256'] == '2aab5ab4109224883b733f476418acac4d42a0c5b4d7b843757df845a334e7c3'
    assert runtime['material_sha256'] and runtime['pid_namespace_inode']
    docker = activation['docker_executable']
    assert Path(docker).is_absolute() and sha(docker) == activation['docker_sha256']
    directory = Path(activation['case_directories'][case])
    assert directory.parent == BASE and directory.name.startswith('init-case-')
    assert directory.is_dir() and not any(directory.iterdir())
    closure = BASE / (directory.name + '-root-closure.json')
    final = BASE / (directory.name + '-controller-receipt.json')
    assert not closure.exists() and not final.exists()
    env_flags = [
        '-e', 'PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        '-e', 'OMP_NUM_THREADS=1', '-e', 'OPENBLAS_NUM_THREADS=1', '-e', 'MKL_NUM_THREADS=1',
        '-e', 'BLIS_NUM_THREADS=1', '-e', 'NUMEXPR_NUM_THREADS=1',
        '-e', 'PYTHONPATH=' + WORKTREE + '/scripts/source_free_sitecustomize',
        '-e', 'PYTEST_PLUGINS=pytest_plugin',
    ]
    argv = [docker, 'exec', '--user', '1000:1000', '-w', WORKTREE, *env_flags, cid,
            WORKTREE + '/.venv/bin/python', '-B', str(PAYLOAD), '--case', case,
            '--case-dir', str(directory)]
    started = time.monotonic()
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True)
    # Popen ownership, never a process-group scan/signal. ROOT retains this controller.
    event('STARTED', case=case, container_id=cid, proxy_pid=process.pid,
          activation_sha256=activation_sha)
    selector = selectors.DefaultSelector()
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    counts = {'stdout': 0, 'stderr': 0}
    for name, stream in (('stdout', process.stdout), ('stderr', process.stderr)):
        assert stream is not None
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, name)
    reasons = []
    target_announced = False
    root_closure = None

    def hold(reason):
        if reason not in reasons and len(reasons) < 16:
            reasons.append(reason)
            if len(reasons) == 1:
                event('HOLD_ROOT_CLOSE_CONTAINER', case=case, container_id=cid,
                      proxy_pid=process.pid, reason=reason)

    # No automatic SIGTERM/SIGKILL of target/container/proxy on deadline. ROOT owns
    # container closure. Keep draining/discarding past budget to unblock CLI pipes.
    while True:
        try:
            if time.monotonic() - started > DEADLINE_SECONDS and (
                process.poll() is None or selector.get_map()
            ):
                hold('absolute target deadline exceeded')
            for key, _ in selector.select(0.1):
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                name = key.data
                counts[name] += len(chunk)
                remaining = max(0, BYTE_BUDGET - len(buffers[name]))
                buffers[name].extend(chunk[:remaining])
                if counts[name] > BYTE_BUDGET:
                    hold(name + ' byte budget exceeded')
            status = process.poll()
            if status is not None and not selector.get_map() and not target_announced:
                target_announced = True
                if status != CASES[case]:
                    hold('actual exec status differs from fixed case')
                event('TARGET_EXIT', case=case, container_id=cid,
                      actual_exec_status=status, byte_counts=counts)
            if closure.exists() and root_closure is None:
                candidate = read_json(closure)
                assert candidate['container_id'] == cid
                assert candidate['pid_namespace_inode'] == runtime['pid_namespace_inode']
                assert candidate['init_identity'] == runtime['init_identity']
                assert candidate['engine_running'] is False
                assert candidate['engine_state'] == 'exited'
                assert candidate['actual_pid1_terminal_and_reaped'] is True
                assert type(candidate['engine_wait_status']) is int
                assert candidate['no_other_workload'] is True
                # cgroup may be shared/unknown: namespace/init closure is the basis.
                assert candidate['cgroup_scope'] in ('owned-empty', 'shared', 'unknown')
                root_closure = candidate
                event('ROOT_CLOSURE_RECEIVED', case=case, container_id=cid)
            if root_closure is not None and process.poll() is not None and not selector.get_map():
                break
            # On proxy hang AFTER verified container closure, ROOT must explicitly
            # authorize direct-Popen proxy cleanup in its closure receipt. No PGID.
            if root_closure is not None and process.poll() is None:
                if root_closure.get('permit_owned_proxy_cleanup') is True:
                    hold('proxy survived verified namespace closure')
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
        except (KeyboardInterrupt, Exception) as error:
            # Preserve ownership/reaper lifetime through root recovery. Malformed
            # closure files never count as acceptance; ROOT may replace its receipt.
            hold(type(error).__name__ + ': ' + str(error)[:512])
            time.sleep(0.1)
    status = process.wait()
    selector.close()
    if status != CASES[case]:
        hold('final actual exec status differs from fixed case')
    text = {}
    for name, raw in buffers.items():
        try:
            text[name] = raw.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            hold(name + ' invalid UTF8')
            text[name] = raw.hex()  # Bounded raw bytes retained, never silently accepted.
    if case in ('exit0', 'exit7') and not reasons:
        if text['stdout'] != 'SP113_' + case.upper() + '\n' or text['stderr']:
            hold('fixed stdlib status frame differs')
    if case == 'adoption' and not reasons:
        try:
            ready = read_json(directory / 'leaf-ready.json')
            adopted = read_json(directory / 'leaf-adopted.json')
            complete = read_json(directory / 'leaf-complete.json')
            acknowledgement = json.loads(text['stdout'])
            assert acknowledgement == {'case': 'adoption', 'acknowledged_leaf': ready}
            assert type(ready['pid']) is int and ready['pid'] > 1
            assert type(ready['ppid']) is int and ready['ppid'] > 1
            assert type(ready['start_ticks']) is int and ready['start_ticks'] > 0
            assert adopted == complete
            assert adopted == {**ready, 'ppid': 1}
            terminal = root_closure['adoption_terminal_observation']
            assert terminal['pid'] == ready['pid'] and terminal['start_ticks'] == ready['start_ticks']
            assert terminal['absent_before_namespace_close'] is True
            assert not text['stderr']
        except (AssertionError, OSError, KeyError, TypeError, ValueError) as error:
            hold('finite init adoption capability: ' + type(error).__name__)
    if case.startswith('typing-') and not reasons:
        try:
            report = json.loads(text['stdout'])
            summary = report['summary']
            assert type(summary['filesAnalyzed']) is int and summary['filesAnalyzed'] >= 1
            errors = summary['errorCount']
            assert type(errors) is int
            assert errors == 0 if case == 'typing-valid' else errors >= 1
        except (AssertionError, KeyError, TypeError, ValueError) as error:
            hold('typing JSON capability: ' + type(error).__name__)
    receipt = {'case': case, 'activation_sha256': activation_sha, 'runtime': runtime,
               'argv': argv, 'proxy_pid': process.pid, 'actual_exec_status': status,
               'expected_exec_status': CASES[case], 'byte_counts': counts,
               'retained_channels': text, 'root_closure': root_closure,
               'hold_reasons': reasons, 'proxy_reaped': process.returncode is not None,
               'pipes_closed': process.stdout.closed and process.stderr.closed,
               'limits': 'finite transport/capability only; not product/type/scientific acceptance'}
    raw = json.dumps(receipt, sort_keys=True).encode()
    assert len(raw) <= 128 * 1024
    with final.open('xb') as stream:
        stream.write(raw)
    event('RECORDED', case=case, receipt=str(final), hold=bool(reasons), actual_exec_status=status)
    return 1 if reasons else 0


if __name__ == '__main__':
    raise SystemExit(main())
