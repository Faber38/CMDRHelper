from __future__ import annotations

from collections import defaultdict
from math import ceil, log10
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPixmap
from PySide6.QtWidgets import QWidget, QToolTip


class SystemMapWidget(QWidget):
    bodyClicked = Signal(object)

    BODY_W = 145
    BODY_H = 230
    X_GAP = 24
    LEVEL_GAP = 28
    MARGIN_X = 26
    MARGIN_Y = 16
    ROW_GAP = 36

    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_name = ""
        self.bodies = []
        self._body_rects = []
        self._light_mode = False

        # Optionale eigene Körperbilder.
        # Fehlt eine Datei, bleibt automatisch die bisherige
        # gezeichnete Standarddarstellung erhalten.
        self._body_image_dir = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "bodies"
        )
        self._body_image_cache = {}

        self.setMouseTracking(True)
        self.setMinimumHeight(360)

    def set_light_mode(self, enabled: bool):
        self._light_mode = bool(enabled)
        self.update()

    def set_system(self, system_name: str, bodies: list[dict]):
        self.system_name = system_name or ""
        self.bodies = list(bodies or [])
        self._update_size()
        self.update()

    def sizeHint(self):
        return QSize(
            max(900, self.minimumWidth()),
            max(360, self.minimumHeight())
        )

    @staticmethod
    def _already_discovered(body):
        return (
            body.get("was_discovered") is True
            or body.get("edsm_was_discovered") is True
        )

    @staticmethod
    def _already_mapped(body):
        return (
            body.get("was_mapped") is True
            or body.get("edsm_was_mapped") is True
        )

    @staticmethod
    def _body_sort_key(body):
        body_id = body.get("body_id")

        try:
            if body_id is not None:
                return (0, int(body_id), "")
        except Exception:
            pass

        return (
            1,
            999999,
            str(
                body.get("name")
                or body.get("short_name")
                or ""
            ).lower(),
        )

    def _children_map(self):
        children = defaultdict(list)
        by_id = {}

        for body in self.bodies:
            body_id = body.get("body_id")

            if body_id is not None:
                by_id[body_id] = body

        for body in self.bodies:
            pid = body.get("parent_id")
            if pid is not None and pid in by_id:
                children[pid].append(body)

        for items in children.values():
            items.sort(key=self._body_sort_key)

        return children, by_id

    def _roots(self, by_id):
        roots = []

        for body in self.bodies:
            pid = body.get("parent_id")
            if pid is None or pid not in by_id:
                roots.append(body)

        roots.sort(key=self._body_sort_key)
        return roots

    def _flatten_columns(self):
        children, by_id = self._children_map()
        roots = self._roots(by_id)
        columns = []

        def visit(body, level):
            columns.append((body, level))

            for child in children.get(body.get("body_id"), []):
                visit(child, level + 1)

        for root in roots:
            visit(root, 0)

        return columns, children

    def _layout_rows(self):
        """
        Explorer-Layout mit bis zu vier Reihen.

        Elternkörper und ihre Monde bleiben nach Möglichkeit zusammen.
        Sehr große Familien dürfen umbrechen; bei extrem großen Systemen
        wird lieber horizontal gescrollt als mehr als vier Reihen erzeugt.
        """
        columns, children = self._flatten_columns()

        if not columns:
            return [[]], children

        target_columns = 9

        desired_rows = min(
            4,
            max(1, ceil(len(columns) / target_columns))
        )

        target_columns = max(
            target_columns,
            ceil(len(columns) / desired_rows)
        )

        groups = []
        current_group = []

        for item in columns:
            _body, level = item

            if level == 0 and current_group:
                groups.append(current_group)
                current_group = []

            current_group.append(item)

        if current_group:
            groups.append(current_group)

        rows = []
        current_row = []

        for group in groups:
            group = list(group)

            if (
                current_row
                and len(current_row) + len(group) > target_columns
            ):
                rows.append(current_row)
                current_row = []

            while len(group) > target_columns:
                if current_row:
                    rows.append(current_row)
                    current_row = []

                rows.append(group[:target_columns])
                group = group[target_columns:]

            if group:
                current_row.extend(group)

        if current_row:
            rows.append(current_row)

        if len(rows) > 4:
            fourth_row = []

            for extra_row in rows[3:]:
                fourth_row.extend(extra_row)

            rows = rows[:3] + [fourth_row]

        return rows, children

    def _row_height(self, row):
        max_level = max((level for _, level in row), default=0)

        return (
            self.BODY_H
            + max_level * self.LEVEL_GAP
        )

    def _update_size(self):
        rows, _ = self._layout_rows()

        max_columns = max(
            (len(row) for row in rows),
            default=1
        )

        width = (
            self.MARGIN_X * 2
            + max_columns * self.BODY_W
            + max(0, max_columns - 1) * self.X_GAP
        )

        height = self.MARGIN_Y * 2

        for row_index, row in enumerate(rows):
            height += self._row_height(row)

            if row_index < len(rows) - 1:
                height += self.ROW_GAP

        self.setMinimumSize(
            max(900, width),
            max(360, height)
        )

    @staticmethod
    def _body_image_name(body):
        """Dateiname für ein optionales eigenes Körperbild."""
        if SystemMapWidget._is_belt_cluster(body):
            return "belt_cluster.png"

        star = (body.get("star_type") or "").strip()
        planet = (body.get("planet_class") or "").strip().lower()

        star_images = {
            "O": "star_o.png",
            "B": "star_b.png",
            "A": "star_a.png",
            "F": "star_f.png",
            "G": "star_g.png",
            "K": "star_k.png",
            "M": "star_m.png",
            "L": "star_l.png",
            "T": "star_t.png",
            "Y": "star_y.png",
            "TTS": "star_t_tauri.png",
            "AeBe": "star_herbig_aebe.png",
            "Neutron": "star_neutron.png",
            "BlackHole": "black_hole.png",
            "SupermassiveBlackHole": "black_hole_supermassive.png",
            "WhiteDwarf": "star_white_dwarf.png",
        }

        if star:
            return star_images.get(star)

        planet_images = {
            "high metal content body": "planet_hmc.png",
            "metal rich body": "planet_metal_rich.png",
            "rocky body": "planet_rocky.png",
            "icy body": "planet_icy.png",
            "rocky ice body": "planet_rocky_ice.png",
            "earthlike body": "planet_earthlike.png",
            "water world": "planet_water_world.png",
            "ammonia world": "planet_ammonia_world.png",
            "sudarsky class i gas giant": "gas_giant_class_1.png",
            "sudarsky class ii gas giant": "gas_giant_class_2.png",
            "sudarsky class iii gas giant": "gas_giant_class_3.png",
            "sudarsky class iv gas giant": "gas_giant_class_4.png",
            "sudarsky class v gas giant": "gas_giant_class_5.png",
            "class i gas giant": "gas_giant_class_1.png",
            "class ii gas giant": "gas_giant_class_2.png",
            "class iii gas giant": "gas_giant_class_3.png",
            "class iv gas giant": "gas_giant_class_4.png",
            "class v gas giant": "gas_giant_class_5.png",
            "gas giant with water based life":
                "gas_giant_water_life.png",
            "gas giant with ammonia based life":
                "gas_giant_ammonia_life.png",
            "helium rich gas giant":
                "gas_giant_helium_rich.png",
            "helium gas giant":
                "gas_giant_helium.png",
            "water giant":
                "water_giant.png",
            "water giant with life":
                "water_giant_life.png",
        }

        return planet_images.get(planet)

    def _body_pixmap(self, body):
        image_name = self._body_image_name(body)

        if not image_name:
            return None

        if image_name in self._body_image_cache:
            cached = self._body_image_cache[image_name]
            return cached if not cached.isNull() else None

        image_path = self._body_image_dir / image_name

        if not image_path.is_file():
            self._body_image_cache[image_name] = QPixmap()
            return None

        pixmap = QPixmap(str(image_path))
        self._body_image_cache[image_name] = pixmap

        return pixmap if not pixmap.isNull() else None

    @staticmethod
    def _visual_body_size(body):
        """Optische Bildgröße aus dem realen Radius ableiten.

        Sterne und Planeten werden bewusst getrennt logarithmisch
        skaliert. So bleiben kleine Monde sichtbar, während große
        Körper trotzdem deutlich größer erscheinen.
        """
        is_star = bool(
            body.get("star_type")
            or body.get("body_type") == "Star"
        )

        # Bevorzugt Journalwert in Metern. Für spätere EDSM-Daten
        # akzeptieren wir zusätzlich radius_km bzw. radius.
        radius_m = body.get("radius_m")

        if radius_m is None:
            radius_km = body.get("radius_km")
            if radius_km is not None:
                try:
                    radius_m = float(radius_km) * 1000.0
                except Exception:
                    radius_m = None

        if radius_m is None:
            raw_radius = body.get("radius")
            if raw_radius is not None:
                try:
                    # CMDRHelper-interner Fallback: radius wird als Meter
                    # interpretiert, wenn keine explizite Einheit vorliegt.
                    radius_m = float(raw_radius)
                except Exception:
                    radius_m = None

        try:
            radius_m = float(radius_m)
        except (TypeError, ValueError):
            radius_m = 0.0

        if radius_m <= 0:
            return 80.0 if is_star else 54.0

        radius_km = radius_m / 1000.0

        if is_star:
            # Sterne: ca. 70.000 km bis 14 Mio. km Radius
            # auf 65 bis 100 Pixel abbilden. Damit heben sie sich
            # optisch klarer von Planeten und Monden ab.
            min_radius = 70_000.0
            max_radius = 14_000_000.0
            min_size = 65.0
            max_size = 100.0
        else:
            # Monde/Planeten: ca. 250 km bis 80.000 km Radius
            # auf 24 bis 60 Pixel abbilden.
            min_radius = 250.0
            max_radius = 80_000.0
            min_size = 24.0
            max_size = 60.0

        radius_km = max(
            min_radius,
            min(max_radius, radius_km)
        )

        span = (
            log10(max_radius)
            - log10(min_radius)
        )

        if span <= 0:
            return max_size

        factor = (
            log10(radius_km)
            - log10(min_radius)
        ) / span

        return (
            min_size
            + factor * (max_size - min_size)
        )

    @staticmethod
    def _body_color(body):
        star = (body.get("star_type") or "").upper()
        planet = (body.get("planet_class") or "").lower()

        if star:
            if star.startswith(("O", "B", "A")):
                return QColor("#82baff")
            if star.startswith(("F", "G")):
                return QColor("#ffd56a")
            if star.startswith("K"):
                return QColor("#ffae52")
            if star.startswith("M"):
                return QColor("#ff6b4a")
            if "TTS" in star or star == "T":
                return QColor("#b46a3e")

            return QColor("#f6c86a")

        if "earthlike" in planet:
            return QColor("#4fa6d8")
        if "water world" in planet:
            return QColor("#3377c9")
        if "ammonia" in planet:
            return QColor("#b27758")
        if "high metal content" in planet:
            return QColor("#b58a58")
        if "metal rich" in planet:
            return QColor("#b77b48")
        if "gas giant" in planet:
            return QColor("#b79b76")
        if "icy" in planet:
            return QColor("#c8d1d8")
        if "rocky" in planet:
            return QColor("#8d7b6b")

        return QColor("#8f9498")

    @staticmethod
    def _is_belt_cluster(body):
        name = (
            body.get("name")
            or body.get("short_name")
            or ""
        ).lower()

        body_type = (
            body.get("body_type")
            or ""
        ).lower()

        planet_class = (
            body.get("planet_class")
            or ""
        ).lower()

        return (
            "belt cluster" in name
            or "asteroid belt" in body_type
            or "belt cluster" in body_type
            or "asteroid belt" in planet_class
            or "belt cluster" in planet_class
        )

    @staticmethod
    def _format_credits(value):
        try:
            return f"{int(value):,} Cr".replace(",", ".")
        except Exception:
            return "0 Cr"

    @staticmethod
    def _type_text(body):
        if SystemMapWidget._is_belt_cluster(body):
            return "Asteroiden-Cluster"

        if body.get("star_type"):
            star = body["star_type"]

            star_names = {
                "O": "O-Stern",
                "B": "B-Stern",
                "A": "A-Stern",
                "F": "F-Stern",
                "G": "G-Stern",
                "K": "K-Stern",
                "M": "M-Stern",
                "L": "L-Zwerg",
                "T": "T-Zwerg",
                "Y": "Y-Zwerg",
                "TTS": "T-Tauri-Stern",
                "AeBe": "Herbig-Ae/Be-Stern",
                "Neutron": "Neutronenstern",
                "BlackHole": "Schwarzes Loch",
                "SupermassiveBlackHole": "Supermassereiches Schwarzes Loch",
                "WhiteDwarf": "Weißer Zwerg",
            }

            return star_names.get(
                star,
                f"{star} Stern"
            )

        planet = body.get("planet_class") or "Planet"

        replacements = {
            "High metal content body": "HMC-Planet",
            "Metal rich body": "Metallreicher Planet",
            "Rocky body": "Felsplanet",
            "Icy body": "Eisplanet",
            "Rocky ice body": "Fels-/Eisplanet",

            "Earthlike body": "Erdähnliche Welt",
            "Water world": "Wasserwelt",
            "Ammonia world": "Ammoniakwelt",

            "Sudarsky class I gas giant": "Gasriese Klasse I",
            "Sudarsky class II gas giant": "Gasriese Klasse II",
            "Sudarsky class III gas giant": "Gasriese Klasse III",
            "Sudarsky class IV gas giant": "Gasriese Klasse IV",
            "Sudarsky class V gas giant": "Gasriese Klasse V",

            "Class I gas giant": "Gasriese Klasse I",
            "Class II gas giant": "Gasriese Klasse II",
            "Class III gas giant": "Gasriese Klasse III",
            "Class IV gas giant": "Gasriese Klasse IV",
            "Class V gas giant": "Gasriese Klasse V",

            "Gas giant with water based life":
                "Gasriese mit wasserbasiertem Leben",

            "Gas giant with ammonia based life":
                "Gasriese mit ammoniakbasiertem Leben",

            "Helium rich gas giant":
                "Heliumreicher Gasriese",

            "Helium gas giant":
                "Helium-Gasriese",

            "Water giant":
                "Wasserriese",

            "Water giant with life":
                "Wasserriese mit Leben",
        }

        return replacements.get(
            planet,
            planet
        )

    def _tooltip(self, body):
        if self._is_belt_cluster(body):
            name = (
                body.get("name")
                or body.get("short_name")
                or "Asteroiden-Cluster"
            )

            parts = [
                name,
                "Asteroiden-Cluster",
                "",
                "Keine Explorer-/Kartographie-Auswertung",
            ]

            if body.get("distance_ls") is not None:
                parts.insert(
                    2,
                    f"Entfernung: {body['distance_ls']:.1f} ls"
                )

            return "\n".join(parts)

        parts = [
            body.get("name")
            or body.get("short_name")
            or "Körper",

            self._type_text(body),
        ]

        if body.get("gravity_g") is not None:
            parts.append(
                f"Schwerkraft: {body['gravity_g']:.2f} g"
            )

        if body.get("distance_ls") is not None:
            parts.append(
                f"Entfernung: {body['distance_ls']:.1f} ls"
            )

        if body.get("landable"):
            parts.append("Landbar")

        if body.get("terraformable"):
            parts.append("Terraforming-Kandidat")

        if body.get("biological_signals"):
            parts.append(
                f"Biologische Signale: "
                f"{body['biological_signals']}"
            )

        if body.get("geological_signals"):
            parts.append(
                f"Geologische Signale: "
                f"{body['geological_signals']}"
            )

        if body.get("atmosphere"):
            parts.append(
                f"Atmosphäre: {body['atmosphere']}"
            )

        if body.get("volcanism"):
            parts.append(
                f"Vulkanismus: {body['volcanism']}"
            )

        if body.get("journal_scanned", True):
            was_discovered = body.get("was_discovered")
            was_mapped = body.get("was_mapped")
            self_mapped = bool(body.get("self_mapped"))

            if (
                was_discovered is False
                and not self._already_discovered(body)
            ):
                parts.append("★ Erstentdeckung möglich")
            elif self._already_discovered(body):
                parts.append("Bereits zuvor entdeckt")

            is_star = bool(
                body.get("star_type")
                or body.get("body_type") == "Star"
            )

            if not is_star:
                if (
                    was_mapped is False
                    and not self._already_mapped(body)
                ):
                    if self_mapped:
                        parts.append("◉ First Mapping beansprucht")
                    else:
                        parts.append("◉ First Mapping möglich")
                elif self._already_mapped(body):
                    parts.append("Bereits zuvor kartographiert")

                if self_mapped:
                    parts.append("◎ Von dir kartographiert")
        elif body.get("edsm_known"):
            parts.append("Quelle: EDSM – Explorer-Status erst nach eigenem Scan")

        parts.append("")

        parts.append(
            "Scanwert: "
            + self._format_credits(
                body.get("scan_value", 0)
            )
        )

        parts.append(
            "Mit Kartographie: "
            + self._format_credits(
                body.get("mapped_value", 0)
            )
        )

        parts.append(
            "Aktueller Wert: "
            + self._format_credits(
                body.get("current_value", 0)
            )
        )

        if body.get("high_value"):
            parts.append(
                "★ LOHNENSWERT: über 200.000 Cr"
            )

        return "\n".join(parts)

    def _build_positions(self, rows):
        positions = {}
        current_y = self.MARGIN_Y

        for row_index, row in enumerate(rows):
            for column_index, (body, level) in enumerate(row):
                x = (
                    self.MARGIN_X
                    + column_index
                    * (self.BODY_W + self.X_GAP)
                )

                y = (
                    current_y
                    + level * self.LEVEL_GAP
                )

                positions[id(body)] = {
                    "x": x,
                    "y": y,
                    "row": row_index,
                    "body": body,
                    "level": level,
                }

            current_y += self._row_height(row)

            if row_index < len(rows) - 1:
                current_y += self.ROW_GAP

        return positions

    def _draw_connections(
        self,
        painter,
        rows,
        children,
        positions
    ):
        painter.setPen(
            QPen(
                QColor("#9ba3aa"),
                1.2
            )
        )

        for row in rows:
            for body, _level in row:
                bid = body.get("body_id")

                for child in children.get(bid, []):
                    child_id = child.get("body_id")

                    parent_key = id(body)
                    child_key = id(child)

                    if (
                        parent_key not in positions
                        or child_key not in positions
                    ):
                        continue

                    parent_pos = positions[parent_key]
                    child_pos = positions[child_key]

                    # Keine diagonale Linie quer durch beide Reihen.
                    if (
                        parent_pos["row"]
                        != child_pos["row"]
                    ):
                        continue

                    px = (
                        parent_pos["x"]
                        + self.BODY_W / 2
                    )

                    py = parent_pos["y"]

                    cx = (
                        child_pos["x"]
                        + self.BODY_W / 2
                    )

                    cy = child_pos["y"]

                    line_y = min(py, cy) + 18
                    child_top = cy + 8

                    painter.drawLine(
                        int(px),
                        int(line_y),
                        int(cx),
                        int(line_y)
                    )

                    painter.drawLine(
                        int(cx),
                        int(line_y),
                        int(cx),
                        int(child_top)
                    )

    def _draw_body(
        self,
        painter,
        body,
        x,
        y
    ):
        body_rect = QRectF(
            x,
            y,
            self.BODY_W,
            self.BODY_H
        )

        self._body_rects.append(
            (body_rect, body)
        )

        is_belt_cluster = self._is_belt_cluster(body)
        body_pixmap = self._body_pixmap(body)

        bio_count = int(
            body.get("biological_signals") or 0
        )
        geo_count = int(
            body.get("geological_signals") or 0
        )

        # BIO-Körper deutlich hervorheben.
        if bio_count > 0 and not is_belt_cluster:
            painter.setPen(
                QPen(
                    QColor("#39ff56"),
                    4
                )
            )

            painter.setBrush(
                QColor(
                    80,
                    220,
                    90,
                    18
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    x + 1,
                    y + 1,
                    self.BODY_W - 2,
                    self.BODY_H - 2
                ),
                8,
                8
            )


        if body.get("high_value") and not is_belt_cluster:
            painter.setPen(
                QPen(
                    QColor("#ff9d00"),
                    2
                )
            )

            painter.setBrush(
                QColor(
                    255,
                    157,
                    0,
                    14
                )
            )

            painter.drawRoundedRect(
                QRectF(
                    x + 5,
                    y + 5,
                    self.BODY_W - 10,
                    self.BODY_H - 10
                ),
                7,
                7
            )

            painter.setPen(
                QColor("#ffb000")
            )

            font = painter.font()
            font.setBold(True)
            font.setPointSize(12)
            painter.setFont(font)

            painter.drawText(
                QRectF(
                    x,
                    y + 2,
                    self.BODY_W,
                    18
                ),
                Qt.AlignHCenter
                | Qt.AlignTop,
                "★"
            )

        color = self._body_color(body)

        is_star = bool(
            body.get("star_type")
        )

        visual_size = self._visual_body_size(body)

        radius = visual_size / 2.0

        cx = (
            x
            + self.BODY_W / 2
        )

        cy = y + 44

        if is_star and body_pixmap is None:
            painter.setPen(Qt.NoPen)

            glow = QColor(color)
            glow.setAlpha(55)

            painter.setBrush(glow)

            painter.drawEllipse(
                QRectF(
                    cx - radius - 8,
                    cy - radius - 8,
                    (radius + 8) * 2,
                    (radius + 8) * 2
                )
            )

        painter.setPen(
            QPen(
                QColor("#d9dde1"),
                1
            )
        )

        painter.setBrush(
            QBrush(color)
        )

        if body_pixmap is not None:
            # Eigene PNGs folgen ebenfalls dem realen Körperradius.
            # Die Funktion begrenzt die Größen bewusst, damit das Layout
            # trotz astronomischer Größenunterschiede lesbar bleibt.
            image_size = visual_size

            # Seitenverhältnis des Originalbildes beibehalten.
            # Dadurch werden runde Sterne/Planeten nicht zu Eiern verzerrt.
            pix_w = body_pixmap.width()
            pix_h = body_pixmap.height()

            if pix_w > 0 and pix_h > 0:
                scale = min(
                    image_size / pix_w,
                    image_size / pix_h
                )
                draw_w = pix_w * scale
                draw_h = pix_h * scale

                target = QRectF(
                    cx - draw_w / 2,
                    cy - draw_h / 2,
                    draw_w,
                    draw_h
                )

                painter.drawPixmap(
                    target,
                    body_pixmap,
                    QRectF(body_pixmap.rect())
                )

        elif is_belt_cluster:
            asteroid_color = QColor("#8f9498")
            asteroid_edge = QColor("#d9dde1")

            painter.setPen(
                QPen(asteroid_edge, 1)
            )
            painter.setBrush(
                QBrush(asteroid_color)
            )

            painter.drawEllipse(
                QRectF(cx - 22, cy - 7, 14, 14)
            )
            painter.drawEllipse(
                QRectF(cx - 5, cy - 15, 18, 18)
            )
            painter.drawEllipse(
                QRectF(cx + 13, cy - 5, 12, 12)
            )

        if bio_count > 0 and not is_belt_cluster:
            painter.setPen(
                QPen(
                    QColor("#39ff56"),
                    3
                )
            )
        elif geo_count > 0:
            painter.setPen(
                QPen(
                    QColor("#28c9e8"),
                    3
                )
            )

        if not is_belt_cluster and body_pixmap is None:
            painter.drawEllipse(
                QRectF(
                    cx - radius,
                    cy - radius,
                    radius * 2,
                    radius * 2
                )
            )

        if (
            not is_star
            and not is_belt_cluster
            and body_pixmap is None
        ):
            painter.setPen(
                QPen(
                    QColor(
                        255,
                        255,
                        255,
                        55
                    ),
                    1
                )
            )

            painter.drawArc(
                QRectF(
                    cx - radius + 4,
                    cy - radius + 7,
                    (radius - 4) * 2,
                    (radius - 7) * 2
                ),
                25 * 16,
                110 * 16
            )

        name = (
            body.get("short_name")
            or body.get("name")
            or "?"
        )

        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)

        painter.setPen(
            QColor("#f1f3f5")
        )

        painter.drawText(
            QRectF(
                x,
                y + 69,
                self.BODY_W,
                20
            ),
            Qt.AlignHCenter
            | Qt.AlignTop,
            name
        )

        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)

        painter.setPen(
            QColor("#b5bdc5")
        )

        painter.drawText(
            QRectF(
                x + 3,
                y + 88,
                self.BODY_W - 6,
                31
            ),
            Qt.AlignHCenter
            | Qt.TextWordWrap,
            self._type_text(body)
        )

        badge_count = 0

        if bio_count > 0 and not is_belt_cluster:
            badge_rect = QRectF(
                x + 22,
                y + 113,
                self.BODY_W - 44,
                19
            )

            painter.setPen(
                QPen(
                    QColor("#39ff56"),
                    1
                )
            )
            painter.setBrush(
                QColor(25, 110, 35, 105)
            )
            painter.drawRoundedRect(
                badge_rect, 5, 5
            )

            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(
                QColor("#7dff8c")
            )
            painter.drawText(
                badge_rect,
                Qt.AlignCenter,
                f"BIO ×{bio_count}"
            )
            badge_count += 1

        if geo_count > 0 and not is_belt_cluster:
            geo_y = 113 + badge_count * 21
            badge_rect = QRectF(
                x + 22,
                y + geo_y,
                self.BODY_W - 44,
                19
            )

            painter.setPen(
                QPen(
                    QColor("#28c9e8"),
                    1
                )
            )
            painter.setBrush(
                QColor(20, 95, 115, 110)
            )
            painter.drawRoundedRect(
                badge_rect, 5, 5
            )

            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.setPen(
                QColor("#76eaff")
            )
            painter.drawText(
                badge_rect,
                Qt.AlignCenter,
                f"GEO ×{geo_count}"
            )
            badge_count += 1

        meta = []

        if body.get("gravity_g") is not None:
            meta.append(
                f"{body['gravity_g']:.2f} g"
            )

        if body.get("distance_ls") is not None:
            meta.append(
                f"{body['distance_ls']:.1f} ls"
            )

        painter.setPen(
            QColor("#d3d7db")
        )

        painter.drawText(
            QRectF(
                x,
                y + (116 + badge_count * 21),
                self.BODY_W,
                17
            ),
            Qt.AlignHCenter
            | Qt.AlignTop,
            " · ".join(meta)
        )

        value_y = y + (136 + badge_count * 21)

        if is_belt_cluster:
            font.setBold(False)
            font.setPointSize(7)
            painter.setFont(font)
            painter.setPen(
                QColor("#65717c" if self._light_mode else "#8e969e")
            )
            painter.drawText(
                QRectF(
                    x + 4,
                    value_y + 10,
                    self.BODY_W - 8,
                    34
                ),
                Qt.AlignHCenter | Qt.TextWordWrap,
                "Keine Explorer-Auswertung"
            )

            markers = []

            if body.get("landable"):
                markers.append(
                    ("⌄", QColor("#d8dde3"))
                )

            marker_widths = [
                15 for _text, _color in markers
            ]
            total_marker_width = sum(marker_widths)
            marker_x = cx - total_marker_width / 2
            marker_y = y + 208

            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)

            for (text, marker_color), marker_width in zip(
                markers,
                marker_widths
            ):
                painter.setPen(marker_color)
                painter.drawText(
                    QRectF(
                        marker_x,
                        marker_y,
                        marker_width,
                        16
                    ),
                    Qt.AlignCenter,
                    text
                )
                marker_x += marker_width

            return

        value_rect = QRectF(
            x + 6,
            value_y,
            self.BODY_W - 12,
            48
        )

        painter.setPen(
            QPen(
                QColor("#27313a"),
                1
            )
        )

        painter.setBrush(
            QColor("#0b1117")
        )

        painter.drawRoundedRect(
            value_rect,
            4,
            4
        )

        font.setBold(False)
        font.setPointSize(7)
        painter.setFont(font)

        rows = [
            (
                "Scan",
                body.get("scan_value", 0)
            ),
            (
                "Kart.",
                None if is_star else body.get("mapped_value", 0)
            ),
            (
                "Aktuell",
                body.get("current_value", 0)
            ),
        ]

        ry = value_y + 3

        for label, value in rows:
            painter.setPen(
                QColor("#9099a2")
            )

            painter.drawText(
                QRectF(
                    x + 10,
                    ry,
                    48,
                    13
                ),
                Qt.AlignLeft
                | Qt.AlignVCenter,
                label
            )

            if (
                label == "Kart."
                and body.get("high_value")
            ):
                painter.setPen(
                    QColor("#ffb000")
                )

            elif (
                label == "Aktuell"
                and body.get("self_mapped")
            ):
                painter.setPen(
                    QColor("#79d45a")
                )

            else:
                painter.setPen(
                    QColor("#d3d7db")
                )

            painter.drawText(
                QRectF(
                    x + 55,
                    ry,
                    self.BODY_W - 65,
                    13
                ),
                Qt.AlignRight
                | Qt.AlignVCenter,
                (
                    "—"
                    if value is None
                    else self._format_credits(value)
                )
            )

            ry += 14

        markers = []

        if body.get("terraformable"):
            markers.append(
                ("T", QColor("#4bb8ff"))
            )

        if body.get("journal_scanned", True):
            if (
                body.get("was_discovered") is False
                and not self._already_discovered(body)
            ):
                markers.append(
                    ("★", QColor("#ffae28"))
                )

            if (
                not is_star
                and body.get("was_mapped") is False
                and not self._already_mapped(body)
            ):
                markers.append(
                    (
                        "◉✓"
                        if body.get("self_mapped")
                        else "◉",
                        QColor("#68c7ff")
                    )
                )

        if (
            not is_star
            and body.get("self_mapped")
        ):
            markers.append(
                ("◎", QColor("#65d067"))
            )

        if body.get("landable"):
            markers.append(
                ("⌄", QColor("#d8dde3"))
            )

        marker_widths = [
            (
                26
                if str(text) == "◉✓"
                else 15
            )
            for text, _color in markers
        ]

        total_marker_width = sum(marker_widths)

        marker_x = (
            cx
            - total_marker_width / 2
        )

        marker_y = y + 208

        if (
            body.get("edsm_known")
            and not body.get("journal_scanned", True)
        ):
            font.setBold(True)
            font.setPointSize(7)
            painter.setFont(font)
            painter.setPen(QColor("#65717c" if self._light_mode else "#7f8993"))
            painter.drawText(
                QRectF(
                    x,
                    y + 194,
                    self.BODY_W,
                    13
                ),
                Qt.AlignHCenter | Qt.AlignVCenter,
                "EDSM"
            )

        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)

        for (text, marker_color), marker_width in zip(
            markers,
            marker_widths
        ):
            painter.setPen(marker_color)

            painter.drawText(
                QRectF(
                    marker_x,
                    marker_y,
                    marker_width,
                    16
                ),
                Qt.AlignCenter,
                text
            )

            marker_x += marker_width

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )

        painter.fillRect(
            self.rect(),
            QColor("#080d12")
        )

        self._body_rects = []

        if not self.bodies:
            painter.setPen(
                QColor("#8e969e")
            )

            painter.drawText(
                28,
                50,
                "Für das aktuelle System liegen "
                "noch keine Scan-Daten im Journal vor."
            )

            return

        rows, children = self._layout_rows()

        positions = self._build_positions(
            rows
        )

        self._draw_connections(
            painter,
            rows,
            children,
            positions
        )

        for row in rows:
            for body, _level in row:
                pos = positions[
                    id(body)
                ]

                self._draw_body(
                    painter,
                    body,
                    pos["x"],
                    pos["y"]
                )

    def mouseMoveEvent(self, event):
        pos = event.position()

        for rect, body in self._body_rects:
            if rect.contains(pos):
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    self._tooltip(body),
                    self
                )
                return

        QToolTip.hideText()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position()

            for rect, body in self._body_rects:
                if rect.contains(pos):
                    self.bodyClicked.emit(body)
                    return

        super().mousePressEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)
