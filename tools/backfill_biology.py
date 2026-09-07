#!/usr/bin/env python3
"""Preview missing BIO body findings; --apply inserts them after a DB backup."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmdrhelper.biology_backfill import backfill_biology


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--commander-id", type=int, required=True)
    parser.add_argument("--journal", action="append", dest="journals", type=Path)
    parser.add_argument("--system-address", type=int)
    parser.add_argument("--body-id", type=int)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-path", type=Path)
    args = vars(parser.parse_args())
    print(json.dumps(backfill_biology(**args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
