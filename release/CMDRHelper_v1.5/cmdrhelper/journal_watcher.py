from pathlib import Path
import logging

from PySide6.QtCore import QObject, QTimer, Signal

from cmdrhelper.journal_reader import journal_files

logger = logging.getLogger(__name__)


class JournalWatcher(QObject):
    journalChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.folder = None
        self._sig = None
        self._pending_sig = None
        self._refresh_in_progress = False

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._poll)

    def set_folder(self, folder):
        self.folder = (
            Path(folder)
            if folder
            else None
        )
        self._sig = None
        self._pending_sig = None
        self._refresh_in_progress = False

    def start(self):
        if not self.timer.isActive():
            self.timer.start()

    def check_now(self):
        """Prüft sofort; reguläre Folgeprüfungen bleiben beim 1-s-Timer."""
        self._poll()

    def refresh_finished(self, success):
        """Bestätigt eine Änderung erst nach erfolgreichem State-Refresh."""
        if not self._refresh_in_progress:
            return

        pending = self._pending_sig
        if success and pending is not None:
            old_path = self._sig[0] if self._sig else ""
            self._sig = pending
            if old_path != pending[0]:
                logger.info("Journal überwacht: %s", Path(pending[0]).name)
        elif pending is not None:
            logger.warning(
                "Journaländerung nicht bestätigt; erneuter Versuch beim "
                "nächsten Poll: %s",
                pending[0],
            )

        self._pending_sig = None
        self._refresh_in_progress = False

    @staticmethod
    def _file_signature(path):
        """
        Robuste Signatur der aktuellsten Journaldatei.

        Dateiname + Größe sind für Elite-Journale besonders wichtig:
        Unter Windows ist die Zeitauflösung/Weitergabe von mtime nicht
        auf jedem Dateisystem gleich zuverlässig.
        """
        try:
            st = path.stat()
        except (OSError, PermissionError) as exc:
            logger.warning(
                "Journaldatei kann nicht geprüft werden: %s (%s)",
                path,
                exc,
            )
            return None

        return (
            str(path),
            int(st.st_size),
            int(getattr(st, "st_mtime_ns", 0)),
        )

    def _poll(self):
        if not self.folder or self._refresh_in_progress:
            return

        try:
            files = journal_files(self.folder)
        except (OSError, PermissionError) as exc:
            logger.warning(
                "Journalordner kann nicht gelesen werden: %s (%s)",
                self.folder,
                exc,
                exc_info=True,
            )
            return

        if not files:
            return

        # journal_files() liefert die Elite-Journale chronologisch
        # sortiert. files[-1] ist daher die aktuelle Journaldatei.
        current = files[-1]
        sig = self._file_signature(current)

        if sig is None:
            return

        if sig == self._sig:
            return

        if self._sig is not None and self._sig[0] != str(current):
            logger.info("Neue Journaldatei erkannt: %s", current.name)
        logger.debug("Journaländerung erkannt: %s", current.name)

        # Noch nicht als verarbeitet markieren. Der direkt verbundene
        # AppState bestätigt die Signatur erst nach erfolgreichem Lesen.
        self._pending_sig = sig
        self._refresh_in_progress = True
        self.journalChanged.emit()
