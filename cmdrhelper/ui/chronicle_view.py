from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget, QToolTip

from cmdrhelper.i18n import tr


class ChronicleMapWidget(QWidget):
    """
    Interaktive 3D-Chronik auf Basis der Elite-StarPos-Koordinaten.

    Bedienung:
      - Linksklick auf System: auswählen
      - Linke Maustaste auf freie Fläche ziehen: Karte drehen
      - Mittlere oder rechte Maustaste ziehen: Karte verschieben
      - Mausrad: Zoom
      - Doppelklick auf freie Fläche: Ansicht zurücksetzen
    """

    systemClicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.systems = []

        # Kamera / Projektion
        self.scale = 1.0
        self.pan = QPointF()
        self.yaw = math.radians(-28.0)
        self.pitch = math.radians(24.0)

        self._center = (0.0, 0.0, 0.0)
        self._drag_start = None
        self._drag_mode = None
        self._rotation_pivot_screen = None
        self._rotation_pivot_world = None

        # Zoom-Rahmen mit mittlerer Maustaste
        self._zoom_rect_start = None
        self._zoom_rect_end = None

        self.hover_index = -1
        self.selected_address = None

        # Aktuell vom Commander besuchtes System.
        # Wird unabhängig von der normalen Auswahl gelb hervorgehoben.
        self.current_system_name = ""
        self.current_system_address = None

        # Stilisiertes Milchstraßen-Modell als räumliche Orientierung.
        # Sol liegt im Elite-Koordinatensystem bei (0, 0, 0).
        self.show_galaxy = True
        self.galaxy_radius = 52000.0
        self.galaxy_half_thickness = 1800.0
        self.galactic_center = (0.0, 0.0, 25899.0)
        self._galaxy_points = self._build_galaxy_points()

        self.setMinimumSize(700, 520)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Daten / Ansicht
    # ------------------------------------------------------------------

    def set_systems(self, systems):
        selected = self.selected_address
        self.systems = list(systems or [])

        if selected is not None and not any(
            s.get("system_address") == selected
            for s in self.systems
        ):
            self.selected_address = None

        self.fit_map()
        self.update()

    def set_current_system(self, system_name):
        """Markiert das aktuell besuchte System in der Chronik."""
        self.current_system_name = str(system_name or "").strip()
        self.current_system_address = None

        if self.current_system_name:
            wanted = self.current_system_name.casefold()
            for system in self.systems:
                name = str(system.get("name") or "").strip()
                if name.casefold() == wanted:
                    self.current_system_address = system.get("system_address")
                    break

        self.update()

    def focus_current_system(self):
        """Zentriert die Ansicht auf das aktuell besuchte System."""
        if not self.current_system_name:
            return False

        wanted = self.current_system_name.casefold()
        current = None

        for system in self.systems:
            name = str(system.get("name") or "").strip()
            if name.casefold() == wanted:
                current = system
                break

        if current is None:
            return False

        # Das aktuelle System wird zum echten Mittelpunkt der 3D-Ansicht.
        self._center = (
            float(current.get("x") or 0.0),
            float(current.get("y") or 0.0),
            float(current.get("z") or 0.0),
        )
        self.pan = QPointF()

        # Sinnvoller Nah-Zoom, ohne eine bereits stärkere Vergrößerung
        # des Benutzers unnötig zurückzusetzen.
        self.scale = max(self.scale, 0.12)

        self.hover_index = -1
        self.update()
        return True

    def fit_map(self):
        if not self.systems:
            self.scale = 1.0
            self.pan = QPointF()
            self._center = (0.0, 0.0, 0.0)
            return

        xs = [float(s["x"]) for s in self.systems]
        ys = [float(s["y"]) for s in self.systems]
        zs = [float(s["z"]) for s in self.systems]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        self._center = (
            (min_x + max_x) / 2.0,
            (min_y + max_y) / 2.0,
            (min_z + max_z) / 2.0,
        )

        span = max(
            max_x - min_x,
            max_y - min_y,
            max_z - min_z,
            100.0,
        )

        usable = max(
            260.0,
            min(self.width(), self.height()) - 120.0,
        )

        self.scale = max(
            0.0001,
            min(usable / span, 25.0),
        )

        self.pan = QPointF()

    def reset_view(self):
        self.yaw = math.radians(-28.0)
        self.pitch = math.radians(24.0)
        self.fit_map()
        self.update()

    def align_galaxy(self):
        """
        Richtet die Galaxie wieder sauber als Draufsicht auf die
        galaktische Ebene aus. Zoom und Pan bleiben erhalten.
        """
        self.yaw = 0.0
        self.pitch = math.pi / 2.0
        self.update()

    # ------------------------------------------------------------------
    # 3D Projektion
    # ------------------------------------------------------------------

    def _camera_coordinates(self, system):
        cx, cy, cz = self._center

        x = float(system["x"]) - cx
        y = float(system["y"]) - cy
        z = float(system["z"]) - cz

        # Drehung um galaktische Y-Achse (Yaw)
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)

        x1 = x * cos_yaw - z * sin_yaw
        z1 = x * sin_yaw + z * cos_yaw

        # Drehung um X-Achse (Pitch)
        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)

        y2 = y * cos_pitch - z1 * sin_pitch
        depth = y * sin_pitch + z1 * cos_pitch

        return x1, y2, depth

    def _project(self, system):
        x, y, depth = self._camera_coordinates(system)

        # Leichte Perspektive. Große Galaxiereisen bleiben so lesbar,
        # ohne dass nahe Punkte übertrieben groß werden.
        perspective = 1.0

        if self.systems:
            depths = [
                self._camera_coordinates(s)[2]
                for s in self.systems[::max(1, len(self.systems) // 80)]
            ]
            if depths:
                depth_span = max(
                    max(depths) - min(depths),
                    1.0,
                )
                perspective = 1.0 + (depth / depth_span) * 0.16
                perspective = max(0.82, min(1.18, perspective))

        px = (
            self.width() / 2.0
            + x * self.scale * perspective
            + self.pan.x()
        )

        py = (
            self.height() / 2.0
            - y * self.scale * perspective
            + self.pan.y()
        )

        return QPointF(px, py), depth, perspective


    def _build_galaxy_points(self):
        """Erzeugt eine leichte, reproduzierbare Spiralgalaxie."""
        points = []

        for arm in range(4):
            arm_offset = arm * (math.pi / 2.0)

            for i in range(115):
                t = i / 114.0
                radius = 3500.0 + t * (self.galaxy_radius - 3500.0)
                angle = arm_offset + 1.25 + t * 5.15

                wobble = (
                    math.sin(i * 1.73 + arm * 2.1) * 1050.0
                    + math.sin(i * 0.47 + arm) * 520.0
                )
                radius2 = radius + wobble

                x = radius2 * math.cos(angle)
                z = radius2 * math.sin(angle)
                y = (
                    math.sin(i * 2.31 + arm * 0.8)
                    * self.galaxy_half_thickness
                    * (0.30 + 0.70 * t)
                )

                points.append(
                    (
                        x + self.galactic_center[0],
                        y + self.galactic_center[1],
                        z + self.galactic_center[2],
                        0.22 + (1.0 - t) * 0.35,
                    )
                )

        for i in range(150):
            angle = i * 2.399963229728653
            radius = 10500.0 * math.sqrt((i + 1) / 150.0)

            x = radius * math.cos(angle)
            z = radius * math.sin(angle) * 0.72
            y = (
                math.sin(i * 1.91)
                * self.galaxy_half_thickness
                * 1.8
                * (1.0 - min(radius / 12000.0, 0.85))
            )

            points.append(
                (
                    x + self.galactic_center[0],
                    y + self.galactic_center[1],
                    z + self.galactic_center[2],
                    0.42,
                )
            )

        return points

    def _camera_coordinates_xyz(self, x, y, z):
        cx, cy, cz = self._center

        x = float(x) - cx
        y = float(y) - cy
        z = float(z) - cz

        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)

        x1 = x * cos_yaw - z * sin_yaw
        z1 = x * sin_yaw + z * cos_yaw

        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)

        y2 = y * cos_pitch - z1 * sin_pitch
        depth = y * sin_pitch + z1 * cos_pitch

        return x1, y2, depth

    def _project_xyz(self, x, y, z):
        x2, y2, depth = self._camera_coordinates_xyz(x, y, z)

        px = self.width() / 2.0 + x2 * self.scale + self.pan.x()
        py = self.height() / 2.0 - y2 * self.scale + self.pan.y()

        return QPointF(px, py), depth

    def _draw_galaxy(self, painter):
        if not self.show_galaxy:
            return

        from PySide6.QtGui import QPolygonF

        gcx, gcy, gcz = self.galactic_center
        ring = []

        for i in range(96):
            angle = (i / 96.0) * math.tau
            x = gcx + math.cos(angle) * self.galaxy_radius
            z = gcz + math.sin(angle) * self.galaxy_radius
            point, _ = self._project_xyz(x, gcy, z)
            ring.append(point)

        if ring:
            painter.setPen(QPen(QColor(86, 108, 128, 55), 1))
            painter.setBrush(QBrush(QColor(50, 62, 78, 18)))
            painter.drawPolygon(QPolygonF(ring))

        for x, y, z, strength in self._galaxy_points:
            point, _depth = self._project_xyz(x, y, z)

            if not self.rect().adjusted(-10, -10, 10, 10).contains(
                point.toPoint()
            ):
                continue

            alpha = int(35 + 85 * strength)
            radius = 0.8 + strength * 1.4

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(160, 178, 196, alpha)))
            painter.drawEllipse(point, radius, radius)

        center_point, _ = self._project_xyz(gcx, gcy, gcz)
        painter.setPen(QPen(QColor(255, 190, 90, 150), 1))
        painter.setBrush(QBrush(QColor(255, 175, 65, 105)))
        painter.drawEllipse(center_point, 6.0, 6.0)
        painter.drawText(
            int(center_point.x() + 10),
            int(center_point.y() - 7),
            tr("chronicle.galactic_center"),
        )

        sol_point, _ = self._project_xyz(0.0, 0.0, 0.0)
        painter.setPen(QPen(QColor(255, 235, 155, 190), 1))
        painter.setBrush(QBrush(QColor(255, 220, 110, 170)))
        painter.drawEllipse(sol_point, 4.5, 4.5)
        painter.drawText(
            int(sol_point.x() + 9),
            int(sol_point.y() + 14),
            "Sol",
        )

    # ------------------------------------------------------------------
    # Zeichnen
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(
            self.rect(),
            QColor("#071017"),
        )

        self._draw_grid(painter)
        self._draw_galaxy(painter)
        self._draw_axis_indicator(painter)

        if not self.systems:
            painter.setPen(QColor("#93a4b2"))
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "Noch keine Systeme mit Koordinaten.\n"
                "Journal-Archiv unter Einstellungen erneut importieren.",
            )
            return

        projected = [
            (i, system, *self._project(system))
            for i, system in enumerate(self.systems)
        ]

        # Route zuerst zeichnen.
        painter.setPen(
            QPen(
                QColor("#d89224"),
                1.5,
            )
        )

        for first, second in zip(
            projected,
            projected[1:],
        ):
            painter.drawLine(
                first[2],
                second[2],
            )

        # Entfernte Punkte zuerst, nahe Punkte zuletzt.
        projected_sorted = sorted(
            projected,
            key=lambda item: item[3],
        )

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        for index, system, point, depth, perspective in projected_sorted:
            hover = index == self.hover_index
            selected = (
                system.get("system_address")
                == self.selected_address
            )
            current = (
                self.current_system_address is not None
                and system.get("system_address")
                == self.current_system_address
            )

            radius = 4.0 * perspective

            if hover:
                radius = 6.0
            if selected:
                radius = 7.0
            if current:
                radius = 8.0

            if current:
                # Aktuelle Commander-Position: bewusst kräftig gelb,
                # damit sie auch in einer dichten Route sofort auffällt.
                painter.setPen(
                    QPen(
                        QColor("#fff6a0"),
                        2.5,
                    )
                )
                painter.setBrush(
                    QBrush(
                        QColor("#ffd400")
                    )
                )
            elif selected:
                painter.setPen(
                    QPen(
                        QColor("#ffffff"),
                        2,
                    )
                )
                painter.setBrush(
                    QBrush(
                        QColor("#ff9d00")
                    )
                )
            elif hover:
                painter.setPen(
                    QPen(
                        QColor("#ffe29a"),
                        1.5,
                    )
                )
                painter.setBrush(
                    QBrush(
                        QColor("#ffb000")
                    )
                )
            else:
                painter.setPen(
                    QPen(
                        QColor("#8fe7ff"),
                        1,
                    )
                )
                painter.setBrush(
                    QBrush(
                        QColor("#22b7d6")
                    )
                )

            painter.drawEllipse(
                point,
                radius,
                radius,
            )

            if hover or selected or current:
                painter.setPen(
                    QColor("#fff3a6") if current else QColor("#e9f1f5")
                )
                painter.drawText(
                    int(point.x() + 11),
                    int(point.y() - 9),
                    system.get("name") or "Unbekannt",
                )

        self._draw_zoom_rect(painter)
        self._draw_help(painter)

    def _draw_grid(self, painter):
        painter.setPen(
            QPen(
                QColor("#13242e"),
                1,
            )
        )

        step = 100

        for x in range(
            0,
            self.width(),
            step,
        ):
            painter.drawLine(
                x,
                0,
                x,
                self.height(),
            )

        for y in range(
            0,
            self.height(),
            step,
        ):
            painter.drawLine(
                0,
                y,
                self.width(),
                y,
            )

    def _draw_axis_indicator(self, painter):
        origin = QPointF(
            72,
            self.height() - 70,
        )

        length = 38.0

        # Kamera-projizierte Einheitsachsen.
        axes = [
            ((1.0, 0.0, 0.0), "X", QColor("#ff6b6b")),
            ((0.0, 1.0, 0.0), "Y", QColor("#65d067")),
            ((0.0, 0.0, 1.0), "Z", QColor("#68c7ff")),
        ]

        for vector, label, color in axes:
            x, y, z = vector

            cos_yaw = math.cos(self.yaw)
            sin_yaw = math.sin(self.yaw)

            x1 = x * cos_yaw - z * sin_yaw
            z1 = x * sin_yaw + z * cos_yaw

            cos_pitch = math.cos(self.pitch)
            sin_pitch = math.sin(self.pitch)

            y2 = y * cos_pitch - z1 * sin_pitch

            end = QPointF(
                origin.x() + x1 * length,
                origin.y() - y2 * length,
            )

            painter.setPen(
                QPen(
                    color,
                    2,
                )
            )
            painter.drawLine(
                origin,
                end,
            )
            painter.drawText(
                int(end.x() + 4),
                int(end.y() - 3),
                label,
            )

        painter.setPen(
            QColor("#7d8c98")
        )
        painter.drawText(
            20,
            self.height() - 18,
            "3D: X / Y / Z",
        )

    def _draw_zoom_rect(self, painter):
        if (
            self._zoom_rect_start is None
            or self._zoom_rect_end is None
        ):
            return

        x1 = self._zoom_rect_start.x()
        y1 = self._zoom_rect_start.y()
        x2 = self._zoom_rect_end.x()
        y2 = self._zoom_rect_end.y()

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width < 2 or height < 2:
            return

        from PySide6.QtCore import QRectF

        rect = QRectF(
            left,
            top,
            width,
            height,
        )

        painter.setPen(
            QPen(
                QColor(120, 220, 140, 220),
                1.5,
                Qt.DashLine,
            )
        )
        painter.setBrush(
            QBrush(
                QColor(90, 180, 110, 28)
            )
        )
        painter.drawRect(rect)

    def _draw_help(self, painter):
        painter.setPen(
            QColor("#6f808c")
        )

        painter.drawText(
            16,
            24,
            tr("chronicle.map_controls"),
        )

    def _screen_to_galactic_plane(self, pos):
        """
        Wandelt die Mausposition bei der aktuellen orthografischen Kamera
        in einen Punkt auf der galaktischen Ebene Y=0 um.

        Damit kann die Szene tatsächlich um den angeklickten Ort gedreht
        werden, statt nur die 2D-Pan-Position nachzuahmen.
        """
        if self.scale == 0:
            return None

        cx, cy, cz = self._center

        camera_x = (
            pos.x()
            - self.width() / 2.0
            - self.pan.x()
        ) / self.scale

        camera_y = -(
            pos.y()
            - self.height() / 2.0
            - self.pan.y()
        ) / self.scale

        # Welt-Y=0 entspricht relativ zum Kartenmittelpunkt y=-cy.
        world_y_rel = -float(cy)

        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)

        # Bei nahezu exakt horizontaler Ansicht ist der Schnitt mit Y=0
        # numerisch nicht eindeutig. Dann lieber auf die Kartenmitte fallen.
        if abs(sin_pitch) < 0.035:
            return (
                float(cx),
                0.0,
                float(cz),
            )

        # y2 = y*cos(pitch) - z1*sin(pitch)
        z1 = (
            world_y_rel * cos_pitch
            - camera_y
        ) / sin_pitch

        x1 = camera_x

        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)

        # Inverse Yaw-Drehung.
        world_x_rel = (
            x1 * cos_yaw
            + z1 * sin_yaw
        )
        world_z_rel = (
            -x1 * sin_yaw
            + z1 * cos_yaw
        )

        return (
            world_x_rel + cx,
            0.0,
            world_z_rel + cz,
        )

    def _project_world_pivot(self, pivot):
        if pivot is None:
            return None

        point, _depth = self._project_xyz(
            pivot[0],
            pivot[1],
            pivot[2],
        )
        return point

    # ------------------------------------------------------------------
    # Maus
    # ------------------------------------------------------------------

    def wheelEvent(self, event):
        factor = (
            1.16
            if event.angleDelta().y() > 0
            else 1.0 / 1.16
        )

        self.scale = max(
            0.00005,
            min(
                self.scale * factor,
                80.0,
            ),
        )

        self.update()

    def mousePressEvent(self, event):
        self._drag_start = event.position()
        self._press_hit = self._hit(event.position())
        self._dragged = False

        if event.button() == Qt.LeftButton:
            self._drag_mode = "rotate"

            # Echter 3D-Drehpunkt:
            # - System getroffen -> dessen StarPos
            # - freie Fläche -> Punkt auf galaktischer Ebene unter der Maus
            if self._press_hit >= 0:
                system = self.systems[self._press_hit]
                pivot = (
                    float(system.get("x") or 0.0),
                    float(system.get("y") or 0.0),
                    float(system.get("z") or 0.0),
                )
            else:
                pivot = self._screen_to_galactic_plane(
                    event.position()
                )

            if pivot is not None:
                self._rotation_pivot_world = pivot

                # Der Drehpunkt wird zum echten Kamera-/Rotationszentrum.
                self._center = (
                    float(pivot[0]),
                    float(pivot[1]),
                    float(pivot[2]),
                )

                # Nach dem Wechsel des Zentrums liegt der Pivot geometrisch
                # bei (0,0,0). Pan wird so gesetzt, dass genau dieser Punkt
                # unter der Maus bleibt und die Ansicht beim Drücken nicht springt.
                self.pan = QPointF(
                    event.position().x() - self.width() / 2.0,
                    event.position().y() - self.height() / 2.0,
                )

            self._rotation_pivot_screen = QPointF(
                event.position()
            )

        elif event.button() == Qt.RightButton:
            self._drag_mode = "pan"
            self._rotation_pivot_screen = None
            self._rotation_pivot_world = None

        elif event.button() == Qt.MiddleButton:
            self._drag_mode = "zoom_rect"
            self._rotation_pivot_screen = None
            self._rotation_pivot_world = None
            self._zoom_rect_start = QPointF(
                event.position()
            )
            self._zoom_rect_end = QPointF(
                event.position()
            )

        else:
            self._drag_mode = None
            self._rotation_pivot_screen = None
            self._rotation_pivot_world = None

    def mouseMoveEvent(self, event):
        if (
            self._drag_start is not None
            and self._drag_mode is not None
        ):
            delta = (
                event.position()
                - self._drag_start
            )

            if (
                abs(delta.x()) > 0.5
                or abs(delta.y()) > 0.5
            ):
                self._dragged = True

            if self._drag_mode == "rotate":
                # Weil self._center beim Mausklick auf den gewählten
                # Weltpunkt gesetzt wurde, drehen sich alle Objekte jetzt
                # tatsächlich um genau diesen Punkt.
                self.yaw += (
                    delta.x() * 0.008
                )
                self.pitch += (
                    delta.y() * 0.008
                )

                limit = math.radians(88.0)
                self.pitch = max(
                    -limit,
                    min(
                        limit,
                        self.pitch,
                    ),
                )

                self._drag_start = (
                    event.position()
                )

            elif self._drag_mode == "pan":
                self.pan += delta
                self._drag_start = (
                    event.position()
                )

            elif self._drag_mode == "zoom_rect":
                self._zoom_rect_end = QPointF(
                    event.position()
                )

            self.update()
            return

        hit = self._hit(
            event.position()
        )

        if hit != self.hover_index:
            self.hover_index = hit
            self.update()

        if hit >= 0:
            system = self.systems[hit]

            QToolTip.showText(
                event.globalPosition().toPoint(),
                (
                    f"{system.get('name') or 'Unbekannt'}\n"
                    f"X: {float(system.get('x') or 0):.1f} ly\n"
                    f"Y: {float(system.get('y') or 0):.1f} ly\n"
                    f"Z: {float(system.get('z') or 0):.1f} ly"
                ),
                self,
            )
        else:
            QToolTip.hideText()

    def _apply_zoom_rect(self):
        """
        Zoomt exakt auf den mit der mittleren Maustaste markierten
        Bildschirmbereich.

        Der aktuelle 3D-Drehpunkt/self._center bleibt dabei unverändert.
        Nur scale und pan werden angepasst.
        """
        if (
            self._zoom_rect_start is None
            or self._zoom_rect_end is None
        ):
            return

        x1 = self._zoom_rect_start.x()
        y1 = self._zoom_rect_start.y()
        x2 = self._zoom_rect_end.x()
        y2 = self._zoom_rect_end.y()

        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width < 12 or height < 12:
            return

        rect_center = QPointF(
            (x1 + x2) / 2.0,
            (y1 + y2) / 2.0,
        )

        widget_center = QPointF(
            self.width() / 2.0,
            self.height() / 2.0,
        )

        usable_w = max(
            100.0,
            self.width() - 40.0,
        )
        usable_h = max(
            100.0,
            self.height() - 40.0,
        )

        requested_factor = min(
            usable_w / width,
            usable_h / height,
        )

        requested_factor = max(
            1.0,
            min(
                requested_factor,
                20.0,
            ),
        )

        old_scale = float(self.scale)

        new_scale = max(
            0.00005,
            min(
                old_scale * requested_factor,
                80.0,
            ),
        )

        actual_factor = (
            new_scale / old_scale
            if old_scale > 0
            else 1.0
        )

        old_pan = QPointF(self.pan)

        # Aktuelle projizierte Weltkomponente des Rahmenmittelpunkts:
        #
        # screen = widget_center + world_component + pan
        #
        # Nach dem Zoom wird world_component mit actual_factor skaliert.
        # Wir wählen new_pan so, dass der Rahmenmittelpunkt anschließend
        # exakt auf widget_center liegt.
        world_component = (
            rect_center
            - widget_center
            - old_pan
        )

        self.scale = new_scale

        self.pan = QPointF(
            -world_component.x() * actual_factor,
            -world_component.y() * actual_factor,
        )

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and not getattr(self, "_dragged", False)
        ):
            hit = self._hit(event.position())

            if hit >= 0:
                system = self.systems[hit]
                self.selected_address = system.get(
                    "system_address"
                )
                self.systemClicked.emit(system)

        elif event.button() == Qt.MiddleButton:
            self._zoom_rect_end = QPointF(
                event.position()
            )
            self._apply_zoom_rect()

        self._drag_start = None
        self._drag_mode = None
        self._rotation_pivot_screen = None
        self._rotation_pivot_world = None
        self._press_hit = -1
        self._dragged = False

        self._zoom_rect_start = None
        self._zoom_rect_end = None

        self.update()

    def mouseDoubleClickEvent(self, event):
        if self._hit(event.position()) < 0:
            self.reset_view()

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Treffererkennung
    # ------------------------------------------------------------------

    def _hit(self, pos):
        best = -1
        best_distance = 12.0

        for index, system in enumerate(
            self.systems
        ):
            point, _depth, _perspective = (
                self._project(system)
            )

            distance = math.hypot(
                point.x() - pos.x(),
                point.y() - pos.y(),
            )

            if distance < best_distance:
                best = index
                best_distance = distance

        return best
