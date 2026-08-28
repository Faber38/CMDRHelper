from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QFormLayout,
    QPushButton,
    QScrollArea,
    QWidget,
)


class BodyDetailWindow(QDialog):
    def __init__(self, body: dict, parent=None):
        super().__init__(parent)

        self.body = dict(body or {})

        name = (
            self.body.get("name")
            or self.body.get("short_name")
            or "Körper"
        )

        self.setWindowTitle(
            f"CMDRHelper – {name}"
        )
        self.resize(650, 620)

        root = QVBoxLayout(self)

        title = QLabel(name)
        title.setStyleSheet(
            "font-size: 20px; font-weight: 700;"
        )
        root.addWidget(title)

        source = self._source_text()
        source_label = QLabel(source)
        source_label.setObjectName("muted")
        root.addWidget(source_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        explorer_card, explorer_form = self._card(
            "EXPLORER-STATUS"
        )
        self._add_explorer_rows(explorer_form)
        content_layout.addWidget(explorer_card)

        body_card, body_form = self._card(
            "KÖRPERDATEN"
        )
        self._add_body_rows(body_form)
        content_layout.addWidget(body_card)

        value_card, value_form = self._card(
            "WERTE"
        )
        self._add_value_rows(value_form)
        content_layout.addWidget(value_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton("Schließen")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)

        root.addLayout(buttons)

    @staticmethod
    def _card(title):
        frame = QFrame()
        frame.setObjectName("card")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)

        form = QFormLayout()
        layout.addLayout(form)

        return frame, form

    @staticmethod
    def _yes_no(value):
        if value is None:
            return "Unbekannt"
        return "Ja" if bool(value) else "Nein"

    @staticmethod
    def _number(value, digits=2, suffix=""):
        if value is None:
            return "–"

        try:
            text = f"{float(value):.{digits}f}"
        except Exception:
            return str(value)

        return text + suffix

    @staticmethod
    def _credits(value):
        try:
            return (
                f"{int(value or 0):,} Cr"
                .replace(",", ".")
            )
        except Exception:
            return "0 Cr"

    def _source_text(self):
        if (
            self.body.get("journal_scanned")
            and self.body.get("edsm_known")
        ):
            return "Quelle: eigenes Journal + EDSM"

        if self.body.get("journal_scanned"):
            return "Quelle: eigenes Journal"

        if self.body.get("edsm_known"):
            return "Quelle: EDSM"

        return "Quelle: unbekannt"

    def _add_row(self, form, label, value):
        text = "–" if value in (None, "") else str(value)
        widget = QLabel(text)
        widget.setWordWrap(True)
        form.addRow(label, widget)

    def _add_explorer_rows(self, form):
        journal = bool(
            self.body.get("journal_scanned")
        )

        self._add_row(
            form,
            "Selbst gescannt:",
            "Ja" if journal else "Nein"
        )

        if journal:
            discovered = self.body.get(
                "was_discovered"
            )
            mapped = self.body.get(
                "was_mapped"
            )

            if discovered is False:
                discovery_text = (
                    "Nein – Erstentdeckung möglich"
                )
            elif discovered is True:
                discovery_text = (
                    "Ja – bereits zuvor entdeckt"
                )
            else:
                discovery_text = "Unbekannt"

            if self.body.get("self_mapped"):
                mapping_text = (
                    "Von dir kartographiert"
                )
            elif mapped is False:
                mapping_text = (
                    "Nein – First Mapping möglich"
                )
            elif mapped is True:
                mapping_text = (
                    "Ja – bereits zuvor kartographiert"
                )
            else:
                mapping_text = "Unbekannt"

            self._add_row(
                form,
                "Zuvor entdeckt:",
                discovery_text
            )
            self._add_row(
                form,
                "Kartographie:",
                mapping_text
            )
        else:
            self._add_row(
                form,
                "Erstentdeckung:",
                "Noch unbekannt – eigenen Scan abwarten"
            )
            self._add_row(
                form,
                "First Mapping:",
                "Noch unbekannt – eigenen Scan abwarten"
            )

        self._add_row(
            form,
            "BIO-Signale:",
            int(
                self.body.get(
                    "biological_signals"
                ) or 0
            )
        )

        self._add_row(
            form,
            "Effizient kartographiert:",
            self._yes_no(
                self.body.get(
                    "efficient_mapping"
                )
            )
            if self.body.get("self_mapped")
            else "–"
        )

    def _add_body_rows(self, form):
        self._add_row(
            form,
            "Körperart:",
            (
                self.body.get("planet_class")
                or self.body.get("star_type")
                or self.body.get("body_type")
                or "–"
            )
        )

        if self.body.get("mass_em") is not None:
            self._add_row(
                form,
                "Masse:",
                self._number(
                    self.body.get("mass_em"),
                    3,
                    " Erdmassen"
                )
            )
        elif self.body.get("stellar_mass") is not None:
            self._add_row(
                form,
                "Masse:",
                self._number(
                    self.body.get("stellar_mass"),
                    3,
                    " Sonnenmassen"
                )
            )

        self._add_row(
            form,
            "Entfernung:",
            self._number(
                self.body.get("distance_ls"),
                1,
                " ls"
            )
        )

        self._add_row(
            form,
            "Schwerkraft:",
            self._number(
                self.body.get("gravity_g"),
                2,
                " g"
            )
        )

        self._add_row(
            form,
            "Atmosphäre:",
            self.body.get("atmosphere") or "Keine / unbekannt"
        )

        self._add_row(
            form,
            "Vulkanismus:",
            self.body.get("volcanism") or "Keiner / unbekannt"
        )

        self._add_row(
            form,
            "Landbar:",
            self._yes_no(
                self.body.get("landable")
            )
        )

        self._add_row(
            form,
            "Terraforming-Kandidat:",
            self._yes_no(
                self.body.get("terraformable")
            )
        )

    def _add_value_rows(self, form):
        self._add_row(
            form,
            "Scanwert:",
            self._credits(
                self.body.get("scan_value")
            )
        )
        self._add_row(
            form,
            "Mit Kartographie:",
            self._credits(
                self.body.get("mapped_value")
            )
        )
        self._add_row(
            form,
            "Aktueller Wert:",
            self._credits(
                self.body.get("current_value")
            )
        )
