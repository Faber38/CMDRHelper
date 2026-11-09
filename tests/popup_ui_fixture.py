"""Shared popup UI preparation; contains no discoverable test cases."""
import tempfile
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QWidget
from cmdrhelper.i18n import set_language
from cmdrhelper.ui.main_window import ExplorerLiveListWindow, MainWindow


class PopupUiFixture:
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language("de")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "settings.ini")
        self.settings = QSettings(self.path, QSettings.IniFormat)
        self.addCleanup(self.app.setStyleSheet, "")

    def keep(self, widget):
        from PySide6.QtCore import QCoreApplication, QEvent
        self.addCleanup(QCoreApplication.sendPostedEvents, None, QEvent.DeferredDelete)
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        return widget

    def popup(self, kind="bio", settings=None):
        return self.keep(ExplorerLiveListWindow("Test", ["Body", "BIO / GEO", "Progress", "Value"],
            settings or self.settings, f"explorer_live/{kind}_geometry", window_kind=kind))

    def main(self, settings=None):
        state = SimpleNamespace(settings=settings or self.settings, system="Test", system_address=1,
            system_bodies=[], database=SimpleNamespace(learned_bio_values=lambda: {}, biology_predictor=lambda: None),
            initializationStarted=Mock(), initializationProgress=Mock(), initializationFinished=Mock(),
            changed=Mock(), viewedCommanderChanged=Mock())
        with ExitStack() as stack:
            for name in ("_apply_saved_ui_font", "refresh_all", "_apply_cargo_hud_enabled"):
                stack.enter_context(patch.object(MainWindow, name))
            for name in ("_overview", "_missions", "_explorer", "_chronicle", "_score_page", "_settings", "_navigation_page"):
                stack.enter_context(patch.object(MainWindow, name, side_effect=lambda: QWidget()))
            stack.enter_context(patch("cmdrhelper.ui.main_window.QTimer.singleShot"))
            for name in ("RoutePlannerView", "ScreenshotView", "CommanderView"):
                stack.enter_context(patch("cmdrhelper.ui.main_window." + name, side_effect=lambda *a: QWidget()))
            main = self.keep(MainWindow(state))
        main._explorer_live_system = "Test"
        main._apply_cargo_hud_enabled = Mock()
        return main

    def explorer(self, main):
        with patch("cmdrhelper.ui.favorites_view.FavoritesView", side_effect=lambda *a, **kw: QWidget()):
            return self.keep(main._explorer())

