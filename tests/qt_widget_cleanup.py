"""GUI-thread cleanup for test widgets without asynchronous workers.

Worker-owning fixtures must finish their workers before calling this helper.
Holding the wrappers until DeferredDelete completes also keeps cyclic Python
objects from being collected during a later application's stylesheet update.
"""
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QThread, QTimer
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid


def destroy_widget(widget, *, close=True):
    app = QApplication.instance()
    assert app is not None and QThread.currentThread() == app.thread()
    if not isValid(widget):
        return
    children = widget.findChildren(QObject)
    for timer in widget.findChildren(QTimer):
        timer.stop()
    if close:
        assert widget.close(), 'test widget refused close; finish its workers first'
    else:
        # Partially constructed MainWindow fixtures have no full shutdown
        # infrastructure. Their caller must cancel any tested exit controller.
        widget.hide()
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not isValid(widget), 'test widget survived DeferredDelete'
    assert all(not isValid(child) for child in children), 'test child survived its parent'
