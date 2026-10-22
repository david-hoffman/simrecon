"""Supplement R10/C73/C74 through the documented source-free Python CLI.

Automated assertions cover caller fields, source suppression, categories, stack
locations and process status. They do not interpret unrestricted diagnostic prose.
The captured JSON observations (visible with pytest -rP) require separate semantic
review against caller-owned expectations for the exact candidate: complete field
association, polarity, honest unavailable identity, exact available identity and
numeric meaning. A passing pytest run alone does not establish those properties.

These are constructor/rendering examples, not claims about valid Popen argv or
actual child failures. No diagnostic wording, order or punctuation is prescribed.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "source_free_check.py"
CALLER = Path(__file__).with_name("shared_node_baseline_diagnostic_metadata_fixture.py")
ARGUMENT_MARKER = "A10_PRIVATE_COMMAND_ARGUMENT_62c093"
INLINE_MARKER = "A10_PRIVATE_INLINE_SOURCE_a7184d"
SOURCE_MARKER = "A10_SOURCE_SNIPPET_MUST_BE_HIDDEN_9087e1"
SHAPES = (
    "list-none",
    "tuple-none",
    "list-integer",
    "tuple-integer",
    "string",
    "list-text",
    "tuple-text",
    "list-bytes",
    "tuple-bytes",
    "list-path",
    "tuple-path",
)


class FormattingReport(TypedDict):
    """Explicit caller observations, without printing the command fields."""

    rendered: dict[str, str]
    field_checks: dict[str, dict[str, bool]]


def run_caller(kind: str, shape: str, channel: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HARNESS), "python", str(CALLER), kind, shape, channel],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def record_observation(
    kind: str, shape: str, channel: str, result: subprocess.CompletedProcess[str]
) -> None:
    """Keep complete public observations for candidate-specific semantic review.

    Expected values come from the authorized examples, never from rendered text.
    This record is test evidence, not a production diagnostic schema or an oracle
    verdict. Preserve both streams so contradictory claims cannot be hidden by
    extracting only a matching word, number or clause.
    """
    print(
        "DIAGNOSTIC_OBSERVATION "
        + json.dumps(
            {
                "kind": kind,
                "shape": shape,
                "channel": channel,
                "expected": {
                    "executable": (
                        sys.executable if shape.endswith(("-text", "-bytes", "-path")) else None
                    ),
                    "timeout_seconds": "1.75" if kind == "timeout" else None,
                    "child_status": 23 if kind == "child" else None,
                },
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    )


def assert_source_suppression_and_category(
    rendered: str, kind: str, *, includes_category: bool
) -> None:
    """Check only the stated mechanical properties, not message semantics."""
    assert rendered.strip(), rendered
    if includes_category:
        category = "TimeoutExpired" if kind == "timeout" else "CalledProcessError"
        assert category in rendered, rendered
    assert ARGUMENT_MARKER not in rendered, rendered
    assert INLINE_MARKER not in rendered, rendered
    assert SOURCE_MARKER not in rendered, rendered


@pytest.mark.parametrize("kind", ("timeout", "child"))
@pytest.mark.parametrize("shape", SHAPES)
def test_constructor_fields_survive_standard_rendering(kind: str, shape: str) -> None:
    result = run_caller(kind, shape, "formatting")
    record_observation(kind, shape, "formatting", result)
    assert result.returncode == 0, result.stderr
    report = cast("FormattingReport", json.loads(result.stdout))
    assert set(report["field_checks"]) == {
        "before",
        "after_str",
        "after_exception_only",
        "after_traceback",
    }
    expected_fields = {
        "cmd_identity",
        "cmd_contents",
        "output_identity",
        "stdout_alias",
        "stderr_identity",
        "duration_or_status",
        "attributes_unchanged",
        "args_unchanged",
    }
    for stage, checks in report["field_checks"].items():
        assert set(checks) == expected_fields, (stage, checks)
        assert all(checks.values()), (stage, checks)
    assert set(report["rendered"]) == {"str", "exception_only", "traceback"}
    for channel, rendered in report["rendered"].items():
        assert_source_suppression_and_category(rendered, kind, includes_category=channel != "str")
    formatted_stack = report["rendered"]["traceback"]
    assert CALLER.name in formatted_stack, formatted_stack
    assert re.search(r"line \d+", formatted_stack), formatted_stack


@pytest.mark.parametrize("kind", ("timeout", "child"))
@pytest.mark.parametrize("shape", SHAPES)
def test_uncaught_constructor_exception_retains_category_and_stack(kind: str, shape: str) -> None:
    result = run_caller(kind, shape, "uncaught")
    record_observation(kind, shape, "uncaught", result)
    # Python's uncaught-exception exit is 1; no operation returned child status 23.
    assert result.returncode == 1, result.stderr
    assert_source_suppression_and_category(result.stderr, kind, includes_category=True)
    assert CALLER.name in result.stderr, result.stderr
    assert re.search(r"line \d+", result.stderr), result.stderr
