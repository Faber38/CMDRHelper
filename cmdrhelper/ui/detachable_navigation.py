"""Move the existing navigator between its tab and a reusable window."""
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import QApplication, QFrame, QPushButton, QScrollArea, QVBoxLayout, QWidget

from cmdrhelper.i18n import tr


class _NavigationWindow(QWidget):
    def __init__(self, dock, parent):
        super().__init__(parent, Qt.Window)
        self.dock = dock
        self.setWindowTitle(tr("planet_nav.title"))
        self.resize(500, 700)
        layout = QVBoxLayout(self)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.scroll)

    def closeEvent(self, event):
        self.dock.attach()
        event.accept()


class DetachableNavigation(QObject):
    geometry_key = "planet_navigation/geometry"

    def __init__(self, view, home, main_window):
        super().__init__(main_window)
        self.view = view
        self.home = home
        self.main_window = main_window
        self.settings = view.settings
        self.window = None
        self.detached = False
        self.stopping = False
        self.button = QPushButton(tr("planet_nav.detach"), view)
        self.button.clicked.connect(self.toggle)
        view.layout().insertWidget(0, self.button, alignment=Qt.AlignRight)
        self.placeholder = QWidget(home)
        layout = QVBoxLayout(self.placeholder)
        self.open_button = QPushButton(tr("planet_nav.detach"))
        self.open_button.clicked.connect(self.detach)
        layout.addWidget(self.open_button, alignment=Qt.AlignTop | Qt.AlignRight)
        layout.addStretch()
        self.placeholder.hide()
        QApplication.instance().aboutToQuit.connect(self.shutdown)

    def toggle(self):
        if self.detached:
            self.attach()
        else:
            self.detach()

    def detach(self):
        if self.stopping:
            return
        if self.window is None:
            self.window = _NavigationWindow(self, self.main_window)
        if not self.detached:
            geometry = self.settings.value(self.geometry_key)
            if geometry is not None:
                try:
                    self.window.restoreGeometry(geometry)
                except (TypeError, ValueError):
                    pass
            self.home.takeWidget()
            self.home.setWidget(self.placeholder)
            self.window.scroll.setWidget(self.view)
            self.detached = True
            self.button.setText(tr("planet_nav.attach"))
        if self.window.isMinimized():
            self.window.showNormal()
        else:
            self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def attach(self, activate=True):
        if not self.detached:
            return
        self.settings.setValue(self.geometry_key, self.window.saveGeometry())
        self.settings.sync()
        self.window.scroll.takeWidget()
        self.home.takeWidget()
        self.placeholder.hide()
        self.placeholder.setParent(self.home)
        self.home.setWidget(self.view)
        self.detached = False
        self.button.setText(tr("planet_nav.detach"))
        self.window.hide()
        if activate and not self.stopping:
            self.main_window._show_planet_navigation()

    def shutdown(self):
        self.stopping = True
        self.attach(activate=False)
        self.view.hide()
