"""Compact local Powerplay overview, following the shared card/theme styles."""
from datetime import timedelta
from PySide6.QtCore import QEvent, QLocale, QRect, QSize, QTimer, Qt, QTime
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHeaderView, QLabel, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QMenu, QMessageBox, QProgressBar, QCheckBox, QTimeEdit, QToolButton, QLayout,
)

from cmdrhelper.i18n import get_language, tr
from cmdrhelper.ui.auxiliary_window import AuxiliaryWindow
from cmdrhelper.ui.table_widths import ResponsiveColumnWidths
from cmdrhelper.ui.powerplay_portraits import PowerPortrait
from cmdrhelper.ui.powerplay_system import SystemPresentation
from cmdrhelper.powerplay_rank import rank_progress
from cmdrhelper.powerplay_chronicle import local_today, today_groups, is_rare_sale
from cmdrhelper.powerplay_store import DayCache
from cmdrhelper.powerplay import (
    PowerplayState, PowersCache, ACTION_TOKENS, powerplay_actions, context, number,
    powers_cache_path, timestamp, onboard_articles,
)


class _ChronicleControlsLayout(QLayout):
    """Wrap existing controls at their natural widths, without touching data."""

    def __init__(self):
        super().__init__()
        self._items = []
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(6)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < self.count() else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < self.count() else None

    def expandingDirections(self):
        return Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0))

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def sizeHint(self):
        return self.minimumSize()

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, apply=True)

    def _arrange(self, rect, apply=False):
        rows, row, used = [], [], 0
        gap = self.spacing()
        for index, item in enumerate(self._items):
            size = item.sizeHint().expandedTo(item.minimumSize())
            required = size.width()
            if index == self.count() - 2:
                last = self._items[-1]
                pair = required + gap + last.sizeHint().expandedTo(last.minimumSize()).width()
                # Keep management and docking together whenever a complete
                # row can hold both; very narrow windows may split them.
                if pair <= rect.width():
                    required = pair
            if row and used + gap + required > rect.width():
                rows.append(row)
                row, used = [], 0
            used += (gap if row else 0) + size.width()
            row.append((index, item, size))
        if row:
            rows.append(row)
        y = rect.y()
        for row in rows:
            height = max(size.height() for _, _, size in row)
            x = rect.x()
            for position, (index, item, size) in enumerate(row):
                # The final two controls form the right-aligned group. Free
                # space belongs before them, including on a wrapped row.
                if index >= self.count() - 2 and (position == 0 or row[position - 1][0] < self.count() - 2):
                    remaining = sum(s.width() for _, _, s in row[position:])
                    remaining += gap * (len(row) - position - 1)
                    x = max(x, rect.x() + rect.width() - remaining)
                if apply:
                    item.setGeometry(QRect(x, y + (height - size.height()) // 2,
                                           size.width(), size.height()))
                x += size.width() + gap
            y += height + gap
        return y - rect.y() - (gap if rows else 0)


class _SystemFilterMenu(QMenu):
    """Keep checkbox choices open for multiple selections, including keyboard use."""

    def mouseReleaseEvent(self, event):
        action = self.actionAt(event.position().toPoint())
        if event.button() == Qt.LeftButton and action and action.isEnabled() and action.isCheckable():
            action.trigger()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        action = self.activeAction()
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter) and action and action.isCheckable():
            action.trigger()
            event.accept()
            return
        super().keyPressEvent(event)


class RecommendationLabel(QLabel):
    """Let the outer scroll area grow instead of clipping wrapped advice."""
    def setText(self, text):
        super().setText(text)
        self._fit_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_text()

    def _fit_text(self):
        # QLabel includes its minimum in heightForWidth; clear the previous
        # width's constraint so widening/shorter text can shrink again.
        self.setMinimumHeight(0)
        self.setMinimumHeight(max(0, self.heightForWidth(self.width())))


class _SectionHeading(QWidget):
    """Collapse only presentation; keep the existing data widgets alive."""

    def __init__(self, view, label, body, key):
        super().__init__()
        self.view, self.body, self.key = view, body, key
        self.label = label
        self.button = QToolButton()
        self.button.setAutoRaise(True)
        self.button.setCheckable(True)
        self.button.setAccessibleName(label.text())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.button, alignment=Qt.AlignTop)
        layout.addWidget(label, 1)
        label.setTextInteractionFlags(Qt.NoTextInteraction)
        for widget in (self, label):
            widget.setCursor(Qt.PointingHandCursor)
            widget.installEventFilter(self)
        settings = getattr(view.state, 'settings', None)
        saved = settings.value(key, False) if settings is not None else False
        expanded = str(saved).lower() in ('true', '1')
        self.button.setChecked(expanded)
        self._display(expanded)
        # Restore before connecting: construction must never overwrite settings.
        self.button.toggled.connect(self._toggle)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.button.click()
            return True
        return super().eventFilter(watched, event)

    def _display(self, expanded):
        self.button.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.body.setVisible(expanded)

    def _toggle(self, expanded):
        self._display(expanded)
        settings = getattr(self.view.state, 'settings', None)
        if settings is not None:
            settings.setValue(self.key, expanded)
            settings.sync()
        if expanded:
            self.view.render()


