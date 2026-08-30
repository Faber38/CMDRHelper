from __future__ import annotations

from collections import defaultdict
from math import ceil, log10
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPixmap
from PySide6.QtWidgets import QWidget, QToolTip, QAbstractScrollArea

from cmdrhelper.i18n import tr


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

        # Rechte Maustaste: Systemkarte vertikal verschieben.
        self._right_drag_active = False
        self._right_drag_last_y = 0.0

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

    def _family_roots(self):
        children, by_id = self._children_map()
        roots = self._roots(by_id)
        return roots, children, by_id

    def _subtree_units(self, body, children, memo):
        """
        Ermittelt, wie viel horizontalen Platz ein Ast benötigt.

        Ein Blatt benötigt eine Einheit. Ein Elternkörper erhält mindestens
        so viel Platz wie alle seine Kinder zusammen. Dadurch bleiben Monde
        sichtbar unter ihrem Planeten und Familien überschneiden sich nicht.
        """
        key = id(body)
        if key in memo:
            return memo[key]

        items = children.get(body.get("body_id"), [])
        if not items:
            memo[key] = 1
            return 1

        units = max(
            1,
            sum(self._subtree_units(child, children, memo) for child in items)
        )
        memo[key] = units
        return units

    def _tree_layout(self):
        """
        Elite-artige Systemkarte.

        Jeder Root-Körper (typischerweise Stern) bildet eine eigene Familie.
        Kinder liegen unterhalb ihres Parents; Monde wiederum unterhalb ihres
        Planeten. Die reale Parent-Struktur aus dem Journal bleibt erhalten.
        """
        roots, children, _by_id = self._family_roots()

        if not roots:
            return {}, children, [], 1, 1

        memo = {}
        x_step = self.BODY_W + self.X_GAP
        y_step = self.BODY_H + 42

        positions = {}
        families = []

        cursor_units = 0
        max_depth = 0
        family_gap_units = 1

        def place(body, depth, left_unit):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            body_children = children.get(body.get("body_id"), [])
            subtree_units = self._subtree_units(body, children, memo)

            if body_children:
                child_cursor = left_unit
                child_centers = []

                for child in body_children:
                    child_units = self._subtree_units(child, children, memo)
                    child_center = place(child, depth + 1, child_cursor)
                    child_centers.append(child_center)
                    child_cursor += child_units

                center_unit = (
                    child_centers[0] + child_centers[-1]
                ) / 2.0
            else:
                center_unit = left_unit + 0.5

            x = (
                self.MARGIN_X
                + center_unit * x_step
                - self.BODY_W / 2
            )
            y = self.MARGIN_Y + depth * y_step

            positions[id(body)] = {
                "x": x,
                "y": y,
                "body": body,
                "level": depth,
                "center_unit": center_unit,
            }

            return center_unit

        for root in roots:
            units = self._subtree_units(root, children, memo)
            family_left = cursor_units

            place(root, 0, family_left)

            families.append(
                {
                    "root": root,
                    "left_unit": family_left,
                    "units": units,
                }
            )

            cursor_units += units + family_gap_units

        used_units = max(1, cursor_units - family_gap_units)
        return positions, children, families, used_units, max_depth + 1

    def _update_size(self):
        positions, _children, _families, used_units, depth_count = (
            self._tree_layout()
        )

        x_step = self.BODY_W + self.X_GAP
        y_step = self.BODY_H + 42

        width = (
            self.MARGIN_X * 2
            + used_units * x_step
        )

        height = (
            self.MARGIN_Y * 2
            + max(1, depth_count) * y_step
        )

        # Falls ein sehr breiter Parent über viele Kinder zentriert wurde,
        # die tatsächlichen Körperrechtecke ebenfalls berücksichtigen.
        if positions:
            right = max(
                pos["x"] + self.BODY_W
                for pos in positions.values()
            )
            width = max(width, right + self.MARGIN_X)

        self.setMinimumSize(
            max(900, int(width)),
            max(360, int(height))
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
            "K_OrangeGiant": "star_k_orange_giant.png",
            "M": "star_m.png",
            "M_RedGiant": "star_m_red_giant.png",
            "M_RedSuperGiant": "star_m_red_super_giant.png",
            "B_BlueWhiteSuperGiant": "star_b_blue_white_super_giant.png",
            "A_BlueWhiteSuperGiant": "star_a_blue_white_super_giant.png",
            "F_WhiteSuperGiant": "star_f_white_super_giant.png",
            "G_WhiteSuperGiant": "star_g_white_super_giant.png",
            "L": "star_l.png",
            "T": "star_t.png",
            "Y": "star_y.png",
            "TTS": "star_t_tauri.png",
            "AeBe": "star_herbig_aebe.png",
            "N": "star_neutron.png",
            "Neutron": "star_neutron.png",
            "H": "black_hole.png",
            "BlackHole": "black_hole.png",
            "SupermassiveBlackHole": "black_hole_supermassive.png",
            "D": "star_white_dwarf.png",
            "DA": "star_white_dwarf.png",
            "DAB": "star_white_dwarf.png",
            "DAO": "star_white_dwarf.png",
            "DAZ": "star_white_dwarf.png",
            "DAV": "star_white_dwarf.png",
            "DB": "star_white_dwarf.png",
            "DBZ": "star_white_dwarf.png",
            "DBV": "star_white_dwarf.png",
            "DO": "star_white_dwarf.png",
            "DOV": "star_white_dwarf.png",
            "DQ": "star_white_dwarf.png",
            "DC": "star_white_dwarf.png",
            "DCV": "star_white_dwarf.png",
            "DX": "star_white_dwarf.png",
            "WhiteDwarf": "star_white_dwarf.png",

            # Wolf-Rayet-Sterne
            "W": "star_w_wolf_rayet.png",
            "WN": "star_wn_wolf_rayet.png",
            "WNC": "star_wnc_wolf_rayet.png",
            "WC": "star_wc_wolf_rayet.png",
            "WO": "star_wo_wolf_rayet.png",

            # Kohlenstoff- und S-Sterne
            "C": "star_c_carbon.png",
            "CS": "star_cs_carbon.png",
            "CN": "star_cn_carbon.png",
            "CJ": "star_cj_carbon.png",
            "CHd": "star_chd_carbon.png",
            "MS": "star_ms.png",
            "S": "star_s.png",
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

        visual_size = (
            min_size
            + factor * (max_size - min_size)
        )

        if is_star:
            star_type = str(body.get("star_type") or "").strip()

            # Giants and supergiants should be immediately recognizable
            # in the system map. The real radius still determines the base
            # size, but these stellar classes receive a sensible visual
            # minimum without becoming so large that they break the layout.
            giant_types = {
                "K_OrangeGiant",
                "M_RedGiant",
            }
            supergiant_types = {
                "B_BlueWhiteSuperGiant",
                "A_BlueWhiteSuperGiant",
                "F_WhiteSuperGiant",
                "G_WhiteSuperGiant",
                "M_RedSuperGiant",
            }

            if star_type in supergiant_types:
                visual_size = max(132.0, visual_size)
            elif star_type in giant_types:
                visual_size = max(112.0, visual_size)

        return visual_size

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
            return tr("system_view.type.asteroid_cluster")

        if body.get("star_type"):
            star = body["star_type"]

            star_names = {
                "O": "o_star",
                "B": "b_star",
                "A": "a_star",
                "F": "f_star",
                "G": "g_star",
                "K": "k_star",
                "M": "m_star",
                "L": "l_dwarf",
                "T": "t_dwarf",
                "Y": "y_dwarf",
                "TTS": "t_tauri",
                "AeBe": "herbig_aebe",
                "N": "neutron",
                "Neutron": "neutron",
                "H": "black_hole",
                "BlackHole": "black_hole",
                "SupermassiveBlackHole": "supermassive_black_hole",
                "D": "white_dwarf",
                "DA": "white_dwarf",
                "DAB": "white_dwarf",
                "DAO": "white_dwarf",
                "DAZ": "white_dwarf",
                "DAV": "white_dwarf",
                "DB": "white_dwarf",
                "DBZ": "white_dwarf",
                "DBV": "white_dwarf",
                "DO": "white_dwarf",
                "DOV": "white_dwarf",
                "DQ": "white_dwarf",
                "DC": "white_dwarf",
                "DCV": "white_dwarf",
                "DX": "white_dwarf",
                "WhiteDwarf": "white_dwarf",
            }

            star_key = star_names.get(star)
            if star_key:
                return tr(f"system_view.type.{star_key}")

            return tr("system_view.type.generic_star", star=star)

        planet = body.get("planet_class") or ""

        replacements = {
            "High metal content body": "hmc",
            "Metal rich body": "metal_rich",
            "Rocky body": "rocky",
            "Icy body": "icy",
            "Rocky ice body": "rocky_ice",
            "Earthlike body": "earthlike",
            "Water world": "water_world",
            "Ammonia world": "ammonia_world",
            "Sudarsky class I gas giant": "gas_i",
            "Sudarsky class II gas giant": "gas_ii",
            "Sudarsky class III gas giant": "gas_iii",
            "Sudarsky class IV gas giant": "gas_iv",
            "Sudarsky class V gas giant": "gas_v",
            "Class I gas giant": "gas_i",
            "Class II gas giant": "gas_ii",
            "Class III gas giant": "gas_iii",
            "Class IV gas giant": "gas_iv",
            "Class V gas giant": "gas_v",
            "Gas giant with water based life": "gas_water_life",
            "Gas giant with ammonia based life": "gas_ammonia_life",
            "Helium rich gas giant": "helium_rich_gas",
            "Helium gas giant": "helium_gas",
            "Water giant": "water_giant",
            "Water giant with life": "water_giant_life",
        }

        planet_key = replacements.get(planet)
        if planet_key:
            return tr(f"system_view.type.{planet_key}")

        return planet or tr("system_view.type.planet")

    def _tooltip(self, body):
        if self._is_belt_cluster(body):
            name = (
                body.get("name")
                or body.get("short_name")
                or tr("system_view.type.asteroid_cluster")
            )

            parts = [
                name,
                tr("system_view.type.asteroid_cluster"),
                "",
                tr("system_view.no_explorer_cartography"),
            ]

            if body.get("distance_ls") is not None:
                parts.insert(
                    2,
                    tr(
                        "system_view.distance_ls",
                        value=f"{body['distance_ls']:.1f}",
                    ),
                )

            return "\n".join(parts)

        parts = [
            body.get("name")
            or body.get("short_name")
            or tr("body_detail.body"),
            self._type_text(body),
        ]

        if body.get("gravity_g") is not None:
            parts.append(
                tr(
                    "system_view.gravity_g",
                    value=f"{body['gravity_g']:.2f}",
                )
            )

        if body.get("distance_ls") is not None:
            parts.append(
                tr(
                    "system_view.distance_ls",
                    value=f"{body['distance_ls']:.1f}",
                )
            )

        if body.get("landable"):
            parts.append(tr("body_detail.landable"))

        if body.get("terraformable"):
            parts.append(tr("body_detail.terraforming_candidate"))

        if body.get("biological_signals"):
            parts.append(
                tr(
                    "system_view.biological_signals",
                    count=body["biological_signals"],
                )
            )

        if body.get("geological_signals"):
            parts.append(
                tr(
                    "system_view.geological_signals",
                    count=body["geological_signals"],
                )
            )

        if body.get("atmosphere"):
            parts.append(
                tr(
                    "system_view.atmosphere",
                    value=body["atmosphere"],
                )
            )

        if body.get("volcanism"):
            parts.append(
                tr(
                    "system_view.volcanism",
                    value=body["volcanism"],
                )
            )

        if body.get("journal_scanned", True):
            was_discovered = body.get("was_discovered")
            was_mapped = body.get("was_mapped")
            self_mapped = bool(body.get("self_mapped"))

            if (
                was_discovered is False
                and not self._already_discovered(body)
            ):
                parts.append(tr("system_view.first_discovery_possible"))
            elif self._already_discovered(body):
                parts.append(tr("system_view.already_discovered"))

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
                        parts.append(tr("system_view.first_mapping_claimed"))
                    else:
                        parts.append(tr("system_view.first_mapping_possible"))
                elif self._already_mapped(body):
                    parts.append(tr("system_view.already_mapped"))

                if self_mapped:
                    parts.append(tr("system_view.mapped_by_you"))
        elif body.get("edsm_known"):
            parts.append(tr("system_view.edsm_wait_own_scan"))

        parts.append("")

        parts.append(
            tr(
                "system_view.scan_value",
                value=self._format_credits(body.get("scan_value", 0)),
            )
        )
        parts.append(
            tr(
                "system_view.mapped_value",
                value=self._format_credits(body.get("mapped_value", 0)),
            )
        )
        parts.append(
            tr(
                "system_view.current_value",
                value=self._format_credits(body.get("current_value", 0)),
            )
        )

        if body.get("high_value"):
            parts.append(tr("system_view.worthwhile"))

        return "\n".join(parts)

    def _draw_tree_connections(
        self,
        painter,
        children,
        positions
    ):
        """
        Rechtwinklige Parent-/Child-Verbindungen ähnlich der Elite-Systemkarte.
        """
        painter.setPen(
            QPen(
                QColor("#7f8993"),
                1.2
            )
        )

        for parent_pos in positions.values():
            body = parent_pos["body"]
            body_children = [
                child
                for child in children.get(body.get("body_id"), [])
                if id(child) in positions
            ]

            if not body_children:
                continue

            px = parent_pos["x"] + self.BODY_W / 2
            parent_bottom = parent_pos["y"] + self.BODY_H

            child_centers = [
                positions[id(child)]["x"] + self.BODY_W / 2
                for child in body_children
            ]
            child_tops = [
                positions[id(child)]["y"]
                for child in body_children
            ]

            nearest_child_top = min(child_tops)
            bus_y = parent_bottom + (
                nearest_child_top - parent_bottom
            ) * 0.45

            # Stamm vom Parent zur gemeinsamen Orbit-/Familienlinie.
            painter.drawLine(
                int(px),
                int(parent_bottom),
                int(px),
                int(bus_y)
            )

            # Gemeinsame horizontale Linie über alle direkten Kinder.
            if len(child_centers) > 1:
                painter.drawLine(
                    int(min(child_centers)),
                    int(bus_y),
                    int(max(child_centers)),
                    int(bus_y)
                )

            # Jedes Kind hängt senkrecht an der gemeinsamen Linie.
            for child in body_children:
                child_pos = positions[id(child)]
                cx = child_pos["x"] + self.BODY_W / 2
                cy = child_pos["y"]

                # Bei nur einem Kind braucht es trotzdem die horizontale
                # Verbindung, wenn Parent und Kind nicht exakt übereinander
                # liegen.
                if len(child_centers) == 1 and abs(cx - px) > 1:
                    painter.drawLine(
                        int(px),
                        int(bus_y),
                        int(cx),
                        int(bus_y)
                    )

                painter.drawLine(
                    int(cx),
                    int(bus_y),
                    int(cx),
                    int(cy)
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
                tr("system_view.no_explorer_evaluation")
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
                tr("system_view.value_scan"),
                body.get("scan_value", 0)
            ),
            (
                tr("system_view.value_mapping"),
                None if is_star else body.get("mapped_value", 0)
            ),
            (
                tr("system_view.value_current"),
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
                label == tr("system_view.value_mapping")
                and body.get("high_value")
            ):
                painter.setPen(
                    QColor("#ffb000")
                )

            elif (
                label == tr("system_view.value_current")
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
                tr("system_view.no_scan_data")
            )

            return

        positions, children, _families, _used_units, _depth_count = (
            self._tree_layout()
        )

        self._draw_tree_connections(
            painter,
            children,
            positions
        )

        # Erst Eltern, dann tiefere Ebenen zeichnen.
        ordered = sorted(
            positions.values(),
            key=lambda item: (
                item["level"],
                item["x"],
            )
        )

        for pos in ordered:
            self._draw_body(
                painter,
                pos["body"],
                pos["x"],
                pos["y"]
            )

    def body_center(self, body):
        """
        Liefert den Mittelpunkt eines Körpers in Widget-Koordinaten.
        Praktisch, damit eine äußere ScrollArea gezielt dorthin springen kann.
        """
        positions, _children, _families, _used_units, _depth_count = (
            self._tree_layout()
        )

        pos = positions.get(id(body))
        if pos is None:
            return None

        return (
            float(pos["x"] + self.BODY_W / 2),
            float(pos["y"] + self.BODY_H / 2),
        )

    def _scroll_area(self):
        """Die umgebende ScrollArea der Explorer-Systemkarte finden."""
        parent = self.parentWidget()

        while parent is not None:
            if isinstance(parent, QAbstractScrollArea):
                return parent
            parent = parent.parentWidget()

        return None

    def wheelEvent(self, event):
        """Mausrad über der Systemkarte zum horizontalen Scrollen."""
        scroll_area = self._scroll_area()

        if scroll_area is None:
            super().wheelEvent(event)
            return

        bar = scroll_area.horizontalScrollBar()
        delta = event.angleDelta()
        wheel_delta = delta.x() if delta.x() else delta.y()

        if wheel_delta == 0:
            event.ignore()
            return

        # Hoch = links, runter = rechts.
        pixels = int((wheel_delta / 120.0) * 90)
        bar.setValue(bar.value() - pixels)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._right_drag_active:
            scroll_area = self._scroll_area()

            if scroll_area is not None:
                current_y = float(event.position().y())
                delta_y = current_y - self._right_drag_last_y
                self._right_drag_last_y = current_y

                bar = scroll_area.verticalScrollBar()
                bar.setValue(bar.value() - int(delta_y))

            QToolTip.hideText()
            event.accept()
            return

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
        if event.button() == Qt.RightButton:
            if self._scroll_area() is not None:
                self._right_drag_active = True
                self._right_drag_last_y = float(event.position().y())
                self.setCursor(Qt.ClosedHandCursor)
                QToolTip.hideText()
                event.accept()
                return

        if event.button() == Qt.LeftButton:
            pos = event.position()

            for rect, body in self._body_rects:
                if rect.contains(pos):
                    self.bodyClicked.emit(body)
                    return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton and self._right_drag_active:
            self._right_drag_active = False
            self.unsetCursor()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)
