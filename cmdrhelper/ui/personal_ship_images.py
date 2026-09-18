"""Per-commander images in Qt's user data area, independent of installation."""
import hashlib
from itertools import product
from pathlib import Path
import re
from uuid import uuid4

from PySide6.QtCore import QIODevice, QSaveFile, QSettings, QStandardPaths
from PySide6.QtGui import QImageReader


# Native dialogs may filter case-sensitively on Linux. Enumerate variants rather
# than rely on bracket patterns, whose native Windows support differs.
IMAGE_NAME_PATTERNS = " ".join(
    "*." + "".join(letters)
    for suffix in ("png", "jpg", "jpeg", "webp")
    for letters in product(*[(letter, letter.upper()) for letter in suffix])
)


def _images_directory(image_kind):
    if image_kind not in {"ship", "carrier"}:
        raise ValueError("Unknown image kind")
    location = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not location:
        raise OSError("No application data location")
    return Path(location) / (image_kind + "_images")


def ship_images_directory():
    return _images_directory("ship")


def carrier_images_directory():
    return _images_directory("carrier")


def _directory(image_kind):
    if image_kind == "ship":
        return ship_images_directory()
    if image_kind == "carrier":
        return carrier_images_directory()
    raise ValueError("Unknown image kind")


def _settings_key(fid, ship_id, image_kind="ship"):
    if image_kind not in {"ship", "carrier"}:
        raise ValueError("Unknown image kind")
    if not fid or ship_id is None:
        raise ValueError("Missing commander or ship identity")
    identity = hashlib.sha256(str(fid).encode("utf-8")).hexdigest()
    ship = str(int(ship_id))
    return f"{image_kind}_images/{identity}/{ship}"


def _internal_path(name, image_kind="ship"):
    # Basenames only, equally safe under POSIX and Windows path semantics.
    if not re.fullmatch(r"[a-f0-9]{32}\.png", str(name or "")):
        return None
    root = _directory(image_kind).resolve()
    path = root / name
    if path.is_symlink() or path.resolve().parent != root:
        return None
    return path


def personal_ship_image(settings, fid, ship_id, *, image_kind="ship"):
    try:
        path = _internal_path(settings.value(_settings_key(fid, ship_id, image_kind), ""), image_kind)
        return path if path is not None and path.is_file() else None
    except (OSError, ValueError, RuntimeError):
        return None


def _save_reference(settings, key, name):
    previous = settings.value(key, "")
    settings.setValue(key, name)
    settings.sync()
    if settings.status() != QSettings.NoError:
        settings.setValue(key, previous)
        raise OSError("Cannot save image reference")


def import_ship_image(settings, fid, ship_id, source, *, image_kind="ship"):
    key = _settings_key(fid, ship_id, image_kind)
    source = Path(source)
    if source.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Unsupported image extension")
    reader = QImageReader(str(source))
    reader.setAutoTransform(True)
    image = reader.read()
    if image.isNull():
        raise ValueError("Unreadable image")
    root = _directory(image_kind)
    root.mkdir(parents=True, exist_ok=True)
    name = uuid4().hex + ".png"
    destination = _internal_path(name, image_kind)
    if destination is None:
        raise OSError("Unsafe destination")
    output = QSaveFile(str(destination))
    if not output.open(QIODevice.WriteOnly):
        raise OSError(output.errorString())
    if not image.save(output, "PNG"):
        output.cancelWriting()
        raise OSError("Cannot encode PNG")
    if not output.commit():
        raise OSError(output.errorString())
    previous = personal_ship_image(settings, fid, ship_id, image_kind=image_kind)
    try:
        _save_reference(settings, key, name)
    except OSError:
        destination.unlink(missing_ok=True)
        raise
    _discard(previous)
    return destination


def _discard(path):
    if path is not None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass  # A stale private copy does not invalidate the new reference.


def remove_ship_image(settings, fid, ship_id, *, image_kind="ship"):
    previous = personal_ship_image(settings, fid, ship_id, image_kind=image_kind)
    _save_reference(settings, _settings_key(fid, ship_id, image_kind), "")
    _discard(previous)


def personal_carrier_image(settings, fid, carrier_id):
    return personal_ship_image(settings, fid, carrier_id, image_kind="carrier")


def import_carrier_image(settings, fid, carrier_id, source):
    return import_ship_image(settings, fid, carrier_id, source, image_kind="carrier")


def remove_carrier_image(settings, fid, carrier_id):
    remove_ship_image(settings, fid, carrier_id, image_kind="carrier")
