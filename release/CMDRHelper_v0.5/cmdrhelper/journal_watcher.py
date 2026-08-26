from PySide6.QtCore import QObject, QTimer, Signal
from cmdrhelper.journal_reader import journal_files

class JournalWatcher(QObject):
    journalChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder = None
        self._sig = None
        self.timer = QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self._poll)

    def set_folder(self, folder):
        self.folder = folder
        self._sig = None

    def start(self):
        self.timer.start()

    def _poll(self):
        files = journal_files(self.folder) if self.folder else []
        if not files:
            return
        p = files[-1]
        st = p.stat()
        sig = (str(p), st.st_mtime_ns, st.st_size)
        if self._sig is None:
            self._sig = sig
        elif sig != self._sig:
            self._sig = sig
            self.journalChanged.emit()
