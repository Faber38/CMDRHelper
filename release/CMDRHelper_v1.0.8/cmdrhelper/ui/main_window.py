from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import re

from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.bio_valuation import base_value, species_name
from cmdrhelper.ui.body_detail_window import BodyDetailWindow
from cmdrhelper.ui.chronicle_view import ChronicleMapWidget
from cmdrhelper.ui.screenshot_view import ScreenshotView
from cmdrhelper.online_services import (
    test_edsm_connection,
    test_inara_connection,
)
from cmdrhelper.version import __version__
from cmdrhelper.i18n import tr, get_language, set_language
from cmdrhelper.mission_manager import translate_mission_text
from cmdrhelper.score_analyzer import ScoreAnalyzer
from cmdrhelper.update import (
    UpdateCheckWorker,
    is_newer_version,
    download_release,
    launch_installer,
)

from PySide6.QtCore import Qt, QTimer, QThreadPool, QUrl, QRectF, Signal
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from PySide6.QtGui import (
    QDesktopServices,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QFont,
    QFontDatabase,
)

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QFormLayout,
    QLineEdit,
    QScrollArea,
    QSplitter,
    QMessageBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QApplication,
    QDialog,
    QProgressBar,
    QTabWidget,
    QSpinBox,
    QFontComboBox,
    QComboBox,
)


class ChronicleSystemWindow(QDialog):
    def __init__(self, system_name, bodies, header_text, body_callback, parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("chronicle.system_window_title", system=system_name))
        self.resize(1250, 760)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel(system_name, objectName="sectionTitle")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        layout.addWidget(title)

        info = QLabel(header_text, objectName="muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.system_map = SystemMapWidget()
        self.system_map.bodyClicked.connect(body_callback)
        self.system_map.set_system(system_name, bodies)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.system_map)

        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton(tr("common.close"))
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        layout.addLayout(buttons)


class ChronicleSearchHelpDialog(QDialog):
    """
    Kompakte Suchhilfe für die Chronik.

    Kategorien sind einzeln aufklappbar. Ein Klick auf einen Begriff
    übernimmt ihn in die Chronik-Suche und startet die Suche direkt.
    """

    def __init__(self, groups, on_term_clicked, parent=None):
        super().__init__(parent)

        self._on_term_clicked = on_term_clicked
        self._groups = groups or {}

        self.setWindowTitle(tr("chronicle.search_help_window_title"))
        self.resize(720, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        title = QLabel(tr("chronicle.search_help"), objectName="sectionTitle")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        root.addWidget(title)

        intro = QLabel(tr("chronicle.search_help_intro"))
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        root.addWidget(intro)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)

        for group_name, terms in self._groups.items():
            self._add_group(
                group_name,
                terms,
            )

        self.content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton(tr("common.close"))
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        root.addLayout(buttons)

    def _add_group(self, group_name, terms):
        terms = [str(term) for term in (terms or []) if str(term).strip()]

        header = QPushButton(f"▸  {group_name}   ({len(terms)})")
        header.setCheckable(True)
        header.setStyleSheet("text-align:left; padding:5px 8px; font-weight:700;")

        body = QFrame()
        body.setVisible(False)

        grid = QGridLayout(body)
        grid.setContentsMargins(8, 4, 8, 6)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(4)

        # Kompakter als die bisherige Darstellung.
        columns = 4

        for index, term in enumerate(terms):
            button = QPushButton(term)
            button.setToolTip(tr("chronicle.search_for_term", term=term))
            button.setMinimumHeight(24)
            button.setStyleSheet("padding:2px 6px; text-align:left;")
            button.clicked.connect(
                lambda checked=False, value=term: self._term_clicked(value)
            )

            row = index // columns
            col = index % columns

            grid.addWidget(
                button,
                row,
                col,
            )

        header.toggled.connect(
            lambda checked, button=header, frame=body, title=group_name, count=len(
                terms
            ): self._toggle_group(
                button,
                frame,
                title,
                count,
                checked,
            )
        )

        self.content_layout.addWidget(header)
        self.content_layout.addWidget(body)

    def _toggle_group(
        self,
        button,
        frame,
        title,
        count,
        checked,
    ):
        frame.setVisible(bool(checked))

        button.setText(
            (f"▾  {title}   ({count})" if checked else f"▸  {title}   ({count})")
        )

    def _term_clicked(self, term):
        if callable(self._on_term_clicked):
            self._on_term_clicked(str(term))


class SystemOverviewMiniMap(QWidget):
    bodyClicked = Signal(object)

    def __init__(self, source_map, parent=None):
        super().__init__(parent)

        self.source_map = source_map
        self._click_rects = []

        self.setMinimumSize(600, 420)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)

        try:
            painter.setRenderHint(
                QPainter.Antialiasing,
                True,
            )

            painter.fillRect(
                self.rect(),
                QColor("#080d12"),
            )

            self._click_rects = []

            if self.source_map is None or not self.source_map.bodies:
                painter.setPen(QColor("#8e969e"))
                painter.drawText(
                    self.rect(),
                    Qt.AlignCenter,
                    tr("explorer.no_system_data_available"),
                )
                return

            (
                positions,
                children,
                _families,
                _used_units,
                _depth_count,
            ) = self.source_map._tree_layout()

            if not positions:
                return

            left = min(pos["x"] for pos in positions.values())
            top = min(pos["y"] for pos in positions.values())
            right = max(pos["x"] + self.source_map.BODY_W for pos in positions.values())
            bottom = max(
                pos["y"] + self.source_map.BODY_H for pos in positions.values()
            )

            source_w = max(
                1.0,
                right - left,
            )
            source_h = max(
                1.0,
                bottom - top,
            )

            margin = 22.0

            scale = min(
                max(
                    0.01,
                    (self.width() - margin * 2) / source_w,
                ),
                max(
                    0.01,
                    (self.height() - margin * 2) / source_h,
                ),
            )

            offset_x = (self.width() - source_w * scale) / 2.0

            offset_y = (self.height() - source_h * scale) / 2.0

            def map_point(x, y):
                return (
                    offset_x + (x - left) * scale,
                    offset_y + (y - top) * scale,
                )

            # Zuerst die Parent-/Child-Verbindungen zeichnen.
            painter.setPen(
                QPen(
                    QColor("#7f8993"),
                    max(1.0, 1.2 * scale),
                )
            )

            for parent_pos in positions.values():
                parent = parent_pos["body"]

                direct_children = [
                    child
                    for child in children.get(
                        parent.get("body_id"),
                        [],
                    )
                    if id(child) in positions
                ]

                if not direct_children:
                    continue

                px_raw = parent_pos["x"] + self.source_map.BODY_W / 2
                py_raw = parent_pos["y"] + self.source_map.BODY_H

                child_centers_raw = [
                    (positions[id(child)]["x"] + self.source_map.BODY_W / 2)
                    for child in direct_children
                ]

                child_tops_raw = [
                    positions[id(child)]["y"] for child in direct_children
                ]

                nearest_top = min(child_tops_raw)

                bus_y_raw = py_raw + (nearest_top - py_raw) * 0.45

                px, py = map_point(
                    px_raw,
                    py_raw,
                )
                _, bus_y = map_point(
                    px_raw,
                    bus_y_raw,
                )

                painter.drawLine(
                    int(px),
                    int(py),
                    int(px),
                    int(bus_y),
                )

                if len(child_centers_raw) > 1:
                    left_x, _ = map_point(
                        min(child_centers_raw),
                        bus_y_raw,
                    )
                    right_x, _ = map_point(
                        max(child_centers_raw),
                        bus_y_raw,
                    )

                    painter.drawLine(
                        int(left_x),
                        int(bus_y),
                        int(right_x),
                        int(bus_y),
                    )

                for child in direct_children:
                    child_pos = positions[id(child)]

                    cx_raw = child_pos["x"] + self.source_map.BODY_W / 2
                    cy_raw = child_pos["y"]

                    cx, cy = map_point(
                        cx_raw,
                        cy_raw,
                    )

                    if len(child_centers_raw) == 1 and abs(cx_raw - px_raw) > 1:
                        painter.drawLine(
                            int(px),
                            int(bus_y),
                            int(cx),
                            int(bus_y),
                        )

                    painter.drawLine(
                        int(cx),
                        int(bus_y),
                        int(cx),
                        int(cy),
                    )

            # Körper als kompakte Miniatur-Symbole.
            for pos in sorted(
                positions.values(),
                key=lambda item: (
                    item["level"],
                    item["x"],
                ),
            ):
                body = pos["body"]

                center_raw_x = pos["x"] + self.source_map.BODY_W / 2
                center_raw_y = pos["y"] + 44

                cx, cy = map_point(
                    center_raw_x,
                    center_raw_y,
                )

                is_star = bool(body.get("star_type") or body.get("body_type") == "Star")

                is_belt = self.source_map._is_belt_cluster(body)

                if is_star:
                    radius = max(
                        7.0,
                        min(
                            18.0,
                            15.0 * scale + 5.0,
                        ),
                    )
                elif is_belt:
                    radius = max(
                        3.0,
                        min(
                            7.0,
                            5.0 * scale + 2.0,
                        ),
                    )
                else:
                    radius = max(
                        4.0,
                        min(
                            11.0,
                            8.0 * scale + 3.0,
                        ),
                    )

                body_color = self.source_map._body_color(body)

                bio_count = int(body.get("biological_signals") or 0)

                geo_count = int(body.get("geological_signals") or 0)

                if bio_count > 0:
                    outline = QColor("#39ff56")
                elif geo_count > 0:
                    outline = QColor("#28c9e8")
                elif body.get("high_value"):
                    outline = QColor("#ffb000")
                else:
                    outline = QColor("#d9dde1")

                painter.setPen(
                    QPen(
                        outline,
                        2,
                    )
                )

                painter.setBrush(QBrush(body_color))

                if is_belt:
                    painter.drawEllipse(
                        QRectF(
                            cx - radius * 1.7,
                            cy - radius * 0.55,
                            radius,
                            radius,
                        )
                    )
                    painter.drawEllipse(
                        QRectF(
                            cx - radius * 0.4,
                            cy - radius,
                            radius * 1.2,
                            radius * 1.2,
                        )
                    )
                    painter.drawEllipse(
                        QRectF(
                            cx + radius * 0.8,
                            cy - radius * 0.4,
                            radius * 0.85,
                            radius * 0.85,
                        )
                    )
                else:
                    painter.drawEllipse(
                        QRectF(
                            cx - radius,
                            cy - radius,
                            radius * 2,
                            radius * 2,
                        )
                    )

                # Größerer unsichtbarer Klickbereich als das Miniatursymbol.
                click_r = max(
                    10.0,
                    radius + 5.0,
                )

                self._click_rects.append(
                    (
                        QRectF(
                            cx - click_r,
                            cy - click_r,
                            click_r * 2,
                            click_r * 2,
                        ),
                        body,
                    )
                )

        finally:
            # Wichtig: QPainter immer sauber beenden.
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            point = event.position()

            for rect, body in self._click_rects:
                if rect.contains(point):
                    self.bodyClicked.emit(body)
                    return

        super().mousePressEvent(event)


class SystemOverviewDialog(QDialog):
    """Sichere Miniaturübersicht ohne Rendern eines bereits sichtbaren Widgets."""

    def __init__(
        self,
        system_name,
        bodies,
        source_map,
        on_body_clicked=None,
        parent=None,
    ):
        super().__init__(parent)

        self.system_name = system_name or ""

        self.setWindowTitle(tr("explorer.show_all_title", system=self.system_name))

        self.resize(
            1050,
            720,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(
            10,
            10,
            10,
            10,
        )
        root.setSpacing(6)

        title = QLabel(
            self.system_name,
            objectName="sectionTitle",
        )
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        root.addWidget(title)

        hint = QLabel(
            tr("explorer.overview_hint"),
            objectName="muted",
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.preview = SystemOverviewMiniMap(
            source_map=source_map,
            parent=self,
        )

        if callable(on_body_clicked):
            self.preview.bodyClicked.connect(on_body_clicked)

        root.addWidget(
            self.preview,
            1,
        )

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton(tr("common.close"))
        close.clicked.connect(self.close)
        buttons.addWidget(close)

        root.addLayout(buttons)


class ExplorerLiveListWindow(QDialog):
    """Kleines frei positionierbares Live-Fenster für Explorer-Hinweise."""

    def __init__(
        self,
        title,
        headers,
        settings,
        geometry_key,
        parent=None,
        window_kind="value",
    ):
        super().__init__(parent)
        self.settings = settings
        self.geometry_key = geometry_key
        self.window_kind = str(window_kind or "value")
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.resize(620, 260)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)

        self.system_label = QLabel("–", objectName="sectionTitle")
        self.system_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        root.addWidget(self.system_label)

        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)

        # Spalten im Live-Fenster frei mit der Maus veränderbar machen.
        # Die gewählten Breiten werden für BIO- und Wertefenster getrennt
        # gespeichert und beim nächsten Öffnen wiederhergestellt.
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)

        if self.window_kind == "bio":
            default_widths = [90, 330, 150, 130]
        else:
            default_widths = [140, 180, 130, 170]

        for column, width in enumerate(default_widths):
            if column < self.table.columnCount():
                self.table.setColumnWidth(column, width)

        self._header_state_key = f"{self.geometry_key}_header_state"
        saved_header_state = self.settings.value(self._header_state_key)
        if saved_header_state is not None:
            try:
                header.restoreState(saved_header_state)
            except Exception:
                pass

        header.sectionResized.connect(self._save_header_state)

        root.addWidget(self.table, 1)

        # Die Live-Fenster bewusst leicht rötlich/braun absetzen, damit sie
        # sich während des Spielens klar vom Hauptfenster unterscheiden,
        # ohne wie ein Warnfenster zu wirken.
        self.setStyleSheet("""
            QDialog {
                background-color: #171012;
            }
            QLabel {
                background: transparent;
            }
            QTableWidget {
                background-color: #151012;
                alternate-background-color: #1d1417;
                gridline-color: #493038;
                border: 1px solid #493038;
                selection-background-color: #50313a;
            }
            QHeaderView::section {
                background-color: #24171b;
                border: 0;
                border-right: 1px solid #493038;
                border-bottom: 1px solid #493038;
                padding: 5px;
            }
            QTableCornerButton::section {
                background-color: #24171b;
                border: 0;
            }
        """)

        geometry = self.settings.value(self.geometry_key)
        if geometry is not None:
            try:
                self.restoreGeometry(geometry)
            except Exception:
                pass

    def _save_geometry(self):
        self.settings.setValue(self.geometry_key, self.saveGeometry())
        self.settings.sync()

    def _save_header_state(self, logical_index, old_size, new_size):
        if not hasattr(self, "table") or not hasattr(self, "_header_state_key"):
            return

        self.settings.setValue(
            self._header_state_key,
            self.table.horizontalHeader().saveState(),
        )
        self.settings.sync()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._save_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._save_geometry()

    def closeEvent(self, event):
        self._save_geometry()
        super().closeEvent(event)

    def set_rows(self, system_name, rows):
        self.system_label.setText(system_name or "–")

        # Vor jedem Neuaufbau alte CellWidgets entfernen.
        # QTableWidget.setRowCount() löscht zwar Items, aber bereits gesetzte
        # QLabel-CellWidgets können beim Zusammenfalten sonst optisch in
        # den neuen Zeilen liegen bleiben und Texte überlagern.
        for row_index in range(self.table.rowCount()):
            for col_index in range(self.table.columnCount()):
                widget = self.table.cellWidget(row_index, col_index)
                if widget is not None:
                    self.table.removeCellWidget(row_index, col_index)
                    widget.deleteLater()

        self.table.clearContents()

        # Das BIO-Fenster bekommt eine dynamische Gruppenansicht:
        # 0 erkannt  -> eine kompakte Zeile
        # teilweise  -> eine Zeile je erkannter Art + Restzeile
        # vollständig-> wieder eine kompakte grüne Zusammenfassung
        if self.window_kind == "bio":
            display_rows = []

            for row in rows:
                if not isinstance(row, dict):
                    continue

                body_name = str(row.get("body_name") or "?")
                signals = max(0, int(row.get("signals") or 0))
                geo_signals = max(0, int(row.get("geo_signals") or 0))
                species = list(row.get("species") or [])
                known_count = len(species)
                known_value = int(row.get("known_value") or 0)

                # Mehr Arten als Signale sollte praktisch nicht vorkommen;
                # für ungewöhnliche Journaldaten trotzdem robust bleiben.
                total_count = max(signals, known_count)

                # BIO-Signalanzahl immer sichtbar lassen. Diese kompakte
                # Kopfzeile zeigt nur die vom DSS/FSS gemeldete Anzahl und
                # greift nicht in die bestehende Arten-/Probenlogik ein.
                if signals > 0:
                    display_rows.append(
                        {
                            "body": body_name,
                            "entry": {
                                "name": f"BIO ×{signals}",
                                "scan_type": "bio_signal",
                                "value": 0,
                            },
                            "progress": "–",
                            "complete": False,
                        }
                    )

                # WICHTIG:
                # "Art bekannt" ist NICHT dasselbe wie "Analyse vollständig".
                # Elite kennt die konkrete Art bereits nach der ersten Probe.
                # Vollständig ist eine BIO-Art erst nach ScanOrganic
                # Analyse/Analyze, also nach der dritten erfolgreichen Probe.
                completed_count = sum(
                    1
                    for entry in species
                    if str(entry.get("scan_type") or "").strip().casefold()
                    in ("analyse", "analyze")
                )
                complete = (
                    total_count > 0
                    and known_count >= total_count
                    and completed_count >= total_count
                )

                if complete:
                    display_rows.append(
                        {
                            "body": "",
                            "find": tr(
                                "explorer.known_ratio",
                                known=known_count,
                                total=total_count,
                            ),
                            "progress": tr(
                                "explorer.complete_ratio",
                                completed=completed_count,
                                total=total_count,
                            ),
                            "value": (
                                MainWindow._format_reward(known_value)
                                if known_value > 0
                                else "–"
                            ),
                            "complete": True,
                        }
                    )

                    if geo_signals > 0:
                        display_rows.append(
                            {
                                "body": "",
                                "entry": {
                                    "name": str(
                                        row.get("geo_text") or f"GEO ×{geo_signals}"
                                    ),
                                    "scan_type": "geo",
                                    "value": 0,
                                },
                                "progress": "–",
                                "complete": False,
                            }
                        )
                    continue

                if known_count == 0:
                    if signals > 0:
                        display_rows.append(
                            {
                                "body": "",
                                "find": tr("explorer.still_unknown"),
                                "progress": tr(
                                    "explorer.known_ratio", known=0, total=total_count
                                ),
                                "value": "–",
                                "complete": False,
                            }
                        )

                    if geo_signals > 0:
                        display_rows.append(
                            {
                                "body": body_name if signals <= 0 else "",
                                "entry": {
                                    "name": str(
                                        row.get("geo_text") or f"GEO ×{geo_signals}"
                                    ),
                                    "scan_type": "geo",
                                    "value": 0,
                                },
                                "progress": "–",
                                "complete": False,
                            }
                        )
                    continue

                # Solange nicht ALLE Arten vollständig analysiert sind,
                # bleibt der Planet aufgeklappt. Das gilt auch dann, wenn
                # bereits z. B. 2/2 Arten namentlich bekannt sind, aber eine
                # davon erst bei Probe 1 oder 2 steht.
                for index, entry in enumerate(species):
                    scan_key = str(entry.get("scan_type") or "").strip().casefold()

                    if scan_key == "geo":
                        step_text = "–"
                    elif scan_key in ("analyse", "analyze"):
                        step_text = tr("explorer.sample_complete")
                    elif scan_key == "sample":
                        step_text = tr("explorer.sample_two")
                    elif scan_key == "log":
                        step_text = tr("explorer.sample_one")
                    else:
                        step_text = tr("explorer.dss_detected")

                    display_rows.append(
                        {
                            "body": "",
                            "entry": entry,
                            "progress": step_text,
                            "complete": False,
                        }
                    )

                remaining = max(0, total_count - known_count)
                if remaining:
                    display_rows.append(
                        {
                            "body": "",
                            "find": (
                                tr("explorer.one_unknown")
                                if remaining == 1
                                else tr("explorer.unknown_count", count=remaining)
                            ),
                            "progress": tr(
                                "explorer.known_ratio",
                                known=known_count,
                                total=total_count,
                            ),
                            "value": "–",
                            "complete": False,
                        }
                    )

                # GEO wird nur als Anzahl dargestellt. Es nimmt ausdrücklich
                # nicht an BIO-Art-, Probe- oder Fortschrittsberechnungen teil.
                if geo_signals > 0:
                    display_rows.append(
                        {
                            "body": "",
                            "entry": {
                                "name": str(
                                    row.get("geo_text") or f"GEO ×{geo_signals}"
                                ),
                                "scan_type": "geo",
                                "value": 0,
                            },
                            "progress": "–",
                            "complete": False,
                        }
                    )

            self.table.setRowCount(len(display_rows))

            for row_index, row in enumerate(display_rows):
                complete = bool(row.get("complete"))

                body_item = QTableWidgetItem(str(row.get("body") or ""))
                progress_item = QTableWidgetItem(str(row.get("progress") or ""))
                value_item = QTableWidgetItem(str(row.get("value") or "–"))

                if complete:
                    green = QColor("#65d067")
                    body_item.setForeground(green)
                    progress_item.setForeground(green)
                    value_item.setForeground(green)

                self.table.setItem(row_index, 0, body_item)

                if "entry" in row:
                    entry = row["entry"]
                    name = str(entry.get("name") or "")
                    scan_type = str(entry.get("scan_type") or "")
                    value = int(entry.get("value") or 0)

                    scan_key = scan_type.strip().casefold()
                    if scan_key == "geo":
                        color = "#28c9e8"
                    elif scan_key == "bio_signal":
                        color = "#66e36a"
                    elif scan_key in ("analyse", "analyze"):
                        color = "#65d067"
                    elif scan_key == "sample":
                        color = "#ffb000"
                    elif scan_key == "log":
                        color = "#f1f3f5"
                    else:
                        color = "#8e969e"

                    from html import escape

                    value_text = MainWindow._format_reward(value) if value > 0 else "–"
                    find_label = QLabel()
                    find_label.setTextFormat(Qt.RichText)
                    find_label.setContentsMargins(6, 0, 4, 0)
                    find_label.setText(
                        f'<span style="color:{color};">'
                        f"{escape(name)}"
                        f" &nbsp; ({escape(value_text)})"
                        f"</span>"
                    )
                    self.table.setCellWidget(row_index, 1, find_label)
                    value_item = QTableWidgetItem(value_text)
                    value_item.setForeground(QColor(color))
                else:
                    find_item = QTableWidgetItem(str(row.get("find") or ""))
                    if complete:
                        find_item.setForeground(QColor("#65d067"))
                    else:
                        find_item.setForeground(QColor("#8e969e"))
                    self.table.setItem(row_index, 1, find_item)

                self.table.setItem(row_index, 2, progress_item)
                self.table.setItem(row_index, 3, value_item)

            return

        # Wertfenster unverändert.
        self.table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for col, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                if col == 2:
                    item.setForeground(QColor("#ffb000"))
                elif col == 3:
                    mapping = str(value)
                    if mapping == tr("explorer.self_mapped"):
                        item.setForeground(QColor("#65d067"))
                    elif mapping == tr("explorer.first_mapping_possible"):
                        item.setForeground(QColor("#68c7ff"))
                    elif mapping == tr("explorer.already_mapped"):
                        item.setForeground(QColor("#9aa3ab"))
                self.table.setItem(row_index, col, item)


