"""Batch-scoped journal bytes shared by live observers; no persistent cache/poller."""
from contextlib import contextmanager
from contextvars import ContextVar
from io import BytesIO
from pathlib import Path
from .startup_runtime import JournalPending, diagnostic

_batch = ContextVar('live_journal_batch', default=None)


@contextmanager
def journal_batch():
    if _batch.get() is not None:
        yield
        return
    token = _batch.set({})
    try:
        yield
    finally:
        _batch.reset(token)


def _signature(path):
    stat = Path(path).stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _change_reason(before, after):
    return ('journal_replaced_or_truncated' if before[:2] != after[:2] or after[2] < before[2]
            else 'journal_changed_during_read')


def _tail(path, offset):
    try:
        return _read_tail(path, offset)
    except OSError as exc:
        diagnostic('live_journal', 'catchup', exc)
        raise


def _read_tail(path, offset):
    cache = _batch.get()
    key = str(Path(path).resolve())
    cached = cache.get(key) if cache is not None else None
    before = _signature(path)
    if cached is None:
        with Path(path).open('rb') as stream:
            stream.seek(offset)
            raw = stream.read()
        cached = offset, raw, before
    else:
        if cached[2] != before:
            raise JournalPending(_change_reason(cached[2], before))
        if offset < cached[0]:
            with Path(path).open('rb') as stream:
                stream.seek(offset)
                prefix = stream.read(cached[0] - offset)
            if len(prefix) != cached[0] - offset:
                raise JournalPending('journal_replaced_or_truncated')
            cached = offset, prefix + cached[1], before
    after = _signature(path)
    if after != before:
        raise JournalPending(_change_reason(before, after))
    if cache is not None:
        cache[key] = cached
    return cached[1][offset - cached[0]:]


def read_bytes(path):
    return _tail(path, 0)


class _TailReader:
    def __init__(self, path):
        self.path = path
        self.base = 0
        self.stream = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.stream is not None:
            self.stream.close()

    def seek(self, offset):
        self.base = offset
        self.stream = BytesIO(_tail(self.path, offset))

    def readline(self):
        return self.stream.readline()

    def tell(self):
        return self.base + self.stream.tell()


def open_journal(path):
    if _batch.get() is None:
        return Path(path).open('rb')
    return _TailReader(path)
