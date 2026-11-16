"""UNEXECUTED: exact frozen nonproduct fixture guard/view qualification only."""
from pathlib import Path
import ast
import errno
import hashlib
import json
import os
import resource
import runpy
import signal
import sys

FIXTURE = Path('/workspace/work/issue-113/tests/single_known_fixture.py')
FIXTURE_SHA = 'a693da50394c158716148d4dca5c9435b4b1518461efb51ebed4837b86fe462b'
CASES = ('guard-normal', 'guard-unusable', 'guard-install-denied', 'guard-readback')


def assigned(node, names):
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return False
    target = node.targets[0]
    actual = (target.id,) if isinstance(target, ast.Name) else tuple(
        part.id for part in target.elts
    ) if isinstance(target, ast.Tuple) and all(isinstance(part, ast.Name) for part in target.elts) else ()
    return actual == names


def execute(nodes, namespace, bindings):
    for node in nodes:
        bindings.append({'first': node.lineno, 'last': node.end_lineno,
                         'ast_sha256': hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()})
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, str(FIXTURE), 'exec'), namespace)


def vm():
    lines = [line.split() for line in Path('/proc/self/status').read_text().splitlines()
             if line.startswith('VmSize:')]
    assert len(lines) == 1 and lines[0][2] == 'kB'
    return int(lines[0][1]) * 1024