class MainWindow(QMainWindow):
    def __init__(self, state):
        super().__init__()

        self.state = state
        self.nav_buttons = []

        self.update_thread_pool = QThreadPool.globalInstance()
        self._update_check_running = False
        self._update_notice_shown = False
        self._update_worker = None
        self._chronicle_system_window = None
        self._chronicle_search_help_window = None
        self._system_overview_window = None
        self._explorer_value_live_window = None
        self._explorer_bio_live_window = None
        self._explorer_live_system = None
        self.ui_theme = str(self.state.settings.value("ui_theme", "dark")).lower()
        set_language(str(self.state.settings.value("ui_language", "de") or "de"))

        # Gespeicherte Anwendungsschrift bereits vor dem Aufbau der
        # Oberfläche anwenden, damit alle Widgets sofort korrekt erscheinen.
        self._apply_saved_ui_font()

        self.setWindowTitle(f"CMDRHelper {__version__}")

        self._build_ui()

        self.state.changed.connect(self.refresh_all)

        self.refresh_all()

        # Updateprüfung bewusst leicht verzögert starten, damit das
        # Hauptfenster zuerst vollständig erscheinen kann.
        QTimer.singleShot(1500, lambda: self._check_for_updates(automatic=True))

    def _nav(self, text, idx):
        button = QPushButton(text)

        button.clicked.connect(lambda: self._show_page(idx))

        self.nav_buttons.append(button)

        return button

    def _show_page(self, idx):
        self.pages.setCurrentIndex(idx)

        for i, button in enumerate(self.nav_buttons):
            button.setObjectName("navActive" if i == idx else "")

            button.style().unpolish(button)
            button.style().polish(button)

    def _card(self, title):
        frame = QFrame(objectName="card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)

        layout.addWidget(QLabel(title, objectName="sectionTitle"))

        return frame, layout

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        main = QHBoxLayout(root)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        side_frame = QFrame(objectName="sidebar")

        side_frame.setFixedWidth(210)

        side = QVBoxLayout(side_frame)
        side.setContentsMargins(12, 12, 12, 12)

        side.addWidget(QLabel("✦  CMDRHelper", objectName="appTitle"))

        side.addWidget(QLabel(tr("app.subtitle"), objectName="appSubTitle"))

        side.addSpacing(20)

        side.addWidget(self._nav("⌂  " + tr("nav.overview"), 0))

        side.addWidget(self._nav("◎  " + tr("nav.missions"), 1))

        side.addWidget(self._nav("✦  " + tr("nav.explorer"), 2))

        side.addWidget(self._nav("↝  " + tr("nav.chronicle"), 3))

        side.addWidget(self._nav("★  " + tr("nav.jump_tip"), 4))

        side.addWidget(self._nav("▣  " + tr("nav.images"), 5))

        side.addWidget(self._nav("⚙  " + tr("nav.settings"), 6))

        side.addStretch()

        # Explorer-Livefenster direkt in der Seitenleiste schalten.
        # Der kleine Block sitzt bewusst etwas oberhalb des Beenden-Schalters.
        live_title = QLabel(tr("settings.auto_show"))
        live_title.setStyleSheet("font-weight: 700;")
        live_title.setToolTip(tr("settings.auto_show_tooltip"))
        side.addWidget(live_title)

        live_frame = QFrame()
        live_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #68727c;
                border-radius: 5px;
            }
            QCheckBox {
                border: none;
            }
        """)

        live_layout = QVBoxLayout(live_frame)
        live_layout.setContentsMargins(7, 4, 7, 4)
        live_layout.setSpacing(2)

        self.explorer_value_live_enabled_check = QCheckBox(
            tr("settings.explorer_value_live_window")
        )
        self.explorer_value_live_enabled_check.setToolTip(
            tr("settings.explorer_value_live_window_tooltip")
        )
        self.explorer_value_live_enabled_check.setChecked(
            self._explorer_live_window_enabled("value")
        )
        self.explorer_value_live_enabled_check.toggled.connect(
            lambda checked: self._set_explorer_live_window_enabled("value", checked)
        )
        live_layout.addWidget(self.explorer_value_live_enabled_check)

        self.explorer_bio_live_enabled_check = QCheckBox(
            tr("settings.explorer_bio_live_window")
        )
        self.explorer_bio_live_enabled_check.setToolTip(
            tr("settings.explorer_bio_live_window_tooltip")
        )
        self.explorer_bio_live_enabled_check.setChecked(
            self._explorer_live_window_enabled("bio")
        )
        self.explorer_bio_live_enabled_check.toggled.connect(
            lambda checked: self._set_explorer_live_window_enabled("bio", checked)
        )
        live_layout.addWidget(self.explorer_bio_live_enabled_check)

        side.addWidget(live_frame)

        # Etwas mehr Abstand zum Ausschalter, damit der Block optisch höher sitzt.
        side.addSpacing(16)

        exit_button = QPushButton("⏻  " + tr("nav.exit"))
        exit_button.setToolTip(tr("nav.exit_tooltip"))
        exit_button.clicked.connect(self.close)
        side.addWidget(exit_button)

        side.addSpacing(10)

        self.sidebar_system = QLabel(tr("sidebar.current_system") + "\n–")
        self.sidebar_system.setWordWrap(True)
        side.addWidget(self.sidebar_system)

        self.sidebar_body = QLabel("", objectName="muted")
        self.sidebar_body.setWordWrap(True)
        side.addWidget(self.sidebar_body)

        side.addWidget(QLabel(f"CMDRHelper {__version__}", objectName="appSubTitle"))

        main.addWidget(side_frame)

        right = QWidget()

        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        top_frame = QFrame(objectName="topbar")

        top = QHBoxLayout(top_frame)

        self.commander_label = QLabel("CMDR –", objectName="commanderTitle")

        self.ship_label = QLabel("", objectName="muted")

        self.last_import_label = QLabel(
            tr("topbar.last_journal_entry", timestamp="–"), objectName="muted"
        )

        self.connection_label = QLabel(
            tr("topbar.journal_not_detected"), objectName="statusWarn"
        )

        self.edsm_upload_label = QLabel(tr("topbar.edsm_waiting"), objectName="muted")
        self.edsm_upload_label.setToolTip(tr("topbar.edsm_tooltip"))

        self.inara_upload_label = QLabel(tr("topbar.inara_waiting"), objectName="muted")
        self.inara_upload_label.setToolTip(tr("topbar.inara_prepared_tooltip"))

        top.addWidget(self.commander_label)

        top.addWidget(self.ship_label)

        top.addStretch()

        top.addWidget(self.last_import_label)

        top.addSpacing(16)

        top.addWidget(self.connection_label)

        top.addSpacing(16)

        top.addWidget(self.edsm_upload_label)

        top.addSpacing(16)

        top.addWidget(self.inara_upload_label)

        right_layout.addWidget(top_frame)

        self.pages = QStackedWidget()

        self.pages.addWidget(self._overview())

        self.pages.addWidget(self._missions())

        self.pages.addWidget(self._explorer())

        self.pages.addWidget(self._chronicle())

        self.pages.addWidget(self._score_page())

        self.screenshot_view = ScreenshotView(
            self.state.settings,
            self,
        )
        self.pages.addWidget(self.screenshot_view)

        self.pages.addWidget(self._settings())

        right_layout.addWidget(self.pages, 1)

        main.addWidget(right, 1)

        self._show_page(0)

    def _overview(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 6, 10, 6)
        page_layout.setSpacing(6)

        page_layout.addWidget(QLabel(tr("overview.title"), objectName="sectionTitle"))

        identity_row = QHBoxLayout()
        identity_row.setSpacing(6)

        identity_card, identity_layout = self._card(tr("overview.commander_ship"))

        self.overview_commander = QLabel("CMDR –", objectName="cardValue")
        identity_layout.addWidget(self.overview_commander)

        self.overview_ship = QLabel(tr("overview.ship", ship="–"))
        self.overview_ship.setWordWrap(True)
        identity_layout.addWidget(self.overview_ship)

        self.overview_location = QLabel(
            tr("overview.location", location="–"), objectName="muted"
        )
        self.overview_location.setWordWrap(True)
        identity_layout.addWidget(self.overview_location)

        identity_row.addWidget(identity_card, 2)

        journal_card, journal_layout = self._card(tr("overview.journal"))

        self.journal_count_value = QLabel("0", objectName="cardValue")
        journal_layout.addWidget(self.journal_count_value)

        journal_layout.addWidget(
            QLabel(tr("overview.journal_files_detected"), objectName="muted")
        )

        self.overview_journal_state = QLabel(
            tr("overview.not_detected"), objectName="statusWarn"
        )
        journal_layout.addWidget(self.overview_journal_state)

        identity_row.addWidget(journal_card, 1)
        page_layout.addLayout(identity_row)

        row = QHBoxLayout()
        row.setSpacing(6)

        mission_card, mission_layout = self._card(tr("overview.missions"))

        self.active_missions_value = QLabel("0", objectName="cardValue")
        mission_layout.addWidget(self.active_missions_value)

        self.mission_start_status = QLabel(
            tr("overview.no_open_missions"), objectName="muted"
        )
        self.mission_start_status.setWordWrap(True)
        mission_layout.addWidget(self.mission_start_status)

        mission_button = QPushButton(
            tr("overview.missions_button"), objectName="primary"
        )
        mission_button.clicked.connect(lambda: self._show_page(1))
        mission_layout.addWidget(mission_button)

        row.addWidget(mission_card, 1)

        location_card, location_layout = self._card(tr("overview.current_location"))

        self.current_system_value = QLabel("–", objectName="cardValue")
        self.current_system_value.setWordWrap(True)
        location_layout.addWidget(self.current_system_value)

        self.current_place_value = QLabel("–", objectName="muted")
        self.current_place_value.setWordWrap(True)
        location_layout.addWidget(self.current_place_value)

        explorer_button = QPushButton(
            tr("overview.open_in_explorer"), objectName="primary"
        )
        explorer_button.clicked.connect(lambda: self._show_page(2))
        location_layout.addWidget(explorer_button)

        row.addWidget(location_card, 1)
        page_layout.addLayout(row)

        status_card, status_layout = self._card(tr("overview.latest_status"))

        self.overview_status = QLabel(tr("overview.no_journal_data"))
        self.overview_status.setWordWrap(True)
        status_layout.addWidget(self.overview_status)

        page_layout.addWidget(status_card)

        recent_card, recent_layout = self._card("Letzte Systeme")

        recent_header = QHBoxLayout()
        recent_header.addWidget(QLabel("Anzahl:", objectName="muted"))

        self.recent_systems_count_spin = QSpinBox()
        self.recent_systems_count_spin.setRange(3, 50)
        self.recent_systems_count_spin.setSingleStep(1)

        try:
            recent_count = int(
                self.state.settings.value(
                    "overview_recent_systems_count",
                    10,
                )
                or 10
            )
        except (TypeError, ValueError):
            recent_count = 10

        self.recent_systems_count_spin.setValue(max(3, min(50, recent_count)))
        self.recent_systems_count_spin.valueChanged.connect(
            self._recent_systems_count_changed
        )

        recent_header.addWidget(self.recent_systems_count_spin)
        recent_header.addStretch()
        recent_layout.addLayout(recent_header)

        self.recent_systems_table = QTableWidget(0, 2)
        self.recent_systems_table.setHorizontalHeaderLabels(["Zeit", "System"])
        self.recent_systems_table.setAlternatingRowColors(True)
        self.recent_systems_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_systems_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_systems_table.setSelectionMode(QTableWidget.SingleSelection)
        self.recent_systems_table.verticalHeader().setVisible(False)
        self.recent_systems_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.recent_systems_table.horizontalHeader().setStretchLastSection(True)
        self.recent_systems_table.setColumnWidth(0, 150)
        self.recent_systems_table.setMinimumHeight(150)

        recent_layout.addWidget(self.recent_systems_table)

        page_layout.addWidget(recent_card, 1)

        return page

    def _recent_systems_count_changed(self, value):
        value = max(3, min(50, int(value or 10)))
        self.state.settings.setValue(
            "overview_recent_systems_count",
            value,
        )
        self.state.settings.sync()
        self._refresh_recent_systems()

    def _refresh_recent_systems(self):
        if not hasattr(self, "recent_systems_table"):
            return

        limit = 10
        if hasattr(self, "recent_systems_count_spin"):
            limit = int(self.recent_systems_count_spin.value())

        try:
            visits = self.state.database.recent_system_visits(limit)
        except Exception:
            visits = []

        self.recent_systems_table.setRowCount(len(visits))

        for row, visit in enumerate(visits):
            visited_at = self._format_timestamp(visit.get("visited_at") or "")
            system_name = visit.get("system_name") or "–"

            time_item = QTableWidgetItem(visited_at)
            system_item = QTableWidgetItem(system_name)

            self.recent_systems_table.setItem(row, 0, time_item)
            self.recent_systems_table.setItem(row, 1, system_item)

    def _explorer(self):
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(10, 6, 10, 6)
        page_layout.setSpacing(6)

        page_layout.addWidget(QLabel(tr("explorer.title"), objectName="sectionTitle"))

        system_card, system_layout = self._card(tr("explorer.current_system"))

        self.system_scan_header = QLabel(
            tr("explorer.no_system_data"), objectName="muted"
        )
        self.system_scan_header.setWordWrap(True)
        self.system_scan_header.setToolTip(tr("explorer.scan_tooltip"))
        system_layout.addWidget(self.system_scan_header)

        self.system_bio_header = QLabel(
            tr("explorer.no_completed_bio"), objectName="muted"
        )
        self.system_bio_header.setWordWrap(True)
        self.system_bio_header.setToolTip(tr("explorer.bio_tooltip"))
        system_layout.addWidget(self.system_bio_header)

        self.unsold_explorer_header = QLabel(
            tr("explorer.unsold_initial"), objectName="muted"
        )
        self.unsold_explorer_header.setWordWrap(True)
        # Offene, noch nicht verkaufte Explorer-Werte deutlich hervorheben.
        self.unsold_explorer_header.setStyleSheet("color: #ffb000; font-weight: 700;")
        self.unsold_explorer_header.setToolTip(tr("explorer.unsold_tooltip"))
        system_layout.addWidget(self.unsold_explorer_header)

        overview_row = QHBoxLayout()
        overview_row.addStretch()

        self.system_overview_button = QPushButton(tr("explorer.show_all"))
        self.system_overview_button.setToolTip(tr("explorer.show_all_tooltip"))
        self.system_overview_button.clicked.connect(self._show_system_overview)
        overview_row.addWidget(self.system_overview_button)

        system_layout.addLayout(overview_row)

        legend_frame = QFrame()
        legend_frame.setObjectName("card")

        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(12, 7, 12, 7)
        legend_layout.setSpacing(18)

        gold_threshold = self._explorer_value_yellow_threshold()

        legend_items = [
            ("BIO ×N", tr("explorer.legend_bio"), "#66e36a"),
            ("GEO ×N", tr("explorer.legend_geo"), "#28c9e8"),
            ("T", tr("explorer.legend_terraforming"), "#4bb8ff"),
            ("★", tr("explorer.legend_first_discovery"), "#ffae28"),
            ("◉", tr("explorer.first_mapping_possible"), "#68c7ff"),
            ("◉✓", tr("explorer.first_mapping_claimed"), "#68c7ff"),
            ("◎", tr("explorer.self_mapped"), "#65d067"),
            ("⌄", tr("explorer.landable"), "#d8dde3"),
            (
                "★",
                tr(
                    "explorer.gold_frame_from",
                    value=self._format_reward(gold_threshold),
                ),
                "#ffb000",
            ),
        ]

        for symbol, text, color in legend_items:
            item = QLabel(
                f'<span style="color:{color}; font-size:14px; '
                f'font-weight:700;">{symbol}</span> '
                f'<span style="font-size:11px;">{text}</span>'
            )
            item.setTextFormat(Qt.RichText)
            item.setWordWrap(False)

            if str(text).startswith(tr("explorer.gold_frame_prefix")):
                self.gold_frame_legend_label = item

            legend_layout.addWidget(item)

        legend_layout.addStretch()
        system_layout.addWidget(legend_frame)

        self.system_map = SystemMapWidget()
        self.system_map.set_light_mode(self.ui_theme == "light")
        self.system_map.bodyClicked.connect(self._show_body_details)

        self.system_scroll = QScrollArea()
        self.system_scroll.setWidgetResizable(False)
        self.system_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.system_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.system_scroll.setFrameShape(QFrame.NoFrame)
        self.system_scroll.setWidget(self.system_map)

        # Neben der grafischen Karte zwei kompakte Textansichten:
        # - Werte: Planeten/Monde nach aktuellem Kartographiewert
        # - BIO/GEO: alle Körper mit biologischen oder geologischen Signalen
        self.explorer_tabs = QTabWidget()
        self.explorer_tabs.addTab(self.system_scroll, tr("explorer.system_map"))

        self.explorer_value_table = QTableWidget(0, 8)
        self.explorer_value_table.setHorizontalHeaderLabels(
            [
                tr("explorer.col_body"),
                tr("explorer.col_type"),
                tr("explorer.col_distance"),
                tr("explorer.col_scan_value"),
                tr("explorer.col_current_value"),
                "Möglicher Wert",
                tr("explorer.col_mapping"),
                tr("explorer.col_status"),
            ]
        )
        self.explorer_value_table.setAlternatingRowColors(True)
        self.explorer_value_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.explorer_value_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.explorer_value_table.setSelectionMode(QTableWidget.SingleSelection)
        self.explorer_value_table.verticalHeader().setVisible(False)
        self.explorer_value_table.setSortingEnabled(False)
        self.explorer_value_table.itemDoubleClicked.connect(
            self._explorer_table_body_activated
        )
        value_header = self.explorer_value_table.horizontalHeader()
        value_header.setSectionResizeMode(QHeaderView.Interactive)
        value_header.setStretchLastSection(True)
        self.explorer_value_table.setColumnWidth(0, 180)
        self.explorer_value_table.setColumnWidth(1, 210)
        self.explorer_value_table.setColumnWidth(2, 105)
        self.explorer_value_table.setColumnWidth(3, 125)
        self.explorer_value_table.setColumnWidth(4, 145)
        self.explorer_value_table.setColumnWidth(5, 235)
        self.explorer_value_table.setColumnWidth(6, 150)

        self.explorer_tabs.addTab(
            self.explorer_value_table,
            tr("explorer.value_list"),
        )

        self.explorer_bio_table = QTableWidget(0, 10)
        self.explorer_bio_table.setHorizontalHeaderLabels(
            [
                tr("explorer.col_body"),
                tr("explorer.col_type"),
                "BIO",
                "GEO",
                tr("explorer.col_bio_findings"),
                tr("explorer.col_bio_value"),
                tr("explorer.col_distance"),
                tr("explorer.col_visited"),
                tr("explorer.col_analysis"),
                tr("explorer.col_status"),
            ]
        )
        self.explorer_bio_table.setAlternatingRowColors(True)
        self.explorer_bio_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.explorer_bio_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.explorer_bio_table.setSelectionMode(QTableWidget.SingleSelection)
        self.explorer_bio_table.verticalHeader().setVisible(False)
        self.explorer_bio_table.setSortingEnabled(False)
        self.explorer_bio_table.itemDoubleClicked.connect(
            self._explorer_table_body_activated
        )
        bio_header = self.explorer_bio_table.horizontalHeader()
        bio_header.setSectionResizeMode(QHeaderView.Interactive)
        bio_header.setStretchLastSection(True)
        self.explorer_bio_table.setColumnWidth(0, 140)
        self.explorer_bio_table.setColumnWidth(1, 160)
        self.explorer_bio_table.setColumnWidth(2, 50)
        self.explorer_bio_table.setColumnWidth(3, 310)
        self.explorer_bio_table.setColumnWidth(4, 330)
        self.explorer_bio_table.setColumnWidth(5, 130)
        self.explorer_bio_table.setColumnWidth(6, 100)
        self.explorer_bio_table.setColumnWidth(7, 95)
        self.explorer_bio_table.setColumnWidth(8, 110)

        self.explorer_tabs.addTab(
            self.explorer_bio_table,
            tr("explorer.bio_planets"),
        )

        system_layout.addWidget(self.explorer_tabs, 1)
        page_layout.addWidget(system_card, 1)

        return page

    @staticmethod
    def _explorer_body_name(body):
        return body.get("short_name") or body.get("name") or "?"

    @staticmethod
    def _explorer_distance_text(body):
        value = body.get("distance_ls")
        if value is None:
            return "–"
        try:
            number = f"{float(value):,.1f}"
            if get_language() == "de":
                number = number.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"{number} ls"
        except Exception:
            return "–"

    @staticmethod
    def _explorer_body_visited(body):
        """
        'Besucht' bedeutet hier: CMDRHelper hat eigene Journaldaten zu
        diesem Körper. Reine EDSM-Ergänzungen gelten nicht als besucht.
        """
        return bool(body.get("journal_scanned", False))

    @staticmethod
    def _translate_volcanism(value):
        """
        Frontiers internen/englischen Vulkanismus-Text über die vorhandenen
        i18n-Schlüssel übersetzen. Unbekannte Werte bleiben als Fallback
        unverändert sichtbar.
        """
        raw = str(value or "").strip()
        if not raw:
            return ""

        normalized = raw.casefold().replace("-", " ").replace("_", " ")
        normalized = " ".join(normalized.split())

        strength_key = None

        if normalized.startswith("major "):
            strength_key = "body_detail.volcanism.major"
            normalized = normalized[6:].strip()
        elif normalized.startswith("minor "):
            strength_key = "body_detail.volcanism.minor"
            normalized = normalized[6:].strip()

        if normalized.endswith(" volcanism"):
            normalized = normalized[:-10].strip()

        kind_keys = {
            "water geysers": "body_detail.volcanism.water_geysers",
            "silicate vapour geysers": "body_detail.volcanism.silicate_vapour_geysers",
            "silicate vapor geysers": "body_detail.volcanism.silicate_vapour_geysers",
            "rocky magma": "body_detail.volcanism.rocky_magma",
            "metallic magma": "body_detail.volcanism.metallic_magma",
            "carbon dioxide geysers": "body_detail.volcanism.carbon_dioxide_geysers",
            "water magma": "body_detail.volcanism.water_magma",
            "ammonia magma": "body_detail.volcanism.ammonia_magma",
            "methane magma": "body_detail.volcanism.methane_magma",
            "nitrogen magma": "body_detail.volcanism.nitrogen_magma",
        }

        kind_key = kind_keys.get(normalized)
        if not kind_key:
            return raw

        kind = tr(kind_key)

        if strength_key:
            return tr(strength_key, kind=kind)

        return kind

    @staticmethod
    def _explorer_geo_text(body, with_count=True):
        """
        GEO-Anzeige aus den bereits vorhandenen Journaldaten bilden.

        Der konkrete Vulkanismus wird über tr() übersetzt, damit die Anzeige
        der in CMDRHelper gewählten Sprache folgt.
        """
        geo_count = max(0, int(body.get("geological_signals") or 0))
        volcanism = MainWindow._translate_volcanism(body.get("volcanism"))

        if not volcanism:
            return f"GEO ×{geo_count}" if with_count and geo_count > 0 else "–"

        if with_count and geo_count > 0:
            return f"GEO ×{geo_count} · {volcanism}"

        return volcanism

    @staticmethod
    def _explorer_bio_progress(body):
        """
        BIO-Fortschritt direkt aus den am Körper gespeicherten Journaldaten
        ableiten. Dadurch aktualisiert sich die BIO-Liste unmittelbar nach
        SAASignalsFound/FSSBodySignals und später nach ScanOrganic.
        """
        biology = list(body.get("biology") or [])

        found = len(biology)
        completed = 0

        for entry in biology:
            if not isinstance(entry, dict):
                continue

            scan_type = (
                str(entry.get("scan_type") or entry.get("ScanType") or "")
                .strip()
                .casefold()
            )

            if scan_type in ("analyse", "analyze"):
                completed += 1

        # Fallback für ältere/ergänzte Datenstände.
        found = max(
            found,
            int(
                body.get("bio_found_count")
                or body.get("biology_found_count")
                or body.get("bio_species_count")
                or 0
            ),
        )

        completed = max(
            completed,
            int(
                body.get("bio_completed_count")
                or body.get("biology_completed_count")
                or body.get("bio_analyzed_count")
                or body.get("bio_analysed_count")
                or 0
            ),
        )

        analysed = bool(
            completed > 0
            or body.get("bio_complete")
            or body.get("biology_complete")
            or body.get("bio_analyzed")
            or body.get("bio_analysed")
        )

        return found, completed, analysed

    @staticmethod
    def _explorer_bio_names(body):
        """
        BIO-Namen samt aktuellem Genetic-Sampler-Schritt liefern.

        Frontier verwendet bei ScanOrganic:
        - Log      = 1. Probe
        - Sample   = 2. Probe
        - Analyse/Analyze = 3. Probe, vollständig

        Sobald ScanOrganic eine konkrete Art/Variante einer Gattung kennt,
        wird der vorher nur vom DSS bekannte allgemeine Gattungsname nicht
        zusätzlich angezeigt.
        """
        entries = []
        seen = set()
        concrete_genuses = set()

        for entry in body.get("biology") or []:
            if not isinstance(entry, dict):
                continue

            name = (
                entry.get("variant") or entry.get("species") or entry.get("genus") or ""
            )
            name = str(name or "").strip()

            if not name:
                continue

            canonical = name.casefold()
            if canonical in seen:
                continue

            scan_type = str(
                entry.get("scan_type") or entry.get("ScanType") or ""
            ).strip()

            entries.append((name, scan_type))
            seen.add(canonical)

            # Der erste Namensbestandteil ist bei Elite-BIO-Namen die
            # Gattung, z. B. "Stratum Paleas - Lime" -> "stratum".
            genus_name = str(entry.get("genus") or "").strip()
            genus_key = (
                genus_name.casefold()
                if genus_name
                else (canonical.split()[0] if canonical.split() else canonical)
            )
            if genus_key:
                concrete_genuses.add(genus_key)

        # DSS/FSS kann bereits alle Genuses kennen, obwohl noch keine
        # ScanOrganic-Probe genommen wurde. Nur noch nicht konkretisierte
        # Gattungen ergänzen.
        for name in body.get("bio_genuses") or []:
            name = str(name or "").strip()
            if not name:
                continue

            canonical = name.casefold()
            genus_key = canonical.split()[0] if canonical.split() else canonical

            if genus_key in concrete_genuses:
                continue
            if canonical in seen:
                continue

            entries.append((name, ""))
            seen.add(canonical)

        return entries

    @staticmethod
    def _explorer_bio_names_html(entries):
        """
        Farbcodierung je BIO-Fund:
        grau  = nur per DSS bekannt, noch nicht beprobt
        weiß  = 1. Probe (Log)
        gelb  = 2. Probe (Sample)
        grün  = 3. Probe / Analyse vollständig
        """
        from html import escape

        parts = []

        for name, scan_type in entries:
            scan_key = str(scan_type or "").strip().casefold()

            if scan_key in ("analyse", "analyze"):
                color = "#65d067"
                title = tr("explorer.sample3_confirmed")
            elif scan_key == "sample":
                color = "#ffb000"
                title = tr("explorer.sample2_taken")
            elif scan_key == "log":
                color = "#f1f3f5"
                title = tr("explorer.sample1_taken")
            else:
                color = "#8e969e"
                title = tr("explorer.dss_fss_only")

            parts.append(
                f'<span style="color:{color};" title="{escape(title)}">'
                f"{escape(str(name))}</span>"
            )

        return ", ".join(parts) if parts else "–"

    def _explorer_bio_known_value(self, body, learned_values=None):
        """
        Summiert die bereits eindeutig bestimmten BIO-Arten dieses Körpers.

        Schon nach der ersten ScanOrganic-Probe kennt Elite die Art/Variante,
        daher kann der Basiswert sofort angezeigt werden. Nur per DSS bekannte
        Gattungen haben noch keinen eindeutigen Artenwert.

        Eigene aus SellOrganicData gelernte Werte haben Vorrang vor der
        statischen Referenztabelle.
        """
        learned_values = learned_values or {}
        learned_folded = {
            str(key).casefold(): int(value or 0)
            for key, value in learned_values.items()
        }

        total = 0
        seen = set()

        for entry in body.get("biology") or []:
            if not isinstance(entry, dict):
                continue

            canonical = str(species_name(entry) or "").strip()
            if not canonical:
                continue

            key = canonical.casefold()
            if key in seen:
                continue
            seen.add(key)

            value = int(learned_folded.get(key, 0) or 0)
            if value <= 0:
                value = int(base_value(entry) or 0)

            total += max(0, value)

        return int(total)

    def _explorer_table_body_activated(self, item):
        body = item.data(Qt.UserRole)
        if isinstance(body, dict):
            self._show_body_details(body)

    def _refresh_explorer_tables(self):
        bodies = list(getattr(self.state, "system_bodies", None) or [])

        # Sterne und Belt Cluster sind für die gewünschte Wertliste nicht
        # relevant. Planeten und Monde nach dem noch erreichbaren Wert
        # absteigend, damit lohnende DSS-Ziele oben stehen.
        value_bodies = [
            body
            for body in bodies
            if not body.get("star_type")
            and body.get("body_type") != "Star"
            and not SystemMapWidget._is_belt_cluster(body)
        ]
        value_bodies.sort(
            key=lambda body: (
                -int(body.get("possible_value") or body.get("current_value") or 0),
                str(self._explorer_body_name(body)).lower(),
            )
        )

        self.explorer_value_table.setRowCount(len(value_bodies))

        for row, body in enumerate(value_bodies):
            visited = self._explorer_body_visited(body)
            self_mapped = bool(body.get("self_mapped"))
            current_value = int(body.get("current_value") or 0)

            was_mapped = body.get("was_mapped")

            # Frontier liefert WasMapped beim Scan als Zustand VOR unserer
            # eigenen DSS-Kartierung. self_mapped zeigt dagegen, dass wir
            # später selbst SurfaceScanComplete erhalten haben.
            if self_mapped:
                mapping_text = "✓ " + tr("explorer.self_mapped")
                status = tr("explorer.status_scanned_self_mapped")
            elif was_mapped is True:
                mapping_text = tr("explorer.already_mapped")
                status = (
                    tr("explorer.status_scanned_already_mapped")
                    if visited
                    else tr("explorer.already_mapped_cap")
                )
            elif was_mapped is False:
                mapping_text = "○ " + tr("explorer.first_mapping_possible")
                status = (
                    tr("explorer.status_scanned_first_mapping")
                    if visited
                    else tr("explorer.first_mapping_possible")
                )
            else:
                mapping_text = "–"
                status = (
                    tr("explorer.scanned") if visited else tr("explorer.not_scanned")
                )

            possible_value = int(body.get("possible_value") or current_value or 0)
            possible_value_without_eff = int(
                body.get("possible_value_without_efficiency") or possible_value or 0
            )
            possible_value_text = (
                f"{self._format_reward(possible_value)} / "
                f"{self._format_reward(possible_value_without_eff)}"
            )

            values = [
                self._explorer_body_name(body),
                SystemMapWidget._type_text(body),
                self._explorer_distance_text(body),
                self._format_reward(body.get("scan_value", 0)),
                self._format_reward(current_value),
                possible_value_text,
                mapping_text,
                status,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, body)

                # Zahlenwerte auch intern numerisch hinterlegen.
                if col == 4:
                    item.setData(Qt.UserRole + 1, current_value)

                # Grün bleibt der aktuell bereits erreichte Wert.
                # Der einstellbare Schwellenwert bewertet dagegen ab jetzt
                # den noch erreichbaren Kartographiewert.
                if col == 4:
                    item.setForeground(QColor("#65d067"))
                    item.setToolTip(tr("explorer.current_value_tooltip"))
                elif col == 5:
                    yellow_threshold = self._explorer_value_yellow_threshold()

                    if yellow_threshold > 0 and possible_value >= yellow_threshold:
                        item.setForeground(QColor("#ffb000"))
                    else:
                        item.setForeground(QColor("#d9dde1"))

                    item.setData(Qt.UserRole + 1, possible_value)
                    item.setToolTip(
                        "Noch erreichbarer Wert: mit Effizienzbonus / "
                        "ohne Effizienzbonus"
                    )
                elif col == 6:
                    if self_mapped:
                        item.setForeground(QColor("#65d067"))
                    elif was_mapped is False:
                        item.setForeground(QColor("#68c7ff"))
                    elif was_mapped is True:
                        item.setForeground(QColor("#9aa3ab"))
                elif col == 7:
                    if not visited:
                        item.setForeground(QColor("#9aa3ab"))

                self.explorer_value_table.setItem(row, col, item)

        # BIO/GEO-Körper gemeinsam. Auch reine GEO-Körper werden hier
        # angezeigt; Körper mit beiden Signalarten erscheinen nur einmal.
        bio_bodies = [
            body
            for body in value_bodies
            if (
                int(body.get("biological_signals") or 0) > 0
                or int(body.get("geological_signals") or 0) > 0
            )
        ]
        bio_bodies.sort(
            key=lambda body: (
                self._explorer_body_visited(body),
                -(
                    int(body.get("biological_signals") or 0)
                    + int(body.get("geological_signals") or 0)
                ),
                -int(body.get("current_value") or 0),
                str(self._explorer_body_name(body)).lower(),
            )
        )

        self.explorer_bio_table.setRowCount(len(bio_bodies))

        try:
            learned_bio_values = self.state.database.learned_bio_values()
        except Exception:
            learned_bio_values = {}

        for row, body in enumerate(bio_bodies):
            visited = self._explorer_body_visited(body)
            signals = int(body.get("biological_signals") or 0)
            geo_signals = int(body.get("geological_signals") or 0)
            found, completed, analysed = self._explorer_bio_progress(body)
            bio_names = self._explorer_bio_names(body)
            bio_names_text = self._explorer_bio_names_html(bio_names)
            known_bio_value = self._explorer_bio_known_value(
                body,
                learned_bio_values,
            )
            first_footfall = bool(body.get("first_footfall"))
            if known_bio_value > 0:
                bio_value_text = self._format_reward(known_bio_value)
                if first_footfall:
                    bio_value_text += (
                        f" / {self._format_reward(known_bio_value * 5)} möglich"
                    )
            else:
                bio_value_text = "–"

            if analysed:
                analysis_text = (
                    tr("explorer.completed_count", count=completed)
                    if completed
                    else tr("explorer.complete")
                )
                status = tr("explorer.bio_analyzed")
            elif visited:
                analysis_text = (
                    tr("explorer.recorded_count", count=found)
                    if found
                    else tr("explorer.open")
                )
                status = tr("explorer.visited_bio_open")
            else:
                # Direkt nach dem DSS-/Signalscan steht die Anzahl der
                # biologischen Signale bereits fest, auch wenn der Körper
                # noch nicht angeflogen wurde.
                analysis_text = tr("explorer.signal_count", count=signals)
                status = tr("explorer.bio_found_not_visited")

            values = [
                self._explorer_body_name(body),
                SystemMapWidget._type_text(body),
                str(signals) if signals > 0 else "–",
                self._explorer_geo_text(body) if geo_signals > 0 else "–",
                bio_names_text if signals > 0 else "–",
                bio_value_text if signals > 0 else "–",
                self._explorer_distance_text(body),
                tr("explorer.visited") if visited else tr("explorer.open_cap"),
                analysis_text if signals > 0 else tr("explorer.open"),
                status if signals > 0 else tr("explorer.open"),
            ]

            for col, value in enumerate(values):
                # BIO-Funde brauchen Rich Text, damit jeder Name einzeln
                # entsprechend seinem Scan-Fortschritt eingefärbt werden kann.
                if col == 4:
                    label = QLabel()
                    label.setTextFormat(Qt.RichText)
                    label.setText(str(value))
                    label.setTextInteractionFlags(Qt.NoTextInteraction)
                    label.setContentsMargins(8, 0, 4, 0)
                    label.setToolTip(tr("explorer.bio_colors_tooltip"))
                    self.explorer_bio_table.setCellWidget(row, col, label)
                    continue

                item = QTableWidgetItem(str(value))

                if col == 5 and known_bio_value > 0 and first_footfall:
                    item.setToolTip(
                        f"Erstbetretung erkannt: möglicher BIO-Wert "
                        f"{self._format_reward(known_bio_value * 5)}"
                    )
                item.setData(Qt.UserRole, body)

                if analysed:
                    item.setForeground(QColor("#65d067"))
                elif visited:
                    item.setForeground(QColor("#ffb000"))
                else:
                    item.setForeground(QColor("#d9dde1"))

                self.explorer_bio_table.setItem(row, col, item)

        self.explorer_tabs.setTabText(
            1,
            tr("explorer.value_list_count", count=len(value_bodies)),
        )
        self.explorer_tabs.setTabText(
            2,
            f"BIO / GEO ({len(bio_bodies)})",
        )

    def _ensure_explorer_live_windows(self):
        if self._explorer_value_live_window is None:
            self._explorer_value_live_window = ExplorerLiveListWindow(
                tr("explorer.live_valuable_title"),
                [
                    tr("explorer.col_body"),
                    tr("explorer.col_type"),
                    tr("explorer.col_value"),
                    tr("explorer.col_mapping"),
                ],
                self.state.settings,
                "explorer_live/value_geometry",
                self,
                window_kind="value",
            )

        if self._explorer_bio_live_window is None:
            self._explorer_bio_live_window = ExplorerLiveListWindow(
                tr("explorer.live_bio_title"),
                [
                    tr("explorer.col_body"),
                    "BIO / GEO",
                    tr("explorer.col_progress"),
                    tr("explorer.col_value"),
                ],
                self.state.settings,
                "explorer_live/bio_geometry",
                self,
                window_kind="bio",
            )

    def _refresh_explorer_live_windows(self):
        """Aktualisiert die beiden kleinen Explorer-Livefenster."""
        system_name = str(getattr(self.state, "system", "") or "")
        bodies = list(getattr(self.state, "system_bodies", None) or [])

        # Beim Systemwechsel alte Treffer sofort ausblenden. Erst neue
        # qualifizierende Scans lassen die Fenster wieder erscheinen.
        system_changed = self._explorer_live_system != system_name
        self._explorer_live_system = system_name

        if system_changed:
            # Beim Eintritt in ein anderes System beide alten Livefenster
            # sofort schließen und leeren. Dieser Refresh wird anschließend
            # beendet, damit Restdaten aus dem vorherigen System das Fenster
            # nicht im selben Zyklus wieder öffnen können.
            if self._explorer_value_live_window is not None:
                self._explorer_value_live_window.hide()
                self._explorer_value_live_window.table.setRowCount(0)

            if self._explorer_bio_live_window is not None:
                self._explorer_bio_live_window.hide()
                self._explorer_bio_live_window.table.setRowCount(0)

            return

        threshold = self._explorer_value_yellow_threshold()
        valuable_rows = []
        for body in bodies:
            if body.get("star_type") or body.get("body_type") == "Star":
                continue
            if SystemMapWidget._is_belt_cluster(body):
                continue

            value = int(body.get("possible_value") or body.get("current_value") or 0)
            if threshold <= 0 or value < threshold:
                continue

            # Im kleinen Livefenster "Wertvolle Körper" erledigte Ziele
            # ausblenden. Die normale Werteliste im Explorer bleibt erhalten.
            if body.get("self_mapped"):
                continue

            if body.get("self_mapped"):
                mapping = tr("explorer.self_mapped")
            elif body.get("was_mapped") is True:
                mapping = tr("explorer.already_mapped")
            elif body.get("was_mapped") is False:
                mapping = tr("explorer.first_mapping_possible")
            else:
                mapping = "–"

                valuable_rows.append(
                    (
                        self._explorer_body_name(body),
                        SystemMapWidget._type_text(body),
                        self._format_reward(value),
                        mapping,
                    )
                )

        valuable_rows.sort(
            key=lambda row: -int(str(row[2]).replace(" Cr", "").replace(".", "") or 0)
        )

        try:
            learned_bio_values = self.state.database.learned_bio_values()
        except Exception:
            learned_bio_values = {}

        bio_rows = []
        for body in bodies:
            signals = int(body.get("biological_signals") or 0)
            geo_signals = int(body.get("geological_signals") or 0)

            # GEO gilt für das kleine Live-Popup als "erledigt", sobald der
            # betreffende Körper erfolgreich mit dem DSS kartographiert wurde.
            # SAAScanComplete setzt dafür self_mapped=True.
            # Die normale BIO/GEO-Ansicht im Explorer bleibt davon unberührt.
            geo_pending = geo_signals > 0 and not bool(body.get("self_mapped"))

            if signals <= 0 and not geo_pending:
                continue

            names = self._explorer_bio_names(body)

            species_rows = []
            seen_species = set()

            # Zuerst konkrete ScanOrganic-Arten aufnehmen.
            concrete_genuses = set()

            for raw_name, scan_type in names:
                raw_name = str(raw_name or "").strip()
                scan_type = str(scan_type or "").strip()

                if not raw_name or not scan_type:
                    continue

                canonical = raw_name.casefold()
                if canonical in seen_species:
                    continue
                seen_species.add(canonical)

                # Der erste Wortbestandteil entspricht bei den bekannten
                # Elite-BIO-Namen der Gattung, z. B.
                # "Bacterium Vesicula - Lime" -> "bacterium".
                genus_key = canonical.split()[0] if canonical.split() else canonical
                if genus_key:
                    concrete_genuses.add(genus_key)

                entry_for_value = None
                for bio_entry in body.get("biology") or []:
                    if not isinstance(bio_entry, dict):
                        continue
                    candidate = str(
                        bio_entry.get("variant")
                        or bio_entry.get("species")
                        or bio_entry.get("genus")
                        or ""
                    ).strip()
                    if candidate.casefold() == canonical:
                        entry_for_value = bio_entry
                        break

                single_value = 0
                if entry_for_value is not None:
                    canonical_species = str(species_name(entry_for_value) or "").strip()
                    if canonical_species:
                        try:
                            single_value = int(
                                learned_bio_values.get(canonical_species, 0) or 0
                            )
                        except Exception:
                            single_value = 0
                        if single_value <= 0:
                            single_value = int(base_value(entry_for_value) or 0)

                species_rows.append(
                    {
                        "name": raw_name,
                        "scan_type": scan_type,
                        "value": max(0, single_value),
                    }
                )

            # Danach DSS/FSS-Gattungen ergänzen. Genau das fehlte bislang:
            # Nach dem Oberflächenscan kann Elite z. B. schon "Bacterium"
            # melden, obwohl noch keine ScanOrganic-Probe genommen wurde.
            # Sobald eine konkrete Art dieser Gattung bekannt ist, wird der
            # allgemeine Gattungsname nicht zusätzlich angezeigt.
            for raw_name, scan_type in names:
                raw_name = str(raw_name or "").strip()
                scan_type = str(scan_type or "").strip()

                if not raw_name or scan_type:
                    continue

                canonical = raw_name.casefold()
                genus_key = canonical.split()[0] if canonical.split() else canonical

                if genus_key in concrete_genuses:
                    continue
                if canonical in seen_species:
                    continue

                seen_species.add(canonical)

                species_rows.append(
                    {
                        "name": raw_name,
                        "scan_type": "",
                        "value": 0,
                    }
                )

            # Im BIO-Popup nur noch offene BIO-Körper anzeigen.
            # Sind alle gemeldeten BIO-Signale vollständig analysiert
            # (z. B. 3/3 oder 4/4), verschwindet der Körper aus diesem
            # Livefenster. Die normale BIO/GEO-Ansicht bleibt unverändert.
            total_bio_count = max(signals, len(species_rows))
            completed_bio_count = sum(
                1
                for entry in species_rows
                if str(entry.get("scan_type") or "").strip().casefold()
                in ("analyse", "analyze")
            )

            bio_complete = (
                signals > 0
                and total_bio_count > 0
                and len(species_rows) >= total_bio_count
                and completed_bio_count >= total_bio_count
            )

            # Ist BIO vollständig, verschwindet nur der BIO-Anteil.
            # Ein noch nicht DSS-kartierter GEO-Anteil desselben Körpers
            # bleibt dagegen im Popup sichtbar.
            if bio_complete and not geo_pending:
                continue

            popup_signals = 0 if bio_complete else signals
            popup_species_rows = [] if bio_complete else species_rows

            known_value = sum(
                int(entry.get("value") or 0) for entry in popup_species_rows
            )

            bio_rows.append(
                {
                    "body_name": self._explorer_body_name(body),
                    # BIO und GEO bewusst getrennt halten:
                    # Die bestehende BIO-Fortschrittslogik darf ausschließlich
                    # biologische Signale auswerten.
                    "signals": popup_signals,
                    "geo_signals": geo_signals if geo_pending else 0,
                    "geo_text": (self._explorer_geo_text(body) if geo_pending else "–"),
                    "species": popup_species_rows,
                    "known_value": known_value,
                }
            )

        self._ensure_explorer_live_windows()

        self._explorer_value_live_window.set_rows(system_name, valuable_rows)
        self._explorer_bio_live_window.set_rows(system_name, bio_rows)

        value_live_enabled = self._explorer_live_window_enabled("value")
        bio_live_enabled = self._explorer_live_window_enabled("bio")

        if value_live_enabled and valuable_rows:
            if not self._explorer_value_live_window.isVisible():
                self._explorer_value_live_window.show()
                self._explorer_value_live_window.raise_()
        elif self._explorer_value_live_window.isVisible():
            self._explorer_value_live_window.hide()

        if bio_live_enabled and bio_rows:
            if not self._explorer_bio_live_window.isVisible():
                self._explorer_bio_live_window.show()
                self._explorer_bio_live_window.raise_()
        elif self._explorer_bio_live_window.isVisible():
            self._explorer_bio_live_window.hide()

    def _show_system_overview(self):
        bodies = list(
            getattr(
                self.state,
                "system_bodies",
                None,
            )
            or []
        )

        if not bodies:
            QMessageBox.information(
                self,
                tr("explorer.show_all"),
                tr("explorer.no_body_data"),
            )
            return

        if self._system_overview_window is not None:
            try:
                self._system_overview_window.close()
            except Exception:
                pass

        self._system_overview_window = SystemOverviewDialog(
            system_name=(
                getattr(
                    self.state,
                    "system",
                    None,
                )
                or tr("explorer.current_system")
            ),
            bodies=bodies,
            source_map=self.system_map,
            on_body_clicked=self._focus_system_body,
            parent=self,
        )

        self._system_overview_window.show()
        self._system_overview_window.raise_()
        self._system_overview_window.activateWindow()

    def _focus_system_body(self, body):
        if not hasattr(
            self,
            "system_scroll",
        ):
            return

        (
            positions,
            _children,
            _families,
            _used_units,
            _depth_count,
        ) = self.system_map._tree_layout()

        body_pos = positions.get(id(body))

        if body_pos is None:
            return

        center_x = float(body_pos["x"]) + float(self.system_map.BODY_W) / 2.0

        center_y = float(body_pos["y"]) + float(self.system_map.BODY_H) / 2.0

        viewport = self.system_scroll.viewport()

        self.system_scroll.horizontalScrollBar().setValue(
            int(center_x - viewport.width() / 2.0)
        )

        self.system_scroll.verticalScrollBar().setValue(
            int(center_y - viewport.height() / 2.0)
        )

    def _score_page(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(7)

        header = QHBoxLayout()
        header.addWidget(
            QLabel(
                tr("score.title"),
                objectName="sectionTitle",
            )
        )
        header.addStretch()
        layout.addLayout(header)

        intro = QLabel(
            tr("score.intro"),
            objectName="muted",
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        target_card, target_layout = self._card(tr("score.what_find"))

        target_row = QHBoxLayout()

        target_row.addWidget(QLabel(tr("score.target") + ":"))

        self.score_target_combo = QComboBox()
        self.score_target_combo.setMinimumWidth(430)
        self.score_target_combo.setToolTip(tr("score.target_tooltip"))
        target_row.addWidget(
            self.score_target_combo,
            1,
        )

        self.score_min_samples_spin = QSpinBox()
        self.score_min_samples_spin.setRange(
            1,
            50,
        )
        self.score_min_samples_spin.setValue(3)
        self.score_min_samples_spin.setPrefix(tr("score.min_prefix"))
        self.score_min_samples_spin.setSuffix(tr("score.systems_suffix"))
        self.score_min_samples_spin.setToolTip(tr("score.min_samples_tooltip"))
        target_row.addWidget(self.score_min_samples_spin)

        self.score_refresh_button = QPushButton(
            tr("score.refresh"),
            objectName="primary",
        )
        self.score_refresh_button.setToolTip(tr("score.refresh_tooltip"))
        self.score_refresh_button.clicked.connect(self._refresh_score_page)
        target_row.addWidget(self.score_refresh_button)

        target_layout.addLayout(target_row)

        self.score_target_summary = QLabel(
            "–",
            objectName="muted",
        )
        self.score_target_summary.setWordWrap(True)
        target_layout.addWidget(self.score_target_summary)

        layout.addWidget(target_card)

        ranking_card, ranking_layout = self._card(tr("score.prefer_codes"))

        ranking_hint = QLabel(
            tr("score.ranking_hint"),
            objectName="muted",
        )
        ranking_hint.setWordWrap(True)
        ranking_layout.addWidget(ranking_hint)

        self.score_ranking_table = QTableWidget(
            0,
            5,
        )
        self.score_ranking_table.setHorizontalHeaderLabels(
            [
                tr("score.col_rank"),
                tr("score.col_code"),
                tr("score.col_success"),
                tr("score.col_hit_rate"),
                tr("score.col_recommendation"),
            ]
        )
        self.score_ranking_table.setAlternatingRowColors(True)
        self.score_ranking_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.score_ranking_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.score_ranking_table.setSelectionMode(QTableWidget.SingleSelection)
        self.score_ranking_table.verticalHeader().setVisible(False)

        ranking_header = self.score_ranking_table.horizontalHeader()
        ranking_header.setSectionResizeMode(QHeaderView.Interactive)
        ranking_header.setStretchLastSection(True)

        self.score_ranking_table.setColumnWidth(
            0,
            65,
        )
        self.score_ranking_table.setColumnWidth(
            1,
            180,
        )
        self.score_ranking_table.setColumnWidth(
            2,
            150,
        )
        self.score_ranking_table.setColumnWidth(
            3,
            130,
        )
        self.score_ranking_table.setColumnWidth(
            4,
            300,
        )

        ranking_layout.addWidget(
            self.score_ranking_table,
            1,
        )

        layout.addWidget(
            ranking_card,
            2,
        )

        self.score_status_label = QLabel(
            "",
            objectName="muted",
        )
        self.score_status_label.setWordWrap(True)
        layout.addWidget(self.score_status_label)

        self._score_load_targets()

        self.score_target_combo.currentIndexChanged.connect(self._score_target_changed)
        self.score_min_samples_spin.valueChanged.connect(self._score_options_changed)

        QTimer.singleShot(
            0,
            self._refresh_score_page,
        )

        return page

    def _score_load_targets(self):
        if not hasattr(
            self,
            "score_target_combo",
        ):
            return

        current_key = self.score_target_combo.currentData()

        self.score_target_combo.blockSignals(True)
        self.score_target_combo.clear()

        try:
            targets = self._score_analyzer().available_targets()
        except Exception:
            targets = []

        # "Gesamt" ist für die Rückwärts-Suche nicht sinnvoll:
        # Der Benutzer soll genau angeben, WAS er finden möchte.
        targets = [
            target for target in targets if str(target.get("key") or "") != "overall"
        ]

        for target in targets:
            self.score_target_combo.addItem(
                str(target.get("label") or target.get("key") or ""),
                str(target.get("key") or ""),
            )

        if current_key:
            index = self.score_target_combo.findData(current_key)
            if index >= 0:
                self.score_target_combo.setCurrentIndex(index)

        self.score_target_combo.blockSignals(False)

    def _score_target_key(self):
        if not hasattr(
            self,
            "score_target_combo",
        ):
            return "bio_any"

        return str(self.score_target_combo.currentData() or "bio_any")

    def _score_target_changed(self):
        self._score_mark_pending()

    def _score_options_changed(self, _value=None):
        self._score_mark_pending()

    def _score_mark_pending(self):
        if not hasattr(self, "score_target_summary"):
            return

        target_label = (
            self.score_target_combo.currentText().strip()
            if hasattr(self, "score_target_combo")
            else ""
        )

        self.score_target_summary.setText(
            tr(
                "score.pending_selection",
                target=target_label or "–",
            )
        )
        self.score_target_summary.setTextFormat(Qt.RichText)

        if hasattr(self, "score_status_label"):
            self.score_status_label.setText(tr("score.pending_status"))

    @staticmethod
    def _score_percent(value):
        try:
            text = f"{float(value) * 100:.1f} %"
            if get_language() == "de":
                text = text.replace(".", ",")
            return text
        except Exception:
            return "–"

    @staticmethod
    def _score_color(score):
        score = int(score or 0)

        if score >= 75:
            return QColor("#65d067")
        if score >= 60:
            return QColor("#a6df71")
        if score >= 40:
            return QColor("#d9dde1")
        if score >= 25:
            return QColor("#ffb000")

        return QColor("#e06a6a")

    def _score_analyzer(self):
        return ScoreAnalyzer(self.state.database)

    def _score_make_target_table(
        self,
        first_header,
    ):
        table = QTableWidget(
            0,
            6,
        )
        table.setHorizontalHeaderLabels(
            [
                first_header,
                tr("score.systems"),
                tr("score.hits"),
                tr("score.col_hit_rate"),
                tr("score.finds"),
                tr("score.score"),
            ]
        )
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.verticalHeader().setVisible(False)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        table.setColumnWidth(
            0,
            220,
        )
        table.setColumnWidth(
            1,
            90,
        )
        table.setColumnWidth(
            2,
            90,
        )
        table.setColumnWidth(
            3,
            110,
        )
        table.setColumnWidth(
            4,
            90,
        )

        return table

    def _score_fill_target_table(
        self,
        table,
        rows,
        limit=None,
    ):
        rows = list(rows or [])

        if limit is not None:
            rows = rows[: int(limit)]

        table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row.get(
                    "key",
                    "–",
                ),
                int(row.get("systems") or 0),
                int(row.get("hits") or 0),
                self._score_percent(row.get("rate")),
                int(row.get("finds") or 0),
                int(row.get("score") or 0),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if col == 5:
                    item.setForeground(self._score_color(row.get("score")))

                table.setItem(
                    row_index,
                    col,
                    item,
                )

    def _refresh_score_page(self):
        if not hasattr(
            self,
            "score_ranking_table",
        ):
            return

        target_key = self._score_target_key()

        try:
            min_samples = int(self.score_min_samples_spin.value())
        except Exception:
            min_samples = 3

        try:
            result = self._score_analyzer().jump_recommendations(
                target_key,
                min_samples=min_samples,
                limit=50,
            )
        except Exception as exc:
            self.score_status_label.setText(tr("score.failed", error=exc))
            self.score_ranking_table.setRowCount(0)
            return

        recommendations = list(result.get("recommendations") or [])

        self.score_ranking_table.setRowCount(len(recommendations))

        for row_index, row in enumerate(recommendations):
            stars = int(row.get("stars") or 0)

            values = [
                int(row.get("rank") or (row_index + 1)),
                str(row.get("key") or "–"),
                str(row.get("success_text") or "–"),
                self._score_percent(row.get("rate")),
                str(row.get("recommendation_text") or "–"),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if col == 1:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                    if row_index == 0:
                        item.setForeground(QColor("#65d067"))

                elif col == 2:
                    item.setToolTip(tr("score.success_tooltip"))

                elif col == 4:
                    if stars >= 5:
                        color = QColor("#65d067")
                    elif stars >= 4:
                        color = QColor("#a6df71")
                    elif stars >= 3:
                        color = QColor("#d9dde1")
                    elif stars >= 2:
                        color = QColor("#ffb000")
                    else:
                        color = QColor("#e06a6a")

                    item.setForeground(color)

                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                    item.setToolTip(tr("score.recommendation_tooltip"))

                self.score_ranking_table.setItem(
                    row_index,
                    col,
                    item,
                )

        target_label = str(result.get("target_label") or "–")

        if recommendations:
            top = recommendations[:5]
            preferred = ", ".join(str(row.get("key") or "–") for row in top)

            best = recommendations[0]

            self.score_target_summary.setText(
                tr(
                    "score.summary_with_best",
                    target=target_label,
                    preferred=preferred,
                    best=best.get("key", "–"),
                    success=best.get("success_text", "–"),
                    rate=self._score_percent(best.get("rate")),
                )
            )
        else:
            self.score_target_summary.setText(
                tr(
                    "score.summary_no_result",
                    target=target_label,
                )
            )

        self.score_target_summary.setTextFormat(Qt.RichText)

        self.score_status_label.setText(
            tr(
                "score.data_basis",
                systems=int(result.get("systems") or 0),
                hits=int(result.get("hits") or 0),
                finds=int(result.get("finds") or 0),
                min_samples=min_samples,
            )
        )

    def _chronicle(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.addWidget(QLabel(tr("chronicle.title"), objectName="sectionTitle"))

        self.chronicle_search_edit = QLineEdit()
        self.chronicle_search_edit.setPlaceholderText(
            tr("chronicle.search_placeholder")
        )
        self.chronicle_search_edit.setMinimumWidth(280)
        self.chronicle_search_edit.returnPressed.connect(self._search_chronicle_biology)
        header.addWidget(self.chronicle_search_edit)

        search_button = QPushButton(tr("chronicle.search"))
        search_button.clicked.connect(self._search_chronicle_biology)
        header.addWidget(search_button)

        reset_button = QPushButton(tr("chronicle.reset"))
        reset_button.clicked.connect(self._reset_chronicle_search)
        header.addWidget(reset_button)

        align_button = QPushButton(tr("chronicle.align"))
        align_button.clicked.connect(self._align_chronicle_galaxy)
        header.addWidget(align_button)

        current_position_button = QPushButton("⌖  Aktuelle Position")
        current_position_button.setToolTip("Aktuelles System in der Chronik anzeigen")
        current_position_button.clicked.connect(self._show_current_chronicle_position)
        header.addWidget(current_position_button)

        self.chronicle_legend_button = QPushButton(tr("chronicle.search_help"))
        self.chronicle_legend_button.clicked.connect(self._open_chronicle_search_help)
        header.addWidget(self.chronicle_legend_button)

        header.addStretch()

        refresh = QPushButton(tr("chronicle.refresh"), objectName="primary")
        refresh.clicked.connect(self._refresh_chronicle)
        header.addWidget(refresh)

        layout.addLayout(header)

        map_card, map_layout = self._card(tr("chronicle.visited_systems"))

        self.chronicle_status = QLabel("", objectName="muted")
        self.chronicle_status.setWordWrap(True)
        map_layout.addWidget(self.chronicle_status)

        self.chronicle_map = ChronicleMapWidget()
        self.chronicle_map.systemClicked.connect(self._chronicle_system_clicked)
        map_layout.addWidget(self.chronicle_map, 1)

        self.chronicle_detail = QLabel(
            tr("chronicle.no_system_selected"), objectName="muted"
        )
        self.chronicle_detail.setWordWrap(True)
        map_layout.addWidget(self.chronicle_detail)

        # BIO-Suchergebnisse bleiben bewusst in der Chronik.
        self.chronicle_search_results = QListWidget()
        self.chronicle_search_results.setVisible(False)
        self.chronicle_search_results.setMaximumHeight(190)
        self.chronicle_search_results.itemClicked.connect(
            self._chronicle_search_result_clicked
        )
        map_layout.addWidget(self.chronicle_search_results)

        layout.addWidget(map_card, 1)

        QTimer.singleShot(0, self._refresh_chronicle)

        return page

    def _refresh_chronicle(self):
        if hasattr(self, "chronicle_search_results"):
            self.chronicle_search_results.clear()
            self.chronicle_search_results.setVisible(False)

        try:
            systems = self.state.database.chronicle_systems()
        except Exception as exc:
            systems = []
            self.chronicle_status.setText(tr("chronicle.load_failed", error=exc))
        else:
            self.chronicle_status.setText(
                tr("chronicle.map_status", count=len(systems))
            )
        self.chronicle_map.set_systems(systems)
        self._mark_current_chronicle_system()

    def _mark_current_chronicle_system(self):
        """Übergibt das aktuelle Journal-System an die Chronik-Karte."""
        if not hasattr(self, "chronicle_map"):
            return

        current_system = str(getattr(self.state, "system", "") or "").strip()

        if hasattr(self.chronicle_map, "set_current_system"):
            self.chronicle_map.set_current_system(current_system)

    def _show_current_chronicle_position(self):
        """Setzt die Chronik zurück und springt zum aktuell besuchten System."""
        if not hasattr(self, "chronicle_map"):
            return

        if hasattr(self, "chronicle_search_edit"):
            self.chronicle_search_edit.clear()

        if hasattr(self, "chronicle_search_results"):
            self.chronicle_search_results.clear()
            self.chronicle_search_results.setVisible(False)

        try:
            systems = self.state.database.chronicle_systems()
        except Exception as exc:
            self.chronicle_status.setText(tr("chronicle.load_failed", error=exc))
            return

        self.chronicle_map.set_systems(systems)
        self._mark_current_chronicle_system()

        if hasattr(self.chronicle_map, "focus_current_system"):
            self.chronicle_map.focus_current_system()

        current_system = str(getattr(self.state, "system", "") or "").strip()
        self.chronicle_status.setText(
            f"Aktuelle Position: {current_system}"
            if current_system
            else "Aktuelle Position unbekannt"
        )

    def _align_chronicle_galaxy(self):
        if hasattr(self, "chronicle_map"):
            self.chronicle_map.align_galaxy()

    def _open_chronicle_search_help(self):
        try:
            groups = self.state.database.chronicle_search_terms()
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr("chronicle.search_help"),
                tr("chronicle.search_help_failed", error=exc),
            )
            return

        # Feste Schnellsuchen vor die dynamischen Datenbank-Kategorien setzen.
        merged = {
            tr("chronicle.quick_search"): [
                "Terraforming",
                "BIO",
                "GEO",
                "Water world",
                "Earthlike",
                "Ammonia world",
                "FSS-Signal",
            ]
        }

        merged.update(groups or {})

        # Vorhandenes Fenster wiederverwenden, wenn es schon offen ist.
        if self._chronicle_search_help_window is not None:
            try:
                self._chronicle_search_help_window.close()
            except Exception:
                pass

        self._chronicle_search_help_window = ChronicleSearchHelpDialog(
            groups=merged,
            on_term_clicked=self._chronicle_search_term_clicked,
            parent=self,
        )

        # Nicht modal: Chronik bleibt weiter bedienbar.
        self._chronicle_search_help_window.show()
        self._chronicle_search_help_window.raise_()
        self._chronicle_search_help_window.activateWindow()

    def _chronicle_search_term_clicked(
        self,
        term,
    ):
        self.chronicle_search_edit.setText(str(term))
        self._search_chronicle_biology()

    def _search_chronicle_biology(self):
        query = self.chronicle_search_edit.text().strip()

        if not query:
            self._reset_chronicle_search()
            return

        try:
            results = self.state.database.search_chronicle(query)
        except Exception as exc:
            self.chronicle_status.setText(tr("chronicle.search_failed", error=exc))
            return

        self.chronicle_search_results.clear()

        if not results:
            self.chronicle_search_results.setVisible(False)
            self.chronicle_status.setText(tr("chronicle.no_results", query=query))
            # Die normale Reisekarte bleibt sichtbar.
            return

        systems_by_address = {}

        for result in results:
            address = result.get("system_address")

            if address in systems_by_address:
                continue

            systems_by_address[address] = {
                "system_address": address,
                "name": result.get("system_name") or "",
                "x": result.get("x"),
                "y": result.get("y"),
                "z": result.get("z"),
                "first_seen": result.get("system_first_seen") or "",
                "last_seen": result.get("system_last_seen") or "",
                "body_count": int(result.get("body_count") or 0),
                "visits": 0,
            }

        matching_systems = [
            system
            for system in systems_by_address.values()
            if (
                system.get("x") is not None
                and system.get("y") is not None
                and system.get("z") is not None
            )
        ]

        # Während der Suche zeigt die Karte ausschließlich die Systeme
        # mit passenden biologischen Funden.
        self.chronicle_map.set_systems(matching_systems)

        for result in results:
            kind = result.get("kind") or tr("chronicle.hit")
            match_name = (
                result.get("match_name") or result.get("detail") or tr("chronicle.hit")
            )

            system_name = result.get("system_name") or "Unbekannt"

            body_name = result.get("short_name") or result.get("body_name") or ""

            parts = [f"[{kind}]", system_name]

            if body_name:
                parts.append(body_name)

            parts.append(str(match_name))

            item = QListWidgetItem("  ·  ".join(parts))

            item.setData(Qt.UserRole, result)

            self.chronicle_search_results.addItem(item)

        self.chronicle_search_results.setVisible(True)

        self.chronicle_status.setText(
            tr(
                "chronicle.results_summary",
                results=len(results),
                systems=len(systems_by_address),
                query=query,
            )
        )

    def _reset_chronicle_search(self):
        if hasattr(self, "chronicle_search_edit"):
            self.chronicle_search_edit.clear()

        if hasattr(self, "chronicle_search_results"):
            self.chronicle_search_results.clear()
            self.chronicle_search_results.setVisible(False)

        self._refresh_chronicle()

    def _chronicle_search_result_clicked(
        self,
        item,
    ):
        result = item.data(Qt.UserRole)

        if not isinstance(result, dict):
            return

        system = {
            "system_address": result.get("system_address"),
            "name": (result.get("system_name") or ""),
            "x": result.get("x"),
            "y": result.get("y"),
            "z": result.get("z"),
            "first_seen": result.get("system_first_seen") or "",
            "last_seen": result.get("system_last_seen") or "",
            "body_count": int(result.get("body_count") or 0),
            "visits": 0,
        }

        body_name = result.get("short_name") or result.get("body_name") or ""

        match_name = (
            result.get("match_name") or result.get("detail") or tr("chronicle.hit")
        )

        kind = result.get("kind") or tr("chronicle.hit")

        hit_parts = [kind]

        if body_name:
            hit_parts.append(body_name)

        hit_parts.append(str(match_name))

        self._chronicle_system_clicked(
            system,
            hit_text=tr("chronicle.hit_prefix") + " " + " – ".join(hit_parts),
        )

    def _chronicle_system_clicked(
        self,
        system,
        hit_text="",
    ):
        name = system.get("name") or tr("chronicle.unknown")
        address = system.get("system_address")

        self.chronicle_detail.setText(
            tr(
                "chronicle.system_detail",
                name=name,
                visits=system.get("visits", 0),
                bodies=system.get("body_count", 0),
                first=self._format_timestamp(system.get("first_seen")),
                last=self._format_timestamp(system.get("last_seen")),
                x=float(system.get("x") or 0),
                y=float(system.get("y") or 0),
                z=float(system.get("z") or 0),
            )
        )

        try:
            details = self.state.database.chronicle_system_details(address)
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr("chronicle.title"),
                tr("chronicle.system_data_failed", name=name, error=exc),
            )
            return

        bodies = details.get("bodies") or []

        bio_bodies = sum(
            1 for body in bodies if int(body.get("biological_signals") or 0) > 0
        )

        geo_bodies = sum(
            1 for body in bodies if int(body.get("geological_signals") or 0) > 0
        )

        header_text = tr("chronicle.stored_bodies", count=len(bodies))
        if bio_bodies:
            header_text += tr("chronicle.bio_on_bodies", count=bio_bodies)
        if geo_bodies:
            header_text += tr("chronicle.geo_on_bodies", count=geo_bodies)
        if hit_text:
            header_text += f" · {hit_text}"
        header_text += tr("chronicle.click_body_details")

        # Vorheriges Chronik-Systemfenster schließen, damit immer nur
        # ein historisches Systemfenster gleichzeitig offen bleibt.
        if self._chronicle_system_window is not None:
            try:
                self._chronicle_system_window.close()
            except Exception:
                pass

        self._chronicle_system_window = ChronicleSystemWindow(
            system_name=name,
            bodies=bodies,
            header_text=header_text,
            body_callback=self._show_body_details,
            parent=self,
        )

        self._chronicle_system_window.system_map.set_light_mode(
            self.ui_theme == "light"
        )

        # Nicht modal: Die Chronik-Karte bleibt weiter bedienbar.
        self._chronicle_system_window.show()
        self._chronicle_system_window.raise_()
        self._chronicle_system_window.activateWindow()

    def _show_body_details(self, body):
        dialog = BodyDetailWindow(body, self)
        dialog.exec()

    def _save_overview_splitter(self, pos, index):
        if not hasattr(self, "overview_splitter"):
            return

        self.state.settings.setValue(
            "overview_splitter_sizes", self.overview_splitter.sizes()
        )

    def reset_overview_splitter(self):
        if not hasattr(self, "overview_splitter"):
            return

        self.overview_splitter.setSizes([220, 675])

        self.state.settings.setValue("overview_splitter_sizes", [220, 675])

    def _missions(self):
        page = QWidget()

        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        header = QHBoxLayout()

        header.addWidget(QLabel(tr("missions.title"), objectName="sectionTitle"))

        header.addStretch()

        refresh = QPushButton(tr("missions.refresh_journal"), objectName="primary")

        refresh.clicked.connect(self.state.refresh)

        header.addWidget(refresh)

        reset_missions = QPushButton(tr("missions.reset"))
        reset_missions.clicked.connect(self._reset_missions)
        header.addWidget(reset_missions)

        layout.addLayout(header)

        card, card_layout = self._card(tr("missions.active"))

        mission_summary_row = QHBoxLayout()

        self.mission_total_reward_label = QLabel(
            tr("missions.total_reward", value="0 Cr"), objectName="cardValue"
        )
        self.mission_total_reward_label.setToolTip(tr("missions.total_reward_tooltip"))

        mission_summary_row.addWidget(self.mission_total_reward_label)
        mission_summary_row.addStretch()

        card_layout.addLayout(mission_summary_row)

        self.missions_table = QTableWidget(0, 7)

        self.missions_table.setHorizontalHeaderLabels(
            [
                tr("missions.col_mission"),
                tr("missions.col_system"),
                tr("missions.col_place"),
                tr("missions.col_status"),
                tr("missions.col_next_step"),
                tr("missions.col_reward"),
                tr("missions.col_expiry"),
            ]
        )

        self.missions_table.setAlternatingRowColors(True)

        self.missions_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.missions_table.verticalHeader().setVisible(False)

        header_view = self.missions_table.horizontalHeader()

        # Alle Missionsspalten dürfen vom Benutzer mit der Maus
        # frei in der Breite verändert werden.
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setStretchLastSection(False)

        self.missions_table.setColumnWidth(0, 260)

        self.missions_table.setColumnWidth(1, 210)

        self.missions_table.setColumnWidth(2, 260)

        self.missions_table.setColumnWidth(3, 155)

        self.missions_table.setColumnWidth(4, 300)

        self.missions_table.setColumnWidth(5, 125)

        self.missions_table.setColumnWidth(6, 170)

        # Gespeicherte Spaltenbreiten nach den Standardwerten
        # wiederherstellen. saveState() speichert die komplette
        # Header-Konfiguration robust als QByteArray.
        saved_header_state = self.state.settings.value("missions_table_header_state")
        if saved_header_state is not None:
            try:
                header_view.restoreState(saved_header_state)
            except Exception:
                pass

        # Jede Änderung durch Ziehen einer Spaltengrenze sofort speichern.
        header_view.sectionResized.connect(self._save_missions_header_state)

        self.missions_table.itemSelectionChanged.connect(
            self._mission_selection_changed
        )

        card_layout.addWidget(self.missions_table)

        layout.addWidget(card, 1)

        detail_card, detail_layout = self._card(tr("missions.details"))

        self.mission_detail_title = QLabel(tr("missions.none_selected"))

        self.mission_detail_title.setStyleSheet("font-size: 15px; font-weight: 700;")

        detail_layout.addWidget(self.mission_detail_title)

        self.mission_detail_text = QLabel(tr("missions.select_above"))

        self.mission_detail_text.setWordWrap(True)

        self.mission_detail_text.setObjectName("muted")

        detail_layout.addWidget(self.mission_detail_text)

        self.mission_progress_text = QLabel("")

        self.mission_progress_text.setWordWrap(True)

        detail_layout.addWidget(self.mission_progress_text)

        layout.addWidget(detail_card)

        return page

    def _save_missions_header_state(self, logical_index, old_size, new_size):
        if not hasattr(self, "missions_table"):
            return

        self.state.settings.setValue(
            "missions_table_header_state",
            self.missions_table.horizontalHeader().saveState(),
        )

    def _settings(self):
        # Die Einstellungsseite kann inzwischen höher als das Hauptfenster
        # werden. Deshalb liegt der komplette Inhalt in einem Scrollbereich.
        page = QWidget()

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        layout.addWidget(QLabel(tr("settings.title"), objectName="sectionTitle"))

        card, card_layout = self._card(tr("settings.journal"))

        form = QFormLayout()

        self.journal_path_edit = QLineEdit()
        self.journal_path_edit.setReadOnly(True)

        self.journal_file_count = QLabel("0")

        self.journal_oldest_file = QLabel("–")
        self.journal_oldest_file.setWordWrap(True)

        self.journal_newest_file = QLabel("–")
        self.journal_newest_file.setWordWrap(True)

        self.journal_newest_name = QLabel("–")
        self.journal_newest_name.setWordWrap(True)

        self.journal_last_read = QLabel("–")
        self.journal_last_read.setWordWrap(True)

        form.addRow(tr("settings.journal_folder") + ":", self.journal_path_edit)

        form.addRow(tr("settings.journal_files_found") + ":", self.journal_file_count)

        form.addRow(tr("settings.oldest_journal") + ":", self.journal_oldest_file)

        form.addRow(tr("settings.newest_journal") + ":", self.journal_newest_file)

        form.addRow(tr("settings.newest_file") + ":", self.journal_newest_name)

        form.addRow(tr("settings.last_read_entry") + ":", self.journal_last_read)

        card_layout.addLayout(form)

        buttons = QHBoxLayout()

        choose = QPushButton(tr("settings.choose_journal_folder"))

        choose.clicked.connect(self.choose_journal_folder)

        buttons.addWidget(choose)

        refresh = QPushButton(tr("settings.read_now"), objectName="primary")

        refresh.clicked.connect(self.state.refresh)

        buttons.addWidget(refresh)
        buttons.addStretch()

        card_layout.addLayout(buttons)

        layout.addWidget(card)

        online_card, online_layout = self._card(tr("settings.online_services"))

        online_layout.addWidget(
            QLabel(
                tr("settings.online_hint"),
                objectName="muted",
            )
        )

        # -----------------------------
        # EDSM
        # -----------------------------
        edsm_title = QLabel("EDSM")
        edsm_title.setStyleSheet("font-weight: 700;")
        online_layout.addWidget(edsm_title)

        edsm_form = QFormLayout()

        self.edsm_commander_edit = QLineEdit()
        self.edsm_commander_edit.setText(self.state.edsm_commander)
        self.edsm_commander_edit.setPlaceholderText(tr("settings.commander_name"))

        self.edsm_api_key_edit = QLineEdit()
        self.edsm_api_key_edit.setText(self.state.edsm_api_key)
        self.edsm_api_key_edit.setEchoMode(QLineEdit.Password)
        self.edsm_api_key_edit.setPlaceholderText(tr("settings.edsm_api_key"))

        self.edsm_enabled_check = QCheckBox(tr("settings.use_edsm"))
        self.edsm_enabled_check.setChecked(self.state.edsm_enabled)

        edsm_form.addRow(tr("settings.commander_name") + ":", self.edsm_commander_edit)
        edsm_form.addRow(tr("settings.api_key") + ":", self.edsm_api_key_edit)
        edsm_form.addRow("", self.edsm_enabled_check)

        online_layout.addLayout(edsm_form)

        edsm_test_row = QHBoxLayout()

        self.edsm_test_button = QPushButton(tr("settings.test_edsm"))
        self.edsm_test_button.clicked.connect(self._test_edsm_connection)
        edsm_test_row.addWidget(self.edsm_test_button)

        self.edsm_test_status = QLabel(tr("settings.not_tested"), objectName="muted")
        self.edsm_test_status.setWordWrap(True)
        edsm_test_row.addWidget(self.edsm_test_status, 1)

        online_layout.addLayout(edsm_test_row)

        # -----------------------------
        # Inara
        # -----------------------------
        inara_title = QLabel("Inara")
        inara_title.setStyleSheet("font-weight: 700;")
        online_layout.addWidget(inara_title)

        inara_form = QFormLayout()

        self.inara_commander_edit = QLineEdit()
        self.inara_commander_edit.setText(self.state.inara_commander)
        self.inara_commander_edit.setPlaceholderText(tr("settings.commander_name"))

        self.inara_api_key_edit = QLineEdit()
        self.inara_api_key_edit.setText(self.state.inara_api_key)
        self.inara_api_key_edit.setEchoMode(QLineEdit.Password)
        self.inara_api_key_edit.setPlaceholderText(tr("settings.inara_api_key"))

        self.inara_enabled_check = QCheckBox(tr("settings.use_inara"))
        self.inara_enabled_check.setChecked(self.state.inara_enabled)

        inara_form.addRow(
            tr("settings.commander_name") + ":", self.inara_commander_edit
        )
        inara_form.addRow(tr("settings.api_key") + ":", self.inara_api_key_edit)
        inara_form.addRow("", self.inara_enabled_check)

        online_layout.addLayout(inara_form)

        inara_test_row = QHBoxLayout()

        self.inara_test_button = QPushButton(tr("settings.test_inara"))
        self.inara_test_button.clicked.connect(self._test_inara_connection)
        inara_test_row.addWidget(self.inara_test_button)

        self.inara_test_status = QLabel(tr("settings.not_tested"), objectName="muted")
        self.inara_test_status.setWordWrap(True)
        inara_test_row.addWidget(self.inara_test_status, 1)

        online_layout.addLayout(inara_test_row)

        save_online = QPushButton(tr("settings.save_online"), objectName="primary")
        save_online.clicked.connect(self._save_online_settings)
        online_layout.addWidget(save_online)

        layout.addWidget(online_card)

        database_card, database_layout = self._card(tr("settings.database"))

        database_layout.addWidget(
            QLabel(
                tr("settings.database_hint"),
                objectName="muted",
            )
        )

        self.database_status_label = QLabel(
            tr("settings.database_loading"), objectName="muted"
        )
        self.database_status_label.setWordWrap(True)
        database_layout.addWidget(self.database_status_label)

        self.database_progress_bar = QProgressBar()
        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(0)
        self.database_progress_bar.setTextVisible(True)
        self.database_progress_bar.setFormat(tr("settings.ready"))
        self.database_progress_bar.setVisible(False)
        database_layout.addWidget(self.database_progress_bar)

        self.database_progress_file = QLabel("", objectName="muted")
        self.database_progress_file.setWordWrap(True)
        self.database_progress_file.setVisible(False)
        database_layout.addWidget(self.database_progress_file)

        database_buttons = QHBoxLayout()

        self.database_import_button = QPushButton(tr("settings.import_archive"))
        self.database_import_button.clicked.connect(self._import_journal_archive)
        database_buttons.addWidget(self.database_import_button)

        database_buttons.addStretch()
        database_layout.addLayout(database_buttons)

        layout.addWidget(database_card)

        self.state.databaseImportProgress.connect(self._database_import_progress)
        self.state.databaseImportFinished.connect(self._database_import_finished)

        self._refresh_database_status()

        update_card, update_layout = self._card(tr("settings.update"))

        update_form = QFormLayout()

        self.update_current_version = QLabel(__version__)
        self.update_status_label = QLabel(
            tr("settings.not_checked"), objectName="muted"
        )
        self.update_status_label.setWordWrap(True)

        update_form.addRow(
            tr("settings.installed_version") + ":", self.update_current_version
        )
        update_form.addRow(tr("settings.github_status") + ":", self.update_status_label)

        update_layout.addLayout(update_form)

        update_row = QHBoxLayout()

        self.update_check_button = QPushButton(tr("settings.check_now"))
        self.update_check_button.clicked.connect(
            lambda: self._check_for_updates(automatic=False)
        )
        update_row.addWidget(self.update_check_button)
        update_row.addStretch()

        update_layout.addLayout(update_row)

        layout.addWidget(update_card)

        ui_card, ui_layout = self._card(tr("settings.interface"))

        theme_row = QHBoxLayout()

        theme_row.addWidget(QLabel(tr("settings.appearance") + ":"))

        self.theme_group = QButtonGroup(self)

        self.theme_dark_radio = QRadioButton(tr("settings.dark"))
        self.theme_light_radio = QRadioButton(tr("settings.light"))

        self.theme_group.addButton(self.theme_dark_radio)
        self.theme_group.addButton(self.theme_light_radio)

        if self.ui_theme == "light":
            self.theme_light_radio.setChecked(True)
        else:
            self.theme_dark_radio.setChecked(True)

        self.theme_dark_radio.toggled.connect(
            lambda checked: (self._set_theme("dark") if checked else None)
        )

        self.theme_light_radio.toggled.connect(
            lambda checked: (self._set_theme("light") if checked else None)
        )

        theme_row.addWidget(self.theme_dark_radio)
        theme_row.addWidget(self.theme_light_radio)
        theme_row.addStretch()

        ui_layout.addLayout(theme_row)

        language_row = QHBoxLayout()
        language_row.addWidget(QLabel(tr("settings.language") + ":"))

        self.ui_language_combo = QComboBox()

        # Sprachname bewusst jeweils in der eigenen Sprache anzeigen.
        # Der gespeicherte Sprachcode liegt als Item-Data vor, damit die
        # Auswahl unabhängig von Reihenfolge und sichtbarem Text bleibt.
        languages = [
            ("Deutsch", "de"),
            ("English", "en"),
            ("Français", "fr"),
            ("Italiano", "it"),
            ("Norsk (Bokmål)", "no"),
            ("Svenska", "sv"),
            ("Suomi", "fi"),
            ("Polski", "pl"),
            ("Nederlands", "nl"),
            ("Español", "es"),
            ("Türkçe", "tr"),
            ("Ελληνικά", "el"),
        ]

        for label, code in languages:
            self.ui_language_combo.addItem(label, code)

        active_language = get_language()
        language_index = self.ui_language_combo.findData(active_language)
        if language_index >= 0:
            self.ui_language_combo.setCurrentIndex(language_index)

        self.ui_language_save_button = QPushButton(tr("settings.save_language"))
        self.ui_language_save_button.clicked.connect(self._save_ui_language_settings)

        self.ui_language_status = QLabel("", objectName="muted")

        language_row.addWidget(self.ui_language_combo)
        language_row.addWidget(self.ui_language_save_button)
        language_row.addWidget(self.ui_language_status)
        language_row.addStretch()
        ui_layout.addLayout(language_row)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel(tr("settings.font") + ":"))

        self.ui_font_combo = QFontComboBox()
        self.ui_font_combo.setMinimumWidth(260)
        self.ui_font_combo.setToolTip(tr("settings.font_tooltip"))

        app = QApplication.instance()
        current_font = app.font() if app is not None else QFont()

        saved_family = str(
            self.state.settings.value(
                "ui_font_family",
                current_font.family(),
            )
            or current_font.family()
        ).strip()

        saved_size = self._saved_ui_font_size(current_font.pointSize())

        self.ui_font_combo.setCurrentFont(QFont(saved_family))

        font_row.addWidget(self.ui_font_combo)

        font_row.addSpacing(12)
        font_row.addWidget(QLabel(tr("settings.font_size") + ":"))

        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(7, 24)
        self.ui_font_size_spin.setSuffix(" pt")
        self.ui_font_size_spin.setValue(saved_size)
        self.ui_font_size_spin.setToolTip(tr("settings.font_size_tooltip"))
        font_row.addWidget(self.ui_font_size_spin)

        self.ui_font_save_button = QPushButton(tr("settings.save_font"))
        self.ui_font_save_button.clicked.connect(self._save_ui_font_settings)
        font_row.addWidget(self.ui_font_save_button)

        self.ui_font_status = QLabel("", objectName="muted")
        font_row.addWidget(self.ui_font_status)

        font_row.addStretch()
        ui_layout.addLayout(font_row)

        self.ui_font_restart_hint = QLabel(tr("settings.font_restart_hint"))
        self.ui_font_restart_hint.setWordWrap(True)
        self.ui_font_restart_hint.setStyleSheet("color: #ffb000; font-weight: 600;")
        ui_layout.addWidget(self.ui_font_restart_hint)

        value_threshold_row = QHBoxLayout()
        value_threshold_row.addWidget(QLabel(tr("settings.value_threshold") + ":"))

        self.explorer_value_threshold_spin = QSpinBox()
        self.explorer_value_threshold_spin.setRange(0, 2_000_000_000)
        self.explorer_value_threshold_spin.setSingleStep(50_000)
        self.explorer_value_threshold_spin.setSuffix(" Cr")
        self.explorer_value_threshold_spin.setMinimumWidth(160)

        try:
            threshold = int(
                self.state.settings.value(
                    "explorer_value_yellow_threshold",
                    200_000,
                )
                or 200_000
            )
        except (TypeError, ValueError):
            threshold = 200_000

        self.explorer_value_threshold_spin.setValue(max(0, threshold))
        self.explorer_value_threshold_spin.setToolTip(
            tr("settings.value_threshold_tooltip")
        )
        self.explorer_value_threshold_spin.valueChanged.connect(
            self._set_explorer_value_threshold
        )

        value_threshold_row.addWidget(self.explorer_value_threshold_spin)
        value_threshold_row.addStretch()
        ui_layout.addLayout(value_threshold_row)

        layout.addWidget(ui_card)
        layout.addStretch()

        scroll.setWidget(content)
        page_layout.addWidget(scroll, 1)

        return page

    def _refresh_database_status(self):
        if not hasattr(self, "database_status_label"):
            return

        stats = self.state.database_stats()

        self.database_status_label.setText(
            tr(
                "settings.database_stats",
                systems=stats.get("systems", 0),
                bodies=stats.get("bodies", 0),
                materials=stats.get("materials", 0),
                biology=stats.get("biology", 0),
                codex=stats.get("codex_entries", 0),
                journals=stats.get("journal_imports", 0),
            )
        )

    def _import_journal_archive(self):
        self.database_import_button.setEnabled(False)

        self.database_status_label.setText(tr("settings.archive_reading"))

        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(0)
        self.database_progress_bar.setFormat(tr("settings.preparing"))
        self.database_progress_bar.setVisible(True)

        self.database_progress_file.setText(tr("settings.journals_preparing"))
        self.database_progress_file.setVisible(True)

        self.state.import_journal_archive()

    def _database_import_progress(
        self,
        current,
        total,
        name,
    ):
        try:
            current = int(current)
        except Exception:
            current = 0

        try:
            total = int(total)
        except Exception:
            total = 0

        if total > 0:
            percent = int(round((current / total) * 100))
            percent = max(0, min(100, percent))
        else:
            percent = 0

        self.database_status_label.setText(
            tr("settings.archive_progress", current=current, total=total)
        )

        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(percent)
        self.database_progress_bar.setFormat(f"{percent} %   ·   {current} / {total}")
        self.database_progress_bar.setVisible(True)

        self.database_progress_file.setText(tr("settings.current_file", name=name))
        self.database_progress_file.setVisible(True)

    def _database_import_finished(
        self,
        stats,
        error,
    ):
        self.database_import_button.setEnabled(True)

        if error:
            self.database_progress_bar.setRange(0, 100)
            self.database_progress_bar.setValue(0)
            self.database_progress_bar.setFormat(tr("settings.import_failed"))
            self.database_progress_bar.setVisible(True)
            self.database_progress_file.setText("")
            self.database_progress_file.setVisible(False)

            self.database_status_label.setText(
                tr("settings.import_failed_detail", error=error)
            )
            QMessageBox.warning(
                self,
                tr("settings.database"),
                tr("settings.archive_import_failed_message", error=error),
            )
            return

        self._refresh_database_status()

        self.database_progress_bar.setRange(0, 100)
        self.database_progress_bar.setValue(100)
        self.database_progress_bar.setFormat(tr("settings.import_complete"))
        self.database_progress_bar.setVisible(True)

        self.database_progress_file.setText("")
        self.database_progress_file.setVisible(False)

        imported = int(stats.get("imported_journals", 0))
        skipped = int(stats.get("skipped_journals", 0))

        if imported == 0:
            message = tr(
                "settings.archive_no_new_data",
                skipped=skipped,
                systems=stats.get("systems", 0),
                bodies=stats.get("bodies", 0),
                materials=stats.get("materials", 0),
                journals=stats.get("journal_imports", 0),
            )
        else:
            message = tr(
                "settings.archive_import_success",
                imported=imported,
                skipped=skipped,
                systems=stats.get("systems", 0),
                bodies=stats.get("bodies", 0),
                materials=stats.get("materials", 0),
                journals=stats.get("journal_imports", 0),
            )

        QMessageBox.information(self, tr("settings.database"), message)

    def _release_update_worker(self):
        self._update_worker = None

    def _set_update_status(
        self,
        text,
        ok=None,
    ):
        if not hasattr(self, "update_status_label"):
            return

        self.update_status_label.setText(str(text))

        if ok is True:
            self.update_status_label.setObjectName("statusOk")
        elif ok is False:
            self.update_status_label.setObjectName("statusWarn")
        else:
            self.update_status_label.setObjectName("muted")

        self.update_status_label.style().unpolish(self.update_status_label)
        self.update_status_label.style().polish(self.update_status_label)

    @staticmethod
    def _release_requires_database_update(result):
        """
        Ein GitHub-Release kann in den Release-Notes mit

            DB-UPDATE: <Version>

        markieren, dass nach diesem Programmupdate die lokale
        CMDRHelper-Datenbank einmalig neu aufgebaut/aktualisiert wird.

        Ohne diesen Marker erscheint kein Datenbank-Hinweis.
        """
        notes = str((result or {}).get("release_notes") or "")

        return bool(
            re.search(
                r"(?im)^\\s*DB-UPDATE\\s*:\\s*\\d+\\s*$",
                notes,
            )
        )

    def _update_question_text(
        self,
        result,
        latest,
    ):
        text = tr(
            "settings.update_question",
            installed=__version__,
            latest=latest,
        )

        if self._release_requires_database_update(result):
            text += tr("settings.update_database_notice")

        text += tr("settings.update_install_question")
        return text

    def _check_for_updates(
        self,
        automatic=False,
    ):
        if self._update_check_running:
            return

        self._update_check_running = True

        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(False)

        if not automatic:
            self._set_update_status(tr("settings.github_checking"))

        # Worker als Instanzvariable halten. So bleibt das Python-Objekt
        # garantiert bis zum Ende der GitHub-Anfrage erhalten.
        self._update_worker = UpdateCheckWorker(
            owner="Faber38",
            repository="CMDRHelper",
            current_version=__version__,
        )

        self._update_worker.signals.finished.connect(
            lambda result: self._update_check_finished(result, automatic)
        )

        self.update_thread_pool.start(self._update_worker)

    def _update_check_finished(
        self,
        result,
        automatic=False,
    ):
        self._update_check_running = False

        # Erst nach Rückkehr in die Qt-Ereignisschleife freigeben.
        # So wird der Worker nicht während seines finished-Signals zerstört.
        QTimer.singleShot(0, self._release_update_worker)

        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(True)

        if not isinstance(result, dict):
            self._set_update_status(tr("settings.update_check_failed"), False)
            return

        if not result.get("ok"):
            # Beim automatischen Startcheck keine störende Fehlermeldung
            # anzeigen. Der Status bleibt unter Einstellungen sichtbar.
            error = result.get("error") or tr("settings.github_check_failed")

            self._set_update_status(error, False)

            if not automatic:
                QMessageBox.warning(self, tr("settings.update_check_title"), error)
            return

        latest = result.get("version") or ""

        if latest and is_newer_version(
            latest,
            __version__,
        ):
            text = tr(
                "settings.update_available_status", latest=latest, installed=__version__
            )

            self._set_update_status(text, False)

            if automatic and not self._update_notice_shown:
                self._update_notice_shown = True

                answer = QMessageBox.question(
                    self,
                    tr("settings.update_available_title"),
                    self._update_question_text(
                        result,
                        latest,
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if answer == QMessageBox.Yes:
                    self._install_update(result)

            elif not automatic:
                answer = QMessageBox.question(
                    self,
                    tr("settings.update_available_title"),
                    self._update_question_text(
                        result,
                        latest,
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if answer == QMessageBox.Yes:
                    self._install_update(result)

            return

        self._set_update_status(
            tr("settings.update_current_status", version=__version__),
            True,
        )

        if not automatic:
            QMessageBox.information(
                self,
                tr("settings.update_check_title"),
                tr("settings.update_current_message", version=__version__),
            )

    def _install_update(self, result):
        latest = str(result.get("version") or "").strip()

        asset_name = str(result.get("asset_name") or "").strip()

        asset_url = str(result.get("asset_url") or "").strip()

        if not asset_url:
            QMessageBox.warning(
                self,
                tr("settings.update_title"),
                tr("settings.update_no_asset", version=latest),
            )
            return

        self._set_update_status(tr("settings.update_downloading", version=latest))

        if hasattr(self, "update_check_button"):
            self.update_check_button.setEnabled(False)

        QApplication.processEvents()

        try:
            zip_path = download_release(result)

            # main_window.py liegt unter cmdrhelper/ui/.
            # Zwei Ebenen höher liegt das Installationsverzeichnis.
            install_dir = Path(__file__).resolve().parents[2]

            launch_installer(
                zip_path=zip_path,
                install_dir=install_dir,
                current_version=__version__,
                latest_version=latest,
                parent_pid=os.getpid(),
            )

        except Exception as exc:
            if hasattr(self, "update_check_button"):
                self.update_check_button.setEnabled(True)

            self._set_update_status(
                tr("settings.update_failed_status", error=exc), False
            )

            QMessageBox.critical(
                self,
                tr("settings.update_failed_title"),
                tr("settings.update_failed_message", error=exc),
            )
            return

        install_message = tr(
            "settings.update_downloaded_message",
            version=latest,
        )

        if self._release_requires_database_update(result):
            install_message += tr("settings.update_post_restart_database")

        QMessageBox.information(
            self,
            tr("settings.update_title"),
            install_message,
        )

        QApplication.quit()

    def _saved_ui_font_size(self, fallback=10):
        try:
            value = int(
                self.state.settings.value(
                    "ui_font_size",
                    fallback if fallback and fallback > 0 else 10,
                )
                or fallback
                or 10
            )
        except (TypeError, ValueError):
            value = fallback if fallback and fallback > 0 else 10

        return max(7, min(24, int(value)))

    def _font_stylesheet_suffix(self, family=None, size=None):
        """
        Ergänzt die Theme-QSS um die vom Benutzer gewählte Basisschrift.

        QApplication.setFont() allein reicht hier nicht zuverlässig aus,
        weil das CMDRHelper-Stylesheet eigene Font-Angaben enthalten kann.
        Die Theme-Datei setzt die Grundgröße explizit auf QWidget.
        Deshalb muss die Benutzergröße ebenfalls über QWidget gesetzt werden.
        Die Titelgrößen werden proportional zur gewählten Grundgröße angepasst.
        """
        app = QApplication.instance()

        if family is None:
            family = getattr(self, "_active_ui_font_family", "")
        if size is None:
            size = getattr(self, "_active_ui_font_size", 0)

        if not family and app is not None:
            family = app.font().family()

        try:
            size = int(size)
        except (TypeError, ValueError):
            size = 10

        size = max(7, min(24, size or 10))
        safe_family = str(family or "").replace("\\", "\\\\").replace('"', '\\"')

        # WICHTIG:
        # Das Theme setzt seine Grundgröße über "QWidget { font-size: 12px; }".
        # Ein nachgestelltes "*"-Rule ist in Qt nicht spezifisch genug, um
        # diese QWidget-Regel zuverlässig zu überschreiben. Deshalb setzen
        # wir die Benutzergröße ebenfalls explizit auf QWidget.
        #
        # Spezielle Titelregeln (appTitle, commanderTitle, sectionTitle,
        # cardValue) bleiben absichtlich relativ größer als die Grundschrift.
        title_size = max(size + 5, int(round(size * 1.45)))
        section_size = max(size + 1, int(round(size * 1.10)))

        return (
            "\n\n/* CMDRHelper Benutzer-Schrift */\n"
            f'QWidget {{ font-family: "{safe_family}"; font-size: {size}pt; }}\n'
            f'QToolTip {{ font-family: "{safe_family}"; font-size: {size}pt; }}\n'
            f'QLabel#appTitle {{ font-family: "{safe_family}"; '
            f"font-size: {title_size}pt; }}\n"
            f'QLabel#commanderTitle {{ font-family: "{safe_family}"; '
            f"font-size: {title_size}pt; }}\n"
            f'QLabel#cardValue {{ font-family: "{safe_family}"; '
            f"font-size: {title_size}pt; }}\n"
            f'QLabel#sectionTitle {{ font-family: "{safe_family}"; '
            f"font-size: {section_size}pt; }}\n"
        )

    def _apply_saved_ui_font(self):
        app = QApplication.instance()
        if app is None:
            return

        default_font = app.font()

        family = str(
            self.state.settings.value(
                "ui_font_family",
                default_font.family(),
            )
            or default_font.family()
        ).strip()

        size = self._saved_ui_font_size(default_font.pointSize())

        # Aktiver Wert wird beim Programmstart eingefroren. Änderungen in
        # den Einstellungen gelten bewusst erst nach dem nächsten Neustart.
        self._active_ui_font_family = family
        self._active_ui_font_size = size

        app.setFont(QFont(family, size))

        base_stylesheet = (
            LIGHT_STYLESHEET if self.ui_theme == "light" else DARK_STYLESHEET
        )
        app.setStyleSheet(base_stylesheet + self._font_stylesheet_suffix(family, size))

    def _save_ui_font_settings(self):
        family = self.ui_font_combo.currentFont().family()
        size = int(self.ui_font_size_spin.value())

        self.state.settings.setValue("ui_font_family", family)
        self.state.settings.setValue("ui_font_size", size)
        self.state.settings.sync()

        # Nicht sofort anwenden: Einige QSS-Regeln übersteuern die Qt-
        # Standardschrift. Ein sauberer kompletter Neuaufbau beim Neustart
        # vermeidet Mischzustände in bereits existierenden Widgets.
        self.ui_font_status.setText(tr("settings.restart_required"))
        self.ui_font_status.setStyleSheet("color: #ffb000; font-weight: 600;")

    def _save_ui_language_settings(self):
        language = str(self.ui_language_combo.currentData() or "de")
        set_language(language, self.state.settings)

        self.ui_language_status.setText(tr("settings.restart_required"))
        self.ui_language_status.setStyleSheet("color: #ffb000; font-weight: 600;")

    def _set_theme(self, theme):
        theme = "light" if str(theme).lower() == "light" else "dark"

        self.ui_theme = theme

        self.state.settings.setValue("ui_theme", theme)

        app = QApplication.instance()

        if app is not None:
            base_stylesheet = LIGHT_STYLESHEET if theme == "light" else DARK_STYLESHEET
            app.setStyleSheet(base_stylesheet + self._font_stylesheet_suffix())

        if hasattr(self, "system_map"):
            self.system_map.set_light_mode(theme == "light")

        if self._chronicle_system_window is not None and hasattr(
            self._chronicle_system_window, "system_map"
        ):
            self._chronicle_system_window.system_map.set_light_mode(theme == "light")

    def _explorer_live_window_enabled(self, window_kind):
        key = (
            "explorer_live/bio_enabled"
            if str(window_kind) == "bio"
            else "explorer_live/value_enabled"
        )
        value = self.state.settings.value(key, True)

        if isinstance(value, str):
            return value.strip().lower() not in ("0", "false", "no", "off")

        return bool(value)

    def _set_explorer_live_window_enabled(self, window_kind, enabled):
        window_kind = "bio" if str(window_kind) == "bio" else "value"
        enabled = bool(enabled)

        key = (
            "explorer_live/bio_enabled"
            if window_kind == "bio"
            else "explorer_live/value_enabled"
        )
        self.state.settings.setValue(key, enabled)
        self.state.settings.sync()

        window = (
            self._explorer_bio_live_window
            if window_kind == "bio"
            else self._explorer_value_live_window
        )

        if not enabled and window is not None:
            window.hide()

        # Beim Einschalten sofort anhand der bereits bekannten Daten prüfen,
        # ob das betreffende Fenster angezeigt werden soll.
        if enabled and hasattr(self, "explorer_value_table"):
            self._refresh_explorer_live_windows()

    def _set_explorer_value_threshold(self, value):
        value = max(0, int(value or 0))
        self.state.settings.setValue(
            "explorer_value_yellow_threshold",
            value,
        )
        self.state.settings.sync()

        # Derselbe Wert steuert jetzt:
        # - gelbe Hervorhebung in der Wertliste
        # - Livefenster "Wertvolle Körper"
        # - Goldrahmen in der Systemkarte
        self._apply_gold_frame_threshold()

        if hasattr(self, "gold_frame_legend_label"):
            self.gold_frame_legend_label.setText(
                '<span style="color:#ffb000; font-size:14px; '
                'font-weight:700;">★</span> '
                '<span style="font-size:11px;">'
                + tr(
                    "explorer.gold_frame_from",
                    value=self._format_reward(value),
                )
                + "</span>"
            )

        if hasattr(self, "explorer_value_table"):
            self._refresh_explorer_tables()

        if hasattr(self, "system_map"):
            self.system_map.set_system(
                self.state.system or "–",
                self.state.system_bodies,
            )

    def _apply_gold_frame_threshold(self):
        """
        Verknüpft den Goldrahmen der Systemkarte mit demselben
        benutzerdefinierten Schwellenwert wie die Explorer-Wertliste.

        Maßgeblich ist der noch erreichbare Kartographiewert des Körpers.
        Ist der Körper bereits von uns kartiert, zählt der tatsächlich
        erreichte und noch auszuzahlende Wert.
        """
        threshold = self._explorer_value_yellow_threshold()

        for body in getattr(self.state, "system_bodies", None) or []:
            is_star = bool(body.get("star_type") or body.get("body_type") == "Star")
            is_belt = SystemMapWidget._is_belt_cluster(body)

            possible_value = int(
                body.get("possible_value") or body.get("current_value") or 0
            )

            body["high_value"] = bool(
                not is_star
                and not is_belt
                and threshold > 0
                and possible_value >= threshold
            )

    def _explorer_value_yellow_threshold(self):
        try:
            return max(
                0,
                int(
                    self.state.settings.value(
                        "explorer_value_yellow_threshold",
                        200_000,
                    )
                    or 200_000
                ),
            )
        except (TypeError, ValueError):
            return 200_000

    def _reset_missions(self):
        answer = QMessageBox.question(
            self,
            tr("missions.reset"),
            tr("missions.reset_question"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.state.reset_missions()

    def _set_service_test_status(
        self,
        label,
        ok,
        text,
    ):
        label.setText(("✓ " if ok else "✗ ") + text)
        label.setObjectName("statusOk" if ok else "statusWarn")
        label.style().unpolish(label)
        label.style().polish(label)

    def _test_edsm_connection(self):
        self.edsm_test_button.setEnabled(False)
        self.edsm_test_status.setText(tr("settings.connection_testing"))

        try:
            ok, text = test_edsm_connection(
                self.edsm_commander_edit.text(),
                self.edsm_api_key_edit.text(),
            )
            self._set_service_test_status(
                self.edsm_test_status,
                ok,
                text,
            )
        finally:
            self.edsm_test_button.setEnabled(True)

    def _test_inara_connection(self):
        self.inara_test_button.setEnabled(False)
        self.inara_test_status.setText(tr("settings.connection_testing"))

        try:
            ok, text = test_inara_connection(
                self.inara_commander_edit.text(),
                self.inara_api_key_edit.text(),
            )
            self._set_service_test_status(
                self.inara_test_status,
                ok,
                text,
            )
        finally:
            self.inara_test_button.setEnabled(True)

    def _save_online_settings(self):
        self.state.set_edsm_settings(
            commander=self.edsm_commander_edit.text(),
            api_key=self.edsm_api_key_edit.text(),
            enabled=self.edsm_enabled_check.isChecked(),
        )

        self.state.set_inara_settings(
            commander=self.inara_commander_edit.text(),
            api_key=self.inara_api_key_edit.text(),
            enabled=self.inara_enabled_check.isChecked(),
        )

        self.state.refresh()

        QMessageBox.information(
            self,
            tr("settings.online_services"),
            tr("settings.online_saved_message"),
        )

    def _journal_file_diagnostics(self):
        """
        Diagnose direkt aus dem gewählten Journalordner.
        Zeigt, ob neuere Dateien vorhanden sind als der letzte
        von CMDRHelper gelesene Journal-Eintrag.
        """
        folder = self.state.journal_folder

        if not folder:
            return None

        try:
            folder = Path(folder)

            if not folder.is_dir():
                return None

            files = [path for path in folder.glob("Journal*.log") if path.is_file()]

            if not files:
                return None

            files.sort(key=lambda path: path.stat().st_mtime)

            oldest = files[0]
            newest = files[-1]

            oldest_dt = datetime.fromtimestamp(oldest.stat().st_mtime)
            newest_dt = datetime.fromtimestamp(newest.stat().st_mtime)

            return {
                "oldest_time": oldest_dt.strftime("%d.%m.%Y %H:%M:%S"),
                "newest_time": newest_dt.strftime("%d.%m.%Y %H:%M:%S"),
                "newest_name": newest.name,
            }

        except Exception as exc:
            return {
                "oldest_time": tr("common.error"),
                "newest_time": tr("common.error"),
                "newest_name": str(exc),
            }

    def choose_journal_folder(self):
        start = str(self.state.journal_folder or Path.home())

        folder = QFileDialog.getExistingDirectory(
            self,
            tr("settings.choose_journal_folder_title"),
            start,
        )

        if folder:
            self.state.set_journal_folder(Path(folder))

    @staticmethod
    def _format_timestamp(value):
        if not value:
            return "–"

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

            return dt.strftime("%d.%m.%Y %H:%M:%S")

        except ValueError:
            return value

    @staticmethod
    def _format_expiry(value):
        if not value:
            return "–"

        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

            return dt.strftime("%d.%m.%Y %H:%M")

        except ValueError:
            return value

    @staticmethod
    def _format_reward(value):
        text = f"{int(value or 0):,}"
        if get_language() == "de":
            text = text.replace(",", ".")
        return f"{text} Cr"

    @staticmethod
    def _place_text(mission):
        if mission.destination_body:
            if mission.destination_station:
                return f"{mission.destination_body} / " f"{mission.destination_station}"

            return mission.destination_body

        if mission.destination_station:
            return mission.destination_station

        if mission.target:
            return mission.target

        return "–"

    @staticmethod
    def _translate_mission_text(value):
        """Übersetzt ausschließlich von CMDRHelper erzeugte Missions-Anzeigetexte."""
        return translate_mission_text(value)

    def _mission_selection_changed(self):
        selected = self.missions_table.selectionModel().selectedRows()

        if not selected:
            self.mission_detail_title.setText(tr("missions.none_selected"))

            self.mission_detail_text.setText(tr("missions.select_above"))

            self.mission_progress_text.setText("")

            return

        row = selected[0].row()

        if row < 0 or row >= len(self.state.missions):
            return

        mission = self.state.missions[row]

        self.mission_detail_title.setText(
            self._translate_mission_text(mission.name) or tr("missions.col_mission")
        )

        self.mission_detail_text.setText(self._translate_mission_text(mission.summary))

        progress = []

        if mission.progress_text:
            progress.append(
                tr(
                    "missions.progress",
                    value=self._translate_mission_text(mission.progress_text),
                )
            )

        progress.append(
            tr("missions.status", value=self._translate_mission_text(mission.status))
        )

        progress.append(
            tr(
                "missions.next_step",
                value=self._translate_mission_text(mission.next_step),
            )
        )

        self.mission_progress_text.setText("   ·   ".join(progress))

    def refresh_all(self):
        commander = self.state.commander or "–"

        system = self.state.system or "–"

        self.commander_label.setText(f"CMDR {commander}")

        self.ship_label.setText(self.state.ship or "")

        self.last_import_label.setText(
            tr(
                "topbar.last_journal_entry",
                timestamp=self._format_timestamp(self.state.last_timestamp),
            )
        )

        self.connection_label.setText(
            tr("topbar.journal_detected")
            if self.state.connected
            else tr("topbar.journal_not_detected")
        )

        self.connection_label.setObjectName(
            "statusOk" if self.state.connected else "statusWarn"
        )

        self.connection_label.style().unpolish(self.connection_label)

        self.connection_label.style().polish(self.connection_label)

        edsm_status = getattr(
            self.state,
            "edsm_upload_status",
            "disabled",
        )
        edsm_message = getattr(
            self.state,
            "edsm_upload_message",
            "",
        )

        if edsm_status == "ok":
            self.edsm_upload_label.setText(tr("topbar.edsm_transmitting"))
            self.edsm_upload_label.setObjectName("statusOk")
        elif edsm_status == "error":
            self.edsm_upload_label.setText(tr("topbar.edsm_error"))
            self.edsm_upload_label.setObjectName("statusWarn")
        elif edsm_status == "waiting":
            self.edsm_upload_label.setText(tr("topbar.edsm_waiting"))
            self.edsm_upload_label.setObjectName("muted")
        else:
            self.edsm_upload_label.setText(tr("topbar.edsm_off"))
            self.edsm_upload_label.setObjectName("muted")

        self.edsm_upload_label.setToolTip(edsm_message or tr("topbar.edsm_tooltip"))
        self.edsm_upload_label.style().unpolish(self.edsm_upload_label)
        self.edsm_upload_label.style().polish(self.edsm_upload_label)

        # INARA-Anzeige vorbereiten. Bis der automatische INARA-Uploader
        # eingebaut ist, zeigt sie nur Aktiv/Inaktiv an.
        if getattr(self.state, "inara_enabled", False):
            self.inara_upload_label.setText(tr("topbar.inara_waiting"))
            self.inara_upload_label.setObjectName("muted")
            self.inara_upload_label.setToolTip(tr("topbar.inara_enabled_tooltip"))
        else:
            self.inara_upload_label.setText(tr("topbar.inara_off"))
            self.inara_upload_label.setObjectName("muted")
            self.inara_upload_label.setToolTip(tr("topbar.inara_disabled_tooltip"))

        self.inara_upload_label.style().unpolish(self.inara_upload_label)
        self.inara_upload_label.style().polish(self.inara_upload_label)

        self.sidebar_system.setText(f"{tr('sidebar.current_system')}\n{system}")

        body_station = []

        if self.state.body:
            body_station.append(self.state.body)

        if self.state.station:
            body_station.append(self.state.station)

        self.sidebar_body.setText(" / ".join(body_station))

        self.current_system_value.setText(system)

        place_parts = []
        if self.state.body:
            place_parts.append(self.state.body)
        if self.state.station:
            place_parts.append(self.state.station)
        place_text = " / ".join(place_parts) if place_parts else "–"
        self.current_place_value.setText(place_text)

        self.overview_commander.setText(f"CMDR {commander}")

        ship_text = self.state.ship or "–"
        self.overview_ship.setText(tr("overview.ship", ship=ship_text))
        self.overview_location.setText(
            tr(
                "overview.location",
                location=system + (f" · {place_text}" if place_text != "–" else ""),
            )
        )

        mission_count = len(self.state.missions)
        self.active_missions_value.setText(str(mission_count))

        mission_total_reward = sum(
            int(getattr(mission, "reward", 0) or 0) for mission in self.state.missions
        )

        if hasattr(self, "mission_total_reward_label"):
            self.mission_total_reward_label.setText(
                tr(
                    "missions.total_reward",
                    value=self._format_reward(mission_total_reward),
                )
            )

        ready_count = sum(
            1
            for m in self.state.missions
            if m.status in ("Aufgabe erledigt", "Daten erhalten")
            or "Missionsterminal" in (m.next_step or "")
        )

        if mission_count == 0:
            self.mission_start_status.setText(tr("overview.no_open_missions"))
        elif ready_count:
            still_active = mission_count - ready_count
            parts = [tr("overview.ready_to_turn_in", count=ready_count)]
            if still_active:
                parts.append(tr("overview.still_active", count=still_active))
            self.mission_start_status.setText(" · ".join(parts))
        else:
            self.mission_start_status.setText(
                tr("overview.still_active", count=mission_count)
            )

        self.journal_count_value.setText(str(self.state.journal_files))

        if self.state.connected:
            self.overview_journal_state.setText(tr("overview.live_monitoring_active"))
            self.overview_journal_state.setObjectName("statusOk")
        else:
            self.overview_journal_state.setText(tr("overview.not_detected"))
            self.overview_journal_state.setObjectName("statusWarn")
        self.overview_journal_state.style().unpolish(self.overview_journal_state)
        self.overview_journal_state.style().polish(self.overview_journal_state)

        if self.state.connected:
            self.overview_status.setText(
                tr(
                    "overview.journal_summary",
                    commander=commander,
                    system=system,
                    missions=len(self.state.missions),
                )
            )

        else:
            self.overview_status.setText(tr("overview.no_ed_journal_data"))

        self._refresh_recent_systems()

        scanned_count = sum(
            1 for body in self.state.system_bodies if body.get("journal_scanned", True)
        )

        known_count = len(self.state.system_bodies)

        total_count = max(
            int(self.state.system_body_count or 0),
            int(getattr(self.state, "edsm_body_count", 0) or 0),
            known_count,
        )

        signal_count = self.state.system_signals_count

        # Belt Cluster können in Scan-Events auftauchen, zählen aber nicht
        # immer 1:1 zum FSS-BodyCount. Deshalb nicht irreführend >100% zeigen.
        displayed_scanned = (
            min(scanned_count, total_count) if total_count else scanned_count
        )

        bio_body_count = sum(
            1
            for body in self.state.system_bodies
            if int(body.get("biological_signals") or 0) > 0
        )

        geo_body_count = sum(
            1
            for body in self.state.system_bodies
            if int(body.get("geological_signals") or 0) > 0
        )

        scan_status = tr(
            "explorer.scan_count", scanned=displayed_scanned, total=total_count
        )

        edsm_added = int(getattr(self.state, "edsm_added_count", 0) or 0)

        edsm_known = int(getattr(self.state, "edsm_body_count", 0) or 0)

        if self.state.edsm_enabled and edsm_known:
            scan_status += tr("explorer.edsm_known", count=edsm_known)

            if edsm_added:
                scan_status += tr("explorer.edsm_added", count=edsm_added)

        if self.state.system_all_bodies_found:
            scan_status += tr("explorer.all_bodies_found")

        if signal_count:
            scan_status += tr("explorer.signals", count=signal_count)

        if bio_body_count:
            scan_status += tr("explorer.bio_on_bodies", count=bio_body_count)

        if geo_body_count:
            scan_status += tr("explorer.geo_on_bodies", count=geo_body_count)

        current_value = int(getattr(self.state, "system_current_value", 0) or 0)

        scan_status += tr(
            "explorer.value_summary",
            scan=self._format_reward(self.state.system_scan_value),
            current=self._format_reward(current_value),
            mapped=self._format_reward(self.state.system_mapped_value),
        )

        gold_threshold = self._explorer_value_yellow_threshold()
        gold_count = sum(
            1 for body in self.state.system_bodies if bool(body.get("high_value"))
        )

        if gold_count:
            scan_status += tr(
                "explorer.gold_body_count",
                count=gold_count,
                value=self._format_reward(gold_threshold),
            )

        self.system_scan_header.setText(scan_status)

        bio_count = int(getattr(self.state, "system_bio_completed_count", 0) or 0)
        bio_value = int(getattr(self.state, "system_bio_value", 0) or 0)
        bio_first_logged = int(
            getattr(self.state, "system_bio_first_logged_value", 0) or 0
        )
        bio_unknown = list(getattr(self.state, "system_bio_unknown", []) or [])

        if bio_count:
            bio_status = tr(
                "explorer.bio_summary",
                count=bio_count,
                base=self._format_reward(bio_value),
                first=self._format_reward(bio_first_logged),
            )

            if bio_unknown:
                bio_status += tr(
                    "explorer.bio_unknown_value_count", count=len(bio_unknown)
                )
        else:
            bio_status = tr("explorer.no_completed_bio")

        self.system_bio_header.setText(bio_status)

        unsold_cartography = int(
            getattr(self.state, "unsold_cartography_value", 0) or 0
        )
        unsold_cartography_count = int(
            getattr(self.state, "unsold_cartography_count", 0) or 0
        )
        unsold_bio = int(getattr(self.state, "unsold_bio_value", 0) or 0)
        unsold_bio_first = int(
            getattr(self.state, "unsold_bio_first_logged_value", 0) or 0
        )
        unsold_bio_count = int(getattr(self.state, "unsold_bio_count", 0) or 0)
        unsold_bio_unknown = list(getattr(self.state, "unsold_bio_unknown", []) or [])

        open_status = tr(
            "explorer.unsold_summary",
            cartography=self._format_reward(unsold_cartography),
            bodies=unsold_cartography_count,
            bio=self._format_reward(unsold_bio),
            samples=unsold_bio_count,
        )
        if unsold_bio:
            open_status += tr(
                "explorer.unsold_first_logged",
                value=self._format_reward(unsold_bio_first),
            )
        if unsold_bio_unknown:
            open_status += tr(
                "explorer.unsold_bio_unknown", count=len(unsold_bio_unknown)
            )

        self.unsold_explorer_header.setText(open_status)

        # Goldrahmen anhand des unter Einstellungen gewählten
        # Kartographiewert-Schwellenwerts setzen.
        self._apply_gold_frame_threshold()

        self.system_map.set_system(system, self.state.system_bodies)

        # Aktuelle Position auch in einer bereits geöffneten Chronik
        # unmittelbar nach einem Systemwechsel aktualisieren.
        self._mark_current_chronicle_system()

        if hasattr(self, "explorer_value_table"):
            self._refresh_explorer_tables()
            self._refresh_explorer_live_windows()

        self.journal_path_edit.setText(str(self.state.journal_folder or ""))

        self.journal_file_count.setText(str(self.state.journal_files))

        diagnostics = self._journal_file_diagnostics()

        if diagnostics:
            self.journal_oldest_file.setText(diagnostics.get("oldest_time", "–"))
            self.journal_newest_file.setText(diagnostics.get("newest_time", "–"))
            self.journal_newest_name.setText(diagnostics.get("newest_name", "–"))
        else:
            self.journal_oldest_file.setText("–")
            self.journal_newest_file.setText("–")
            self.journal_newest_name.setText("–")

        self.journal_last_read.setText(
            self._format_timestamp(self.state.last_timestamp)
        )

        current_row = self.missions_table.currentRow()

        self.missions_table.setRowCount(len(self.state.missions))

        for row, mission in enumerate(self.state.missions):
            values = [
                self._translate_mission_text(mission.name),
                mission.destination_system or "–",
                self._place_text(mission),
                self._translate_mission_text(mission.status),
                self._translate_mission_text(mission.next_step),
                self._format_reward(mission.reward),
                self._format_expiry(mission.expiry),
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))

                if col == 3:
                    if mission.status in (
                        "Aufgabe erledigt",
                        "Daten erhalten",
                        "Am Missionsziel",
                    ):
                        item.setForeground(Qt.green)

                self.missions_table.setItem(row, col, item)

        if 0 <= current_row < self.missions_table.rowCount():
            self.missions_table.selectRow(current_row)
        else:
            self._mission_selection_changed()
