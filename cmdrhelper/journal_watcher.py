from pathlib import Path
import logging
import os
import time

from PySide6.QtCore import QObject, QTimer, Signal
from cmdrhelper.odyssey_sidecars import OdysseySidecars

logger = logging.getLogger(__name__)


class JournalWatcher(QObject):
    journalChanged = Signal()
    odysseySidecarsChanged = Signal()
    odysseyTrackingUpdated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.folder = None
        self._sig = None
        self._pending_sig = None
        self._refresh_in_progress = False
        self._current = None
        self._poll_count = 0
        self._directory_check_interval = 10
        self._retry_delay = 0
        self._retry_at = 0
        self._catchup_signatures = {}
        self._catchup_requested = False
        self.odyssey_sidecars = OdysseySidecars()

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
        self._current = None
        self._poll_count = 0
        self._retry_delay = 0
        self._retry_at = 0
        self._catchup_signatures = {}
        self._catchup_requested = False
        self.odyssey_sidecars = OdysseySidecars()

    def start(self):
        if not self.timer.isActive():
            self.timer.start()

    def check_now(self):
        """Prüft sofort, unter Beachtung eines ausstehenden Fehler-Backoffs."""
        self._poll()

    def refresh_deferred(self):
        """Release a deferred poll without acknowledging input or adding backoff."""
        self._pending_sig = None
        self._refresh_in_progress = False

    def refresh_finished(self, success):
        """Bestätigt eine Änderung erst nach erfolgreichem State-Refresh."""
        if not self._refresh_in_progress:
            return

        pending = self._pending_sig
        if success and pending is not None:
            self._retry_delay = 0
            self._retry_at = 0
            old_path = self._sig[0] if self._sig else ""
            self._sig = pending
            if old_path != pending[0]:
                logger.info("Journal überwacht: %s", Path(pending[0]).name)
        elif pending is not None:
            self._retry_delay = min(60, max(2, self._retry_delay * 2))
            self._retry_at = time.monotonic() + self._retry_delay
            logger.warning(
                "Journaländerung nicht bestätigt; erneuter Versuch nach Backoff",
                extra={"diagnostic_fields": {"retry_seconds": self._retry_delay}},
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
        # Keep the acknowledged signature unchanged. Even if the file grows,
        # retry the uncommitted input only after the delay (timer stays at 1 s).
        if time.monotonic() < self._retry_at:
            return

        # Files involved in an import pause can still receive a late tail
        # after rotation. Keep observing those few paths, not just the newest.
        for name, previous in self._catchup_signatures.items():
            try:
                st = Path(name).stat()
                current = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
            except OSError:
                current = None
            if current != previous:
                self._catchup_requested = True

        self._poll_count += 1
        rescan = self._current is None or (
            self._poll_count % self._directory_check_interval == 0
        )
        try:
            if rescan:
                # Genau ein scandir-Durchlauf; nur beim Start und danach
                # alle zehn Sekunden nach neu angelegten Sitzungen suchen.
                candidates = []
                with os.scandir(self.folder) as entries:
                    for entry in entries:
                        if entry.is_file(follow_symlinks=False) and (
                            entry.name.startswith("Journal.")
                            and entry.name.endswith(".log")
                        ):
                            candidates.append(Path(entry.path))
                if candidates:
                    from cmdrhelper.journal_files import journal_sort_key
                    newest = max(candidates, key=journal_sort_key)
                    if self._current is None or (
                        journal_sort_key(newest) > journal_sort_key(self._current)
                    ):
                        self._current = newest
            files = [self._current] if self._current is not None else []
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

        # Small personal files may finish after the journal notification. This
        # capture also runs when no material view exists, without a State refresh.
        if self.odyssey_sidecars.poll(current):
            self.odysseySidecarsChanged.emit()
        self.odysseyTrackingUpdated.emit()

        if sig == self._sig and not self._catchup_requested:
            return

        if self._sig is not None and self._sig[0] != str(current):
            logger.info("Neue Journaldatei erkannt: %s", current.name)
        logger.debug("Journaländerung erkannt: %s", current.name)

        # Noch nicht als verarbeitet markieren. Der direkt verbundene
        # AppState bestätigt die Signatur erst nach erfolgreichem Lesen.
        self._pending_sig = sig
        self._refresh_in_progress = True
        self.journalChanged.emit()
