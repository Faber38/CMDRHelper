from __future__ import annotations

import logging
import platform
from pathlib import Path

from PIL import Image, ImageEnhance
from PySide6.QtCore import Qt, QTimer, QSize, QObject, Signal, QRunnable, QThreadPool, QUrl
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QCheckBox, QListWidget,
    QListWidgetItem, QSplitter, QFrame, QMessageBox, QSlider, QSpinBox,
)

logger = logging.getLogger(__name__)


class _Signals(QObject):
    finished = Signal(str, str, bool, str)


class _ConvertWorker(QRunnable):
    def __init__(self, source: Path, target: Path, fmt: str, delete_source: bool, brightness: int = 0):
        super().__init__()
        self.source = Path(source)
        self.target = Path(target)
        self.fmt = fmt
        self.delete_source = delete_source
        self.brightness = max(0, min(50, int(brightness)))
        self.signals = _Signals()

    def run(self):
        try:
            self.target.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(self.source) as img:
                # 0 % = Original. Beispiel: 15 % -> Faktor 1.15.
                if self.brightness > 0:
                    img = ImageEnhance.Brightness(img).enhance(
                        1.0 + self.brightness / 100.0
                    )

                if self.fmt == "JPEG":
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")
                    img.save(self.target, "JPEG", quality=95, optimize=True)
                else:
                    img.save(self.target, "PNG", optimize=True)
            if self.delete_source:
                self.source.unlink(missing_ok=True)
            self.signals.finished.emit(str(self.source), str(self.target), True, "")
        except Exception as exc:
            self.signals.finished.emit(str(self.source), str(self.target), False, str(exc))


