"""Build controlled command fixtures with a same-file shell/Python launcher.

Exact metadata queries and demonstrated no-op phases use shell builtins. Other
calls execute the original Python producer body with its original interpreter
and arguments. The producer body follows the polyglot module docstring unchanged
except for removal of its original module docstring.
"""

from __future__ import annotations

import ast
import shlex

# Every permitted character is literal. None requires escaping inside a JSON
# string. Spaces, quotes, backslashes, controls and non-ASCII characters fall
# back rather than acquiring a second JSON encoder.
JSON_SAFE_CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./:=+@%,-"


def original_body(source: str) -> str:
    """Remove only the initial AST module docstring, preserving other bytes."""
    module = ast.parse(source)
    if not module.body:
        return source
    node = module.body[0]
    if not (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ):
        return source
    assert node.end_lineno is not None and node.end_col_offset is not None
    lines = source.encode("utf-8").splitlines(keepends=True)
    start = sum(map(len, lines[: node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[: node.end_lineno - 1])) + node.end_col_offset
    encoded = source.encode("utf-8")
    return (encoded[:start] + encoded[end:]).decode("utf-8")


def shell_header(python: str, kind: str) -> str:
    """Build only shell builtins plus the original-interpreter fallback exec."""
    if kind not in {"receipt", "measurement", "protection", "hash"}:
        raise ValueError(f"unsupported fixture command kind: {kind}")
    # The shell inspects only arguments and the relevant scalar environment
    # values. It never decodes, modifies or copies producer/configuration JSON.
    # Output-protection action JSON is unconsumed on its metadata fast paths.
    return (
        '''#!/bin/sh
""":"
# Avoid changing a caller's exported variable through a shell temporary.
[ -z "${_simrecon_arg+x}${_simrecon_value+x}${_simrecon_separator+x}${_simrecon_kind+x}${_simrec'''
        """on_metadata+x}${_simrecon_phase+x}" ] || exec __PYTHON__ "$0" "$@"
_simrecon_fallback() {
    exec __PYTHON__ "$0" "$@"
}
_simrecon_safe() {
    case "$1" in
        *[!__CHARACTERS__]*) return 1 ;;
        *) return 0 ;;
    esac
}
for _simrecon_arg do
    _simrecon_safe "$_simrecon_arg" || _simrecon_fallback "$@"
done
for _simrecon_value in "${RECEIPT_FIXTURE_MODE-}" "${EXPORT_FIXTURE_MODE-}" "${SIMRECON_MEASUREM"""
        """ENTS_PATH-}" "${SIMRECON_MEASUREMENTS_RUN_ID-}"; do
    _simrecon_safe "$_simrecon_value" || _simrecon_fallback "$@"
done
_simrecon_args() {
    printf '[' || return "$?"
    _simrecon_separator=
    for _simrecon_value do
        printf '%s"%s"' "$_simrecon_separator" "$_simrecon_value" || return "$?"
        _simrecon_separator=', '
    done
    printf ']'
}
_simrecon_calls() {
    {
        _simrecon_args "$@" || return "$?"
        printf '\\n'
    } >> calls.jsonl
}
_simrecon_measurement_calls() {
    {
        printf '{"args": ' || return "$?"
        _simrecon_args "$@" || return "$?"
        printf ', "path": ' || return "$?"
        if [ "${SIMRECON_MEASUREMENTS_PATH+x}" = x ]; then
            printf '"%s"' "$SIMRECON_MEASUREMENTS_PATH" || return "$?"
        else
            printf 'null' || return "$?"
        fi
        printf ', "run_id": ' || return "$?"
        if [ "${SIMRECON_MEASUREMENTS_RUN_ID+x}" = x ]; then
            printf '"%s"' "$SIMRECON_MEASUREMENTS_RUN_ID" || return "$?"
        else
            printf 'null' || return "$?"
        fi
        printf '}\\n'
    } >> measurement-calls.jsonl
}
_simrecon_kind=__KIND__
_simrecon_metadata=
if [ "$#" -eq 1 ] && [ "$1" = --version ]; then
    _simrecon_metadata=version
elif [ "${0##*/}" = uv ] && [ "$#" -eq 4 ] && [ "$1" = run ] && [ "$2" = --locked ] && [ "$4" = """
        """--version ]; then
    case "$3" in
        ruff|pyright|coverage|pytest) _simrecon_metadata=uv ;;
    esac
fi
_simrecon_phase=
if [ -z "$_simrecon_metadata" ]; then
    [ "$_simrecon_kind" != protection ] || _simrecon_fallback "$@"
    [ "${0##*/}" = make ] || _simrecon_fallback "$@"
    [ "$#" -eq 3 ] && [ "$1" = --no-print-directory ] || _simrecon_fallback "$@"
    case "$3" in
        UV=*) ;;
        *) _simrecon_fallback "$@" ;;
    esac
    for _simrecon_arg do
        case "$_simrecon_arg" in
            sync|coverage-clean|lint|format|types|tests|coverage-combine|coverage-json|coverage-"""
        """html|coverage-report|wheel|wheel-import|audit)
                _simrecon_phase=$_simrecon_arg
                break
                ;;
        esac
    done
    [ "$2" = "$_simrecon_phase" ] || _simrecon_fallback "$@"
    case "$_simrecon_phase" in
        sync|lint|format|types|coverage-combine|coverage-report|wheel-import) ;;
        *) _simrecon_fallback "$@" ;;
    esac
    if [ "$_simrecon_phase" = lint ] && [ "${RECEIPT_FIXTURE_MODE-complete}" = command-failure ]"""
        """; then
        _simrecon_fallback "$@"
    fi
    if [ "$_simrecon_kind" = measurement ] && [ "$_simrecon_phase" = types ]; then
        _simrecon_fallback "$@"
    fi
fi
# Existing fixture ledgers are ordinary local files. Nonregular, linked or
# unwritable ledger destinations take Python's existing diagnostics path.
if [ -e calls.jsonl ] || [ -L calls.jsonl ]; then
    [ -f calls.jsonl ] && [ ! -L calls.jsonl ] && [ -w calls.jsonl ] || _simrecon_fallback "$@"
fi
if [ "$_simrecon_kind" = measurement ]; then
    if [ -e measurement-calls.jsonl ] || [ -L measurement-calls.jsonl ]; then
        [ -f measurement-calls.jsonl ] && [ ! -L measurement-calls.jsonl ] && [ -w measurement-c"""
        '''alls.jsonl ] || _simrecon_fallback "$@"
    fi
    _simrecon_measurement_calls "$@" || exit "$?"
fi
if [ "$_simrecon_metadata" = version ]; then
    printf 'fixture tool 1.0\\n' || exit "$?"
    exit 0
fi
_simrecon_calls "$@" || exit "$?"
if [ "$_simrecon_metadata" = uv ]; then
    printf 'controlled uv command\\n' || exit "$?"
else
    printf 'controlled phase %s\\n' "$_simrecon_phase" || exit "$?"
fi
exit 0
":"""
'''.replace("__PYTHON__", shlex.quote(python))
        .replace("__KIND__", kind)
        .replace("__CHARACTERS__", JSON_SAFE_CHARACTERS)
    )


def launcher(source: str, *, python: str, kind: str) -> str:
    """Return executable text; fallback execs Python with this exact same $0."""
    return shell_header(python, kind) + original_body(source)
