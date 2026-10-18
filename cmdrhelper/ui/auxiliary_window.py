"""Independent desktop windows with the main widget retaining Qt ownership."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget


class AuxiliaryWindow:
    """Opt-in mixin for modeless windows, never for modal dialogs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        owner = self.parentWidget()
        while owner is not None and owner.parentWidget() is not None:
            owner = owner.parentWidget()
        # Keep lifetime ownership, but not a nested auxiliary's lifetime.
        # OR-ing Qt.Window into Qt.Dialog does not change the window type.
        flags = ((self.windowFlags() & ~Qt.WindowType_Mask)
                 | Qt.Window | Qt.WindowMinMaxButtonsHint)
        self.setParent(owner, flags)
        QApplication.instance().aboutToQuit.connect(self.close)

    def showEvent(self, event):
        super().showEvent(event)
        # Qt creates the native transient relationship from QWidget parenting.
        # Remove only that WM relationship; signals, ownership and data stay.
        handle = self.windowHandle()
        if handle is not None:
            handle.setTransientParent(None)


def close_auxiliary_windows(owner):
    """Close owned modeless windows when the main window accepts closing."""
    for window in owner.findChildren(QWidget):
        if isinstance(window, AuxiliaryWindow):
            window.close()
