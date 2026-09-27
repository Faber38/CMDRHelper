"""One persisted age selection for all trade searches."""
from datetime import timedelta
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QObject, Signal
from cmdrhelper.i18n import tr

HOURS = (1, 6, 12, 24, 48, 72, 168, 336, 720, 0)
SETTING = 'trade/max_age_hours'


class _AgeEvents(QObject):
    changed = Signal()


age_events = _AgeEvents()


def saved_hours(settings):
    value = settings.value(SETTING, 24) if settings is not None else 24
    value = int(value) if type(value) is str and value in {str(h) for h in HOURS} else value
    return value if type(value) is int and value in HOURS else 24


def saved_max_age(settings):
    hours = saved_hours(settings)
    return timedelta(hours=hours) if hours else None


class MarketAgeCombo(QComboBox):
    def __init__(self, state):
        super().__init__()
        self.settings = getattr(state, 'settings', None)
        for hours in HOURS:
            self.addItem(tr('trade.age_option_' + str(hours)), hours)
        value = saved_hours(self.settings)
        self.setCurrentIndex(self.findData(value))
        self.currentIndexChanged.connect(self._save)

    def max_age(self):
        hours = self.currentData()
        return timedelta(hours=hours) if hours else None

    def _save(self):
        if self.settings is not None:
            self.settings.setValue(SETTING, self.currentData())
            self.settings.sync()
            age_events.changed.emit()
