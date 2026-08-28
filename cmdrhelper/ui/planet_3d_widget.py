from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QImage, QPainter, QColor, QRadialGradient, QBrush, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class Planet3DWidget(QWidget):
    """
    CPU-basierter 3D-Kugelrenderer für equirectangulare 2:1-Texturen.

    Vorteil:
    - keine zusätzliche OpenGL-/PyOpenGL-Abhängigkeit
    - funktioniert direkt mit PySide6 + numpy
    - echte Kugelprojektion statt rotierender 2D-Scheibe
    """

    def __init__(
        self,
        texture_path: Path,
        parent=None,
        diameter: int = 230,
        seconds_per_rotation: float = 18.0,
        life_effect: bool | str = False,
    ):
        super().__init__(parent)

        self.texture_path = Path(texture_path)
        self.diameter = int(diameter)
        self.seconds_per_rotation = max(4.0, float(seconds_per_rotation))
        # Unterstützt weiterhin True/False, zusätzlich aber benannte
        # Life-Stile wie "water" und "ammonia".
        if life_effect is True:
            self.life_effect = "water"
        elif isinstance(life_effect, str):
            self.life_effect = life_effect.strip().lower()
        else:
            self.life_effect = ""

        self._rotation = 0.0
        self._life_phase = 0.0
        self._frame = None
        self._texture = None
        self._texture_h = 0
        self._texture_w = 0

        self.setFixedSize(
            self.diameter + 24,
            self.diameter + 24
        )

        self._load_texture()

        # Ca. 20 FPS reichen bei 230 px völlig aus.
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._advance_rotation)

        if self._texture is not None:
            self._timer.start()
            self._render_frame()

    def sizeHint(self):
        return QSize(
            self.diameter + 24,
            self.diameter + 24
        )

    def _load_texture(self):
        image = QImage(str(self.texture_path))

        if image.isNull():
            return

        image = image.convertToFormat(
            QImage.Format_RGBA8888
        )

        width = image.width()
        height = image.height()

        ptr = image.bits()
        arr = np.frombuffer(
            ptr,
            dtype=np.uint8,
            count=height * width * 4,
        ).reshape((height, width, 4)).copy()

        self._texture = arr
        self._texture_h = height
        self._texture_w = width

    def _advance_rotation(self):
        # 50 ms pro Tick.
        step = (
            (2.0 * math.pi)
            * 0.05
            / self.seconds_per_rotation
        )

        self._rotation = (
            self._rotation + step
        ) % (2.0 * math.pi)

        # Unabhängige, deutlich langsamere Bewegung der Lebenspunkte.
        self._life_phase = (
            self._life_phase + 0.018
        ) % (2.0 * math.pi)

        self._render_frame()
        self.update()

    def _render_frame(self):
        if self._texture is None:
            self._frame = None
            return

        size = self.diameter

        # Pixelkoordinaten auf -1..+1 normieren.
        yy, xx = np.mgrid[
            0:size,
            0:size
        ]

        nx = (
            (xx + 0.5)
            / size
            * 2.0
            - 1.0
        )

        ny = -(
            (yy + 0.5)
            / size
            * 2.0
            - 1.0
        )

        r2 = nx * nx + ny * ny
        mask = r2 <= 1.0

        nz = np.zeros_like(nx)
        nz[mask] = np.sqrt(
            np.maximum(
                0.0,
                1.0 - r2[mask]
            )
        )

        # Kugelkoordinaten.
        longitude = np.arctan2(
            nx,
            nz
        ) + self._rotation

        latitude = np.arcsin(
            np.clip(ny, -1.0, 1.0)
        )

        u = (
            longitude
            / (2.0 * math.pi)
            + 0.5
        ) % 1.0

        v = (
            0.5
            - latitude
            / math.pi
        )

        tx = np.clip(
            (u * (self._texture_w - 1)).astype(np.int32),
            0,
            self._texture_w - 1
        )

        ty = np.clip(
            (v * (self._texture_h - 1)).astype(np.int32),
            0,
            self._texture_h - 1
        )

        frame = np.zeros(
            (size, size, 4),
            dtype=np.uint8
        )

        sampled = self._texture[
            ty,
            tx
        ].astype(np.float32)

        # ----------------------------------------------------
        # Beleuchtung: Licht von oben links/vorne.
        # ----------------------------------------------------
        light = np.array(
            [-0.45, 0.35, 0.82],
            dtype=np.float32
        )

        light /= np.linalg.norm(light)

        lambert = (
            nx * light[0]
            + ny * light[1]
            + nz * light[2]
        )

        lambert = np.clip(
            lambert,
            0.0,
            1.0
        )

        # Schatten nie völlig schwarz werden lassen.
        brightness = (
            0.30
            + 0.78 * lambert
        )

        # Rand leicht abdunkeln für mehr Kugelwirkung.
        limb = np.clip(
            nz,
            0.0,
            1.0
        )

        brightness *= (
            0.72
            + 0.28 * limb
        )

        rgb = sampled[..., :3]
        rgb *= brightness[..., None]

        # Dezenter bläulicher Atmosphärenrand.
        rim = np.clip(
            (1.0 - nz) ** 3.0,
            0.0,
            1.0
        )

        rgb[..., 0] += 10.0 * rim
        rgb[..., 1] += 32.0 * rim
        rgb[..., 2] += 58.0 * rim

        rgb = np.clip(
            rgb,
            0,
            255
        ).astype(np.uint8)

        frame[..., :3] = rgb
        frame[..., 3] = 0
        frame[..., 3][mask] = 255

        # Alpha des Texturbildes innerhalb der Kugel berücksichtigen,
        # falls die Textur selbst einen Alphakanal besitzt.
        source_alpha = sampled[..., 3].astype(np.uint8)
        frame[..., 3][mask] = source_alpha[mask]

        # QImage besitzt den numpy-Puffer nicht; copy() löst ihn sauber.
        qimg = QImage(
            frame.data,
            size,
            size,
            size * 4,
            QImage.Format_RGBA8888,
        ).copy()

        self._frame = qimg

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.Antialiasing,
            True
        )
        painter.setRenderHint(
            QPainter.SmoothPixmapTransform,
            True
        )

        if self._frame is None:
            painter.setPen(
                QColor("#8e969e")
            )
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                "3D-Textur nicht verfügbar"
            )
            return

        x = (
            self.width()
            - self.diameter
        ) // 2

        y = (
            self.height()
            - self.diameter
        ) // 2

        painter.drawImage(
            x,
            y,
            self._frame
        )

        if self.life_effect == "water":
            self._paint_life_effect(
                painter,
                x,
                y
            )
        elif self.life_effect == "ammonia":
            self._paint_ammonia_life_effect(
                painter,
                x,
                y
            )
        elif self.life_effect == "water_giant":
            self._paint_water_giant_life_effect(
                painter,
                x,
                y
            )

    def _paint_life_effect(self, painter, image_x, image_y):
        """
        Organischere atmosphärische Lebensformen:
        kleine leuchtende 'Quallen' mit Körper, weichem Halo und
        sanft schwingenden Schweifen. Die Bewegung bleibt bewusst dezent.
        """
        radius = self.diameter / 2.0
        cx = image_x + radius
        cy = image_y + radius

        organisms = (
            (-0.58, -0.24, 0.72, 0.70, 0.0, 1.00),
            (-0.18,  0.31, 0.55, 0.90, 1.2, 0.85),
            ( 0.36, -0.38, 0.62, 0.60, 2.5, 1.10),
            ( 0.53,  0.18, 0.48, 1.00, 3.7, 0.78),
            (-0.42,  0.48, 0.42, 0.80, 4.8, 0.92),
        )

        painter.save()

        clip = QPainterPath()
        clip.addEllipse(
            image_x,
            image_y,
            self.diameter,
            self.diameter
        )
        painter.setClipPath(clip)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for base_x, base_y, drift, speed, phase, scale in organisms:
            t = self._life_phase * speed + phase

            px = (
                cx
                + radius * base_x
                + math.sin(t * 1.7) * radius * 0.08 * drift
            )
            py = (
                cy
                + radius * base_y
                + math.cos(t * 1.25) * radius * 0.055 * drift
            )

            dx = (px - cx) / radius
            dy = (py - cy) / radius
            dist2 = dx * dx + dy * dy

            if dist2 >= 0.90:
                continue

            # Am Kugelrand werden die Wesen schwächer/kleiner.
            depth = math.sqrt(max(0.0, 1.0 - dist2))
            pulse = 0.5 + 0.5 * math.sin(t * 2.35)
            body_r = 3.0 * (2.3 + 0.7 * pulse) * scale * (0.72 + 0.28 * depth)
            glow_r = body_r * 3.0
            alpha = int((105 + 80 * pulse) * (0.55 + 0.45 * depth))

            # Bewegungsrichtung für einen sanften Schweif.
            vx = math.cos(t * 1.7)
            vy = -math.sin(t * 1.25)
            norm = max(0.001, math.hypot(vx, vy))
            vx /= norm
            vy /= norm

            tail_len = 3.0 * (7.0 + 3.0 * pulse) * scale
            side_x = -vy
            side_y = vx
            wave = math.sin(t * 3.1) * 2.0 * scale

            # Zwei dünne, leicht schwingende Tentakel/Schweife.
            for side in (-1.0, 1.0):
                path = QPainterPath()
                path.moveTo(
                    px - vx * body_r * 0.6 + side_x * side * body_r * 0.45,
                    py - vy * body_r * 0.6 + side_y * side * body_r * 0.45,
                )
                path.cubicTo(
                    px - vx * tail_len * 0.35 + side_x * (wave + side * 1.2),
                    py - vy * tail_len * 0.35 + side_y * (wave + side * 1.2),
                    px - vx * tail_len * 0.72 - side_x * wave,
                    py - vy * tail_len * 0.72 - side_y * wave,
                    px - vx * tail_len,
                    py - vy * tail_len,
                )

                pen = QPen(
                    QColor(90, 235, 245, max(25, int(alpha * 0.52)))
                )
                pen.setWidthF(max(0.7, 1.05 * scale))
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

            # Weicher Halo.
            gradient = QRadialGradient(px, py, glow_r)
            gradient.setColorAt(
                0.0,
                QColor(225, 255, 255, min(255, alpha + 65))
            )
            gradient.setColorAt(
                0.22,
                QColor(95, 250, 238, alpha)
            )
            gradient.setColorAt(
                0.58,
                QColor(25, 185, 225, int(alpha * 0.38))
            )
            gradient.setColorAt(
                1.0,
                QColor(0, 80, 170, 0)
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(
                int(px - glow_r),
                int(py - glow_r),
                max(2, int(glow_r * 2)),
                max(2, int(glow_r * 2)),
            )

            # Leicht länglicher Körper statt eines simplen Lichtpunkts.
            painter.setBrush(
                QColor(185, 255, 250, min(255, alpha + 45))
            )
            painter.drawEllipse(
                int(px - body_r * 0.72),
                int(py - body_r),
                max(2, int(body_r * 1.44)),
                max(3, int(body_r * 2.0)),
            )

            # Winziger heller Kern.
            core = max(0.9, body_r * 0.38)
            painter.setBrush(
                QColor(240, 255, 255, min(255, alpha + 85))
            )
            painter.drawEllipse(
                int(px - core),
                int(py - core),
                max(2, int(core * 2)),
                max(2, int(core * 2)),
            )

        painter.restore()

    def _paint_ammonia_life_effect(self, painter, image_x, image_y):
        """
        Eigene Lebensform für Ammoniak-Gasriesen.

        Statt der cyanfarbenen Wasser-Quallen schweben hier größere,
        halbtransparente violett/amberfarbene "Gasblasen" mit kurzem
        Fadenkranz und pulsierendem Kern.
        """
        radius = self.diameter / 2.0
        cx = image_x + radius
        cy = image_y + radius

        organisms = (
            (-0.52, -0.20, 0.66, 0.55, 0.2, 1.00),
            (-0.10,  0.33, 0.52, 0.72, 1.4, 0.82),
            ( 0.34, -0.34, 0.61, 0.48, 2.7, 1.10),
            ( 0.50,  0.22, 0.47, 0.68, 4.0, 0.90),
        )

        painter.save()

        clip = QPainterPath()
        clip.addEllipse(
            image_x,
            image_y,
            self.diameter,
            self.diameter
        )
        painter.setClipPath(clip)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for base_x, base_y, drift, speed, phase, scale in organisms:
            t = self._life_phase * speed + phase

            # Langsamer und schwebender als Water-Life.
            px = (
                cx
                + radius * base_x
                + math.sin(t * 1.15) * radius * 0.075 * drift
            )
            py = (
                cy
                + radius * base_y
                + math.cos(t * 0.92) * radius * 0.065 * drift
            )

            dx = (px - cx) / radius
            dy = (py - cy) / radius
            dist2 = dx * dx + dy * dy

            if dist2 >= 0.90:
                continue

            depth = math.sqrt(max(0.0, 1.0 - dist2))

            # Etwas unregelmäßigeres, "atmendes" Pulsieren.
            pulse = (
                0.58
                + 0.24 * math.sin(t * 1.9)
                + 0.18 * math.sin(t * 3.4 + phase)
            )
            pulse = max(0.0, min(1.0, pulse))

            body_r = (
                7.5
                + 3.0 * pulse
            ) * scale * (0.72 + 0.28 * depth)

            glow_r = body_r * 2.5
            alpha = int(
                (105 + 95 * pulse)
                * (0.50 + 0.50 * depth)
            )

            # Weicher violett-goldener Halo.
            gradient = QRadialGradient(
                px,
                py,
                glow_r
            )
            gradient.setColorAt(
                0.0,
                QColor(
                    255, 238, 170,
                    min(255, alpha + 55)
                )
            )
            gradient.setColorAt(
                0.20,
                QColor(
                    255, 170, 72,
                    alpha
                )
            )
            gradient.setColorAt(
                0.48,
                QColor(
                    190, 82, 230,
                    int(alpha * 0.72)
                )
            )
            gradient.setColorAt(
                0.76,
                QColor(
                    95, 42, 180,
                    int(alpha * 0.32)
                )
            )
            gradient.setColorAt(
                1.0,
                QColor(45, 16, 95, 0)
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(
                int(px - glow_r),
                int(py - glow_r),
                max(2, int(glow_r * 2)),
                max(2, int(glow_r * 2)),
            )

            # Halbtransparente "Gasblase".
            bubble_color = QColor(
                210,
                118,
                235,
                min(210, alpha + 20)
            )
            bubble_pen = QPen(
                QColor(
                    255,
                    205,
                    120,
                    min(235, alpha + 35)
                )
            )
            bubble_pen.setWidthF(
                max(1.0, 1.4 * scale)
            )

            painter.setPen(bubble_pen)
            painter.setBrush(bubble_color)
            painter.drawEllipse(
                int(px - body_r * 0.78),
                int(py - body_r),
                max(3, int(body_r * 1.56)),
                max(4, int(body_r * 2.0)),
            )

            # Pulsierender amberfarbener Kern.
            core = body_r * (
                0.24 + 0.06 * pulse
            )

            core_gradient = QRadialGradient(
                px - body_r * 0.10,
                py - body_r * 0.08,
                core * 2.4,
            )
            core_gradient.setColorAt(
                0.0,
                QColor(255, 255, 210, 245)
            )
            core_gradient.setColorAt(
                0.35,
                QColor(255, 190, 62, 220)
            )
            core_gradient.setColorAt(
                1.0,
                QColor(190, 60, 230, 0)
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(core_gradient))
            painter.drawEllipse(
                int(px - core),
                int(py - core),
                max(2, int(core * 2)),
                max(2, int(core * 2)),
            )

            # Kurzer Fadenkranz statt langer Quallenschweife.
            thread_count = 4

            for i in range(thread_count):
                a = (
                    math.pi * 0.35
                    + i * (math.pi * 0.30)
                    + 0.20 * math.sin(t + i)
                )

                start_x = (
                    px
                    + math.cos(a)
                    * body_r * 0.68
                )
                start_y = (
                    py
                    + math.sin(a)
                    * body_r * 0.78
                )

                length = (
                    body_r
                    * (1.10 + 0.25 * math.sin(t * 1.6 + i))
                )

                end_x = (
                    start_x
                    + math.cos(a + 0.25)
                    * length
                )
                end_y = (
                    start_y
                    + math.sin(a + 0.25)
                    * length
                )

                path = QPainterPath()
                path.moveTo(start_x, start_y)
                path.cubicTo(
                    start_x
                    + math.cos(a) * length * 0.32,
                    start_y
                    + math.sin(a) * length * 0.24,
                    end_x
                    - math.cos(a) * length * 0.28,
                    end_y
                    - math.sin(a) * length * 0.18,
                    end_x,
                    end_y,
                )

                pen = QPen(
                    QColor(
                        224,
                        105,
                        245,
                        max(30, int(alpha * 0.58))
                    )
                )
                pen.setWidthF(
                    max(0.8, 1.15 * scale)
                )

                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

        painter.restore()


    def _paint_water_giant_life_effect(self, painter, image_x, image_y):
        """Große manta-/quallenartige Lebensformen für Water Giants."""
        radius = self.diameter / 2.0
        cx = image_x + radius
        cy = image_y + radius

        organisms = (
            (-0.38, -0.28, 0.55, 0.42, 0.0, 1.05),
            ( 0.08,  0.18, 0.48, 0.34, 1.8, 1.28),
            ( 0.43, -0.12, 0.44, 0.39, 3.5, 0.88),
            (-0.34,  0.43, 0.38, 0.31, 5.1, 0.78),
        )

        painter.save()
        clip = QPainterPath()
        clip.addEllipse(image_x, image_y, self.diameter, self.diameter)
        painter.setClipPath(clip)
        painter.setRenderHint(QPainter.Antialiasing, True)

        for base_x, base_y, drift, speed, phase, scale in organisms:
            t = self._life_phase * speed + phase
            px = cx + radius*base_x + math.sin(t*0.95)*radius*0.105*drift
            py = cy + radius*base_y + math.cos(t*0.72)*radius*0.075*drift

            dx, dy = (px-cx)/radius, (py-cy)/radius
            dist2 = dx*dx + dy*dy
            if dist2 >= 0.88:
                continue

            depth = math.sqrt(max(0.0, 1.0-dist2))
            pulse = 0.5 + 0.5*math.sin(t*1.55+phase)
            body_w = (20.0+4.0*pulse)*scale*(0.70+0.30*depth)
            body_h = body_w*0.48
            alpha = int((125+65*pulse)*(0.48+0.52*depth))

            vx = math.cos(t*0.95+phase*0.15)
            vy = -math.sin(t*0.72+phase*0.10)
            norm = max(0.001, math.hypot(vx, vy))
            vx, vy = vx/norm, vy/norm
            side_x, side_y = -vy, vx

            tail_len = body_w*(2.0+0.28*pulse)
            for i in range(5):
                spread = (i-2.0)/4.0
                sx = px-vx*body_w*0.26+side_x*spread*body_w*0.34
                sy = py-vy*body_w*0.26+side_y*spread*body_w*0.34
                wave = math.sin(t*2.0+i*1.15)*body_w*0.18
                ex, ey = sx-vx*tail_len+side_x*wave, sy-vy*tail_len+side_y*wave
                path = QPainterPath()
                path.moveTo(sx, sy)
                path.cubicTo(
                    sx-vx*tail_len*0.30+side_x*wave*0.80,
                    sy-vy*tail_len*0.30+side_y*wave*0.80,
                    sx-vx*tail_len*0.68-side_x*wave*0.45,
                    sy-vy*tail_len*0.68-side_y*wave*0.45,
                    ex, ey
                )
                pen = QPen(QColor(80+i*8, 205+min(35,i*7), 255,
                                  max(25,int(alpha*(0.48-i*0.035)))))
                pen.setWidthF(max(0.75,(1.45-i*0.08)*scale))
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

            glow_r = body_w*1.05
            glow = QRadialGradient(px, py, glow_r)
            glow.setColorAt(0.0,QColor(205,255,255,min(230,alpha+35)))
            glow.setColorAt(0.32,QColor(55,235,245,int(alpha*0.72)))
            glow.setColorAt(0.68,QColor(40,120,245,int(alpha*0.25)))
            glow.setColorAt(1.0,QColor(25,45,180,0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(int(px-glow_r),int(py-glow_r),
                                max(2,int(glow_r*2)),max(2,int(glow_r*2)))

            nose_x, nose_y = px+vx*body_w*0.52, py+vy*body_w*0.52
            back_x, back_y = px-vx*body_w*0.42, py-vy*body_w*0.42
            left_x = px+side_x*body_w*0.56-vx*body_w*0.05
            left_y = py+side_y*body_w*0.56-vy*body_w*0.05
            right_x = px-side_x*body_w*0.56-vx*body_w*0.05
            right_y = py-side_y*body_w*0.56-vy*body_w*0.05

            body = QPainterPath()
            body.moveTo(nose_x,nose_y)
            body.cubicTo(px+vx*body_w*0.22+side_x*body_h,
                         py+vy*body_w*0.22+side_y*body_h,
                         left_x,left_y,back_x,back_y)
            body.cubicTo(right_x,right_y,
                         px+vx*body_w*0.22-side_x*body_h,
                         py+vy*body_w*0.22-side_y*body_h,
                         nose_x,nose_y)
            body.closeSubpath()

            fill = QRadialGradient(px+vx*body_w*0.12,py+vy*body_w*0.12,body_w*0.75)
            fill.setColorAt(0.0,QColor(225,255,255,min(235,alpha+45)))
            fill.setColorAt(0.28,QColor(75,245,245,min(220,alpha+10)))
            fill.setColorAt(0.62,QColor(45,150,245,int(alpha*0.72)))
            fill.setColorAt(1.0,QColor(70,45,210,int(alpha*0.22)))
            pen = QPen(QColor(125,245,255,min(245,alpha+50)))
            pen.setWidthF(max(1.0,1.25*scale))
            painter.setPen(pen)
            painter.setBrush(QBrush(fill))
            painter.drawPath(body)

            core_r = body_w*(0.12+0.025*pulse)
            kx, ky = px+vx*body_w*0.12, py+vy*body_w*0.12
            core = QRadialGradient(kx,ky,core_r*2.4)
            core.setColorAt(0.0,QColor(255,255,255,250))
            core.setColorAt(0.35,QColor(80,255,240,225))
            core.setColorAt(1.0,QColor(55,100,255,0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(core))
            painter.drawEllipse(int(kx-core_r),int(ky-core_r),
                                max(2,int(core_r*2)),max(2,int(core_r*2)))

            for i in range(5):
                frac = (i-2)/4.0
                dot_r = (1.1+0.55*(0.5+0.5*math.sin(t*2.1+i*1.35)))*scale
                dot_x = px+vx*body_w*(0.18-abs(frac)*0.10)+side_x*frac*body_w*0.48
                dot_y = py+vy*body_w*(0.18-abs(frac)*0.10)+side_y*frac*body_w*0.48
                painter.setBrush(QColor(205,120+i*12,255,min(255,alpha+55)))
                painter.drawEllipse(int(dot_x-dot_r),int(dot_y-dot_r),
                                    max(2,int(dot_r*2)),max(2,int(dot_r*2)))

        painter.restore()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
