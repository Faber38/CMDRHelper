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
from cmdrhelper.i18n import tr, get_language


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

        name = self.body.get("name") or self.body.get("short_name") or tr("body_detail.body")

        self.setWindowTitle(f"CMDRHelper – {name}")
        self.resize(650, 620)

        root = QVBoxLayout(self)

        title = QLabel(name)
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
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

        explorer_card, explorer_form = self._card(tr("body_detail.explorer_status"))
        self._add_explorer_rows(explorer_form)
        content_layout.addWidget(explorer_card)

        body_card, body_form = self._card(tr("body_detail.body_data"))
        self._add_body_rows(body_form)
        content_layout.addWidget(body_card)

        materials_card, materials_form = self._card(tr("body_detail.materials"))
        self._add_material_rows(materials_form)
        content_layout.addWidget(materials_card)

        value_card, value_form = self._card(tr("body_detail.values"))
        self._add_value_rows(value_form)
        content_layout.addWidget(value_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        close = QPushButton(tr("common.close"))
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
            return tr("common.unknown")
        return tr("common.yes") if bool(value) else tr("common.no")

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
            text = f"{int(value or 0):,}"
            if get_language() == "de":
                text = text.replace(",", ".")
            return f"{text} Cr"
        except Exception:
            return "0 Cr"

    def _body_texture_name(self):
        """3D-Texturdatei passend zum normalen Körperbild."""
        image_name = SystemMapWidget._body_image_name(self.body)

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
                elif texture_stem == "water_giant_life_texture":
                    life_effect = "water_giant"
                else:
                    life_effect = False

                self._planet_3d_widget = Planet3DWidget(
                    texture_path,
                    self,
                    diameter=230,
                    seconds_per_rotation=60.0,
                    life_effect=life_effect,
                )

                self._planet_3d_widget.setToolTip(texture_name)

                return self._planet_3d_widget

        return self._body_image_widget()

    def _body_image_widget(self):
        """Große Vorschau des Körperbildes im Detailfenster."""
        image_name = SystemMapWidget._body_image_name(self.body)

        if not image_name:
            return None

        image_path = (
            Path(__file__).resolve().parent.parent / "assets" / "bodies" / image_name
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
        if self._body_image_label is None or self._body_image_source is None:
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
        self._body_image_timer.timeout.connect(self._animate_body_image)
        self._body_image_timer.start()

    def _animate_body_image(self):
        if self._body_image_label is None:
            return

        import math

        self._body_image_phase += 0.0625

        if self._body_image_phase >= math.tau:
            self._body_image_phase = 0.0

        # 216–224 px: sichtbar, aber bewusst sehr dezent.
        size = 220.0 + 4.0 * math.sin(self._body_image_phase)

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
        if self.body.get("journal_scanned") and self.body.get("edsm_known"):
            return tr("body_detail.source_journal_edsm")
        if self.body.get("journal_scanned"):
            return tr("body_detail.source_journal")
        if self.body.get("edsm_known"):
            return tr("body_detail.source_edsm")
        return tr("body_detail.source_unknown")

    def _add_row(self, form, label, value):
        text = "–" if value in (None, "") else str(value)
        widget = QLabel(text)
        widget.setWordWrap(True)
        form.addRow(label, widget)

    @staticmethod
    def _volcanism_text(value):
        raw = str(value or "").strip()
        if not raw:
            return ""

        key = raw.lower().strip()
        if key.endswith(" volcanism"):
            key = key[:-10].strip()

        strength = ""
        if key.startswith("major "):
            strength = "major"
            key = key[6:].strip()
        elif key.startswith("minor "):
            strength = "minor"
            key = key[6:].strip()

        translations = {
            "water geysers": "water_geysers",
            "silicate vapour geysers": "silicate_vapour_geysers",
            "rocky magma": "rocky_magma",
            "metallic magma": "metallic_magma",
            "carbon dioxide geysers": "carbon_dioxide_geysers",
            "water magma": "water_magma",
            "ammonia magma": "ammonia_magma",
            "methane magma": "methane_magma",
            "nitrogen magma": "nitrogen_magma",
        }

        kind_key = translations.get(key)
        if kind_key is None:
            return raw

        kind = tr(f"body_detail.volcanism.{kind_key}")

        if strength == "major":
            return tr("body_detail.volcanism.major", kind=kind)
        if strength == "minor":
            return tr("body_detail.volcanism.minor", kind=kind)

        return kind

    def _add_explorer_rows(self, form):
        journal = bool(self.body.get("journal_scanned"))

        self._add_row(
            form,
            tr("body_detail.self_scanned") + ":",
            tr("common.yes") if journal else tr("common.no"),
        )

        if not journal:
            self._add_row(
                form,
                tr("body_detail.already_discovered") + ":",
                tr("body_detail.unknown_wait_scan"),
            )
            self._add_row(
                form,
                tr("body_detail.already_mapped") + ":",
                tr("body_detail.unknown_wait_scan"),
            )
            self._add_row(
                form,
                tr("body_detail.first_discovery") + ":",
                tr("common.unknown"),
            )
            self._add_row(
                form,
                tr("body_detail.first_mapping") + ":",
                tr("common.unknown"),
            )
        else:
            discovered = self.body.get("was_discovered")
            mapped = self.body.get("was_mapped")
            self_mapped = bool(self.body.get("self_mapped"))

            if discovered is True:
                already_discovered = tr("common.yes")
                first_discovery = tr("body_detail.no_already_discovered")
            elif discovered is False:
                already_discovered = tr("common.no")
                first_discovery = tr("body_detail.first_discovery_possible")
            else:
                already_discovered = tr("common.unknown")
                first_discovery = tr("common.unknown")

            if mapped is True:
                already_mapped = tr("common.yes")
                first_mapping = tr("body_detail.no_already_mapped")
            elif mapped is False:
                already_mapped = tr("common.no")
                if self_mapped:
                    first_mapping = tr("body_detail.first_mapping_claimed")
                else:
                    first_mapping = tr("body_detail.first_mapping_possible")
            else:
                already_mapped = tr("common.unknown")
                first_mapping = (
                    tr("body_detail.mapped_by_you")
                    if self_mapped
                    else tr("common.unknown")
                )

            self._add_row(
                form,
                tr("body_detail.already_discovered") + ":",
                already_discovered,
            )
            self._add_row(
                form,
                tr("body_detail.already_mapped") + ":",
                already_mapped,
            )
            self._add_row(
                form,
                tr("body_detail.first_discovery") + ":",
                first_discovery,
            )
            self._add_row(
                form,
                tr("body_detail.first_mapping") + ":",
                first_mapping,
            )
            self._add_row(
                form,
                tr("body_detail.mapped_by_you_label") + ":",
                tr("common.yes") if self_mapped else tr("common.no"),
            )

        bio_count = int(self.body.get("biological_signals") or 0)
        self._add_row(form, tr("body_detail.bio_signals") + ":", bio_count)

        biology = self.body.get("biology") or []
        names = []
        seen = set()

        for item in biology:
            if not isinstance(item, dict):
                continue
            name = item.get("variant") or item.get("species") or item.get("genus") or ""
            name = str(name).strip()
            if name and name not in seen:
                seen.add(name)
                names.append(name)

        if names:
            known_count = len(names)
            lines = [
                tr("body_detail.count_of", known=known_count, total=bio_count)
                if bio_count > 0
                else str(known_count)
            ]
            lines.extend(f"• {name}" for name in names)

            if bio_count > known_count:
                missing = bio_count - known_count
                lines.append(tr("body_detail.bio_unidentified", count=missing))

            self._add_row(
                form,
                tr("body_detail.known_biology") + ":",
                "\n".join(lines),
            )
        elif bio_count > 0:
            self._add_row(
                form,
                tr("body_detail.known_biology") + ":",
                tr("body_detail.bio_none_identified", total=bio_count),
            )

        geo_count = int(self.body.get("geological_signals") or 0)
        self._add_row(form, tr("body_detail.geo_signals") + ":", geo_count)

        if geo_count > 0:
            geology = self.body.get("geology") or []
            geo_names = []
            geo_seen = set()

            for item in geology:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("raw_name") or ""
                else:
                    name = item

                name = str(name or "").strip()
                if name and name not in geo_seen:
                    geo_seen.add(name)
                    geo_names.append(name)

            if geo_names:
                self._add_row(
                    form,
                    tr("body_detail.found_geo_types") + ":",
                    "\n".join(f"• {name}" for name in geo_names),
                )
            else:
                geo_name = self._volcanism_text(self.body.get("volcanism"))

                if geo_name:
                    geo_text = (
                        f"• {geo_name}\n"
                        + tr(
                            "body_detail.geo_signals_unnamed_bullet",
                            count=geo_count,
                        )
                    )
                else:
                    geo_text = tr(
                        "body_detail.geo_signals_unnamed",
                        count=geo_count,
                    )

                self._add_row(
                    form,
                    tr("body_detail.geological_type") + ":",
                    geo_text,
                )

        self._add_row(
            form,
            tr("body_detail.efficient_mapping") + ":",
            (
                self._yes_no(self.body.get("efficient_mapping"))
                if self.body.get("self_mapped")
                else "–"
            ),
        )

    def _add_body_rows(self, form):
        self._add_row(
            form,
            tr("body_detail.body_type") + ":",
            (
                self.body.get("planet_class")
                or self.body.get("star_type")
                or self.body.get("body_type")
                or "–"
            ),
        )

        if self.body.get("mass_em") is not None:
            self._add_row(
                form,
                tr("body_detail.mass") + ":",
                self._number(
                    self.body.get("mass_em"),
                    3,
                    tr("body_detail.earth_masses_suffix"),
                ),
            )
        elif self.body.get("stellar_mass") is not None:
            self._add_row(
                form,
                tr("body_detail.mass") + ":",
                self._number(
                    self.body.get("stellar_mass"),
                    3,
                    tr("body_detail.solar_masses_suffix"),
                ),
            )

        self._add_row(
            form,
            tr("body_detail.distance") + ":",
            self._number(self.body.get("distance_ls"), 1, " ls"),
        )
        self._add_row(
            form,
            tr("body_detail.gravity") + ":",
            self._number(self.body.get("gravity_g"), 2, " g"),
        )
        self._add_row(
            form,
            tr("body_detail.atmosphere") + ":",
            self.body.get("atmosphere") or tr("body_detail.none_unknown"),
        )
        self._add_row(
            form,
            tr("body_detail.landable") + ":",
            self._yes_no(self.body.get("landable")),
        )
        self._add_row(
            form,
            tr("body_detail.terraforming_candidate") + ":",
            self._yes_no(self.body.get("terraformable")),
        )

    @staticmethod
    def _material_name(name):
        """Translate material names regardless of the Elite/database language."""
        aliases = {
            "iron": "iron",
            "eisen": "iron",
            "nickel": "nickel",
            "sulphur": "sulphur",
            "sulfur": "sulphur",
            "schwefel": "sulphur",
            "carbon": "carbon",
            "kohlenstoff": "carbon",
            "chromium": "chromium",
            "chrom": "chromium",
            "manganese": "manganese",
            "mangan": "manganese",
            "phosphorus": "phosphorus",
            "phosphor": "phosphorus",
            "vanadium": "vanadium",
            "germanium": "germanium",
            "cadmium": "cadmium",
            "kadmium": "cadmium",
            "niobium": "niobium",
            "niob": "niobium",
            "arsenic": "arsenic",
            "arsen": "arsenic",
            "molybdenum": "molybdenum",
            "molybdän": "molybdenum",
            "tin": "tin",
            "zinn": "tin",
            "tungsten": "tungsten",
            "wolfram": "tungsten",
            "mercury": "mercury",
            "quecksilber": "mercury",
            "polonium": "polonium",
            "ruthenium": "ruthenium",
            "tellurium": "tellurium",
            "tellur": "tellurium",
            "technetium": "technetium",
            "yttrium": "yttrium",
            "antimony": "antimony",
            "antimon": "antimony",
            "selenium": "selenium",
            "selen": "selenium",
            "zirconium": "zirconium",
            "zirkonium": "zirconium",
        }

        raw = str(name or "").strip()

        if raw.startswith("$") and raw.endswith(";"):
            raw = raw[1:-1]

        lower = raw.casefold()

        # Frontier tokens can contain prefixes/suffixes; exact aliases are
        # preferred, then a contained alias is accepted as fallback.
        material_key = aliases.get(lower)
        if material_key is None:
            for alias, candidate in aliases.items():
                if alias in lower:
                    material_key = candidate
                    break

        if material_key:
            return tr(f"body_detail.material.{material_key}")

        return raw or tr("common.unknown")

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
                    else (
                        item.get("percent")
                        if item.get("percent") is not None
                        else (
                            item.get("percentage")
                            if item.get("percentage") is not None
                            else (
                                item.get("share")
                                if item.get("share") is not None
                                else item.get("amount")
                            )
                        )
                    )
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

        normalized.sort(key=lambda item: item[1], reverse=True)

        if not normalized:
            self._add_row(
                form,
                tr("body_detail.materials") + ":",
                tr("body_detail.no_material_data"),
            )
            return

        for name, amount in normalized:
            amount_text = f"{amount:.2f}"
            if get_language() == "de":
                amount_text = amount_text.replace(".", ",")
            self._add_row(form, f"{name}:", f"{amount_text} %")

    def _add_value_rows(self, form):
        self._add_row(form, tr("body_detail.scan_value") + ":", self._credits(self.body.get("scan_value")))
        self._add_row(
            form, tr("body_detail.with_mapping") + ":", self._credits(self.body.get("mapped_value"))
        )
        self._add_row(
            form, tr("body_detail.current_value") + ":", self._credits(self.body.get("current_value"))
        )
