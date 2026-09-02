from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


_JOURNAL_NAME_RE = re.compile(
    r"^Journal\.(?:(?P<short>\d{12})|"
    r"(?P<long>\d{4}-\d{2}-\d{2}T\d{6}))\."
    r"(?P<part>\d+)\.log$"
)


def journal_sort_key(path: Path) -> tuple:
    """Return a stable chronological key for known Elite journal names."""
    path = Path(path)
    match = _JOURNAL_NAME_RE.fullmatch(path.name)
    if match is not None:
        try:
            if match.group("short"):
                # Elite's compact journal stamp uses a two-digit 20xx year.
                stamp = "20" + match.group("short")
                parsed = datetime.strptime(stamp, "%Y%m%d%H%M%S")
            else:
                parsed = datetime.strptime(
                    match.group("long"), "%Y-%m-%dT%H%M%S"
                )
        except ValueError:
            pass
        else:
            return (
                1,
                parsed,
                int(match.group("part")),
                path.name.casefold(),
            )

    # Unknown or invalid names come before every parsed journal. This keeps a
    # stray matching file from being mistaken for the current live journal.
    return (0, datetime.min, 0, path.name.casefold())


def journal_files(folder: Path) -> list[Path]:
    if not folder or not folder.exists():
        return []
    return sorted(folder.glob("Journal.*.log"), key=journal_sort_key)
