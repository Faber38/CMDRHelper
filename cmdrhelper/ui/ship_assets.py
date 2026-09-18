"""Local, presentation-only ship names and bounded thumbnail cache."""
from functools import lru_cache
from pathlib import Path
import re

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QImageReader, QPixmap

SHIP_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "ships"
# Only confirmed names; unknown identifiers deliberately remain unchanged.
SHIP_DISPLAY_NAMES = {
    "type9": "Type-9 Heavy",
    "asp": "Asp Explorer",
    "cobramkv": "Cobra Mk V",
    "mandalay": "Mandalay",
    "panthermkii": "Panther Clipper Mk II",
}


def canonical_ship_type(ship_type):
    value = str(ship_type or "").strip().casefold()
    aliases = {name.casefold(): key for key, name in SHIP_DISPLAY_NAMES.items()}
    return aliases.get(value, value)


def ship_display_name(ship_type):
    return SHIP_DISPLAY_NAMES.get(canonical_ship_type(ship_type), str(ship_type or "–"))


def resolve_ship_image(ship_type):
    """Resolve safe lowercase basenames inside the bundled directory only."""
    key = canonical_ship_type(ship_type)
    if not re.fullmatch(r"[a-z0-9_]+", key):
        return None
    try:
        root = SHIP_ASSET_DIR.resolve()
        for suffix in (".webp", ".png", ".jpg", ".jpeg"):
            path = root / (key + suffix)
            if path.is_file() and path.resolve().parent == root:
                return path
    except (OSError, RuntimeError):
        pass
    return None


def resolve_standard_ship_image():
    """Bundled fallback, kept separate from personal AppData images."""
    try:
        root = SHIP_ASSET_DIR.resolve()
        path = root / "standart.png"
        if path.is_file() and path.resolve().parent == root:
            return path
    except (OSError, RuntimeError):
        pass
    return None


@lru_cache(maxsize=128)
def _thumbnail(path, stamp, width, height, dpr):
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid():
        reader.setScaledSize(size.scaled(QSize(round(width * dpr), round(height * dpr)),
                                         Qt.KeepAspectRatio))
    image = reader.read()
    if image.isNull():
        return None
    pixmap = QPixmap.fromImage(image).scaled(round(width * dpr), round(height * dpr),
                                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
    pixmap.setDevicePixelRatio(dpr)
    return pixmap


def ship_preview(ship_type, width, height, dpr=1.0, personal_path=None):
    """Return the thumbnail and the exact source that successfully decoded."""
    return _image_preview((personal_path, resolve_ship_image(ship_type), resolve_standard_ship_image()),
                          width, height, dpr)


def resolve_standard_carrier_image():
    """Separate fallback hook for a future bundled carrier motif."""
    return resolve_standard_ship_image()


def carrier_preview(_ship_type, width, height, dpr=1.0, personal_path=None):
    return _image_preview((personal_path, resolve_standard_carrier_image()), width, height, dpr)


def _image_preview(paths, width, height, dpr):
    for path in paths:
        if path is None:
            continue
        try:
            stat = path.stat()
            pixmap = _thumbnail(str(path), (stat.st_mtime_ns, stat.st_size), width, height, dpr)
            if pixmap is not None:
                return pixmap, path
        except OSError:
            pass
    return None, None


def ship_pixmap(ship_type, width, height, dpr=1.0, personal_path=None):
    return ship_preview(ship_type, width, height, dpr, personal_path)[0]
