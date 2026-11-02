"""One reversible, event-driven preflight for MainWindow.close()."""
import time
from PySide6.QtCore import QObject, QTimer, Qt, QSettings, QEvent, Signal
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel,
                              QDialogButtonBox, QProgressBar, QScrollArea, QFrame,
                              QLayout, QSizePolicy)
from cmdrhelper.exit_tasks import task_gate
from cmdrhelper.i18n import tr
from cmdrhelper.exit_diagnostics import record as record_diagnostics


def values(window, section):
    if section in ('edsm', 'inara'):
        fields = ['commander_combo', 'commander_edit', 'api_key_edit', 'enabled_check']
        if section == 'edsm':
            fields.append('receive_check')
        result = []
        for field in fields:
            widget = getattr(window, section + '_' + field)
            result.append(widget.currentData() if field.endswith('combo') else
                          widget.isChecked() if field.endswith('check') else widget.text().strip())
        return tuple(result)
    if section == 'language':
        return window.ui_language_combo.currentData()
    return (window.ui_font_combo.currentFont().family(), window.ui_font_size_spin.value())


def remember(window, *sections):
    if not hasattr(window, '_exit_saved'):
        window._exit_saved = {}
    for section in sections or ('edsm', 'inara', 'language', 'font'):
        try:
            window._exit_saved[section] = values(window, section)
        except AttributeError:
            pass  # Settings are still being constructed.


def confirm_saved(window, *sections):
    settings = window.state.settings
    settings.sync()
    if isinstance(settings, QSettings) and settings.status() != QSettings.NoError:
        raise OSError('Settings could not be synchronized')
    remember(window, *sections)


class ExitStatusLabel(QLabel):
    changed = Signal()

    def setText(self, text):
        if text != self.text():
            super().setText(text)
            self.changed.emit()