def main():
    assert __debug__
    assert len(sys.argv) == 5 and sys.argv[1] == '--case' and sys.argv[3] == '--case-dir'
    case = sys.argv[2]
    assert case in CASES
    directory = Path(sys.argv[4])
    assert directory.is_dir() and directory.name.startswith('init-case-')
    signal.alarm(40)
    raw = FIXTURE.read_bytes()
    assert len(raw) < 128 * 1024 and hashlib.sha256(raw).hexdigest() == FIXTURE_SHA
    tree = ast.parse(raw, str(FIXTURE))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'bounded_declaration_child')
    split = next(i for i, node in enumerate(function.body) if assigned(node, ('q', 'v')))
    prefix = function.body[:split]
    qv_node = function.body[split]
    assert isinstance(qv_node.value, ast.Call) and isinstance(qv_node.value.func, ast.Name)
    assert qv_node.value.func.id == 'arrays'
    wide = next(node for node in function.body if isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name)
                and node.test.left.id == 'case' and len(node.test.comparators) == 1
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == 'wide')
    begin = next(i for i, node in enumerate(wide.body) if assigned(node, ('directions', 'orders')))
    positive = next(i for i, node in enumerate(wide.body) if assigned(node, ('positive_q', 'positive_v')))
    views = next(i for i, node in enumerate(wide.body) if assigned(node, ('q_view',)))
    forged = next(i for i, node in enumerate(wide.body) if assigned(node, ('count_forged',)))
    assert begin < positive < views < forged
    selected_views = [qv_node, *wide.body[begin:positive], *wide.body[views:forged]]
    # Freeze selected call families; no declare/call/reconstruct/backend execution.
    permitted_names = {'arrays', 'sum', 'zip', 'all', 'type', 'tuple', 'callable', 'int', 'RuntimeError'}
    for node in selected_views:
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                if isinstance(item.func, ast.Name):
                    assert item.func.id in permitted_names, item.func.id
                else:
                    assert isinstance(item.func, ast.Attribute)
                    assert isinstance(item.func.value, ast.Name) and item.func.value.id == 'np'
                    assert item.func.attr in ('broadcast_to', 'zeros', 'ones')
    # Same real top-level imports/constant/definition context as declaration child,
    # with __main__ dispatch false. No product function is called or replaced.
    namespace = runpy.run_path(str(FIXTURE), run_name='sp113_g1_import_context')
    assert Path(namespace['sr'].__file__).resolve() == Path('/workspace/work/issue-113/src/simrecon/__init__.py')
    namespace['case'] = 'wide'
    original_get, original_set = resource.getrlimit, resource.setrlimit
    original_limits = original_get(resource.RLIMIT_AS)
    baseline_before = vm()
    calls = []
    query_count = 0
    controlled = None
    if case == 'guard-unusable':
        page = int(os.sysconf('SC_PAGE_SIZE'))
        soft = ((baseline_before + page - 1) // page) * page + 16 * 1024**2
        old_soft, hard = original_limits
        assert old_soft == resource.RLIM_INFINITY or soft <= old_soft
        assert hard == resource.RLIM_INFINITY or soft <= hard
        original_set(resource.RLIMIT_AS, (soft, hard))
        assert original_get(resource.RLIMIT_AS) == (soft, hard)
        controlled = 'REAL_CHILD_ONLY_PREEXISTING_SOFT_LIMIT_16MiB_HEADROOM'

    def set_limit(kind, limits):
        calls.append({'kind': kind, 'requested': list(limits)})
        if case == 'guard-install-denied':
            raise PermissionError(errno.EPERM, 'G1 controlled child-local installer denial')
        return original_set(kind, limits)

    def get_limit(kind):
        nonlocal query_count
        query_count += 1
        result = original_get(kind)
        if case == 'guard-readback' and query_count == 2:
            return result[0] - int(os.sysconf('SC_PAGE_SIZE')), result[1]
        return result

    resource.setrlimit, resource.getrlimit = set_limit, get_limit
    bindings = []
    failure = None
    try:
        execute(prefix, namespace, bindings)
    except (RuntimeError, OSError) as error:
        failure = {'type': type(error).__name__, 'message': str(error)}
    finally:
        resource.getrlimit, resource.setrlimit = original_get, original_set
    actual_limits = original_get(resource.RLIMIT_AS)
    if case == 'guard-normal':
        assert failure is None and len(calls) == 1
        assert actual_limits == (namespace['cap'], namespace['cap'])
        assert namespace['cap'] - namespace['guarded_vm'] >= namespace['minimum']
        execute(selected_views, namespace, bindings)
        backings = [namespace[name] for name in ('q', 'v', 'carrier_back', 'modulation_back')]
        assert sum(value.nbytes for value in backings) == 144
        assert all(value.nbytes <= 96 for value in backings)
        before = tuple(value.tobytes() for value in backings)  # Actual tiny buffers ONLY.
        metadata = namespace['logical_view_metadata']()
        assert len(metadata) == 4 and metadata == namespace['logical_view_metadata']()
        assert tuple(value.tobytes() for value in backings) == before
        details = {'baseline_vm_bytes': namespace['baseline'], 'cap_bytes': namespace['cap'],
                   'guard_vm_bytes': namespace['guarded_vm'], 'page_bytes': namespace['page'],
                   'minimum_reserve_bytes': namespace['minimum'], 'tiny_backing_bytes': 144,
                   'view_shapes': [list(view.shape) for view, _ in namespace['view_backings']],
                   'view_strides': [list(view.strides) for view, _ in namespace['view_backings']]}
    elif case == 'guard-unusable':
        assert failure is not None and failure['type'] == 'RuntimeError'
        assert 'unusable existing address-space limit/baseline' in failure['message']
        assert not calls and actual_limits[0] < namespace['rounded_baseline'] + namespace['minimum']
        details = {'failure': failure, 'control': controlled, 'guard_installer_calls': 0}
    elif case == 'guard-install-denied':
        assert failure is not None and failure['type'] == 'PermissionError'
        assert 'G1 controlled child-local installer denial' in failure['message']
        assert len(calls) == 1 and actual_limits == original_limits
        details = {'failure': failure, 'control': 'INJECTED_PUBLIC_RESOURCE_SETLIMIT_ERROR_NOT_PLATFORM_FAILURE'}
    else:
        assert failure is not None and failure['type'] == 'RuntimeError'
        assert 'RLIMIT_AS installation failed' in failure['message']
        assert len(calls) == 1 and actual_limits == tuple(calls[0]['requested'])
        details = {'failure': failure, 'control': 'INJECTED_READBACK_MISMATCH_REAL_CHILD_CAP_RETAINED'}
    print(json.dumps({'case': case, 'scope': 'G1_NONPRODUCT_GUARD_METADATA_ONLY',
                      'control_expectation_met': True, 'fixture_sha256': FIXTURE_SHA,
                      'bindings': bindings, 'details': details,
                      'initial_limits': list(original_limits), 'final_limits': list(actual_limits),
                      'limits': 'no product calls/large allocation/logical view scans or copies; child-local resource controls only'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