class ScreenshotView(QWidget):
    """BMP-Konverter und Galerie für Elite-Dangerous-Screenshots."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.pool = QThreadPool.globalInstance()
        self._known: set[str] = set()
        self._pending: dict[str, tuple[int, int]] = {}
        self._converting: set[str] = set()
        self._workers: set[_ConvertWorker] = set()
        self._gallery_state = None

        self._build_ui()
        self._load_settings()
        self._refresh_gallery()

        self.timer = QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self._scan)
        self._update_watch_state()

        # Galerie unabhängig von der BMP-Überwachung aktuell halten.
        # So verschwinden auch extern gelöschte/verschobene Bilder automatisch.
        self.gallery_timer = QTimer(self)
        self.gallery_timer.setInterval(2000)
        self.gallery_timer.timeout.connect(self._check_gallery_changes)
        self.gallery_timer.start()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)
        root.addWidget(QLabel("Bilder", objectName="sectionTitle"))

        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(QLabel("ELITE-SCREENSHOTS", objectName="sectionTitle"))

        info = QLabel(
            "Elite Dangerous speichert F10-Screenshots als BMP. CMDRHelper kann "
            "neue Bilder automatisch erkennen und nach PNG oder JPG konvertieren.",
            objectName="muted",
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        self.source_edit = QLineEdit()
        self.target_edit = QLineEdit()

        self.source_edit.editingFinished.connect(self._path_edited)
        self.target_edit.editingFinished.connect(self._path_edited)

        source_row = QHBoxLayout(); source_row.addWidget(self.source_edit, 1)
        b = QPushButton("Wählen …"); b.clicked.connect(self._choose_source); source_row.addWidget(b)
        target_row = QHBoxLayout(); target_row.addWidget(self.target_edit, 1)
        b = QPushButton("Wählen …"); b.clicked.connect(self._choose_target); target_row.addWidget(b)

        self.format_combo = QComboBox(); self.format_combo.addItems(["PNG", "JPG"])
        self.format_combo.currentTextChanged.connect(self._save_settings)
        self.auto_check = QCheckBox("Neue BMP-Dateien automatisch konvertieren")
        self.auto_check.toggled.connect(self._auto_toggled)
        self.delete_check = QCheckBox("BMP nach erfolgreicher Konvertierung löschen")
        self.delete_check.toggled.connect(self._save_settings)

        checkbox_style = """
            QCheckBox {
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid palette(mid);
                border-radius: 3px;
                background: palette(base);
            }

            QCheckBox::indicator:hover {
                border: 2px solid palette(highlight);
            }

            QCheckBox::indicator:checked {
                border: 2px solid palette(highlight);
                background: palette(highlight);
            }

            QCheckBox::indicator:disabled {
                border: 2px solid palette(midlight);
                background: palette(window);
            }
        """

        self.auto_check.setStyleSheet(checkbox_style)
        self.delete_check.setStyleSheet(checkbox_style)

        form.addRow("Elite-Screenshot-Ordner:", source_row)
        form.addRow("Zielordner:", target_row)
        form.addRow("Ausgabeformat:", self.format_combo)

        brightness_row = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 50)
        self.brightness_slider.setSingleStep(1)
        self.brightness_slider.setPageStep(5)
        self.brightness_slider.setToolTip(
            "Aufhellung der konvertierten Bilder. 0 % lässt das Original unverändert."
        )

        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(0, 50)
        self.brightness_spin.setSuffix(" %")
        self.brightness_spin.setFixedWidth(85)

        self.brightness_slider.valueChanged.connect(self.brightness_spin.setValue)
        self.brightness_spin.valueChanged.connect(self.brightness_slider.setValue)
        self.brightness_slider.valueChanged.connect(self._save_settings)

        brightness_row.addWidget(self.brightness_slider, 1)
        brightness_row.addWidget(self.brightness_spin)
        form.addRow("Aufhellung:", brightness_row)

        form.addRow("", self.auto_check)
        form.addRow("", self.delete_check)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.convert_button = QPushButton("Vorhandene BMPs konvertieren", objectName="primary")
        self.convert_button.clicked.connect(self._convert_existing)
        buttons.addWidget(self.convert_button)
        b = QPushButton("Zielordner öffnen"); b.clicked.connect(self._open_target); buttons.addWidget(b)
        buttons.addStretch()
        self.status = QLabel("● Überwachung aus", objectName="muted"); buttons.addWidget(self.status)
        layout.addLayout(buttons)

        self.last_action = QLabel("Noch kein Bild konvertiert.", objectName="muted")
        self.last_action.setWordWrap(True)
        layout.addWidget(self.last_action)
        root.addWidget(card)

        gallery_card = QFrame(objectName="card")
        gallery_layout = QVBoxLayout(gallery_card)
        gallery_layout.setContentsMargins(10, 8, 10, 8)
        top = QHBoxLayout(); top.addWidget(QLabel("GALERIE", objectName="sectionTitle")); top.addStretch()
        self.delete_selected_button = QPushButton("Ausgewählte löschen")
        self.delete_selected_button.clicked.connect(self._delete_selected_images)
        top.addWidget(self.delete_selected_button)

        b = QPushButton("Galerie aktualisieren"); b.clicked.connect(self._refresh_gallery); top.addWidget(b)
        gallery_layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListWidget.IconMode)
        self.gallery.setIconSize(QSize(150, 95))
        self.gallery.setGridSize(QSize(180, 135))
        self.gallery.setResizeMode(QListWidget.Adjust)
        self.gallery.setMovement(QListWidget.Static)
        self.gallery.setSelectionMode(QListWidget.ExtendedSelection)
        self.gallery.installEventFilter(self)
        self.gallery.itemClicked.connect(self._show_preview)
        self.gallery.itemDoubleClicked.connect(self._open_image)

        preview = QFrame(); preview_layout = QVBoxLayout(preview)
        self.preview = QLabel("Bild anklicken, um es anzusehen.", objectName="muted")
        self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumSize(480, 300)
        self.preview_name = QLabel("", objectName="muted"); self.preview_name.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview, 1); preview_layout.addWidget(self.preview_name)

        splitter.addWidget(self.gallery); splitter.addWidget(preview); splitter.setSizes([520, 850])
        gallery_layout.addWidget(splitter, 1)
        root.addWidget(gallery_card, 1)

    def _key(self, name):
        return f"screenshots/{name}"

    @staticmethod
    def _default_source_dir():
        """
        Unter Linux den üblichen Steam/Proton-Pfad von Elite Dangerous
        als Vorgabe verwenden. Der Benutzer kann ihn jederzeit ändern.
        """
        if platform.system().lower() != "linux":
            return ""

        candidates = [
            Path.home()
            / ".steam"
            / "steam"
            / "steamapps"
            / "compatdata"
            / "359320"
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "Pictures"
            / "Frontier Developments"
            / "Elite Dangerous",

            Path.home()
            / ".local"
            / "share"
            / "Steam"
            / "steamapps"
            / "compatdata"
            / "359320"
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "Pictures"
            / "Frontier Developments"
            / "Elite Dangerous",
        ]

        for candidate in candidates:
            if candidate.is_dir():
                return str(candidate)

        # Auch wenn der Ordner noch nicht existiert, den bei Pop!_OS /
        # normalem Steam üblichen Pfad als editierbare Vorgabe anzeigen.
        return str(candidates[0])

    def _load_settings(self):
        saved_source = str(
            self.settings.value(
                self._key("source_dir"),
                "",
            )
            or ""
        ).strip()

        if not saved_source:
            saved_source = self._default_source_dir()

        self.source_edit.setText(saved_source)
        self.target_edit.setText(str(self.settings.value(self._key("target_dir"), "") or ""))
        fmt = str(self.settings.value(self._key("format"), "PNG") or "PNG").upper()
        self.format_combo.setCurrentText(fmt if fmt in ("PNG", "JPG") else "PNG")

        try:
            brightness = int(self.settings.value(self._key("brightness"), 15) or 0)
        except (TypeError, ValueError):
            brightness = 15
        brightness = max(0, min(50, brightness))
        self.brightness_slider.setValue(brightness)
        self.brightness_spin.setValue(brightness)

        auto = str(self.settings.value(self._key("auto"), "false")).lower() in ("1", "true", "yes", "on")
        delete_bmp = str(self.settings.value(self._key("delete_bmp"), "false")).lower() in ("1", "true", "yes", "on")
        self.auto_check.setChecked(auto); self.delete_check.setChecked(delete_bmp)

        if saved_source:
            self.settings.setValue(
                self._key("source_dir"),
                saved_source,
            )

        self._baseline()

    def _save_settings(self, *args):
        self.settings.setValue(self._key("source_dir"), self.source_edit.text().strip())
        self.settings.setValue(self._key("target_dir"), self.target_edit.text().strip())
        self.settings.setValue(self._key("format"), self.format_combo.currentText())
        self.settings.setValue(self._key("brightness"), self.brightness_slider.value())
        self.settings.setValue(self._key("auto"), self.auto_check.isChecked())
        self.settings.setValue(self._key("delete_bmp"), self.delete_check.isChecked())
        self.settings.sync()

    def _path_edited(self):
        self._save_settings()
        self._baseline()
        self._refresh_gallery()
        self._update_watch_state()

    def _source(self):
        text = self.source_edit.text().strip()
        return Path(text).expanduser() if text else None

    def _target(self):
        text = self.target_edit.text().strip()
        return Path(text).expanduser() if text else None

    def _choose_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Elite-Screenshot-Ordner wählen", self.source_edit.text() or str(Path.home()))
        if folder:
            self.source_edit.setText(folder); self._save_settings(); self._baseline(); self._update_watch_state()

    def _choose_target(self):
        folder = QFileDialog.getExistingDirectory(self, "Zielordner wählen", self.target_edit.text() or str(Path.home()))
        if folder:
            self.target_edit.setText(folder); self._save_settings(); self._refresh_gallery(); self._update_watch_state()

    def _auto_toggled(self, checked):
        self._save_settings()
        if checked:
            self._baseline()  # alte BMPs nicht ungefragt automatisch konvertieren
        self._update_watch_state()

    def _baseline(self):
        self._known.clear(); self._pending.clear()
        source = self._source()
        if source and source.is_dir():
            for p in source.glob("*"):
                if p.is_file() and p.suffix.lower() == ".bmp":
                    self._known.add(str(p.resolve()))

    def _update_watch_state(self):
        source, target = self._source(), self._target()
        active = self.auto_check.isChecked() and source and source.is_dir() and target
        if active:
            target.mkdir(parents=True, exist_ok=True); self.timer.start()
            self.status.setText("● Überwachung aktiv"); self.status.setObjectName("statusOk")
        else:
            self.timer.stop()
            if self.auto_check.isChecked():
                self.status.setText("● Ordner fehlen"); self.status.setObjectName("statusWarn")
            else:
                self.status.setText("● Überwachung aus"); self.status.setObjectName("muted")
        self.status.style().unpolish(self.status); self.status.style().polish(self.status)

    def _scan(self):
        source = self._source()
        if not source or not source.is_dir():
            self._update_watch_state(); return
        files = [p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".bmp"]
        current = {str(p.resolve()) for p in files}
        self._known.intersection_update(current)
        for p in files:
            key = str(p.resolve())
            if key in self._known or key in self._converting:
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            old = self._pending.get(key)
            count = old[1] + 1 if old and old[0] == size and size > 0 else 1
            self._pending[key] = (size, count)
            if count >= 2:
                self._known.add(key); self._pending.pop(key, None); self._queue(p)

    def _output_path(self, source: Path):
        target = self._target()
        if not target:
            return None
        suffix = ".jpg" if self.format_combo.currentText() == "JPG" else ".png"
        return target / f"{source.stem}{suffix}"

    def _queue(self, source: Path):
        target = self._output_path(source)
        if not target or target.exists():
            return
        key = str(source.resolve())
        if key in self._converting:
            return
        worker = _ConvertWorker(
            source,
            target,
            "JPEG" if target.suffix.lower() == ".jpg" else "PNG",
            self.delete_check.isChecked(),
            self.brightness_slider.value(),
        )
        worker.signals.finished.connect(self._converted)
        self._workers.add(worker); self._converting.add(key)
        self.last_action.setText(f"Konvertiere: {source.name}")
        self.pool.start(worker)

    def _converted(self, source_text, target_text, ok, error):
        source, target = Path(source_text), Path(target_text)
        try:
            self._converting.discard(str(source.resolve()))
        except Exception:
            pass
        for worker in list(self._workers):
            if worker.source == source and worker.target == target:
                self._workers.discard(worker)
        if ok:
            logger.info("Screenshot konvertiert: %s -> %s", source.name, target.name)
            self.last_action.setText(f"✓ Konvertiert: {source.name} → {target.name}")
            self._refresh_gallery(target)
        else:
            logger.warning("Screenshot-Konvertierung fehlgeschlagen: %s", error)
            self.last_action.setText(f"✗ Fehler bei {source.name}: {error}")

    def _convert_existing(self):
        source, target = self._source(), self._target()
        if not source or not source.is_dir():
            QMessageBox.warning(self, "Bilder", "Bitte zuerst einen gültigen Elite-Screenshot-Ordner wählen."); return
        if not target:
            QMessageBox.warning(self, "Bilder", "Bitte zuerst einen Zielordner wählen."); return
        target.mkdir(parents=True, exist_ok=True)
        queued = 0
        for p in sorted(source.iterdir()):
            if p.is_file() and p.suffix.lower() == ".bmp":
                out = self._output_path(p)
                if out and not out.exists():
                    self._known.add(str(p.resolve())); self._queue(p); queued += 1
        if queued == 0:
            self.last_action.setText("Keine neuen BMP-Dateien zum Konvertieren gefunden.")

    def _gallery_snapshot(self):
        target = self._target()

        if not target or not target.is_dir():
            return ()

        entries = []

        try:
            for path in target.iterdir():
                if (
                    path.is_file()
                    and path.suffix.lower() in (".png", ".jpg", ".jpeg")
                ):
                    stat = path.stat()
                    entries.append(
                        (
                            path.name,
                            int(stat.st_mtime_ns),
                            int(stat.st_size),
                        )
                    )
        except OSError:
            return ()

        entries.sort()
        return tuple(entries)

    def _check_gallery_changes(self):
        snapshot = self._gallery_snapshot()

        if snapshot != self._gallery_state:
            self._refresh_gallery()

    def _refresh_gallery(self, select_path: Path | None = None):
        self.gallery.clear()
        self._gallery_state = self._gallery_snapshot()

        target = self._target()
        if not target or not target.is_dir():
            self.preview.clear()
            self.preview.setText("Bild anklicken, um es anzusehen.")
            self.preview_name.clear()
            return
        files = [p for p in target.iterdir() if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg")]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        selected = None
        for p in files:
            pix = QPixmap(str(p))
            if pix.isNull():
                continue
            thumb = pix.scaled(150, 95, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            item = QListWidgetItem(QIcon(thumb), p.name)
            item.setData(Qt.UserRole, str(p)); item.setToolTip(str(p)); self.gallery.addItem(item)
            if select_path and p == select_path:
                selected = item
        if selected:
            self.gallery.setCurrentItem(selected); self._show_preview(selected)
        elif self.gallery.count() == 0:
            self.preview.clear()
            self.preview.setText("Keine Bilder im Zielordner.")
            self.preview_name.clear()

    def eventFilter(self, watched, event):
        if watched is self.gallery and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Delete:
                self._delete_selected_images()
                return True

        return super().eventFilter(watched, event)

    def _delete_selected_images(self):
        items = self.gallery.selectedItems()

        if not items:
            QMessageBox.information(
                self,
                "Bilder löschen",
                "Bitte zuerst mindestens ein Bild auswählen.",
            )
            return

        paths = []

        for item in items:
            path_text = item.data(Qt.UserRole)

            if not path_text:
                continue

            path = Path(path_text)

            # Nur Dateien aus dem aktuell eingestellten Zielordner zulassen.
            target = self._target()

            try:
                if (
                    target is None
                    or path.parent.resolve() != target.resolve()
                ):
                    continue
            except Exception:
                continue

            paths.append(path)

        if not paths:
            QMessageBox.warning(
                self,
                "Bilder löschen",
                "Keine gültigen Bilder im Zielordner ausgewählt.",
            )
            return

        count = len(paths)

        answer = QMessageBox.question(
            self,
            "Bilder löschen",
            (
                f"Sollen {count} ausgewählte "
                f"{'Bild' if count == 1 else 'Bilder'} wirklich gelöscht werden?\n\n"
                "Es werden nur die konvertierten PNG/JPG-Dateien "
                "im Zielordner gelöscht. Die ursprünglichen BMP-Dateien "
                "bleiben unverändert."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        deleted = 0
        errors = []

        for path in paths:
            try:
                if (
                    path.is_file()
                    and path.suffix.lower() in (".png", ".jpg", ".jpeg")
                ):
                    path.unlink()
                    deleted += 1
            except Exception as exc:
                errors.append(
                    f"{path.name}: {exc}"
                )

        self._refresh_gallery()

        if deleted:
            self.last_action.setText(
                f"✓ {deleted} "
                f"{'Bild gelöscht' if deleted == 1 else 'Bilder gelöscht'}."
            )

        if errors:
            QMessageBox.warning(
                self,
                "Bilder löschen",
                (
                    "Einige Bilder konnten nicht gelöscht werden:\n\n"
                    + "\n".join(errors)
                ),
            )

    def _show_preview(self, item):
        path = Path(item.data(Qt.UserRole))
        pix = QPixmap(str(path))
        if pix.isNull():
            return
        self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.preview_name.setText(path.name)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.gallery.currentItem():
            self._show_preview(self.gallery.currentItem())

    def _open_image(self, item):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(item.data(Qt.UserRole))))

    def _open_target(self):
        target = self._target()
        if target:
            target.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
