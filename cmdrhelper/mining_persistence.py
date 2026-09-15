"""Checked publication of Mining settings; restore prior values on failure."""
from copy import deepcopy
from PySide6.QtCore import QSettings


def save_values(settings, values):
    changed = {key: value for key, value in values.items() if settings.value(key) != value}
    if not changed:
        return
    before = {key: deepcopy(settings.value(key)) for key in changed}
    for key, value in changed.items():
        settings.setValue(key, value)
    settings.sync()
    if settings.status() != QSettings.Status.NoError:
        for key, value in before.items():
            if value is None:
                settings.remove(key)
            else:
                settings.setValue(key, value)
        settings.sync()  # Best effort; a still failing disk cannot be repaired here.
        raise OSError("Mining settings could not be persisted")
