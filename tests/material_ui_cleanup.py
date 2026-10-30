"""Deterministic GUI-thread teardown for the material window test fixtures."""
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QThread, QTimer
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid


def cleanup_material_view(view):
    app = QApplication.instance()
    assert QThread.currentThread() == app.thread(), 'material cleanup must run on GUI thread'
    if not isValid(view):
        return
    # Include the explicitly supplied controller as well as parented controllers
    # and the trader panel (which uses the global pool).
    objects = [view.controller, *view.findChildren(QObject)]
    timers = list(view.findChildren(QTimer))
    timer = getattr(view.controller, 'timer', None)
    if timer is not None:
        timers.append(timer)
    pools = {obj.pool for obj in objects if hasattr(obj, 'pool')}
    for timer in timers:
        timer.stop()
    for pool in pools:
        assert pool.waitForDone(10000), 'material fixture worker did not finish within 10 seconds'
    # Deliver queued results while their receivers are still alive. Result handlers
    # may restart refresh/highlight timers, so stop them again before deletion.
    app.processEvents()
    for timer in timers:
        if isValid(timer):
            timer.stop()
    for pool in pools:
        assert pool.waitForDone(10000), 'material fixture follow-up worker did not finish'
    view.close()
    view.deleteLater()
    # Same explicit DeferredDelete delivery used by adjacent Qt lifecycle tests.
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not isValid(view), 'material fixture window survived DeferredDelete'
