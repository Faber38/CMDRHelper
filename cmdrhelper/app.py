import sys
import logging
import platform
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings, QLockFile, QDir
from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.logging_config import configure_logging, log_event
from cmdrhelper.version import __version__
from cmdrhelper.i18n import tr, set_language
from cmdrhelper.update import consume_update_status


INITIAL_WINDOW_WIDTH = 1500
INITIAL_WINDOW_HEIGHT = 900
INITIAL_WINDOW_MARGIN = 80


def _bounded_initial_dimension(preferred, available, minimum):
    return max(minimum, min(preferred, max(0, available - INITIAL_WINDOW_MARGIN)))


def _resize_initial_window(window, screen):
    available = screen.availableGeometry()
    minimum_hint = window.minimumSizeHint()

    width = _bounded_initial_dimension(
        INITIAL_WINDOW_WIDTH,
        available.width(),
        max(window.minimumWidth(), minimum_hint.width()),
    )
    height = _bounded_initial_dimension(
        INITIAL_WINDOW_HEIGHT,
        available.height(),
        max(window.minimumHeight(), minimum_hint.height()),
    )
    window.resize(width, height)


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
    from cmdrhelper.diagnostics import system_info
    info = system_info()
    log_event(logger, 'Application started; installation=<installation>; database=<database>; journals=<journals>',
              version=info['version'], os=info['os'], python=info['python'],
              qt=info['qt'], pyside=info['pyside'], architecture=info['architecture'], pid=os.getpid())

    app = QApplication(sys.argv)
    app.setApplicationName("CMDRHelper")
    app.setOrganizationName("CMDRHelper")

    settings = QSettings("CMDRHelper", "CMDRHelper")
    set_language(settings.value("ui_language", "de"))

    # Nur eine CMDRHelper-Instanz gleichzeitig zulassen.
    lock_path = QDir.temp().filePath("cmdrhelper.lock")
    instance_lock = QLockFile(lock_path)
    if os.name == "nt":
        instance_lock.setStaleLockTime(0)

    if not instance_lock.tryLock(100):
        logger.warning("Programmstart abgebrochen: CMDRHelper läuft bereits.")
        log_event(logger, "Application instance lock busy", pid=os.getpid())

        QMessageBox.information(
            None,
            tr("app.already_running_title"),
            tr("app.already_running_text"),
        )

        return

    # Lock während der gesamten Laufzeit behalten.
    app._cmdrhelper_instance_lock = instance_lock

    update_status = consume_update_status(Path(__file__).resolve().parents[1])
    if update_status and update_status.get("kind") == "rollback":
        QMessageBox.warning(
            None,
            tr("settings.update_failed_title"),
            tr(
                "app.update_rollback_text",
                phase=update_status.get("phase") or "–",
                log=update_status.get("log") or "–",
            ),
        )

    theme = str(settings.value("ui_theme", "dark")).lower()

    app.setStyleSheet(LIGHT_STYLESHEET if theme == "light" else DARK_STYLESHEET)

    # Gate before schema initialization, journal watchers and startup repairs.
    from cmdrhelper.database import default_database_path
    from cmdrhelper.journal_reader import default_journal_paths
    from cmdrhelper.parent_migration import migration_required
    from cmdrhelper.ui.parent_migration import ParentMigrationDialog
    from PySide6.QtWidgets import QDialog

    db_path = default_database_path()
    if migration_required(db_path):
        saved = settings.value("journal_folder", "")
        folders = default_journal_paths()
        folder = Path(saved) if saved and Path(saved).exists() else (folders[0] if folders else None)
        dialog = ParentMigrationDialog(db_path, folder, light=theme == "light")
        if dialog.exec() != QDialog.Accepted:
            return

    state = AppState()
    window = MainWindow(state)
    _resize_initial_window(window, app.primaryScreen())
    window.show()
    try:
        raise SystemExit(app.exec())
    finally:
        logger.info("Application ended; database access ended")
