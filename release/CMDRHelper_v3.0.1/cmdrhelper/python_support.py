"""Zentrale, auch aus install.bat ausführbare Python-Kompatibilitätsprüfung."""
from __future__ import annotations

import argparse
import json
import struct
import sys
import sysconfig

MIN_PYTHON = (3, 10)


def is_supported(version_info=None) -> bool:
    version = tuple(version_info or sys.version_info)
    if sys.platform == "win32":
        return (
            version[:2] >= MIN_PYTHON
            and struct.calcsize("P") == 8
            and sysconfig.get_platform() == "win-amd64"
        )
    return version[:2] >= MIN_PYTHON


def supported_description() -> str:
    if sys.platform == "win32":
        return "Python 3.10 oder neuer (Windows x64 / 64 Bit erforderlich)"
    return "Python 3.10 oder neuer (64-Bit empfohlen)"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--describe", action="store_true")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)
    if args.describe:
        print(f"Unterstuetzt: {supported_description()}")
    if (args.check or args.probe) and not is_supported():
        print(
            f"Nicht unterstuetzt: Python {sys.version_info.major}."
            f"{sys.version_info.minor}; erwartet {supported_description()}",
            file=sys.stderr,
        )
        return 1
    if args.probe:
        print(json.dumps({
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
