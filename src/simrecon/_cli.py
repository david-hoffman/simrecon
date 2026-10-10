"""Thin JSON command-line interface for the public conversion functions."""

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any, NoReturn

import numpy as np

from ._imagej import export_imagej
from ._legacy import inspect
from ._metadata import harmonize
from ._model import SimreconError
from ._modern import write


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise SimreconError("config_invalid", message)


def json_value(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return json_value(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {k: json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(v) for v in value]
    if isinstance(value, (Path, np.dtype)):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def reject_constant(value: str) -> NoReturn:
    raise ValueError(f"Nonfinite JSON constant: {value}")


def load_config(path: str) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        try:
            config = json.load(handle, parse_constant=reject_constant)
        except (ValueError, UnicodeError) as exc:
            raise SimreconError(
                "config_invalid", "Configuration must be valid finite JSON"
            ) from exc
    if not isinstance(config, dict):
        raise SimreconError("config_invalid", "Configuration must be a JSON object")
    return config


def main() -> int:
    parser = Parser(prog="simrecon")
    commands = parser.add_subparsers(dest="command", required=True)
    inspection = commands.add_parser("inspect")
    inspection.add_argument("source")
    conversion = commands.add_parser("convert")
    conversion.add_argument("source")
    conversion.add_argument("destination")
    conversion.add_argument("--config", required=True)
    conversion.add_argument("--block-planes", type=int, default=1)
    imagej = commands.add_parser("export-imagej")
    imagej.add_argument("source")
    imagej.add_argument("destination")
    imagej.add_argument("--config", required=True)
    imagej.add_argument("--block-planes", type=int, default=1)
    try:
        args = parser.parse_args()
        info = inspect(args.source)
        if args.command == "inspect":
            result = info
        else:
            exporter = export_imagej if args.command == "export-imagej" else write
            result = exporter(
                args.destination,
                harmonize(info, config=load_config(args.config)),
                block_planes=args.block_planes,
            )
        print(
            json.dumps(json_value(result), allow_nan=False, sort_keys=True, separators=(",", ":"))
        )
        return 0
    except SimreconError as exc:
        print(json.dumps({"code": exc.code, "message": exc.message}), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"code": "io_error", "message": str(exc)}), file=sys.stderr)
        return 1
