"""Compact local Powerplay overview, following the shared card/theme styles."""
from datetime import timedelta
from PySide6.QtCore import QLocale, QTimer, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHeaderView, QLabel, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QMenu, QMessageBox, QProgressBar,
)

from cmdrhelper.i18n import get_language, tr
from cmdrhelper.ui.table_widths import ResponsiveColumnWidths
from cmdrhelper.ui.powerplay_portraits import PowerPortrait
from cmdrhelper.ui.powerplay_system import SystemPresentation
from cmdrhelper.powerplay_rank import rank_progress
from cmdrhelper.powerplay_chronicle import local_today, today_groups
from cmdrhelper.powerplay import (
    PowerplayState, PowersCache, ACTION_TOKENS, powerplay_actions, context, number,
    powers_cache_path, timestamp, onboard_articles,
)


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


class PowerplayView(QScrollArea):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.cache = PowersCache()
        self.selected_day = None
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
        layout.addWidget(card)
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
        card, grid = self.card("pp2.system")
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
        self.action_heading = self.label("", "sectionTitle")
        action_section_layout.addWidget(self.action_heading)
        card = QFrame(objectName="card")
        actions_layout = QVBoxLayout(card)
        self.mode = self.label("", "sectionTitle")
        self.actions = self.label("")
        self.notice = self.label("", "muted")
        for label in (self.mode, self.actions, self.notice):
            actions_layout.addWidget(label)
        action_section_layout.addWidget(card)
        right.addWidget(self.action_section)
        self.cargo_card, grid = self.card("pp2.onboard")
        self.cargo = self.label("")
        grid.addWidget(self.cargo, 0, 0)
        left.addWidget(self.cargo_card)
        self.recent_section = QWidget()
        recent_layout = QVBoxLayout(self.recent_section)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(6)
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
        self.recent.setWordWrap(True)
        self.recent.verticalHeader().hide()
        header = self.recent.horizontalHeader()
        self.recent.configure_widths(getattr(state, 'settings', None))
        header.sectionResized.connect(lambda *_: self.recent.resizeRowsToContents())
        self.chronicle_header = QGridLayout()
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
        for widget in (self.previous_day, self.day_label, self.next_day, self.today_button):
            navigation.addWidget(widget)
        recent_layout.addLayout(self.chronicle_header)
        self.chronicle_help = self.label(tr("pp2.history.legend"), "muted")
        self.chronicle_help.setToolTip(tr("pp2.history.help"))
        recent_layout.addWidget(self.chronicle_help)
        recent_layout.addWidget(self.recent, 1)
        layout.addWidget(self.recent_section, 1)
        self._arrange_columns()
        state.changed.connect(self._changed)
        cargo_signal = getattr(state, "cargoSnapshotChanged", None)
        if cargo_signal is not None:
            cargo_signal.connect(self._changed)
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self._changed)
        self.render()

    @staticmethod
    def label(text, name=""):
        label = QLabel(text, objectName=name)
        label.setWordWrap(True)
        label.setTextFormat(Qt.PlainText)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def card(self, key):
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.addWidget(self.label(tr(key), "sectionTitle"))
        grid = QGridLayout()
        layout.addLayout(grid)
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
        # A font-relative breakpoint respects font scaling without fixing any
        # card width. Independent column layouts keep short cargo cards compact.
        wide = self.viewport().width() >= self.fontMetrics().horizontalAdvance("0") * 110
        stacked = self.viewport().width() < self.fontMetrics().horizontalAdvance("0") * 65
        if stacked != self._portrait_stacked:
            self._portrait_stacked = stacked
            self.personal_grid.removeWidget(self.personal_info)
            self.personal_grid.addWidget(self.personal_info, 1 if stacked else 0,
                                         0 if stacked else 1, 1, 2 if stacked else 1)
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
        for widget in (self.chronicle_title, self.navigation, self.manage_history):
            self.chronicle_header.removeWidget(widget)
        self.chronicle_header.addWidget(self.chronicle_title, 0, 0, 1, 1 if wide else 2)
        self.chronicle_header.addWidget(self.navigation, 0 if wide else 1, 1 if wide else 0,
                                       alignment=Qt.AlignLeft)
        self.chronicle_header.addWidget(self.manage_history, 0 if wide else 2, 2 if wide else 0,
                                       1, 1 if wide else 2, alignment=Qt.AlignRight if wide else Qt.AlignLeft)
        self.chronicle_header.setColumnStretch(0, 1 if wide else 0)
        self.chronicle_header.setColumnStretch(1, 0 if wide else 1)
        self.recent.fit_columns()

    @staticmethod
    def _activity_time(value, locale, today):
        local = value.astimezone()
        clock = local.strftime("%H:%M")
        return clock if local.date() == today else locale.toString(local.date(), QLocale.ShortFormat) + " " + clock

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def _changed(self, *_):
        if self.isVisible():
            self.render()

    def _move_day(self, delta):
        today = local_today()
        target = min((self.selected_day or today) + timedelta(days=delta), today)
        self.selected_day = None if target == today else target
        self.render()

    def _today(self):
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
        if getattr(self.state, "system", "") != system.get("StarSystem", ""):
            system = {}
            relationship, mode = "unknown", None
        else:
            relationship, mode = context(data)
        self.system_presentation.render(system, getattr(self.state, "system", ""), relationship, fmt)
        at = timestamp(system.get("timestamp"))
        self.observed.setText(tr("pp2.observed", time=date(at)) if at else tr("pp2.no_data"))
        self.action_heading.setText(tr("pp2.actions_for", power=data.power) if data.power else tr("pp2.actions"))
        powers = self.cache.load(powers_cache_path(getattr(self.state, "journal_folder", None)))
        self._render_rank(data, powers, locale, fmt)
        self.notice.setText(tr("pp2.cache_unavailable") if powers is None else tr("pp2.cache_source"))
        self.mode.setText(tr("pp2.mode." + mode) if mode else tr("pp2.mode.unknown"))
        self.actions.setToolTip("")
        if not data.power:
            message = tr("pp2.need_power")
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

    def _render_rank(self, data, powers, locale, fmt):
        progress = rank_progress(data.power, data.rank, data.merits, powers)
        self.personal['rank'].setToolTip(tr('pp2.rank.journal', rank=fmt(data.rank)))
        self.rank_bar.hide()
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
        if progress.status == 'confirmed':
            self.rank_summary.setText(next_text)
            percent = 100*progress.earned/progress.span
            self.rank_bar.setValue(progress.earned*1000//progress.span)
            self.rank_bar.setFormat(tr('pp2.rank.bar', current=fmt(progress.lower),
                percent=locale.toString(percent, 'f', 1), next=fmt(progress.upper)))
            self.rank_bar.show()
        else:
            self.rank_summary.setText(tr('pp2.rank.'+progress.status, rank=calculated)+'\n'+next_text)
        diagnostic = tr('pp2.rank.diagnostic', confirmed=fmt(data.rank), calculated=calculated,
                        earned=fmt(progress.earned), span=fmt(progress.span))
        self.rank_summary.setToolTip(diagnostic)
        self.rank_bar.setToolTip(diagnostic)

    def _render_chronicle(self, data, locale, fmt, unknown):
        today = local_today()
        selected = self.selected_day or today
        self.day_label.setText(locale.toString(selected, QLocale.ShortFormat))
        self.next_day.setEnabled(selected < today)
        db = getattr(self.state, "database", None)
        cid = getattr(self.state, "commander_id", None)
        for action in self.manage_history.menu().actions()[:3]:
            action.setEnabled(db is not None and cid is not None)
        chronicle = db.powerplay_day(cid, selected) if db is not None and cid is not None else data.chronicle
        groups = today_groups(chronicle, selected)
        self.recent.setRowCount(len(groups))
        for row, group in enumerate(groups):
            event = group.action
            kind = event.get("event")
            at = timestamp(event.get("timestamp"))
            when = self._activity_time(at, locale, today) if at else unknown
            if group.certainty == "unknown":
                action = tr("pp2.unknown")
                details = tr("pp2.chronicle.unassigned")
            elif kind in ("PowerplayCollect", "PowerplayDeliver", "SearchAndRescue"):
                action = tr("pp2.chronicle." + kind)
                field = "Name" if kind == "SearchAndRescue" else "Type"
                name = event.get(field + "_Localised") or event.get(field) or unknown
                details = tr("pp2.chronicle.item", count=fmt(event.get("Count")), name=name)
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
                details += "\n" + place
            gains = ["+" + fmt(credit["MeritsGained"]) for credit in group.credits]
            merits = " / ".join(gains[:5]) + (" / …" if len(gains) > 5 else "") if gains else "—"
            symbol = {"explicit": "✓", "temporal": "≈", "unknown": "?"}[group.certainty]
            exact = [str(event.get("timestamp") or unknown) + "  " + action, details]
            for credit in group.credits:
                exact.append(str(credit.get("timestamp") or unknown) + "  "
                             + tr("pp2.merit_gain", amount=fmt(credit["MeritsGained"]))
                             + " · " + tr("pp2.merits") + ": " + fmt(credit.get("TotalMerits")))
            if group.certainty == "temporal":
                gaps = [fmt(data.chronicle._gap(event, credit)) for credit in group.credits]
                safety = "\n".join(tr("pp2.chronicle.temporal", seconds=gap) for gap in dict.fromkeys(gaps))
            else:
                safety = tr("pp2.chronicle." + group.certainty)
            if group.certainty == "explicit" and gains:
                safety += "\n" + tr("pp2.chronicle.credit_caution")
            tooltip = safety + "\n\n" + "\n".join(exact)
            for col, text in enumerate((when, action, details, merits, symbol)):
                item = QTableWidgetItem(text)
                item.setToolTip(tooltip)
                self.recent.setItem(row, col, item)
        self.recent.resizeRowsToContents()
