"""One persisted age selection for all trade searches."""
from datetime import timedelta
from PySide6.QtWidgets import QComboBox
from cmdrhelper.i18n import tr

HOURS = (1, 6, 12, 24, 48, 72, 168, 336, 720, 0)
SETTING = 'trade/max_age_hours'


class MarketAgeCombo(QComboBox):
    def __init__(self, state):
        super().__init__()
        self.settings = getattr(state, 'settings', None)
        for hours in HOURS:
            self.addItem(tr('trade.age_option_' + str(hours)), hours)
        value = self.settings.value(SETTING, 24) if self.settings is not None else 24
        # QSettings may return strings; reject booleans, floats and unknown values.
        value = int(value) if type(value) is str and value in {str(h) for h in HOURS} else value
        if type(value) is not int or value not in HOURS:
            value = 24
        self.setCurrentIndex(self.findData(value))
        self.currentIndexChanged.connect(self._save)

    def max_age(self):
        hours = self.currentData()
        return timedelta(hours=hours) if hours else None

    def _save(self):
        if self.settings is not None:
            self.settings.setValue(SETTING, self.currentData())
            self.settings.sync()
