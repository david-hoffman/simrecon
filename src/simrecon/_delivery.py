"""Thin native launcher for the bounded delivery doctor procedure."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Launch one fresh doctor session and preserve its output and status."""
    parser = argparse.ArgumentParser(prog="delivery", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", allow_abbrev=False)
    doctor.add_argument("--check", action="store_true", help="Report only; write no files")
    args = parser.parse_args()

    prompt = (
        "Use $review-work in doctor mode in this fresh native root session. "
        "Read and follow docs/agentic-software-delivery-v1.0/DOCTOR-PROMPT.md. "
        "Disable optional memory and delegation. "
    )
    command = [
        "codex",
        "exec",
        "--ignore-user-config",
        "--disable",
        "memories",
        "--disable",
        "multi_agent",
        "--model",
        "gpt-6.1-sol",
        "-C",
        str(Path.cwd()),
    ]
    if args.check:
        command.extend(["--sandbox", "read-only"])
        prompt += "Run with --check: report only and do not write files."
    else:
        command.append("--approve-for-me")
        prompt += (
            "Authorize only the bounded documentation patch under the doctor procedure. "
            "Present the exact diff and evidence, then wait for explicit owner approval "
            "before committing, pushing, or merging."
        )
    command.append("-")
    try:
        return subprocess.run(command, input=prompt, text=True, check=False).returncode
    except FileNotFoundError:
        print(
            "delivery: codex was not found on PATH; make the native Codex CLI available.",
            file=sys.stderr,
        )
        return 127
