"""Filesystem and QImage work only; never accesses widgets or the database."""
from threading import Event

from PySide6.QtCore import QObject, Signal, QRunnable, QSize, Qt
from PySide6.QtGui import QImage, QImageReader

from cmdrhelper.screenshot_paths import commander_screenshot_folder, safe_filename_component


def read_image(path, size):
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    original = reader.size()
    if original.isValid():
        reader.setScaledSize(original.scaled(size, Qt.KeepAspectRatio))
    image = reader.read()
    return image if image.isNull() else image.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class LoadSignals(QObject):
    finished = Signal(object)


class GalleryWorker(QRunnable):
    def __init__(self, target, mode, commanders, current, previous=None):
        super().__init__()
        self.target, self.mode = target, mode
        self.commanders, self.current = commanders, current
        self.previous = previous
        self.cancelled = Event()
        self.signals = LoadSignals()

    def run(self):
        try:
            entries = []
            target = self.target
            directories = []
            if target and target.exists():
                if not target.is_dir():
                    raise OSError(str(target))
                if self.mode == 'unassigned':
                    directories = [target]
                elif self.mode == 'all':
                    suffixes = {'_' + safe_filename_component(c.get('fid')).casefold()
                                for c in self.commanders} | {'_unknown'}
                    directories = [p for p in target.iterdir() if not p.is_symlink()
                                   and p.is_dir() and any(p.name.casefold().endswith(s) for s in suffixes)]
                else:
                    c = self.current or {}
                    folder = commander_screenshot_folder(target, c.get('current_name'), c.get('fid'))
                    if folder and folder.is_dir():
                        directories = [folder]
                for directory in directories:
                    for path in directory.iterdir():
                        if self.cancelled.is_set():
                            return
                        if not path.is_symlink() and path.suffix.lower() in ('.png', '.jpg', '.jpeg') and path.is_file():
                            stat = path.stat()
                            entries.append((str(path.relative_to(target)), stat.st_mtime_ns, stat.st_size))
            snapshot = tuple(sorted(entries))
            rows, broken = [], []
            if snapshot != self.previous:
                for name, _, _ in sorted(entries, key=lambda e: (e[1], e[0]), reverse=True):
                    if self.cancelled.is_set():
                        return
                    path = target / name
                    image = read_image(path, QSize(150, 95))
                    if image.isNull():
                        broken.append(name)
                    else:
                        rows.append((str(path), image))
            self.signals.finished.emit((snapshot, rows, broken, ''))
        except Exception as exc:
            self.signals.finished.emit((None, [], [], str(exc)))


class PreviewWorker(QRunnable):
    def __init__(self, path, size):
        super().__init__()
        self.path, self.size = path, size
        self.signals = LoadSignals()

    def run(self):
        try:
            image = read_image(self.path, self.size)
        except Exception:
            image = QImage()
        self.signals.finished.emit((self.path, image))
