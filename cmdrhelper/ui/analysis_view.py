"""User-triggered system analysis; the historical pattern view stays separate."""
import logging

from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
)

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.jump_tip import HierarchicalJumpTip

logger = logging.getLogger(__name__)


class SystemAnalysisView(QScrollArea):
    def __init__(self, state, format_credits, *, light=False, parent=None):
        super().__init__(parent)
        self.state = state
        self.format_credits = format_credits
        self.light = light
        self.result = None
        self._commander = None
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("QFrame#card QLabel { background: transparent; }")
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 8, 10, 8)
        entry = QHBoxLayout()
        caption = QLabel(tr("analysis.system") + ":")
        entry.addWidget(caption)
        self.system_input = QLineEdit()
        caption.setBuddy(self.system_input)
        self.system_input.setPlaceholderText(tr("analysis.placeholder"))
        self.system_input.setAccessibleName(tr("analysis.system"))
        entry.addWidget(self.system_input, 1)
        self.current_button = QPushButton(tr("analysis.current"))
        self.current_button.clicked.connect(self.use_current_system)
        entry.addWidget(self.current_button)
        self.analyze_button = QPushButton(tr("analysis.run"), objectName="primary")
        self.analyze_button.clicked.connect(self.analyze)
        self.system_input.returnPressed.connect(self.analyze)
        entry.addWidget(self.analyze_button)
        layout.addLayout(entry)
        self.status = self.label(tr("analysis.prompt"), "muted")
        layout.addWidget(self.status)

        self.result_panel = QWidget()
        results = QVBoxLayout(self.result_panel)
        results.setContentsMargins(0, 0, 0, 0)
        self.target = self.label("", "sectionTitle")
        self.recommendation = self.label("", "cardValue")
        self.index = self.label("")
        self.index.setToolTip(tr("analysis.index_explanation"))
        self.index_explanation = self.label(tr("analysis.index_explanation"), "muted")
        self.local_quality = self.label("")
        heading = QVBoxLayout()
        heading.setSpacing(3)
        self.index.setStyleSheet("font-size: 16px; font-weight: 600;")
        for label in (self.target, self.recommendation, self.index, self.index_explanation, self.local_quality):
            heading.addWidget(label)
        results.addLayout(heading)

        card, grid = self.card("analysis.basis")
        self.comparison_table = QTableWidget(3, 4)
        table = self.comparison_table
        table.setHorizontalHeaderLabels([tr("analysis.column.level"), tr("analysis.column.comparison"),
                                         tr("score.systems"), tr("analysis.data_quality")])
        table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        table.setStyleSheet("QTableWidget::item { padding: 3px 6px; } "
                           "QHeaderView::section { padding: 4px 6px; }")
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        grid.addWidget(table, 0, 0, 1, 2)
        results.addWidget(card)

        card, grid = self.card("analysis.experience")
        self.experience_grid = grid
        self.scope = self.label("", "muted")
        grid.addWidget(self.label(tr("analysis.scope_label")), 0, 0)
        grid.addWidget(self.scope, 0, 1)
        self.metric_labels = {}
        for row, name in enumerate(("systems", "hits", "median", "potential"), 1):
            caption = self.label(tr("analysis.metric." + name))
            caption.setWordWrap(False)
            grid.addWidget(caption, row, 0)
            self.metric_labels[name] = self.label("")
            grid.addWidget(self.metric_labels[name], row, 1)
        results.addWidget(card)
        self.finds = self.label("")
        results.addWidget(self.label(tr("analysis.finds"), "sectionTitle"))
        results.addWidget(self.finds)
        results.addWidget(self.label("BIO", "sectionTitle"))
        self.bio = self.label("")
        results.addWidget(self.bio)
        results.addWidget(self.label(tr("analysis.bio.informational"), "muted"))
        layout.addWidget(self.result_panel)
        layout.addStretch()
        self.result_panel.hide()
        if hasattr(state, "changed"):
            state.changed.connect(self._invalidate_commander)

    @staticmethod
    def label(text, name=""):
        label = QLabel(text, objectName=name)
        label.setTextFormat(Qt.PlainText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label

    def card(self, title):
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.addWidget(self.label(tr(title), "sectionTitle"))
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        return card, grid

    def use_current_system(self):
        self.system_input.setText(str(getattr(self.state, "system", "") or ""))
        self.system_input.setFocus()

    def _invalidate_commander(self):
        if self.result is not None and self._commander != getattr(self.state.database, "active_commander_id", None):
            self.result = None
            self.result_panel.hide()
            self.status.setText(tr("analysis.prompt"))
            self.status.show()

    def analyze(self):
        name = self.system_input.text().strip()
        self.result = None
        self.result_panel.hide()
        self.status.show()
        if not name:
            self.status.setText(tr("analysis.error.empty"))
            return
        self.analyze_button.setEnabled(False)
        try:
            result = HierarchicalJumpTip(self.state.database).evaluate(name)
            if not result.get("ok"):
                reason = result.get("reason")
                key = {"unsupported_name": "unsupported", "no_mass_observations": "mass",
                       "no_qualified_observations": "no_data"}.get(reason, "failed")
                self.status.setText(tr("analysis.error." + key))
                return
            self.render(result)
        except Exception:
            logger.exception("System analysis failed")
            self.result = None
            self.result_panel.hide()
            self.status.setText(tr("analysis.error.failed"))
        finally:
            self.analyze_button.setEnabled(True)

    def render(self, result):
        self.result = result
        self._commander = getattr(self.state.database, "active_commander_id", None)
        self.target.setText(result["target"])
        self.recommendation.setText(QLocale(get_language()).toUpper(tr("analysis.class." + result["recommendation"])))
        self.index.setText(tr("analysis.index") + " " + str(round(result["potential_index"])))
        self.local_quality.setText(tr("analysis.local_quality") + ": " + tr("analysis.quality." + result["family_data_quality"]))
        levels = result["levels"]
        names = {"mass": result["mass"], "sector_mass": result["sector"] + " · " + result["mass"],
                 "family": result["family_key"]}
        for row, level in enumerate(levels):
            quality = tr("analysis.quality." + level["data_quality"])
            if not level["systems"]:
                quality += " · " + tr("analysis.inherited")
            values = (tr("analysis.level." + level["kind"]), names[level["kind"]], str(level["systems"]), quality)
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.comparison_table.setItem(row, column, item)
        self.comparison_table.resizeRowsToContents()
        self.comparison_table.setFixedHeight(self.comparison_table.horizontalHeader().height()
                                            + sum(self.comparison_table.rowHeight(r) for r in range(3)) + 4)
        used = next(level for level in reversed(levels) if level["systems"] > 0)
        self.scope.setText(tr("analysis.level." + used["kind"]) + " · " + names[used["kind"]])
        for key in ("systems", "hits"):
            self.metric_labels[key].setText(str(used[key]))
        self.metric_labels["median"].setText(self.format_credits(round(used["median"])) if used["median"] is not None else "–")
        self.metric_labels["potential"].setText(self.format_credits(round(used["adjusted_potential"])))
        finds = [tr("analysis.find." + key) + ": " + str(used["counts"].get(key, 0))
                 for key in ("water_world", "terraformable_water_world", "earthlike", "ammonia_world", "terraformable_hmc")
                 if used["counts"].get(key, 0) > 0]
        self.finds.setText(" · ".join(finds) if finds else tr("analysis.find.none"))
        bio = used["bio"]
        if bio["comparable_systems"]:
            self.bio.setText(tr("analysis.bio.covered", count=bio["comparable_systems"],
                                value=self.format_credits(round(bio["median_base_value"]))))
        elif bio["signal_systems"] or bio["analysed_systems"]:
            self.bio.setText(tr("analysis.bio.partial", signals=bio["signal_systems"], analysed=bio["analysed_systems"]))
        else:
            self.bio.setText(tr("analysis.bio.unknown"))
        self.set_light_mode(self.light)
        self.status.setText("")
        self.status.hide()
        self.result_panel.show()

    def set_light_mode(self, light):
        self.light = bool(light)
        colors = {"weak": ("#a33f3f", "#e09696"), "average": ("#374151", "#d9dde1"),
                  "interesting": ("#856000", "#ffcc66"), "good": ("#237238", "#86cf91"),
                  "very_good": ("#12652c", "#65d067")}
        if self.result:
            color = colors[self.result["recommendation"]][0 if light else 1]
            self.recommendation.setStyleSheet(f"color: {color}; font-size: 19px; font-weight: 600;")
            # Evidence uses muted slate/teal tones, never recommendation warning colors.
            quality_colors = {"very_low": ("#626b76", "#a4afbb"), "low": ("#5e6f7b", "#9cacba"),
                              "usable": ("#416e70", "#93b9ba"), "good": ("#416d59", "#96bca8")}
            quality_color = lambda quality: quality_colors[quality][0 if light else 1]
            self.local_quality.setStyleSheet(f"color: {quality_color(self.result['family_data_quality'])};")
            for row, level in enumerate(self.result["levels"]):
                self.comparison_table.item(row, 3).setForeground(QColor(quality_color(level["data_quality"])))
