from __future__ import annotations

import logging
import platform
import re
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageEnhance
from cmdrhelper.i18n import tr
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


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def safe_filename_component(value, fallback="UNKNOWN"):
    text = INVALID_FILENAME_CHARS.sub("-", str(value or "").strip())
    text = re.sub(r"\s+", "-", text).strip(" .-")
    if not text:
        text = fallback
    if text.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        text = f"_{text}"
    return text[:120].rstrip(" .") or fallback


class ScreenshotView(QWidget):
    """BMP-Konverter und Galerie für Elite-Dangerous-Screenshots."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.settings = state.settings
        self.pool = QThreadPool.globalInstance()
        self._known: set[str] = set()
        self._pending: dict[str, tuple[int, int]] = {}
        self._converting: set[str] = set()
        self._workers: set[_ConvertWorker] = set()
        self._reserved_targets: set[Path] = set()
        self._gallery_state = None
        self._loading_settings = False

        self._build_ui()

        # Der Timer muss bereits existieren, wenn gespeicherte Checkbox-
        # Zustände geladen werden. setChecked(True) kann sofort toggled
        # auslösen und damit _update_watch_state() aufrufen.
        self.timer = QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self._scan)

        self._load_settings()
        self._refresh_gallery()
        self._update_watch_state()

        # Galerie unabhängig von der BMP-Überwachung aktuell halten.
        # So verschwinden auch extern gelöschte/verschobene Bilder automatisch.
        self.gallery_timer = QTimer(self)
        self.gallery_timer.setInterval(2000)
        self.gallery_timer.timeout.connect(self._check_gallery_changes)
        self.gallery_timer.start()
        if hasattr(self.state, "viewedCommanderChanged"):
            self.state.viewedCommanderChanged.connect(
                self._viewed_commander_changed
            )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)
        root.addWidget(QLabel(tr("images.title"), objectName="sectionTitle"))

        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(QLabel(tr("images.elite_screenshots"), objectName="sectionTitle"))

        info = QLabel(
            tr("images.info"),
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
        b = QPushButton(tr("images.choose")); b.clicked.connect(self._choose_source); source_row.addWidget(b)
        target_row = QHBoxLayout(); target_row.addWidget(self.target_edit, 1)
        b = QPushButton(tr("images.choose")); b.clicked.connect(self._choose_target); target_row.addWidget(b)

        self.format_combo = QComboBox(); self.format_combo.addItems(["PNG", "JPG"])
        self.format_combo.currentTextChanged.connect(self._save_settings)
        self.auto_check = QCheckBox(tr("images.auto_convert"))
        self.auto_check.toggled.connect(self._auto_toggled)
        self.delete_check = QCheckBox(tr("images.delete_bmp"))
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

        form.addRow(tr("images.source_folder") + ":", source_row)
        form.addRow(tr("images.target_folder") + ":", target_row)
        form.addRow(tr("images.output_format") + ":", self.format_combo)

        brightness_row = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 50)
        self.brightness_slider.setSingleStep(1)
        self.brightness_slider.setPageStep(5)
        self.brightness_slider.setToolTip(
            tr("images.brightness_tooltip")
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
        form.addRow(tr("images.brightness") + ":", brightness_row)

        form.addRow("", self.auto_check)
        form.addRow("", self.delete_check)
        layout.addLayout(form)

        save_row = QHBoxLayout()
        self.save_settings_button = QPushButton(
            tr("images.save_settings"),
            objectName="primary",
        )
        self.save_settings_button.clicked.connect(
            self._save_settings_clicked
        )
        save_row.addWidget(self.save_settings_button)

        self.save_settings_status = QLabel("", objectName="muted")
        save_row.addWidget(self.save_settings_status)
        save_row.addStretch()
        layout.addLayout(save_row)

        buttons = QHBoxLayout()
        self.convert_button = QPushButton(tr("images.convert_existing"), objectName="primary")
        self.convert_button.clicked.connect(self._convert_existing)
        buttons.addWidget(self.convert_button)
        b = QPushButton(tr("images.open_target")); b.clicked.connect(self._open_target); buttons.addWidget(b)
        buttons.addStretch()
        self.status = QLabel(tr("images.watch_off"), objectName="muted"); buttons.addWidget(self.status)
        layout.addLayout(buttons)

        self.last_action = QLabel(tr("images.no_conversion_yet"), objectName="muted")
        self.last_action.setWordWrap(True)
        layout.addWidget(self.last_action)
        root.addWidget(card)

        gallery_card = QFrame(objectName="card")
        gallery_layout = QVBoxLayout(gallery_card)
        gallery_layout.setContentsMargins(10, 8, 10, 8)
        top = QHBoxLayout(); top.addWidget(QLabel(tr("images.gallery"), objectName="sectionTitle")); top.addStretch()
        self.gallery_filter = QComboBox()
        self.gallery_filter.addItem(tr("images.filter_current"), "current")
        self.gallery_filter.addItem(tr("images.filter_all"), "all")
        self.gallery_filter.addItem(tr("images.filter_unassigned"), "unassigned")
        self.gallery_filter.currentIndexChanged.connect(self._refresh_gallery)
        top.addWidget(self.gallery_filter)
        self.delete_selected_button = QPushButton(tr("images.delete_selected"))
        self.delete_selected_button.clicked.connect(self._delete_selected_images)
        top.addWidget(self.delete_selected_button)

        b = QPushButton(tr("images.refresh_gallery")); b.clicked.connect(self._refresh_gallery); top.addWidget(b)
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
        self.preview = QLabel(tr("images.click_to_preview"), objectName="muted")
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

    @staticmethod
    def _setting_bool(value, default=False):
        if value is None:
            return bool(default)
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)

        text = str(value).strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off", ""):
            return False
        return bool(default)

    def _load_settings(self):
        # Während des Ladens lösen QComboBox, QSlider und QCheckBox teilweise
        # sofort ihre change-/toggled-Signale aus. Ohne Sperre würde
        # _save_settings() dabei die noch nicht geladenen Checkboxen wieder
        # als False in QSettings schreiben.
        self._loading_settings = True

        try:
            saved_source = str(
                self.settings.value(
                    self._key("source_dir"),
                    "",
                )
                or ""
            ).strip()

            if not saved_source:
                saved_source = self._default_source_dir()

            saved_target = str(
                self.settings.value(
                    self._key("target_dir"),
                    "",
                )
                or ""
            )

            fmt = str(
                self.settings.value(
                    self._key("format"),
                    "PNG",
                )
                or "PNG"
            ).upper()

            try:
                brightness = int(
                    self.settings.value(
                        self._key("brightness"),
                        15,
                    )
                    or 0
                )
            except (TypeError, ValueError):
                brightness = 15

            brightness = max(0, min(50, brightness))

            auto = self._setting_bool(
                self.settings.value(
                    self._key("auto"),
                    False,
                ),
                False,
            )

            delete_bmp = self._setting_bool(
                self.settings.value(
                    self._key("delete_bmp"),
                    False,
                ),
                False,
            )

            self.source_edit.setText(saved_source)
            self.target_edit.setText(saved_target)
            self.format_combo.setCurrentText(
                fmt if fmt in ("PNG", "JPG") else "PNG"
            )
            self.brightness_slider.setValue(brightness)
            self.brightness_spin.setValue(brightness)
            self.auto_check.setChecked(auto)
            self.delete_check.setChecked(delete_bmp)

            if saved_source:
                self.settings.setValue(
                    self._key("source_dir"),
                    saved_source,
                )

            self.settings.sync()

        finally:
            self._loading_settings = False

        self._baseline()

    def _save_settings(self, *args):
        if self._loading_settings:
            return

        self.settings.setValue(self._key("source_dir"), self.source_edit.text().strip())
        self.settings.setValue(self._key("target_dir"), self.target_edit.text().strip())
        self.settings.setValue(self._key("format"), self.format_combo.currentText())
        self.settings.setValue(self._key("brightness"), self.brightness_slider.value())
        self.settings.setValue(self._key("auto"), self.auto_check.isChecked())
        self.settings.setValue(self._key("delete_bmp"), self.delete_check.isChecked())
        self.settings.sync()

    def _save_settings_clicked(self):
        self._save_settings()
        self._baseline()
        self._refresh_gallery()
        self._update_watch_state()

        self.save_settings_status.setText(tr("images.settings_saved"))
        QTimer.singleShot(
            3000,
            lambda: self.save_settings_status.setText(""),
        )

    def closeEvent(self, event):
        self._save_settings()
        super().closeEvent(event)

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
        folder = QFileDialog.getExistingDirectory(self, tr("images.choose_source_title"), self.source_edit.text() or str(Path.home()))
        if folder:
            self.source_edit.setText(folder); self._save_settings(); self._baseline(); self._update_watch_state()

    def _choose_target(self):
        folder = QFileDialog.getExistingDirectory(self, tr("images.choose_target_title"), self.target_edit.text() or str(Path.home()))
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
            self.status.setText(tr("images.watch_active")); self.status.setObjectName("statusOk")
        else:
            self.timer.stop()
            if self.auto_check.isChecked():
                self.status.setText(tr("images.folders_missing")); self.status.setObjectName("statusWarn")
            else:
                self.status.setText(tr("images.watch_off")); self.status.setObjectName("muted")
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

    def _identity_snapshot(self):
        return {
            "fid": str(getattr(self.state, "commander_fid", "") or "").strip(),
            "commander": str(getattr(self.state, "commander", "") or "").strip(),
            "system": str(getattr(self.state, "system", "") or "").strip(),
        }

    @staticmethod
    def _folder_name(commander, fid):
        return (
            f"{safe_filename_component(commander)}_"
            f"{safe_filename_component(fid)}"
        )

    def _known_commanders(self):
        try:
            return list(self.state.database.list_commanders())
        except Exception:
            return []

    def _commander_for_id(self, commander_id):
        try:
            wanted = int(commander_id)
        except (TypeError, ValueError):
            return None
        return next(
            (item for item in self._known_commanders()
             if int(item.get("id")) == wanted),
            None,
        )

    def _folder_for_identity(self, commander, fid, *, existing=True):
        target = self._target()
        if target is None:
            return None
        safe_fid = safe_filename_component(fid)
        if existing and target.is_dir():
            suffix = f"_{safe_fid}".casefold()
            candidates = [
                path for path in target.iterdir()
                if path.is_dir() and not path.is_symlink()
                and path.name.casefold().endswith(suffix)
            ]
            if candidates:
                return sorted(candidates, key=lambda path: path.name.casefold())[0]
        desired = target / self._folder_name(commander, fid)
        if desired.is_symlink() or (desired.exists() and not desired.is_dir()):
            return None
        return desired

    def _viewed_commander_folder(self, *, existing=True):
        item = self._commander_for_id(
            getattr(self.state, "viewed_commander_id", None)
        )
        if item is None:
            return self._folder_for_identity("", "", existing=existing)
        return self._folder_for_identity(
            item.get("current_name") or "", item.get("fid") or "",
            existing=existing,
        )

    def _valid_commander_folders(self):
        target = self._target()
        if target is None or not target.is_dir():
            return []
        suffixes = {
            f"_{safe_filename_component(item.get('fid'))}".casefold()
            for item in self._known_commanders()
        }
        suffixes.add("_unknown")
        return sorted(
            (
                path for path in target.iterdir()
                if path.is_dir() and not path.is_symlink()
                and any(path.name.casefold().endswith(suffix) for suffix in suffixes)
            ),
            key=lambda path: path.name.casefold(),
        )

    def _gallery_directories(self):
        target = self._target()
        if target is None or not target.is_dir():
            return []
        mode = str(self.gallery_filter.currentData() or "current")
        if mode == "unassigned":
            return [target]
        if mode == "all":
            return self._valid_commander_folders()
        folder = self._viewed_commander_folder(existing=True)
        return [folder] if folder is not None and folder.is_dir() else []

    def _output_path(self, source: Path, identity=None):
        target = self._target()
        if not target:
            return None
        identity = dict(identity or self._identity_snapshot())
        folder = self._folder_for_identity(
            identity.get("commander"), identity.get("fid"), existing=True
        )
        if folder is None:
            return None
        try:
            timestamp = datetime.fromtimestamp(source.stat().st_mtime)
        except OSError:
            timestamp = datetime.now()
        parts = [
            timestamp.strftime("%Y-%m-%d_%H-%M-%S"),
            safe_filename_component(identity.get("commander")),
        ]
        system = str(identity.get("system") or "").strip()
        if system:
            parts.append(safe_filename_component(system))
        suffix = ".jpg" if self.format_combo.currentText() == "JPG" else ".png"
        base = "_".join(parts)
        candidate = folder / f"{base}{suffix}"
        number = 2
        while candidate.exists() or candidate in self._reserved_targets:
            candidate = folder / f"{base}_{number}{suffix}"
            number += 1
        return candidate

    def _queue(self, source: Path):
        identity = self._identity_snapshot()
        target = self._output_path(source, identity)
        if not target:
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
        self._reserved_targets.add(target)
        self._workers.add(worker); self._converting.add(key)
        self.last_action.setText(tr("images.converting", name=source.name))
        self.pool.start(worker)

    def _converted(self, source_text, target_text, ok, error):
        source, target = Path(source_text), Path(target_text)
        self._reserved_targets.discard(target)
        try:
            self._converting.discard(str(source.resolve()))
        except Exception:
            pass
        for worker in list(self._workers):
            if worker.source == source and worker.target == target:
                self._workers.discard(worker)
        if ok:
            logger.info("Screenshot konvertiert: %s -> %s", source.name, target.name)
            self.last_action.setText(tr("images.converted", source=source.name, target=target.name))
            self._refresh_gallery(target)
        else:
            logger.warning("Screenshot-Konvertierung fehlgeschlagen: %s", error)
            self.last_action.setText(tr("images.convert_error", name=source.name, error=error))

    def _convert_existing(self):
        source, target = self._source(), self._target()
        if not source or not source.is_dir():
            QMessageBox.warning(self, tr("images.title"), tr("images.invalid_source")); return
        if not target:
            QMessageBox.warning(self, tr("images.title"), tr("images.missing_target")); return
        target.mkdir(parents=True, exist_ok=True)
        queued = 0
        for p in sorted(source.iterdir()):
            if p.is_file() and p.suffix.lower() == ".bmp":
                out = self._output_path(p)
                if out and not out.exists():
                    self._known.add(str(p.resolve())); self._queue(p); queued += 1
        if queued == 0:
            self.last_action.setText(tr("images.no_new_bmps"))

    def _gallery_snapshot(self):
        target = self._target()

        if not target or not target.is_dir():
            return ()

        entries = []

        try:
            for directory in self._gallery_directories():
                for path in directory.iterdir():
                    if (
                        path.is_file() and not path.is_symlink()
                        and path.suffix.lower() in (".png", ".jpg", ".jpeg")
                    ):
                        stat = path.stat()
                        entries.append((
                            str(path.relative_to(target)),
                            int(stat.st_mtime_ns), int(stat.st_size),
                        ))
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
            self.preview.setText(tr("images.click_to_preview"))
            self.preview_name.clear()
            return
        files = [
            path for directory in self._gallery_directories()
            for path in directory.iterdir()
            if path.is_file() and not path.is_symlink()
            and path.suffix.lower() in (".png", ".jpg", ".jpeg")
        ]
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
            self.preview.setText(tr("images.no_images_target"))
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
                tr("images.delete_title"),
                tr("images.select_image_first"),
            )
            return

        paths = []

        for item in items:
            path_text = item.data(Qt.UserRole)

            if not path_text:
                continue

            path = Path(path_text)

            if not self._is_allowed_gallery_path(path):
                continue

            paths.append(path)

        if not paths:
            QMessageBox.warning(
                self,
                tr("images.delete_title"),
                tr("images.no_valid_images"),
            )
            return

        count = len(paths)

        answer = QMessageBox.question(
            self,
            tr("images.delete_title"),
            tr("images.delete_question", count=count),
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
            self.last_action.setText(tr("images.deleted_count", count=deleted))

        if errors:
            QMessageBox.warning(
                self,
                tr("images.delete_title"),
                tr("images.delete_errors") + "\n\n" + "\n".join(errors),
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
            folder = target
            if str(self.gallery_filter.currentData() or "current") == "current":
                current = self._viewed_commander_folder(existing=True)
                if current is not None and current.is_dir():
                    folder = current
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _viewed_commander_changed(self, *_args):
        if str(self.gallery_filter.currentData() or "current") == "current":
            self._refresh_gallery()

    def _is_allowed_gallery_path(self, path):
        target = self._target()
        path = Path(path)
        if target is None or path.is_symlink():
            return False
        try:
            root = target.resolve(strict=True)
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
        except (OSError, ValueError):
            return False
        allowed = set()
        for directory in self._gallery_directories():
            try:
                if not directory.is_symlink():
                    allowed.add(directory.resolve(strict=True))
            except OSError:
                continue
        return (
            resolved.parent in allowed
            and resolved.is_file()
            and resolved.suffix.lower() in (".png", ".jpg", ".jpeg")
        )
