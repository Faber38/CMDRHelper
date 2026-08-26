from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from cmdrhelper.journal_reader import journal_files


class JournalWatcher(QObject):
    journalChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.folder = None
        self._sig = None

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

    def start(self):
        if not self.timer.isActive():
            self.timer.start()

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
        except (OSError, PermissionError):
            return None

        return (
            str(path),
            int(st.st_size),
            int(getattr(st, "st_mtime_ns", 0)),
        )

    def _poll(self):
        if not self.folder:
            return

        try:
            files = journal_files(self.folder)
        except (OSError, PermissionError):
            return

        if not files:
            return

        # journal_files() liefert die Elite-Journale chronologisch
        # sortiert. files[-1] ist daher die aktuelle Journaldatei.
        current = files[-1]
        sig = self._file_signature(current)

        if sig is None:
            return

        if self._sig is None:
            self._sig = sig
            return

        if sig != self._sig:
            self._sig = sig
            self.journalChanged.emit()
