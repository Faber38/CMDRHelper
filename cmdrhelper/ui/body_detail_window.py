from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
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

from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.ui.planet_3d_widget import Planet3DWidget
from cmdrhelper.ui.belt_cluster_widget import BeltClusterWidget


class BodyDetailWindow(QDialog):
    def __init__(self, body: dict, parent=None):
        super().__init__(parent)

        self.body = dict(body or {})

        self._body_image_source = None
        self._body_image_label = None
        self._body_image_phase = 0.0
        self._body_image_timer = None
        self._planet_3d_widget = None
        self._belt_cluster_widget = None

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

        # Wenn eine passende 2:1-Textur existiert, verwenden wir die
        # echte rotierende Kugel. Sonst bleibt die bisherige PNG-Vorschau.
        body_image = self._body_visual_widget()

        if body_image is not None:
            image_row = QHBoxLayout()
            image_row.addStretch()
            image_row.addWidget(body_image)
            image_row.addStretch()
            root.addLayout(image_row)

            if self._planet_3d_widget is None:
                self._start_body_image_animation()

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

        materials_card, materials_form = self._card(
            "MATERIALIEN"
        )
        self._add_material_rows(materials_form)
        content_layout.addWidget(materials_card)

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

    def _body_texture_name(self):
        """3D-Texturdatei passend zum normalen Körperbild."""
        image_name = SystemMapWidget._body_image_name(
            self.body
        )

        if not image_name:
            return None

        stem = Path(image_name).stem
        return f"{stem}_texture.png"

    def _body_visual_widget(self):
        """Cluster animieren, sonst 3D-Kugel oder bisheriges PNG."""
        image_name = SystemMapWidget._body_image_name(self.body)

        if image_name == "belt_cluster.png":
            image_path = (
                Path(__file__).resolve().parent.parent
                / "assets"
                / "bodies"
                / image_name
            )
            if image_path.is_file():
                self._belt_cluster_widget = BeltClusterWidget(
                    image_path, self, width=360, height=230
                )
                self._belt_cluster_widget.setToolTip(
                    "belt_cluster.png – animierter Asteroiden-Cluster"
                )
                return self._belt_cluster_widget

        texture_name = self._body_texture_name()

        if texture_name:
            texture_path = (
                Path(__file__).resolve().parent.parent
                / "assets"
                / "bodies"
                / texture_name
            )

            if texture_path.is_file():
                # Unterschiedliche Lebensformen für unterschiedliche
                # Life-Gasriesen.
                texture_stem = Path(texture_name).stem

                if texture_stem == "gas_giant_water_life_texture":
                    life_effect = "water"
                elif texture_stem == "gas_giant_ammonia_life_texture":
                    life_effect = "ammonia"
                else:
                    life_effect = False

                self._planet_3d_widget = Planet3DWidget(
                    texture_path,
                    self,
                    diameter=230,
                    seconds_per_rotation=18.0,
                    life_effect=life_effect,
                )

                self._planet_3d_widget.setToolTip(
                    texture_name
                )

                return self._planet_3d_widget

        return self._body_image_widget()

    def _body_image_widget(self):
        """Große Vorschau des Körperbildes im Detailfenster."""
        image_name = SystemMapWidget._body_image_name(self.body)

        if not image_name:
            return None

        image_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "bodies"
            / image_name
        )

        if not image_path.is_file():
            return None

        pixmap = QPixmap(str(image_path))

        if pixmap.isNull():
            return None

        self._body_image_source = pixmap

        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(236, 236)
        label.setToolTip(image_name)

        self._body_image_label = label
        self._set_animated_body_image(220)

        return label

    def _set_animated_body_image(self, size):
        if (
            self._body_image_label is None
            or self._body_image_source is None
        ):
            return

        size = max(1, int(round(size)))

        pixmap = self._body_image_source.scaled(
            size,
            size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self._body_image_label.setPixmap(pixmap)

    def _start_body_image_animation(self):
        """Sehr langsames, dezentes 'Atmen' des Körperbildes."""
        if self._body_image_label is None:
            return

        self._body_image_timer = QTimer(self)
        self._body_image_timer.setInterval(80)
        self._body_image_timer.timeout.connect(
            self._animate_body_image
        )
        self._body_image_timer.start()

    def _animate_body_image(self):
        if self._body_image_label is None:
            return

        import math

        self._body_image_phase += 0.0625

        if self._body_image_phase >= math.tau:
            self._body_image_phase = 0.0

        # 216–224 px: sichtbar, aber bewusst sehr dezent.
        size = 220.0 + 4.0 * math.sin(
            self._body_image_phase
        )

        self._set_animated_body_image(size)

    def closeEvent(self, event):
        if self._body_image_timer is not None:
            self._body_image_timer.stop()

        if self._planet_3d_widget is not None:
            self._planet_3d_widget.stop()

        if self._belt_cluster_widget is not None:
            self._belt_cluster_widget.stop()

        super().closeEvent(event)

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

        if not journal:
            self._add_row(
                form,
                "Bereits entdeckt:",
                "Unbekannt – eigenen Scan abwarten"
            )
            self._add_row(
                form,
                "Bereits kartographiert:",
                "Unbekannt – eigenen Scan abwarten"
            )
            self._add_row(
                form,
                "Erstentdeckung:",
                "Unbekannt"
            )
            self._add_row(
                form,
                "First Mapping:",
                "Unbekannt"
            )
        else:
            discovered = self.body.get(
                "was_discovered"
            )
            mapped = self.body.get(
                "was_mapped"
            )
            self_mapped = bool(
                self.body.get("self_mapped")
            )

            if discovered is True:
                already_discovered = "Ja"
                first_discovery = "Nein – bereits zuvor entdeckt"
            elif discovered is False:
                already_discovered = "Nein"
                first_discovery = "★ Möglich / von Elite als zuvor unentdeckt gemeldet"
            else:
                already_discovered = "Unbekannt"
                first_discovery = "Unbekannt"

            if mapped is True:
                already_mapped = "Ja"
                first_mapping = "Nein – bereits zuvor kartographiert"
            elif mapped is False:
                already_mapped = "Nein"

                if self_mapped:
                    first_mapping = (
                        "◉ Von dir kartographiert – First Mapping beansprucht"
                    )
                else:
                    first_mapping = (
                        "◉ Möglich – noch nicht zuvor kartographiert"
                    )
            else:
                already_mapped = "Unbekannt"

                if self_mapped:
                    first_mapping = "Von dir kartographiert"
                else:
                    first_mapping = "Unbekannt"

            self._add_row(
                form,
                "Bereits entdeckt:",
                already_discovered
            )
            self._add_row(
                form,
                "Bereits kartographiert:",
                already_mapped
            )
            self._add_row(
                form,
                "Erstentdeckung:",
                first_discovery
            )
            self._add_row(
                form,
                "First Mapping:",
                first_mapping
            )

            self._add_row(
                form,
                "Von dir kartographiert:",
                "Ja" if self_mapped else "Nein"
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
            "GEO-Signale:",
            int(
                self.body.get(
                    "geological_signals"
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

    @staticmethod
    def _material_name(name):
        translations = {
            "iron": "Eisen",
            "nickel": "Nickel",
            "sulphur": "Schwefel",
            "sulfur": "Schwefel",
            "carbon": "Kohlenstoff",
            "chromium": "Chrom",
            "manganese": "Mangan",
            "phosphorus": "Phosphor",
            "vanadium": "Vanadium",
            "germanium": "Germanium",
            "cadmium": "Cadmium",
            "niobium": "Niob",
            "arsenic": "Arsen",
            "molybdenum": "Molybdän",
            "tin": "Zinn",
            "tungsten": "Wolfram",
            "mercury": "Quecksilber",
            "polonium": "Polonium",
            "ruthenium": "Ruthenium",
            "tellurium": "Tellur",
            "technetium": "Technetium",
            "yttrium": "Yttrium",
            "antimony": "Antimon",
            "selenium": "Selen",
            "zirconium": "Zirkonium",
        }

        raw = str(name or "").strip()

        if raw.startswith("$") and raw.endswith(";"):
            raw = raw[1:-1]

        # Frontier-interne Bezeichner wie Materials_Iron_Name
        lower = raw.lower()
        for key, translated in translations.items():
            if key in lower:
                return translated

        return translations.get(lower, raw or "Unbekannt")

    def _add_material_rows(self, form):
        materials = self.body.get("materials") or {}

        normalized = []

        if isinstance(materials, dict):
            for name, amount in materials.items():
                try:
                    normalized.append(
                        (
                            self._material_name(name),
                            float(amount),
                        )
                    )
                except Exception:
                    continue

        elif isinstance(materials, list):
            for item in materials:
                if not isinstance(item, dict):
                    continue

                name = (
                    item.get("Name")
                    or item.get("name")
                    or item.get("Material")
                    or item.get("material")
                )

                amount = (
                    item.get("Percent")
                    if item.get("Percent") is not None
                    else item.get("percent")
                    if item.get("percent") is not None
                    else item.get("percentage")
                    if item.get("percentage") is not None
                    else item.get("share")
                    if item.get("share") is not None
                    else item.get("amount")
                )

                if not name or amount is None:
                    continue

                try:
                    normalized.append(
                        (
                            self._material_name(name),
                            float(amount),
                        )
                    )
                except Exception:
                    continue

        normalized.sort(
            key=lambda item: item[1],
            reverse=True
        )

        if not normalized:
            self._add_row(
                form,
                "Materialien:",
                (
                    "Keine Materialdaten vorhanden. "
                    "Bei einem eigenen vollständigen Körperscan "
                    "können sie aus dem Elite-Journal übernommen werden."
                )
            )
            return

        for name, amount in normalized:
            self._add_row(
                form,
                f"{name}:",
                f"{amount:.2f} %".replace(".", ",")
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
