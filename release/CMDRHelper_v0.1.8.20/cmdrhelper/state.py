from __future__ import annotations

from pathlib import Path
import threading
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QSettings, Signal

from cmdrhelper.journal_reader import (
    default_journal_paths,
    read_latest_state,
)
from cmdrhelper.mission_manager import normalize_missions
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.valuation import (
    apply_values,
    system_totals,
)
from cmdrhelper.online_services import (
    fetch_edsm_bodies,
    load_cached_edsm_bodies,
)
from cmdrhelper.database import CMDRDatabase


class AppState(QObject):
    changed = Signal()
    edsmBodiesReady = Signal(str, object, str)
    databaseImportProgress = Signal(int, int, str)
    databaseImportFinished = Signal(object, str)

    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            "CMDRHelper",
            "CMDRHelper"
        )

        self.journal_folder = None
        self.database = CMDRDatabase()
        self._database_import_running = False

        self.commander = ""
        self.system = ""
        self.body = ""
        self.station = ""
        self.ship = ""
        self.last_timestamp = ""

        self.missions = []

        self.mission_reset_at = self.settings.value(
            "mission_reset_at",
            ""
        ) or ""

        # Online-Dienste
        self.edsm_commander = self.settings.value(
            "edsm/commander",
            ""
        ) or ""
        self.edsm_api_key = self.settings.value(
            "edsm/api_key",
            ""
        ) or ""
        self.edsm_enabled = (
            str(
                self.settings.value(
                    "edsm/enabled",
                    "false"
                )
            ).lower()
            in ("1", "true", "yes", "on")
        )

        self.inara_commander = self.settings.value(
            "inara/commander",
            ""
        ) or ""
        self.inara_api_key = self.settings.value(
            "inara/api_key",
            ""
        ) or ""
        self.inara_enabled = (
            str(
                self.settings.value(
                    "inara/enabled",
                    "false"
                )
            ).lower()
            in ("1", "true", "yes", "on")
        )

        self.system_bodies = []
        self.system_body_count = 0
        self.system_signals_count = 0
        self.system_all_bodies_found = False
        self.system_scan_value = 0
        self.system_mapped_value = 0
        self.system_current_value = 0
        self.system_high_value_count = 0

        self.edsm_body_count = 0
        self.edsm_added_count = 0
        self.edsm_source_status = ""
        self._edsm_request_system = ""

        self.edsmBodiesReady.connect(
            self._on_edsm_bodies_ready
        )

        self.journal_files = 0
        self.connected = False

        self.watcher = JournalWatcher(self)
        self.watcher.journalChanged.connect(
            self.refresh
        )

        saved = self.settings.value(
            "journal_folder",
            ""
        )

        if saved and Path(saved).exists():
            self.journal_folder = Path(saved)
        else:
            paths = default_journal_paths()
            if paths:
                self.journal_folder = paths[0]

        if self.journal_folder:
            self.watcher.set_folder(
                self.journal_folder
            )
            self.watcher.start()
            self.refresh()
            self.import_journal_archive(
                automatic=True
            )

    def database_stats(self):
        try:
            return self.database.stats()
        except Exception:
            return {
                "systems": 0,
                "bodies": 0,
                "materials": 0,
                "journal_imports": 0,
            }

    def import_journal_archive(self, automatic=False):
        if not self.journal_folder:
            if not automatic:
                self.databaseImportFinished.emit(
                    None,
                    "Kein Journalordner eingestellt."
                )
            return

        # Verhindert, dass automatischer Startimport und manueller
        # Wartungsimport gleichzeitig laufen.
        if self._database_import_running:
            return

        self._database_import_running = True
        folder = Path(self.journal_folder)

        def progress(current, total, name):
            # Der automatische Startabgleich soll still im Hintergrund
            # laufen. Fortschritt zeigen wir nur beim manuellen Import.
            if not automatic:
                self.databaseImportProgress.emit(
                    int(current),
                    int(total),
                    str(name),
                )

        def worker():
            try:
                stats = self.database.import_journal_archive(
                    folder,
                    progress_callback=progress,
                )

                if not automatic:
                    self.databaseImportFinished.emit(
                        stats,
                        ""
                    )
            except Exception as exc:
                error_text = str(exc)

                if automatic:
                    print(
                        "[CMDRHelper DB] Automatischer "
                        f"Archivabgleich fehlgeschlagen: {error_text}"
                    )

                # Auch beim automatischen Startimport an die Oberfläche
                # melden. So ist sofort sichtbar, in welcher Datei/Zeile
                # ein altes oder ungewöhnliches Journal klemmt.
                self.databaseImportFinished.emit(
                    None,
                    error_text
                )
            finally:
                self._database_import_running = False

        threading.Thread(
            target=worker,
            daemon=True,
            name=(
                "CMDRHelper-Database-AutoImport"
                if automatic
                else "CMDRHelper-Database-Import"
            ),
        ).start()

    def set_journal_folder(self, folder):
        self.journal_folder = Path(folder)

        self.settings.setValue(
            "journal_folder",
            str(folder)
        )

        self.watcher.set_folder(
            self.journal_folder
        )
        self.watcher.start()
        self.refresh()
        self.import_journal_archive(
            automatic=True
        )

    def reset_missions(self):
        self.mission_reset_at = (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        self.settings.setValue(
            "mission_reset_at",
            self.mission_reset_at
        )

        self.missions = []
        self.changed.emit()
        self.refresh()

    def set_edsm_settings(
        self,
        commander=None,
        api_key=None,
        enabled=None,
    ):
        if commander is not None:
            self.edsm_commander = commander.strip()
            self.settings.setValue(
                "edsm/commander",
                self.edsm_commander
            )

        if api_key is not None:
            self.edsm_api_key = api_key.strip()
            self.settings.setValue(
                "edsm/api_key",
                self.edsm_api_key
            )

        if enabled is not None:
            self.edsm_enabled = bool(enabled)
            self.settings.setValue(
                "edsm/enabled",
                self.edsm_enabled
            )

    def set_inara_settings(
        self,
        commander=None,
        api_key=None,
        enabled=None,
    ):
        if commander is not None:
            self.inara_commander = commander.strip()
            self.settings.setValue(
                "inara/commander",
                self.inara_commander
            )

        if api_key is not None:
            self.inara_api_key = api_key.strip()
            self.settings.setValue(
                "inara/api_key",
                self.inara_api_key
            )

        if enabled is not None:
            self.inara_enabled = bool(enabled)
            self.settings.setValue(
                "inara/enabled",
                self.inara_enabled
            )

    def _merge_edsm_into_system(
        self,
        edsm_data,
    ):
        if (
            not self.edsm_enabled
            or not isinstance(edsm_data, dict)
        ):
            self.edsm_body_count = 0
            self.edsm_added_count = 0
            return

        edsm_bodies = (
            edsm_data.get("bodies")
            or []
        )

        try:
            self.edsm_body_count = int(
                edsm_data.get("body_count")
                or len(edsm_bodies)
            )
        except Exception:
            self.edsm_body_count = len(
                edsm_bodies
            )

        by_id = {}
        by_name = {}

        for body in self.system_bodies:
            body["journal_scanned"] = True
            body["source"] = "Journal"

            body_id = body.get("body_id")
            if body_id is not None:
                by_id[body_id] = body

            name = body.get("name") or ""
            if name:
                by_name[name] = body

        added = 0

        for edsm_body in edsm_bodies:
            if not isinstance(
                edsm_body,
                dict
            ):
                continue

            body_id = edsm_body.get(
                "body_id"
            )
            name = (
                edsm_body.get("name")
                or ""
            )

            existing = None

            if (
                body_id is not None
                and body_id in by_id
            ):
                existing = by_id[body_id]
            elif name and name in by_name:
                existing = by_name[name]

            if existing is not None:
                existing["edsm_known"] = True
                existing["source"] = (
                    "Journal + EDSM"
                )

                # Grundregel:
                # Journaldaten bleiben führend und EDSM ergänzt nur
                # fehlende Werte.
                #
                # Ausnahme Explorer-Status:
                # Eine positive EDSM-Information "bereits entdeckt"
                # bzw. "bereits kartographiert" hat Vetorecht gegen
                # eine optimistische Journal-Annahme.
                if edsm_body.get("was_discovered") is True:
                    existing["was_discovered"] = True
                    existing["edsm_was_discovered"] = True

                if edsm_body.get("was_mapped") is True:
                    existing["was_mapped"] = True
                    existing["edsm_was_mapped"] = True

                for key, value in (
                    edsm_body.items()
                ):
                    if key in (
                        "journal_scanned",
                        "source",
                        "was_discovered",
                        "was_mapped",
                    ):
                        continue

                    current = existing.get(
                        key
                    )

                    if (
                        current is None
                        or current == ""
                    ):
                        existing[key] = value

                continue

            new_body = dict(
                edsm_body
            )
            new_body["journal_scanned"] = False
            new_body["edsm_known"] = True
            new_body["source"] = "EDSM"

            try:
                apply_values(new_body)
            except Exception:
                pass

            self.system_bodies.append(
                new_body
            )
            added += 1

        self.system_bodies.sort(
            key=lambda b: (
                b.get("body_id")
                if b.get("body_id") is not None
                else 999999
            )
        )

        self.edsm_added_count = added

    def _load_edsm_cache_for_current_system(
        self,
    ):
        self.edsm_body_count = 0
        self.edsm_added_count = 0
        self.edsm_source_status = ""

        if (
            not self.edsm_enabled
            or not self.system
        ):
            return False

        cached = load_cached_edsm_bodies(
            self.system
        )

        if cached is None:
            return False

        self._merge_edsm_into_system(
            cached
        )
        self.edsm_source_status = "Cache"
        return True

    def _request_edsm_for_current_system(
        self,
    ):
        if (
            not self.edsm_enabled
            or not self.system
        ):
            return

        system_name = self.system

        if (
            self._edsm_request_system
            == system_name
        ):
            return

        # Ist ein gültiger Cache vorhanden,
        # wurde er bereits synchron eingelesen.
        if load_cached_edsm_bodies(
            system_name
        ) is not None:
            return

        self._edsm_request_system = (
            system_name
        )

        def worker():
            ok, data, source = (
                fetch_edsm_bodies(
                    system_name
                )
            )

            if ok and data is not None:
                self.edsmBodiesReady.emit(
                    system_name,
                    data,
                    source,
                )
            else:
                self.edsmBodiesReady.emit(
                    system_name,
                    None,
                    source,
                )

        threading.Thread(
            target=worker,
            daemon=True,
            name=(
                "CMDRHelper-EDSM-"
                + system_name[:24]
            ),
        ).start()

    def _on_edsm_bodies_ready(
        self,
        system_name,
        data,
        source,
    ):
        if (
            self._edsm_request_system
            == system_name
        ):
            self._edsm_request_system = ""

        if system_name != self.system:
            return

        if data is None:
            self.edsm_source_status = (
                source or "Fehler"
            )
            self.changed.emit()
            return

        # Vor dem Merge Journalzustand frisch einlesen,
        # falls während der Netzabfrage neue Scans kamen.
        self._merge_edsm_into_system(
            data
        )

        self.edsm_source_status = (
            "EDSM"
            if source == "network"
            else "Cache"
        )

        self.changed.emit()

    def refresh(self):
        if not self.journal_folder:
            self.connected = False
            self.changed.emit()
            return

        data = read_latest_state(
            self.journal_folder,
            mission_reset_at=self.mission_reset_at,
        )

        self.commander = data["commander"]
        self.system = data["system"]
        self.body = data["body"]
        self.station = data["station"]
        self.ship = data["ship"]
        self.last_timestamp = data["last_timestamp"]
        self.journal_files = data["journal_files"]

        self.missions = normalize_missions(
            data["missions"]
        )

        self.system_bodies = data.get("system_bodies", [])

        # Phase 1: Journaldaten zusätzlich dauerhaft speichern.
        # Die bestehende Anzeige liest weiterhin wie bisher aus dem Journal.
        try:
            # Live-Snapshot speichern, aber die Journaldatei hier NICHT
            # als vollständig archiv-importiert markieren. Das erledigt
            # ausschließlich der Archivimport selbst.
            self.database.store_snapshot(data)
        except Exception as exc:
            print(f"[CMDRHelper DB] Speichern fehlgeschlagen: {exc}")

        for body in self.system_bodies:
            body["journal_scanned"] = True
            body["edsm_known"] = False
            body["source"] = "Journal"

        self.system_body_count = data.get("system_body_count", 0)
        self.system_signals_count = data.get("system_signals_count", 0)
        self.system_all_bodies_found = data.get("system_all_bodies_found", False)

        # Werte beziehen sich weiterhin ausschließlich auf
        # die tatsächlich im eigenen Journal vorhandenen Körper.
        totals = system_totals(self.system_bodies)
        self.system_scan_value = totals["scan_total"]
        self.system_mapped_value = totals["mapped_total"]
        self.system_current_value = totals["current_total"]
        self.system_high_value_count = totals["high_value_count"]

        self.connected = (
            self.journal_files > 0
        )

        self._load_edsm_cache_for_current_system()

        self.changed.emit()

        self._request_edsm_for_current_system()