class ExitDialog(QDialog):
    def __init__(self, controller, drafts=False):
        super().__init__(controller.window)
        self.controller, self.drafts = controller, drafts
        self.setWindowTitle(tr('exit.title'))
        self.setWindowModality(Qt.WindowModal)
        layout = QVBoxLayout(self)
        self.message = ExitStatusLabel(tr('exit.unsaved') if drafts else tr('exit.wait'))
        self.message.setTextFormat(Qt.PlainText)
        self.message.setWordWrap(True)
        if drafts:
            layout.addWidget(self.message)
        else:
            layout.setSizeConstraint(QLayout.SetNoConstraint)
            self.message.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.message.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            self.message_area = QScrollArea()
            self.message_area.setFrameShape(QFrame.NoFrame)
            self.message_area.setWidgetResizable(True)
            self.message_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.message_area.setWidget(self.message)
            layout.addWidget(self.message_area, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(not drafts)
        layout.addWidget(self.progress)
        choices = QDialogButtonBox.Cancel
        if drafts:
            choices |= QDialogButtonBox.Save | QDialogButtonBox.Discard
        self.buttons = QDialogButtonBox(choices)
        for role, key in ((QDialogButtonBox.Save, 'exit.save'),
                          (QDialogButtonBox.Discard, 'exit.discard'),
                          (QDialogButtonBox.Cancel, 'exit.cancel')):
            button = self.buttons.button(role)
            if button:
                button.setText(tr(key))
                button.setAutoDefault(False)
        self.buttons.rejected.connect(self.reject)
        if drafts:
            self.buttons.button(QDialogButtonBox.Save).clicked.connect(controller.save)
            self.buttons.button(QDialogButtonBox.Discard).clicked.connect(controller.discard)
        layout.addWidget(self.buttons)
        self.shortcut = QShortcut(self)
        self.shortcut.setContext(Qt.WindowShortcut)
        self.shortcut.setAutoRepeat(False)
        self.shortcut.activated.connect(self.repeat)
        manager = getattr(controller.window, 'shortcut_manager', None)
        if manager is not None:
            manager.changed.connect(self.update_binding)
        self.update_binding()
        if not drafts:
            self.message.changed.connect(self.fit_content)

    def fit_content(self):
        """Size only the waiting dialog; completion and timing stay with the controller."""
        if self.drafts or not self.isVisible():
            return
        screen = self.screen().availableGeometry()
        frame = self.frameGeometry()
        frame_width = max(0, frame.width() - self.width())
        frame_height = max(0, frame.height() - self.height())
        self._fitted_frame_size = (frame_width, frame_height)
        max_width = max(1, screen.width() - frame_width - 16)
        max_height = max(1, screen.height() - frame_height - 16)
        margins = self.layout().contentsMargins()
        horizontal = margins.left() + margins.right()
        vertical = margins.top() + margins.bottom() + 2 * self.layout().spacing()
        button_height = max(self.buttons.sizeHint().height(),
                            *(button.sizeHint().height() for button in self.buttons.buttons()))
        self.buttons.setMinimumHeight(button_height)
        controls = self.progress.sizeHint().height() + button_height
        self.setMinimumSize(min(450, max_width),
                            min(max_height, vertical + controls + self.message.fontMetrics().height()))
        natural = max((self.message.fontMetrics().horizontalAdvance(line)
                       for line in self.message.text().splitlines()), default=0)
        width = min(max_width, max(450, self.buttons.minimumSizeHint().width() + horizontal,
                                   min(720, natural + horizontal)))
        text_width = max(1, width - horizontal)
        self.message.setMinimumHeight(0)
        text_height = self.message.heightForWidth(text_width)
        height = min(max_height, text_height + vertical + controls)
        if height < text_height + vertical + controls:
            text_width -= self.message_area.verticalScrollBar().sizeHint().width()
            text_height = self.message.heightForWidth(max(1, text_width))
        self.message.setMinimumHeight(text_height)
        self.resize(width, height)
        self.layout().activate()
        # Centre on the owner, then keep the complete frame on its screen.
        target = self.controller.window.frameGeometry().center()
        frame = self.frameGeometry()
        frame.moveCenter(target)
        frame.moveLeft(max(screen.left() + 8, min(frame.left(), screen.right() - frame.width() - 7)))
        frame.moveTop(max(screen.top() + 8, min(frame.top(), screen.bottom() - frame.height() - 7)))
        self.move(frame.topLeft())

    def showEvent(self, event):
        super().showEvent(event)
        if not self.drafts:
            self.windowHandle().installEventFilter(self)
            self.fit_content()
            QTimer.singleShot(0, self.fit_content)  # Include window decorations once mapped.

    def eventFilter(self, watched, event):
        if not self.drafts and watched is self.windowHandle() and event.type() in (
                QEvent.Expose, QEvent.Resize, QEvent.Move):
            frame = self.frameGeometry()
            frame_size = (max(0, frame.width() - self.width()),
                          max(0, frame.height() - self.height()))
            if (frame_size != getattr(self, '_fitted_frame_size', None)
                    or not self.screen().availableGeometry().contains(frame)):
                QTimer.singleShot(0, self.fit_content)
        return super().eventFilter(watched, event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.StyleChange) and hasattr(self, 'message_area'):
            QTimer.singleShot(0, self.fit_content)

    def update_binding(self):
        manager = getattr(self.controller.window, 'shortcut_manager', None)
        self.shortcut.setKey(QKeySequence(manager.bindings.get('quit', '') if manager else ''))

    def repeat(self):
        if QApplication.activeModalWidget() is not self or QApplication.activePopupWidget():
            return
        if self.drafts:
            self.message.setText(tr('exit.choose'))
        else:
            self.controller.poll()

    def reject(self):
        self.controller.cancel()


class ExitController(QObject):
    WAIT_NOTICE_SECONDS = 10

    def __init__(self, window):
        super().__init__(window)
        self.window, self.state = window, window.state
        self.gate = task_gate()
        self.token = object()
        gate, token = self.gate, self.token
        def owner_destroyed():
            if gate.owner is token:
                gate.finish()
                gate.resume()
        self.window.destroyed.connect(owner_destroyed)
        self.phase = 'idle'
        self.approved = False
        self.dialog = None
        self.paused = []
        self.observers = []
        self.sealed = False
        self.cancel_requested = False
        self.quiet = False
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.poll)

    def dirty(self):
        return [key for key, saved in getattr(self.window, '_exit_saved', {}).items()
                if values(self.window, key) != saved]

    def request(self):
        if self.approved:
            return True
        if self.phase != 'idle':
            if self.dialog:
                self.dialog.raise_()
            return False
        # Do not close someone else's editor or modal workflow.
        if QApplication.activeModalWidget() is not None or QApplication.activePopupWidget() is not None:
            return False
        if self.dirty():
            self.phase = 'drafts'
            record_diagnostics(self, event='started', force=True)
            self.show_dialog(True)
            return False
        return self.begin()

    def show_dialog(self, drafts=False):
        self.hide_dialog()
        self.dialog = ExitDialog(self, drafts)
        self.dialog.show()

    def status(self, text):
        if self.dialog is None:
            self.show_dialog()
        self.dialog.message.setText(text)

    def hide_dialog(self):
        if self.dialog:
            self.dialog.hide()
            self.dialog.deleteLater()
            self.dialog = None

    def save(self):
        try:
            dirty = self.dirty()
            if 'edsm' in dirty or 'inara' in dirty:
                self.window._save_online_settings(notify=False)
            if 'language' in dirty:
                self.window._save_ui_language_settings()
            if 'font' in dirty:
                self.window._save_ui_font_settings()
            self.check_settings()
            if self.dirty():
                raise ValueError('Unapplied settings')
        except Exception:
            # Never expose API keys or exception payloads in this dialog.
            self.dialog.message.setText(tr('exit.save_failed'))
            return
        self.discard()

    def discard(self):
        self.hide_dialog()
        if self.begin():
            self.window.close()

    def check_settings(self):
        settings = self.state.settings
        settings.sync()
        if isinstance(settings, QSettings) and settings.status() != QSettings.NoError:
            raise OSError('Settings could not be synchronized')

    def pause_timer(self, timer):
        if isinstance(timer, QTimer) and timer.isActive() and timer not in self.paused:
            self.paused.append(timer)
            timer.stop()

    def begin(self):
        from cmdrhelper.observed_market_observer import ObservedMarketObserver
        from .screenshot_view import ScreenshotView
        self.phase = 'draining'
        self.started = time.monotonic()
        self.quiet = False
        self.cancel_requested = False
        self.sealed = False
        self.gate.begin(self.token)
        self.hotkey = getattr(self.window, '_quick_favorite_hotkey', None)
        if self.hotkey is not None:
            self.hotkey.suspended += 1
        sources = getattr(self.state, 'sources', None)
        if sources is not None:
            sources._exit_paused = True
            self.pause_timer(getattr(sources, 'timer', None))
        watchers = [getattr(self.state, 'watcher', None)]
        if sources is not None:
            watchers += [rt.watcher for rt in sources.runtimes.values()]
        observers = [getattr(self.state, 'observed_markets', None)]
        for watcher in watchers:
            if watcher is not None:
                self.pause_timer(getattr(watcher, 'timer', None))
                observers += list(getattr(watcher, 'live_observers', ()))
        self.observers = list(dict.fromkeys(o for o in observers if isinstance(o, ObservedMarketObserver)))
        for observer in self.observers:
            observer.exit_draining = True
        for view in self.window.findChildren(ScreenshotView):
            self.pause_timer(view.timer)
            view._save_settings()  # These fields already use automatic saving.
        mining = getattr(self.state, 'mining_inventory_controller', None)
        if mining is not None:
            mining.retry_pending_save()
        record_diagnostics(self, event='started', force=True)
        # With no admitted work there is no reason to show a confirmation.
        if not self.pending() and not self.writers():
            return self.finish()
        if self.pending():
            self.show_dialog()
        self.timer.start()
        return False

    def pending(self):
        count = self.gate.pending()
        mining = getattr(self.state, 'mining_inventory_controller', None)
        if mining is not None:
            count += bool(mining._running or mining._dirty or mining.timer.isActive()
                          or mining.cargo_retry.isActive() or getattr(mining, '_exit_write_error', False))
        count += sum(writer.pending_count() for writer in self.writers())
        count += sum(observer.pending is not None for observer in self.observers)
        return count

    def writers(self):
        from cmdrhelper.market_writer import active_writers
        return set(active_writers()) | {o.writer for o in self.observers if o.writer is not None}

    def poll(self):
        if self.phase != 'draining':
            return
        record_diagnostics(self)
        if self.cancel_requested:
            self.cancel()
            return
        modal = QApplication.activeModalWidget()
        if (modal is not None and modal is not self.dialog) or QApplication.activePopupWidget():
            return
        mining = getattr(self.state, 'mining_inventory_controller', None)
        if self.gate.failures:
            self.status(tr('exit.write_failed'))
            return
        if mining is not None and getattr(mining, '_exit_write_error', False):
            self.status(tr('exit.write_failed'))
            return
        for observer in self.observers:
            if not self.sealed:
                observer._poll_writes(closing=True)
                if observer.pending is not None:
                    observer.finish_pending_capture(closing=True)
        for writer in self.writers():
            writer.discard_exit_errors()
        count = self.pending()
        if count:
            self.quiet = False
            key = 'exit.wait_long' if time.monotonic() - self.started >= self.WAIT_NOTICE_SECONDS else 'exit.wait_count'
            self.status(tr(key, count=count))
            return
        # A separate event-loop turn lets already emitted Python-thread results
        # publish and request their final essential mining reconstruction.
        if not self.quiet:
            self.quiet = True
            return
        if not self.sealed:
            self.sealed = True
            for observer in self.observers:
                if observer.writer:
                    observer._closing = True
            for writer in self.writers():
                writer.request_close()
        if any(not writer.is_stopped() for writer in self.writers()):
            if time.monotonic() - self.started > .3:
                self.status(tr('exit.wait'))
            return
        if self.finish():
            self.window.close()

    def finish(self):
        try:
            self.state.settings.setValue('main_window/geometry', self.window.saveGeometry())
            self.check_settings()
        except OSError:
            if self.dialog is None:
                self.show_dialog()
                self.timer.start()
            self.dialog.message.setText(tr('exit.save_failed'))
            record_diagnostics(self, event='settings_failed', force=True)
            return False
        self.approved = True
        self.phase = 'finished'
        self.timer.stop()
        self.gate.finish()
        record_diagnostics(self, event='finished', force=True)
        self.hide_dialog()
        return True

    def cancel(self):
        if self.phase == 'finished':
            return
        if self.sealed and any(o.writer and not o.writer.is_stopped() for o in self.observers):
            self.cancel_requested = True
            self.status(tr('exit.resuming'))
            return
        self.timer.stop()
        if self.phase == 'draining':
            if self.sealed:
                for observer in self.observers:
                    if observer.writer:
                        observer.resume_after_close()
            for observer in self.observers:
                observer.exit_draining = False
            sources = getattr(self.state, 'sources', None)
            if sources is not None:
                sources._exit_paused = False
            self.gate.resume()
            for timer in self.paused:
                timer.start()
            self.paused.clear()
            if sources is not None:
                QTimer.singleShot(0, sources._next)
            if self.hotkey is not None:
                self.hotkey.suspended -= 1
        self.hide_dialog()
        self.phase = 'idle'
        self.sealed = False
        self.cancel_requested = False
        record_diagnostics(self, event='cancelled', force=True)
