import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

def run():
    app = QApplication(sys.argv)
    app.setApplicationName("CMDRHelper")
    app.setOrganizationName("CMDRHelper")
    settings = QSettings("CMDRHelper", "CMDRHelper")
    theme = str(settings.value("ui_theme", "dark")).lower()

    app.setStyleSheet(
        LIGHT_STYLESHEET
        if theme == "light"
        else DARK_STYLESHEET
    )

    state = AppState()
    window = MainWindow(state)
    window.resize(1500, 900)
    window.show()
    raise SystemExit(app.exec())
