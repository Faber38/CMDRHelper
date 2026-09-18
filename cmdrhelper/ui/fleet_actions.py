"""UI services for reversible image cleanup and fleet-only background reads."""
from contextlib import contextmanager
from PySide6.QtCore import QObject, QRunnable, Signal, QSaveFile, QIODevice

from cmdrhelper.fleet_reconstruction import reconstruct_fleet
from cmdrhelper.ui.personal_ship_images import _settings_key, _internal_path, _save_reference


@contextmanager
def reversible_image_removal(settings, fid, ship_id):
    """Compensate filesystem/QSettings changes if SQLite persistence fails."""
    key = _settings_key(fid, ship_id)
    name = settings.value(key, "")
    path = _internal_path(name)
    content = path.read_bytes() if path is not None and path.exists() else None
    changed = False

    def remove():
        nonlocal changed
        changed = True
        _save_reference(settings, key, "")
        if path is not None:
            path.unlink(missing_ok=True)

    try:
        yield remove
    except Exception:
        if changed:
            if content is not None and not path.exists():
                output = QSaveFile(str(path))
                if not output.open(QIODevice.WriteOnly) or output.write(content) != len(content) or not output.commit():
                    raise OSError("Could not restore personal image")
            _save_reference(settings, key, name)
        raise


class FleetReadSignals(QObject):
    done = Signal(object, str)


class FleetReadTask(QRunnable):
    def __init__(self, paths, fid):
        super().__init__()
        self.paths, self.fid = paths, fid
        self.signals = FleetReadSignals()

    def run(self):
        try:
            fleet = reconstruct_fleet(self.paths, self.fid)
            if not fleet and not fleet.sales:
                raise ValueError("No identified ships found")
        except Exception as exc:
            self.signals.done.emit(None, str(exc))
        else:
            self.signals.done.emit(fleet, "")
