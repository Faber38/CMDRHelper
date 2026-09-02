"""Reproduzierbar: python3 tests/benchmark_journal_index.py [10 500 4000]."""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder


def run(count):
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        line = json.dumps({"timestamp": "2026-01-01T00:00:00Z",
                           "event": "Commander", "FID": "F-BENCH",
                           "Name": "Bench"}) + "\n"
        for number in range(count):
            (folder / f"Journal.2026-01-01T000000.{number + 1:05d}.log").write_text(line)
        database = CMDRDatabase(folder / "benchmark.db")
        started = time.perf_counter()
        scan_journal_folder(database, folder)
        first = time.perf_counter() - started
        started = time.perf_counter()
        scan_journal_folder(database, folder)
        second = time.perf_counter() - started
        latest = max(folder.glob("Journal.*.log"))
        with latest.open("a") as handle:
            handle.write(line)
        started = time.perf_counter()
        scan_journal_folder(database, folder)
        live = time.perf_counter() - started
        print(f"{count:5d}: first={first:.4f}s second={second:.4f}s live={live:.4f}s")


for value in ([10, 500, 4000] if len(sys.argv) == 1 else map(int, sys.argv[1:])):
    run(value)
