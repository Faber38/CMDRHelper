"""Optional, installation-local power portraits. No download or image writes."""
from pathlib import Path
import re
import unicodedata
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QFrame
from cmdrhelper.i18n import tr

POWERPLAY_ASSET_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'powerplay'


def portrait_key(power):
    text = unicodedata.normalize('NFKD', str(power or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '_', text.casefold()).strip('_')


def portrait_asset_key(power, membership_known=False):
    """Confirmed non-membership has its own asset; unknown is not unaffiliated."""
    if str(power or '').strip():
        return portrait_key(power)
    return 'noMacht' if membership_known else ''


class PowerPortrait(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('muted')
        self.setFixedSize(84, 112)  # Stable 3:4 portrait slot, in Qt logical pixels.
        self.setFrameShape(QFrame.StyledPanel)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setScaledContents(False)
        self.key = ''
        self._signature = None
        self.set_power('')

    def set_power(self, power, membership_known=False):
        self.key = portrait_asset_key(power, membership_known)
        path = POWERPLAY_ASSET_DIR / (self.key + '.png')
        try:
            stat = path.stat() if self.key else None
            signature = (str(path), stat.st_size, stat.st_mtime_ns) if stat else None
        except OSError:
            signature = None
        self.setToolTip(str(power or tr('pp2.no_power' if membership_known else 'pp2.portrait.placeholder')))
        if signature is not None and signature == self._signature:
            return
        self._signature = signature
        pixmap = QPixmap(str(path)) if signature else QPixmap()
        self.clear()
        if pixmap.isNull():
            self.setText(tr('pp2.portrait.placeholder'))
        else:
            self.setPixmap(pixmap.scaled(self.contentsRect().size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
