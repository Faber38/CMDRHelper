"""Batch-scoped journal bytes shared by live observers; no persistent cache/poller."""
from contextlib import contextmanager
from contextvars import ContextVar
from io import BytesIO
from pathlib import Path

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


def _tail(path, offset):
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
            raise OSError('Journal changed during live batch')
        if offset < cached[0]:
            with Path(path).open('rb') as stream:
                stream.seek(offset)
                prefix = stream.read(cached[0] - offset)
            if len(prefix) != cached[0] - offset:
                raise OSError('Journal truncated during live batch')
            cached = offset, prefix + cached[1], before
    if _signature(path) != before:
        raise OSError('Journal changed during live read')
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
