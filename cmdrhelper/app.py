import sys
import logging
import platform
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings, QLockFile, QDir
from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.logging_config import configure_logging
from cmdrhelper.version import __version__


def run():
    log_file = configure_logging()
    logger = logging.getLogger(__name__)

    def exception_hook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Unbehandelte Ausnahme",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = exception_hook

    logger.info("CMDRHelper %s gestartet", __version__)
    logger.info(
        "System: %s %s | Python: %s",
        platform.system(),
        platform.release(),
        platform.python_version(),
    )
    logger.info("Logdatei: %s", log_file)

    app = QApplication(sys.argv)
    app.setApplicationName("CMDRHelper")
    app.setOrganizationName("CMDRHelper")

    # Nur eine CMDRHelper-Instanz gleichzeitig zulassen.
    lock_path = QDir.temp().filePath("cmdrhelper.lock")
    instance_lock = QLockFile(lock_path)

    if not instance_lock.tryLock(100):
        logger.warning("Programmstart abgebrochen: CMDRHelper läuft bereits.")

        QMessageBox.information(
            None,
            "CMDRHelper läuft bereits",
            "CMDRHelper ist bereits gestartet.\n\n"
            "Eine zweite Instanz wird nicht geöffnet.",
        )

        return

    # Lock während der gesamten Laufzeit behalten.
    app._cmdrhelper_instance_lock = instance_lock

    settings = QSettings("CMDRHelper", "CMDRHelper")
    theme = str(settings.value("ui_theme", "dark")).lower()

    app.setStyleSheet(LIGHT_STYLESHEET if theme == "light" else DARK_STYLESHEET)

    state = AppState()
    window = MainWindow(state)
    window.resize(1500, 900)
    window.show()
    raise SystemExit(app.exec())
