#!/usr/bin/env python3
"""Preview system-stay recovery; --apply updates visits after a SQLite backup."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmdrhelper.visits_backfill import backfill_visits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--commander-id", type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-path", type=Path)
    print(json.dumps(backfill_visits(**vars(parser.parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
