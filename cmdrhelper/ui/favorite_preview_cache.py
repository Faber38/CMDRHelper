"""GUI-thread-only, view-owned preview pixels; never an ownership/data cache."""
from collections import OrderedDict
import math
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader, QPixmap


def preview(path, width=600, height=320, *, dpr=1.0):
    if not path:
        return QPixmap()
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    width, height = math.ceil(width * dpr), math.ceil(height * dpr)
    size = reader.size()
    if size.isValid():
        reader.setScaledSize(size.scaled(width, height, Qt.KeepAspectRatio))
    image = reader.read()
    if image.width() > width or image.height() > height:
        image = image.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    pixmap = QPixmap.fromImage(image)
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


class FavoritePreviewCache:
    """24 MiB of decoded pixels, plus at most 256 small bookkeeping entries.

    QPixmap copies share pixels until modified. Eviction releases this cache's
    reference; visible icons/labels may still own their currently displayed copy.
    Decoder work buffers and visible widget pixels are not part of this limit.
    Callers must still validate commander ownership and managed image paths.
    """
    MAX_BYTES = 24 * 1024 * 1024
    MAX_ENTRIES = 256

    def __init__(self):
        self._entries = OrderedDict()
        self.bytes_used = 0
        self.hits = self.misses = self.decodes = self.evictions = 0

    @staticmethod
    def key(path, width=600, height=320, *, dpr=1.0, owner=None):
        if not path:
            return None
        if width <= 0 or height <= 0 or not math.isfinite(dpr) or dpr <= 0:
            return None
        path = Path(path).absolute()
        try:
            stat = path.stat()
        except OSError:
            return None
        version = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        return owner, str(path), version, width, height, float(dpr)

    def _remove(self, key):
        _, size = self._entries.pop(key)
        self.bytes_used -= size

    def discard(self, owner, path):
        if path:
            path = str(Path(path).absolute())
            for key in list(self._entries):
                if key[:2] == (owner, path):
                    self._remove(key)

    def clear(self):
        self._entries.clear()
        self.bytes_used = 0

    def get(self, path, width=600, height=320, *, dpr=1.0, owner=None, decoder=preview):
        key = self.key(path, width, height, dpr=dpr, owner=owner)
        if key is None:
            self.discard(owner, path)
            return QPixmap()
        # Drop old versions in every size, not just the requested variant.
        for old in list(self._entries):
            if old[:2] == key[:2] and old[2] != key[2]:
                self._remove(old)
        if key in self._entries:
            self.hits += 1
            self._entries.move_to_end(key)
            return QPixmap(self._entries[key][0])
        self.misses += 1
        self.decodes += 1
        pixmap = decoder(path, width, height, dpr=dpr)
        if pixmap.isNull() or key != self.key(path, width, height, dpr=dpr, owner=owner):
            return QPixmap()  # Retry failures/concurrent replacements next time.
        size = pixmap.toImage().sizeInBytes()
        if size > self.MAX_BYTES:
            return pixmap  # Displayable, but never retained by this cache.
        while self._entries and (self.bytes_used + size > self.MAX_BYTES
                                 or len(self._entries) >= self.MAX_ENTRIES):
            self._remove(next(iter(self._entries)))
            self.evictions += 1
        self._entries[key] = QPixmap(pixmap), size
        self.bytes_used += size
        return pixmap
