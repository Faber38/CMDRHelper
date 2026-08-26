from __future__ import annotations

import math
import random

from PySide6.QtCore import Qt, QTimer, QSize, QPointF
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


class BeltClusterWidget(QWidget):
    """
    Prozedural animierter Asteroiden-Cluster.

    Jeder Brocken besitzt:
    - eigene Position und Tiefe
    - eigene Driftgeschwindigkeit
    - eigene langsame Rotation
    - eigene unregelmäßige Form
    - eigene Größe/Helligkeit

    Dadurch entsteht echte Bewegung einzelner Objekte statt eines
    verschobenen Hintergrundbildes.
    """

    def __init__(
        self,
        image_path=None,
        parent=None,
        width: int = 360,
        height: int = 230,
    ):
        super().__init__(parent)

        self.view_width = int(width)
        self.view_height = int(height)

        self.setFixedSize(
            self.view_width,
            self.view_height,
        )

        self._phase = 0.0
        self._rng = random.Random(3817)

        self._asteroids = self._create_asteroids()
        self._dust = self._create_dust()

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    def sizeHint(self):
        return QSize(
            self.view_width,
            self.view_height,
        )

    def _create_asteroids(self):
        asteroids = []

        # Wenige große Vordergrundobjekte + viele kleine Brocken.
        count = 34

        for index in range(count):
            depth = self._rng.uniform(0.18, 1.0)

            # Tiefe beeinflusst Größe und Bewegung.
            if index < 6:
                depth = self._rng.uniform(0.72, 1.0)
                radius = self._rng.uniform(12.0, 23.0)
            else:
                radius = self._rng.uniform(2.8, 10.5)

            radius *= 0.55 + 0.65 * depth

            asteroid = {
                "x": self._rng.uniform(0.05, 0.95),
                "y": self._rng.uniform(0.10, 0.90),
                "depth": depth,
                "radius": radius,
                "angle": self._rng.uniform(0.0, math.tau),
                "spin": self._rng.uniform(-0.010, 0.010),
                "vx": self._rng.uniform(-0.00045, 0.00045)
                      * (0.35 + depth),
                "vy": self._rng.uniform(-0.00020, 0.00020)
                      * (0.35 + depth),
                "points": self._rng.randint(7, 11),
                "shape": [
                    self._rng.uniform(0.72, 1.18)
                    for _ in range(12)
                ],
                "warmth": self._rng.uniform(0.0, 1.0),
                "phase": self._rng.uniform(0.0, math.tau),
            }

            asteroids.append(asteroid)

        # Hinten zuerst zeichnen, Vordergrund zuletzt.
        asteroids.sort(
            key=lambda item: item["depth"]
        )

        return asteroids

    def _create_dust(self):
        dust = []

        for _ in range(55):
            dust.append(
                {
                    "x": self._rng.uniform(0.0, 1.0),
                    "y": self._rng.uniform(0.18, 0.82),
                    "depth": self._rng.uniform(0.15, 0.8),
                    "size": self._rng.uniform(0.7, 2.0),
                    "phase": self._rng.uniform(0.0, math.tau),
                }
            )

        return dust

    def _advance(self):
        self._phase = (
            self._phase + 0.016
        ) % math.tau

        for asteroid in self._asteroids:
            asteroid["x"] += asteroid["vx"]
            asteroid["y"] += asteroid["vy"]
            asteroid["angle"] += asteroid["spin"]

            # Weicher Wrap-Around am Rand.
            if asteroid["x"] < -0.10:
                asteroid["x"] = 1.10
            elif asteroid["x"] > 1.10:
                asteroid["x"] = -0.10

            if asteroid["y"] < -0.10:
                asteroid["y"] = 1.10
            elif asteroid["y"] > 1.10:
                asteroid["y"] = -0.10

        self.update()

    def _asteroid_polygon(
        self,
        cx,
        cy,
        radius,
        angle,
        asteroid,
    ):
        points = []
        count = asteroid["points"]
        shape = asteroid["shape"]

        for i in range(count):
            a = (
                angle
                + (i / count) * math.tau
            )

            deformation = shape[i % len(shape)]

            # Kleine langsame Formvariation erzeugt etwas "Tumbling".
            deformation *= (
                1.0
                + 0.035
                * math.sin(
                    self._phase * 0.7
                    + asteroid["phase"]
                    + i
                )
            )

            rr = radius * deformation

            points.append(
                QPointF(
                    cx + math.cos(a) * rr,
                    cy + math.sin(a) * rr,
                )
            )

        return QPolygonF(points)

    def _paint_dust_band(self, painter):
        # Dezenter warmer Staubschleier diagonal durch den Cluster.
        painter.save()
        painter.setPen(Qt.NoPen)

        for dust in self._dust:
            t = (
                self._phase
                + dust["phase"]
            )

            x = (
                dust["x"] * self.width()
                + math.sin(t * 0.7)
                * 4.0
                * dust["depth"]
            )

            # Leichte diagonale Gürtelstruktur.
            center_y = (
                self.height() * 0.50
                + (dust["x"] - 0.5)
                * self.height()
                * 0.24
            )

            y = (
                center_y
                + (dust["y"] - 0.5)
                * self.height()
                * 0.30
                + math.cos(t * 0.8)
                * 2.0
            )

            alpha = int(
                30 + 65 * dust["depth"]
            )

            size = (
                dust["size"]
                * (0.7 + dust["depth"])
            )

            painter.setBrush(
                QColor(
                    225,
                    145,
                    75,
                    alpha,
                )
            )

            painter.drawEllipse(
                QPointF(x, y),
                size,
                size,
            )

        painter.restore()

    def _paint_asteroid(self, painter, asteroid):
        depth = asteroid["depth"]

        # Vordergrund bewegt sich sichtbar stärker als Hintergrund.
        drift_x = (
            math.sin(
                self._phase * (0.42 + depth * 0.25)
                + asteroid["phase"]
            )
            * 5.5
            * depth
        )

        drift_y = (
            math.cos(
                self._phase * (0.31 + depth * 0.18)
                + asteroid["phase"]
            )
            * 3.5
            * depth
        )

        cx = asteroid["x"] * self.width() + drift_x
        cy = asteroid["y"] * self.height() + drift_y

        radius = asteroid["radius"]
        angle = asteroid["angle"]

        polygon = self._asteroid_polygon(
            cx,
            cy,
            radius,
            angle,
            asteroid,
        )

        warmth = asteroid["warmth"]

        # Hinten dunkler und kontrastärmer.
        base = int(
            48 + 52 * depth
        )

        red = min(
            125,
            int(base + warmth * 25)
        )
        green = min(
            105,
            int(base * 0.82 + warmth * 13)
        )
        blue = min(
            95,
            int(base * 0.72)
        )

        painter.save()

        # Kleiner dunkler Schatten hinter jedem Brocken.
        shadow_poly = self._asteroid_polygon(
            cx + 2.0 * depth,
            cy + 2.5 * depth,
            radius,
            angle,
            asteroid,
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(
            QColor(
                0,
                0,
                0,
                int(65 + 70 * depth),
            )
        )
        painter.drawPolygon(shadow_poly)

        # Hauptkörper.
        painter.setBrush(
            QColor(
                red,
                green,
                blue,
                int(150 + 100 * depth),
            )
        )

        outline = QColor(
            min(210, red + 55),
            min(175, green + 45),
            min(145, blue + 35),
            int(105 + 120 * depth),
        )

        pen = QPen(outline)
        pen.setWidthF(
            0.6 + 0.9 * depth
        )
        painter.setPen(pen)
        painter.drawPolygon(polygon)

        # Lichtkante oben links.
        highlight_radius = max(
            1.2,
            radius * 0.34
        )

        gradient = QRadialGradient(
            cx - radius * 0.36,
            cy - radius * 0.33,
            highlight_radius * 2.8,
        )

        gradient.setColorAt(
            0.0,
            QColor(
                255,
                196,
                125,
                int(80 + 95 * depth),
            )
        )
        gradient.setColorAt(
            0.45,
            QColor(
                185,
                110,
                65,
                int(25 + 55 * depth),
            )
        )
        gradient.setColorAt(
            1.0,
            QColor(
                0,
                0,
                0,
                0,
            )
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(
            QBrush(gradient)
        )
        painter.drawEllipse(
            QPointF(cx, cy),
            radius * 0.92,
            radius * 0.92,
        )

        # 1-3 einfache Krater pro größerem Brocken.
        if radius >= 8:
            crater_count = (
                1
                if radius < 13
                else 2
                if radius < 18
                else 3
            )

            for i in range(crater_count):
                a = (
                    asteroid["phase"]
                    + i * 2.1
                    + angle * 0.55
                )

                cr = radius * (
                    0.12 + 0.025 * i
                )

                px = (
                    cx
                    + math.cos(a)
                    * radius
                    * (0.30 + 0.08 * i)
                )

                py = (
                    cy
                    + math.sin(a)
                    * radius
                    * (0.24 + 0.06 * i)
                )

                painter.setBrush(
                    QColor(
                        15,
                        12,
                        12,
                        int(115 + 70 * depth),
                    )
                )
                painter.setPen(
                    QColor(
                        125,
                        85,
                        60,
                        int(75 + 70 * depth),
                    )
                )

                painter.drawEllipse(
                    QPointF(px, py),
                    cr,
                    cr * 0.75,
                )

        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing,
            True,
        )

        # Transparent lassen: passt zum bestehenden Detailfenster.
        painter.fillRect(
            self.rect(),
            Qt.transparent,
        )

        self._paint_dust_band(painter)

        for asteroid in self._asteroids:
            self._paint_asteroid(
                painter,
                asteroid,
            )

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