class ChronicleTable(QTableWidget):
    """Keep all sections draggable, fitting preferences without overwriting them."""
    WIDTHS_KEY = 'pp2/chronicle_column_widths'

    def configure_widths(self, settings):
        unit = self.fontMetrics().horizontalAdvance("0")
        self.column_widths = ResponsiveColumnWidths(
            self, settings, self.WIDTHS_KEY,
            minimums=[max(40, unit*n) for n in (6, 9, 12, 8, 7)],
            defaults=self.default_widths,
        )

    def default_widths(self, width):
        unit = self.fontMetrics().horizontalAdvance("0")
        if width < unit * 90:
            return [int(width * share) for share in (.14, .18, .35, .17, .16)]
        values = [unit*8, unit*16, 0, min(int(width*.18),unit*24), unit*18]
        values[2] = max(unit*12, width-sum(values))
        return values

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_columns()

    def fit_columns(self):
        if hasattr(self, 'column_widths'):
            self.column_widths.fit()
            # Width fitting blocks header signals; refresh scrollbar ranges too.
            self.updateGeometries()


class _ChronicleWindow(AuxiliaryWindow, QWidget):
    """Host the existing PP2 section; closing returns it to its original view."""

    def __init__(self, view):
        super().__init__(view, Qt.Window)
        self.view = view
        self.setWindowTitle(tr('pp2.chronicle.title'))
        self.resize(1000, 600)
        QVBoxLayout(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view._arrange_chronicle()

    def closeEvent(self, event):
        self.view.attach_chronicle()
        event.accept()


class PowerplayView(QScrollArea):
    chronicle_geometry_key = 'pp2/chronicle_geometry'

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.cache = PowersCache()
        self._day_cache = DayCache()
        self.destroyed.connect(self._day_cache.close)
        self._chronicle_render_key = None
        self.section_headings = {}
        self.selected_day = None
        self._selected_systems = None  # None means all, including future systems.
        self._system_context = None
        self._system_names = {}
        self._system_menu_key = None
        self.chronicle_window = None
        self.chronicle_detached = False
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)
        layout.addWidget(self.label(tr("pp2.title"), "pageTitle"))
        self.personal = {}
        card, grid = self.card("pp2.personal")
        card.layout().setContentsMargins(10, 6, 10, 6)
        card.layout().setSpacing(4)
        grid.setVerticalSpacing(2)
        self.personal_grid = grid
        self.portrait = PowerPortrait()
        self.personal_info = QWidget()
        info = QVBoxLayout(self.personal_info)
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(4)
        for key in ("power", "rank", "merits", "joined"):
            self.personal[key] = self.label("", "cardValue" if key in ("power", "merits") else "")
        info.addWidget(self.personal['power'])
        values = QHBoxLayout()
        for key in ('rank', 'merits'):
            values.addWidget(self.label(tr('pp2.'+key), 'muted'))
            values.addWidget(self.personal[key])
        values.addStretch()
        info.addLayout(values)
        self.rank_summary = self.label("", "muted")
        self.rank_bar = QProgressBar(objectName="pp2RankProgress")
        self.rank_bar.setRange(0, 1000)
        self.rank_bar.setMaximumHeight(self.fontMetrics().height()+6)
        self.rank_bar.setMaximumWidth(420)
        info.addWidget(self.rank_summary)
        info.addWidget(self.rank_bar)
        joined = QHBoxLayout()
        joined.addWidget(self.label(tr('pp2.joined'), 'muted'))
        joined.addWidget(self.personal['joined'])
        joined.addStretch()
        info.addLayout(joined)
        grid.addWidget(self.portrait, 0, 0, alignment=Qt.AlignTop)
        grid.addWidget(self.personal_info, 0, 1)
        grid.setColumnStretch(1, 1)
        self._portrait_stacked = None
        self.personal_card = card
        self.columns = QGridLayout()
        self.columns.setContentsMargins(0, 0, 0, 0)
        self.columns.setSpacing(12)
        layout.addLayout(self.columns)
        self.left_column = QWidget()
        self.right_column = QWidget()
        left = QVBoxLayout(self.left_column)
        right = QVBoxLayout(self.right_column)
        for column in (left, right):
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(12)
            column.setAlignment(Qt.AlignTop)
        self._two_columns = None
        left.addWidget(self.personal_card)
        card, grid = self.card("pp2.system", section="system")
        self.system_card = card
        self.system_presentation = SystemPresentation()
        self.system_labels = self.system_presentation.labels
        self.metrics = self.system_presentation.metrics
        self.observed = self.label("", "muted")
        grid.addWidget(self.system_presentation, 0, 0)
        grid.addWidget(self.observed, 1, 0)
        left.addWidget(card)
        self.action_section = QWidget()
        action_section_layout = QVBoxLayout(self.action_section)
        action_section_layout.setContentsMargins(0, 0, 0, 0)
        action_section_layout.setSpacing(12)
        self.action_heading = self.label("", "sectionTitle", recommendation=True)
        card = QFrame(objectName="card")
        actions_layout = QVBoxLayout(card)
        self.mode = self.label("", "sectionTitle", recommendation=True)
        self.actions = self.label("", recommendation=True)
        self.notice = self.label("", "muted", recommendation=True)
        for label in (self.mode, self.actions, self.notice):
            actions_layout.addWidget(label)
        action_section_layout.addWidget(self.section_heading("actions", self.action_heading, card))
        action_section_layout.addWidget(card)
        right.addWidget(self.action_section)
        self.cargo_card, grid = self.card("pp2.onboard", section="cargo")
        self.cargo = self.label("")
        grid.addWidget(self.cargo, 0, 0)
        right.addWidget(self.cargo_card)
        self.recent_section = QWidget()
        recent_layout = QVBoxLayout(self.recent_section)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(6)
        self.detach_chronicle_button = QPushButton(tr('pp2.chronicle.detach'))
        self.detach_chronicle_button.clicked.connect(self.toggle_chronicle)
        self.recent = ChronicleTable(0, 5)
        # Reserve the scrollbar gutter so live rows/day changes cannot shrink
        # the viewport and refit a user's columns when a scrollbar appears.
        self.recent.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.recent.setHorizontalHeaderLabels([tr("pp2.chronicle." + key) for key in (
            "time", "action", "details", "merits", "certainty")])
        for column in range(self.recent.columnCount()):
            item = self.recent.horizontalHeaderItem(column)
            item.setToolTip(item.text())
        self.recent.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recent.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recent.setWordWrap(False)
        self.recent.setTextElideMode(Qt.ElideRight)
        self.recent.verticalHeader().hide()
        header = self.recent.horizontalHeader()
        self.recent.configure_widths(getattr(state, 'settings', None))
        header.sectionResized.connect(lambda *_: self.recent.resizeRowsToContents())
        self.chronicle_header = _ChronicleControlsLayout()
        self.chronicle_title = self.label(tr("pp2.chronicle.title"), "sectionTitle")
        self.navigation = QWidget()
        navigation = QHBoxLayout()
        navigation.setContentsMargins(0, 0, 0, 0)
        self.navigation.setLayout(navigation)
        self.previous_day = QPushButton("‹")
        self.next_day = QPushButton("›")
        self.day_label = self.label("")
        self.day_label.setWordWrap(False)
        self.today_button = QPushButton(tr("pp2.history.today"))
        self.manage_history = QPushButton(tr("pp2.history.manage"))
        self.system_filter = QPushButton(tr('pp2.history.system_filter'))
        self.system_menu = _SystemFilterMenu(self.system_filter)
        self.system_filter.setMenu(self.system_menu)
        self.system_menu.aboutToShow.connect(self._sync_system_menu)
        self.time_filter = QWidget()
        time_layout = QHBoxLayout(self.time_filter)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_filter_enabled = QCheckBox(tr('pp2.history.from_time'))
        self.from_time = QTimeEdit(QTime(0, 0))
        self.from_time.setDisplayFormat('HH:mm')
        self.from_time.setAccessibleName(tr('pp2.history.from_time'))
        self.from_time.setEnabled(False)
        self.time_filter_enabled.toggled.connect(self.from_time.setEnabled)
        self.time_filter_enabled.toggled.connect(lambda *_: self.render())
        self.from_time.timeChanged.connect(lambda *_: self.render())
        time_layout.addWidget(self.time_filter_enabled)
        time_layout.addWidget(self.from_time)
        self.filtered_merits = QLabel()
        self.filtered_merits.setWordWrap(False)
        self.previous_day.clicked.connect(lambda: self._move_day(-1))
        self.next_day.clicked.connect(lambda: self._move_day(1))
        self.today_button.clicked.connect(self._today)
        menu = QMenu(self.manage_history)
        for days, key in ((7, "delete7"), (30, "delete30"), (None, "delete_all")):
            action = menu.addAction(tr("pp2.history." + key))
            action.triggered.connect(lambda checked=False, days=days: self._delete_history(days))
        self.manage_history.setMenu(menu)
        menu.addSeparator()
        self.reset_columns_action = menu.addAction(tr("pp2.history.reset_columns"))
        self.reset_columns_action.triggered.connect(self.recent.column_widths.reset)
        for widget in (self.previous_day, self.day_label, self.next_day):
            navigation.addWidget(widget)
        recent_layout.addWidget(self.chronicle_title)
        for widget in (self.navigation, self.today_button, self.time_filter, self.system_filter,
                       self.filtered_merits, self.manage_history, self.detach_chronicle_button):
            self.chronicle_header.addWidget(widget)
        recent_layout.addLayout(self.chronicle_header)
        self.chronicle_help = self.label(tr("pp2.history.legend"), "muted")
        self.chronicle_help.setToolTip(tr("pp2.history.help"))
        recent_layout.addWidget(self.chronicle_help)
        recent_layout.addWidget(self.recent, 1)
        layout.addWidget(self.recent_section, 1)
        self.chronicle_home = layout
        self.open_chronicle_button = QPushButton(tr('pp2.chronicle.detach'))
        self.open_chronicle_button.clicked.connect(self.detach_chronicle)
        layout.addWidget(self.open_chronicle_button, alignment=Qt.AlignRight)
        self.open_chronicle_button.hide()
        self._arrange_columns()
        state.changed.connect(self._changed)
        for name in ('commanderIdentityChanged', 'viewedCommanderChanged'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self._reset_system_filter)
        cargo_signal = getattr(state, "cargoSnapshotChanged", None)
        if cargo_signal is not None:
            cargo_signal.connect(self._changed)
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self._changed)
        self.render()

    def toggle_chronicle(self):
        if self.chronicle_detached:
            self.attach_chronicle()
        else:
            self.detach_chronicle()

    def detach_chronicle(self):
        if self.chronicle_window is None:
            self.chronicle_window = _ChronicleWindow(self)
        window = self.chronicle_window
        if not self.chronicle_detached:
            settings = getattr(self.state, 'settings', None)
            geometry = settings.value(self.chronicle_geometry_key) if settings is not None else None
            if geometry is not None:
                try:
                    window.restoreGeometry(geometry)
                except (TypeError, ValueError):
                    pass
            self.chronicle_home.removeWidget(self.recent_section)
            window.layout().addWidget(self.recent_section)
            self.chronicle_detached = True
            self.detach_chronicle_button.setText(tr('pp2.chronicle.attach'))
            self.open_chronicle_button.show()
            self.recent_section.show()
            self.timer.start()
            self.render()
        if window.isMinimized():
            window.showNormal()
        else:
            window.show()
        self._arrange_chronicle()
        window.raise_()
        window.activateWindow()

    def attach_chronicle(self):
        if not self.chronicle_detached:
            return
        settings = getattr(self.state, 'settings', None)
        if settings is not None:
            settings.setValue(self.chronicle_geometry_key, self.chronicle_window.saveGeometry())
            settings.sync()
        self.chronicle_window.layout().removeWidget(self.recent_section)
        self.chronicle_home.insertWidget(
            self.chronicle_home.indexOf(self.open_chronicle_button), self.recent_section, 1)
        self.chronicle_detached = False
        self.detach_chronicle_button.setText(tr('pp2.chronicle.detach'))
        self.open_chronicle_button.hide()
        self.recent_section.show()
        self.chronicle_window.hide()
        self._arrange_chronicle()
        if not self.isVisible():
            self.timer.stop()

    @staticmethod
    def label(text, name="", *, recommendation=False):
        label = (RecommendationLabel if recommendation else QLabel)(text, objectName=name)
        label.setWordWrap(True)
        label.setTextFormat(Qt.PlainText)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def section_heading(self, section, label, body):
        heading = _SectionHeading(self, label, body, 'pp2/sections/' + section + '_expanded')
        self.section_headings[section] = heading
        return heading

    def card(self, key, *, section=None):
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        label = self.label(tr(key), "sectionTitle")
        if section is None:
            layout.addWidget(label)
            grid = QGridLayout()
            layout.addLayout(grid)
        else:
            body = QWidget()
            grid = QGridLayout(body)
            grid.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.section_heading(section, label, body))
            layout.addWidget(body)
        return card, grid

    def showEvent(self, event):
        super().showEvent(event)
        self.render()
        self.timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "columns"):
            self._arrange_columns()

    def _arrange_columns(self):
        self._arrange_chronicle()
        # A font-relative breakpoint respects font scaling without fixing any
        # card width. Independent column layouts keep short cargo cards compact.
        wide = self.viewport().width() >= self.fontMetrics().horizontalAdvance("0") * 110
        # The portrait now shares the left column with its details. Base its
        # wrapping on that column's available width, not the whole viewport.
        available = self.viewport().width() - 20
        personal_width = (available - self.columns.spacing()) * .4 if wide else available
        stacked = personal_width < self.fontMetrics().horizontalAdvance("0") * 65
        if stacked != self._portrait_stacked:
            self._portrait_stacked = stacked
            self.personal_grid.removeWidget(self.personal_info)
            self.personal_grid.addWidget(self.personal_info, 1 if stacked else 0,
                                         0 if stacked else 1, 1, 2 if stacked else 1)
        conflict_wide = wide and len(self.system_presentation.conflict_rows) >= 3
        self.system_presentation.arrange_conflicts(conflict_wide)
        # Give this existing card the free width BELOW advice and cargo. The
        # layout reserves their full height, including long translated content.
        spanning = self.columns.indexOf(self.system_card) >= 0
        if spanning != conflict_wide:
            if conflict_wide:
                self.left_column.layout().removeWidget(self.system_card)
                self.columns.addWidget(self.system_card, 1, 0, 1, 2)
            else:
                self.columns.removeWidget(self.system_card)
                self.left_column.layout().addWidget(self.system_card)
            self.system_card.show()
        if wide == self._two_columns:
            return
        self._two_columns = wide
        for widget in (self.left_column, self.right_column):
            self.columns.removeWidget(widget)
        self.columns.addWidget(self.left_column, 0, 0)
        self.columns.addWidget(self.right_column, 0 if wide else 1, 1 if wide else 0)
        self.columns.setColumnStretch(0, 2 if wide else 1)
        self.columns.setColumnStretch(1, 3 if wide else 0)
        self.columns.setRowStretch(0, 0)
        self.columns.setRowStretch(1, 0)

    def _arrange_chronicle(self):
        self.recent.fit_columns()

    @staticmethod
    def _activity_time(value, locale, today):
        local = value.astimezone()
        clock = local.strftime("%H:%M")
        return clock if local.date() == today else locale.toString(local.date(), QLocale.ShortFormat) + " " + clock

    def hideEvent(self, event):
        if not self.chronicle_detached:
            self.timer.stop()
        super().hideEvent(event)

    def _changed(self, *_):
        if self.isVisible() or self.chronicle_detached:
            self.render()

    @staticmethod
    def _group_system(group):
        # Use only the group's existing source context; never nearby events,
        # station names, the current system or merit-correlation certainty.
        return group.system.strip() if isinstance(group.system, str) else ''

    def _reset_system_filter(self, *_):
        self._selected_systems = None
        self._system_context = None
        self._chronicle_render_key = None
        self._changed()

    def _select_system(self, key, checked):
        selected = set(self._selected_systems or ())
        if checked:
            selected.add(key)
        else:
            selected.discard(key)
        self._selected_systems = frozenset(selected)
        self.render()

    def _all_systems(self, *_):
        self._selected_systems = None
        self.render()

    def _sync_system_menu(self):
        # Opening the menu uses only labels from the already loaded day.
        signature = (tuple(self._system_names.items()), get_language())
        if signature != self._system_menu_key:
            self.system_menu.clear()
            action = self.system_menu.addAction(tr('pp2.history.all_systems'))
            action.setCheckable(True)
            action.triggered.connect(self._all_systems)
            self.system_menu.addSeparator()
            for key, name in self._system_names.items():
                action = self.system_menu.addAction((name or tr('pp2.history.unknown_system')).replace('&', '&&'))
                action.setData(key)
                action.setCheckable(True)
                action.triggered.connect(lambda checked, key=key: self._select_system(key, checked))
            self._system_menu_key = signature
        actions = self.system_menu.actions()
        actions[0].setChecked(self._selected_systems is None)
        for action in actions[2:]:
            action.setChecked(self._selected_systems is not None and action.data() in self._selected_systems)
        label = tr('pp2.history.system_filter')
        if self._selected_systems is not None:
            label += ' (' + str(len(self._selected_systems)) + ')'
        self.system_filter.setText(label)
        self.system_filter.setAccessibleName(label)

    def _move_day(self, delta):
        today = local_today()
        target = min((self.selected_day or today) + timedelta(days=delta), today)
        self.selected_day = None if target == today else target
        self.render()

    def _today(self):
        self._selected_systems = None
        self.selected_day = None
        self.render()

    def _delete_history(self, days):
        db = getattr(self.state, "database", None)
        cid = getattr(self.state, "commander_id", None)
        if db is None or cid is None:
            return
        try:
            preview = db.powerplay_delete_preview(cid, days)
            if not preview['has_history']:
                QMessageBox.information(self, tr("pp2.history.manage"), tr("pp2.history.empty"))
                return
            message = tr("pp2.history.confirm", commander=getattr(self.state, "commander", str(cid)),
                         first=preview['first'], last=preview['last'], events=preview['events'], days=preview['days'])
            if QMessageBox.question(self, tr("pp2.history.manage"), message,
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                return
            db.delete_powerplay_history(cid, preview)
            self.render()
        except Exception as exc:
            QMessageBox.warning(self, tr("pp2.history.manage"), tr("pp2.history.error", error=str(exc)))

    def render(self):
        data = getattr(self.state, "powerplay", None) or PowerplayState()
        locale = QLocale(get_language())
        unknown = tr("pp2.unknown")

        def fmt(value):
            if number(value) is None:
                return unknown
            return locale.toString(value) if type(value) is int else locale.toString(value, 'g', 7)

        def date(value):
            return locale.toString(value.astimezone().date(), QLocale.ShortFormat) + " " + value.astimezone().strftime("%H:%M:%S")

        self.personal["power"].setText(data.power or tr("pp2.no_power" if data.membership_known else "pp2.unknown"))
        self.portrait.set_power(data.power, membership_known=data.membership_known)
        self.personal["rank"].setText(fmt(data.rank))
        self.personal["merits"].setText(fmt(data.merits))
        joined = date(data.joined) if data.joined else unknown
        if data.joined and data.joined_estimated:
            joined = tr("pp2.estimated", value=joined)
        self.personal["joined"].setText(joined)
        system = data.system
        # Never recommend actions for a stale system if another local source
        # has already moved the main application to a different system.
        current_snapshot = getattr(self.state, "system", "") == system.get("StarSystem", "")
        if not current_snapshot:
            system = {}
            relationship, mode = "unknown", None
        else:
            relationship, mode = context(data)
        self.system_presentation.render(system, getattr(self.state, "system", ""), relationship, fmt,
                                        own_power=data.power)
        at = timestamp(system.get("timestamp"))
        self.observed.setText(tr("pp2.observed", time=date(at)) if at else tr("pp2.no_data"))
        self.action_heading.setText(tr("pp2.actions_for", power=data.power) if data.power else tr("pp2.actions"))
        self.section_headings['actions'].button.setAccessibleName(self.action_heading.text())
        powers = self.cache.load(powers_cache_path(getattr(self.state, "journal_folder", None)))
        self._render_rank(data, powers, locale, fmt)
        self.notice.setText(tr("pp2.cache_unavailable") if powers is None else tr("pp2.cache_source"))
        self.mode.setText(tr("pp2.mode." + mode) if mode else tr("pp2.mode.unknown"))
        general = mode is None and bool(data.power) and current_snapshot
        self.notice.setVisible(not general)
        if general:
            self.mode.setText(tr("pp2.general.label"))
        self.actions.setToolTip("")
        if not data.power:
            message = tr("pp2.need_power")
        elif general:
            message = tr("pp2.general.hint")
        elif powers is None:
            message = tr("pp2.no_data")
        elif data.power not in powers:
            message = tr("pp2.power_missing", power=data.power)
        elif mode is None:
            message = tr("pp2.context_unknown")
        else:
            rows = []
            activities = powerplay_actions(powers[data.power], mode)
            for activity in activities:
                if activity.token in ACTION_TOKENS:
                    row = "✓ " + tr("pp2.action." + activity.token)
                else:
                    raw_token = "$PP2_Action_" + activity.token + ";" if activity.token else activity.raw
                    row = tr("pp2.action_unknown", token=raw_token)
                if activity.annotations:
                    row += " " + " ".join(activity.annotations)
                if activity.ethos is True:
                    row += " · " + tr("pp2.ethos")
                rows.append(row)
            tips = []
            if any(a.ethos is True for a in activities):
                tips.append(tr("pp2.ethos_tooltip"))
            if any(a.ethos is None or a.annotations for a in activities):
                tips.append(tr("pp2.ethos_unknown_tooltip"))
            self.actions.setToolTip("\n\n".join(tips))
            message = "\n".join(rows) or tr("pp2.no_data")
        self.actions.setText(message)
        inventory = getattr(self.state, "ship_inventory", None)
        total = getattr(self.state, "ship_cargo_total", None)
        if isinstance(total, dict) and total.get("count") == 0:
            inventory = {"inventory": []}
        articles = onboard_articles(data, inventory, powers)
        cargo_rows = []
        for article in articles:
            use = tr("pp2.mode." + article["category"]) if article["category"] else unknown
            cargo_rows.append(tr("pp2.article", name=article["name"], count=fmt(article["count"]),
                                 power=article["power"] or unknown, use=use))
            if article["category"] == "undermining":
                cargo_rows.append(tr("pp2.undermining_help"))
        self.cargo.setText("\n\n".join(cargo_rows) or tr(
            "pp2.cargo_unknown" if inventory is None else "pp2.cargo_empty"))
        self._render_chronicle(data, locale, fmt, unknown)
        self._arrange_columns()

    def _render_rank(self, data, powers, locale, fmt):
        progress = rank_progress(data.power, data.rank, data.merits, powers)
        self.personal['rank'].setToolTip(tr('pp2.rank.journal', rank=fmt(data.rank)))
        self.rank_bar.hide()
        self.rank_bar.reset()
        self.rank_bar.setFormat('')
        self.rank_bar.setToolTip('')
        status = progress.status if progress is not None else 'unavailable'
        if self.rank_bar.property('rankStatus') != status:
            self.rank_bar.setProperty('rankStatus', status)
            self.rank_bar.style().unpolish(self.rank_bar)
            self.rank_bar.style().polish(self.rank_bar)
            self.rank_bar.update()
        if progress is None:
            self.rank_summary.setText(tr('pp2.rank.unavailable'))
            self.rank_summary.setToolTip(tr('pp2.rank.unavailable'))
            return
        calculated = '100+' if progress.calculated > 100 else fmt(progress.calculated)
        next_rank = '100+' if progress.calculated >= 100 else fmt(progress.calculated+1)
        next_key = 'next' if progress.status == 'confirmed' else 'next_calculated'
        next_text = tr('pp2.rank.'+next_key, rank=next_rank, threshold=fmt(progress.upper), remaining=fmt(progress.needed))
        if progress.calculated > 100:
            next_text = tr('pp2.rank.next_band', threshold=fmt(progress.upper), remaining=fmt(progress.needed))
        status_text = tr('pp2.rank.'+progress.status, rank=calculated)
        self.rank_summary.setText(status_text+'\n'+next_text)
        if progress.status in ('confirmed', 'pending'):
            percent = 100*progress.earned/progress.span
            self.rank_bar.setValue(progress.earned*1000//progress.span)
            self.rank_bar.setFormat(tr('pp2.rank.bar', current=fmt(progress.lower),
                percent=locale.toString(percent, 'f', 1), next=fmt(progress.upper)))
            self.rank_bar.show()
        diagnostic = tr('pp2.rank.diagnostic', confirmed=fmt(data.rank), calculated=calculated,
                        earned=fmt(progress.earned), span=fmt(progress.span))
        self.rank_summary.setToolTip(status_text+'\n'+diagnostic)
        self.rank_bar.setToolTip(status_text+'\n'+diagnostic)

    def _render_chronicle(self, data, locale, fmt, unknown):
        today = local_today()
        selected = self.selected_day or today
        self.day_label.setText(locale.toString(selected, QLocale.ShortFormat))
        self.next_day.setEnabled(selected < today)
        db = getattr(self.state, "database", None)
        cid = getattr(self.state, "commander_id", None)
        system_context = (db, cid, getattr(self.state, 'commander_fid', None), selected)
        if system_context != self._system_context:
            self._selected_systems = None
            self._system_context = system_context
        for action in self.manage_history.menu().actions()[:3]:
            action.setEnabled(db is not None and cid is not None)
        if db is not None and cid is not None:
            chronicle, revision = self._day_cache.load(
                db, cid, selected, getattr(self.state, 'commander_fid', None))
        else:
            self._day_cache.close()
            chronicle, revision = data.chronicle, None
        render_key = (revision, selected, today, get_language(), locale.name(),
                      self.recent.font().toString(), self.time_filter_enabled.isChecked(),
                      self.from_time.time().msecsSinceStartOfDay() if self.time_filter_enabled.isChecked() else None,
                      self._selected_systems)
        if revision is not None and render_key == self._chronicle_render_key:
            return
        self._chronicle_render_key = None  # A failed rebuild must be retried.
        groups = today_groups(chronicle, selected)
        names = sorted({self._group_system(group) for group in groups}, key=lambda name: (name.casefold(), name))
        self._system_names = {}
        for name in names:
            self._system_names.setdefault(name.casefold(), name)
        self._sync_system_menu()
        if self._selected_systems is not None:
            groups = [group for group in groups if self._group_system(group).casefold() in self._selected_systems]
        if self.time_filter_enabled.isChecked():
            # Match the existing day filter and displayed action timestamp.
            # Convert each instant locally (including its historical DST offset).
            # Keep groups/credits intact; this is only a presentation filter.
            cutoff = self.from_time.time().toPython()
            groups = [group for group in groups
                      if timestamp(group.action['timestamp']).astimezone().time() >= cutoff]
        self.recent.setRowCount(len(groups))
        # These are the same filtered groups rendered below. Credits also cover
        # unassigned events; never add the action or cumulative TotalMerits.
        filtered_merits = sum(credit['MeritsGained'] for group in groups for credit in group.credits)
        self.filtered_merits.setText(tr('pp2.history.filtered_merits', amount='+' + fmt(filtered_merits)))
        for row, group in enumerate(groups):
            event = group.action
            kind = event.get("event")
            at = timestamp(event.get("timestamp"))
            when = self._activity_time(at, locale, today) if at else unknown
            if group.certainty == "unknown":
                action = tr("pp2.unknown")
                details = tr("pp2.chronicle.unassigned")
            elif kind in ("PowerplayCollect", "PowerplayDeliver", "SearchAndRescue", "MarketSell"):
                action = tr("pp2.chronicle.commodity_sale" if kind == "MarketSell" and not is_rare_sale(event)
                            else "pp2.chronicle." + kind)
                field = "Name" if kind == "SearchAndRescue" else "Type"
                name = event.get(field + "_Localised") or event.get(field) or unknown
                if kind == "MarketSell" and not event.get("Type_Localised"):
                    from cmdrhelper.commodity_master import lookup_by_symbol
                    from cmdrhelper.commodity_localization import commodity_name
                    commodity = lookup_by_symbol(event.get("Type"))
                    if commodity is not None:
                        name = commodity_name(commodity)
                details = tr("pp2.chronicle.tonnes" if kind == "MarketSell" else "pp2.chronicle.item",
                             count=fmt(event.get("Count")), name=name)
            else:
                action = tr("pp2.chronicle." + kind)
                pilot = event.get("PilotName_Localised") or event.get("PilotName")
                field = "Target" if kind == "Bounty" else "Ship"
                ship = event.get(field + "_Localised") or event.get(field)
                parts = [value for value in (pilot, ship) if isinstance(value, str) and value]
                if kind == "Bounty" and number(event.get("TotalReward")) is not None:
                    parts.append(tr("pp2.chronicle.reward", amount=fmt(event["TotalReward"])))
                details = " · ".join(parts) or unknown
            place = " · ".join(value for value in (group.station, group.system) if value)
            if place:
                details += " | " + place
            details = " | ".join(line for line in details.splitlines() if line.strip())
            gains = ["+" + fmt(credit["MeritsGained"]) for credit in group.credits]
            merits = " / ".join(gains[:5]) + (" / …" if len(gains) > 5 else "") if gains else "—"
            if kind == 'MarketSell' and not is_rare_sale(event) and gains:
                merits = '+' + fmt(sum(credit['MeritsGained'] for credit in group.credits))
            symbol = {"explicit": "✓", "temporal": "≈", "unknown": "?"}[group.certainty]
            exact = [str(event.get("timestamp") or unknown) + "  " + action, details]
            for credit in group.credits:
                exact.append(str(credit.get("timestamp") or unknown) + "  "
                             + tr("pp2.merit_gain", amount=fmt(credit["MeritsGained"]))
                             + " · " + tr("pp2.merits") + ": " + fmt(credit.get("TotalMerits")))
            rare_sale = kind == "MarketSell" and is_rare_sale(event)
            if rare_sale:
                safety = tr("pp2.chronicle.sale_evidence")
            if group.certainty == "temporal":
                gaps = [fmt(data.chronicle._gap(event, credit)) for credit in group.credits]
                temporal = "\n".join(tr("pp2.chronicle.temporal", seconds=gap) for gap in dict.fromkeys(gaps))
                safety = safety + "\n" + temporal if rare_sale else temporal
            elif not rare_sale:
                safety = tr("pp2.chronicle." + group.certainty)
            if group.certainty == "explicit" and gains:
                safety += "\n" + tr("pp2.chronicle.credit_caution")
            tooltip = safety + "\n\n" + "\n".join(exact)
            for col, text in enumerate((when, action, details, merits, symbol)):
                item = QTableWidgetItem(text)
                item.setToolTip(tooltip)
                self.recent.setItem(row, col, item)
        self.recent.resizeRowsToContents()
        self._chronicle_render_key = render_key if revision is not None else None
