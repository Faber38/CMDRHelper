"""Zentrale, auch aus install.bat ausführbare Python-Kompatibilitätsprüfung."""
from __future__ import annotations

import argparse
import sys

MIN_PYTHON = (3, 10)
MAX_PYTHON_EXCLUSIVE = (3, 14)


def is_supported(version_info=None) -> bool:
    version = tuple(version_info or sys.version_info)
    return MIN_PYTHON <= version[:2] < MAX_PYTHON_EXCLUSIVE


def supported_description() -> str:
    return "Python 3.10 bis 3.13 (64-Bit empfohlen)"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args(argv)
    if args.describe:
        print(f"Unterstuetzt: {supported_description()}")
    if args.check and not is_supported():
        print(
            f"Nicht unterstuetzt: Python {sys.version_info.major}."
            f"{sys.version_info.minor}; erwartet {supported_description()}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
