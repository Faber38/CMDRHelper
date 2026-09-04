from __future__ import annotations

from pathlib import Path
import logging
import json
import sqlite3
import threading
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QSettings, Signal, QTimer

from cmdrhelper.journal_reader import (
    JournalReadError,
    default_journal_paths,
    read_latest_state,
)
from cmdrhelper.mission_manager import normalize_missions
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.valuation import (
    apply_values,
    calculate_body_values,
    system_totals,
)
from cmdrhelper.online_services import (
    fetch_edsm_bodies,
    load_cached_edsm_bodies,
)
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.edsm_uploader import EDSMJournalUploader
from cmdrhelper.inara_uploader import BATCH_SIZE as INARA_BATCH_SIZE, upload_batch
from cmdrhelper.bio_valuation import biology_totals
from cmdrhelper.route_planner.models import GuardianFsdBooster, ShipLoadoutData
from cmdrhelper.cargo import read_cargo_snapshot

logger = logging.getLogger(__name__)


class AppState(QObject):
    changed = Signal()
    commanderIdentityChanged = Signal(object, str, str)
    viewedCommanderChanged = Signal(object)
    positionChanged = Signal(str, object, str)
    shipLoadoutChanged = Signal(object)
    shipRouteInputsChanged = Signal(object)
    cargoSnapshotChanged = Signal(object)
    edsmBodiesReady = Signal(str, object, str)
    databaseImportProgress = Signal(int, int, str)
    databaseImportFinished = Signal(object, str)
    initializationStarted = Signal(bool, int)
    initializationProgress = Signal(int, int, str, str)
    initializationFinished = Signal(str)
    journalIndexReady = Signal(object)

    def __init__(self):
        super().__init__()

        self.settings = QSettings(
            "CMDRHelper",
            "CMDRHelper"
        )

        self.journal_folder = None
        self.database = CMDRDatabase()
        self._database_import_running = False
        self._database_import_manual_waiting = False
        self._database_import_last_progress = None
        self._journal_index_sessions = None
        self._journal_index_current = None
        self._initialization_visible = False
        self._last_refresh_error = ""

        self.commander = ""
        self.commander_id = None
        self.commander_fid = ""
        self.viewed_commander_id = self._saved_viewed_commander_id()
        self._viewed_commander_user_selected = False
        self.system = ""
        self.system_address = None
        self.body = ""
        self.station = ""
        self.ship = ""
        self.ship_loadout = ShipLoadoutData()
        self.cargo_snapshot = None
        self.last_timestamp = ""

        self.missions = []

        self.mission_reset_at = self.settings.value(
            "mission_reset_at",
            ""
        ) or ""

        # Online-Dienste
        self.edsm_commander = ""
        self.edsm_api_key = ""
        self.edsm_enabled = False
        self.edsm_uploader = None
        self._edsm_upload_running = False
        self._edsm_upload_token = None
        self._edsm_runtime_by_fid = {}
        self.edsm_upload_status = (
            "disabled" if not self.edsm_enabled else "waiting"
        )
        self.edsm_upload_message = (
            "EDSM deaktiviert"
            if not self.edsm_enabled
            else "Warte auf Übertragung"
        )

        self.inara_commander = ""
        self.inara_api_key = ""
        self.inara_enabled = False
        self._inara_upload_running = False
        self._inara_upload_token = None
        self._inara_runtime_by_fid = {}
        self.inara_upload_status = "waiting" if self.inara_enabled else "disabled"
        self.inara_upload_message = (
            "Warte auf Inara-Übertragung" if self.inara_enabled else "Inara deaktiviert"
        )

        self.system_bodies = []
        self.system_body_count = 0
        self.system_signals_count = 0
        self.system_all_bodies_found = False
        self.system_scan_value = 0
        self.system_mapped_value = 0
        self.system_current_value = 0
        self.system_high_value_count = 0

        # Exobiologie getrennt von Kartographie führen.
        self.system_bio_completed_count = 0
        self.system_bio_value = 0
        self.system_bio_first_logged_value = 0
        self.system_bio_unknown = []

        # Noch nicht abgegebene Explorer-Daten über alle Systeme.
        self.unsold_cartography_value = 0
        self.unsold_cartography_count = 0
        self.unsold_bio_value = 0
        self.unsold_bio_first_logged_value = 0
        self.unsold_bio_count = 0
        self.unsold_bio_unknown = []

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
            self._refresh_from_watcher
        )
        self.journalIndexReady.connect(self._finish_initial_journal_index)

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
            logger.info("Journalordner: %s", self.journal_folder)
            self.watcher.set_folder(
                self.journal_folder
            )
            QTimer.singleShot(0, self._start_initial_journal_index)

    def _start_initial_journal_index(self):
        """Startet den potenziell teuren Erstindex außerhalb des GUI-Threads."""
        if not self.journal_folder:
            return
        folder = Path(self.journal_folder)

        def worker():
            try:
                from cmdrhelper.journal_index import (
                    journal_index_plan, scan_journal_folder,
                    should_show_index_progress,
                )
                total, changed = journal_index_plan(self.database, folder)
                # Kurze inkrementelle Abgleiche bleiben unsichtbar. Ein leerer
                # Altindex oder mindestens 25 Inhaltsprüfungen ist sichtbar.
                visible = should_show_index_progress(total, changed)
                self._initialization_visible = visible
                self.initializationStarted.emit(visible, total)

                def progress(current, count, name):
                    self.initializationProgress.emit(
                        int(current), int(count), "startup.phase.index", str(name)
                    )

                sessions = scan_journal_folder(
                    self.database, folder,
                    progress_callback=progress if visible else None,
                )
                commander_ids = sorted({
                    int(item["commander_id"])
                    for item in sessions
                    if item.get("attribution_status") == "identified"
                    and item.get("commander_id") is not None
                })
                pending_mining = [
                    commander_id for commander_id in commander_ids
                    if self.database.commander_state_repair_needed(
                        commander_id, "surface_mining"
                    )
                ]
                if pending_mining:
                    mining_total = sum(
                        1 for item in sessions
                        if item.get("attribution_status") == "identified"
                        and item.get("commander_id") in pending_mining
                        and int(item.get("last_read_offset") or 0) > 0
                    )
                    if mining_total:
                        visible = True
                        self._initialization_visible = True
                        self.initializationStarted.emit(True, mining_total)
                    completed = 0
                    for commander_id in pending_mining:
                        commander_total = sum(
                            1 for item in sessions
                            if item.get("attribution_status") == "identified"
                            and item.get("commander_id") == commander_id
                            and int(item.get("last_read_offset") or 0) > 0
                        )

                        def mining_progress(current, _count, name, base=completed):
                            self.initializationProgress.emit(
                                base + int(current), mining_total,
                                "startup.phase.history", str(name),
                            )

                        self.database.backfill_surface_mining(
                            commander_id, sessions,
                            progress_callback=mining_progress if mining_total else None,
                        )
                        completed += commander_total
                for commander_id in commander_ids:
                    if self.database.commander_state_repair_needed(
                        commander_id, "body_scan_attributes"
                    ):
                        self.database.backfill_body_scan_attributes(
                            commander_id, sessions
                        )
                    if self.database.commander_state_repair_needed(
                        commander_id, "mercenary_credits"
                    ):
                        self.database.backfill_mercenary_credits(
                            commander_id, sessions
                        )
                self.journalIndexReady.emit(sessions)
            except Exception as exc:
                logger.exception("Initialer Journalindex fehlgeschlagen")
                self.initializationFinished.emit(str(exc))

        threading.Thread(
            target=worker, daemon=True, name="CMDRHelper-JournalIndex"
        ).start()

    def _finish_initial_journal_index(self, sessions):
        """Übernimmt das Worker-Ergebnis und setzt im GUI-Thread fort."""
        self._journal_index_sessions = list(sessions or [])
        self._journal_index_current = (
            str(Path(self._journal_index_sessions[-1]["journal_file"]))
            if self._journal_index_sessions else None
        )
        active_session = self._prepare_indexed_live_state(emit_identity=True)
        self._repair_latest_position_gap(active_session)
        # Indexzahl, Identität und persistenter Zustand sind bereits sicher
        # bekannt und sollen auch bei einem nachfolgenden Deltafehler sichtbar
        # bleiben.
        self.changed.emit()
        try:
            commander_id = (
                active_session.get("commander_id") if active_session else None
            )
            if commander_id is not None:
                features = [
                    feature for feature in ("unsold", "missions")
                    if self.database.commander_state_repair_needed(
                        int(commander_id), feature
                    )
                ]
                if features:
                    self.database.repair_commander_state(
                        self.journal_folder, self._journal_index_sessions,
                        int(commander_id), features=features,
                    )
        except Exception:
            logger.exception("Commander-Zustandsreparatur fehlgeschlagen")
        if not self.refresh():
            self.watcher.start()
            self.initializationFinished.emit(
                self._last_refresh_error or "Journal konnte nicht gelesen werden."
            )
            return
        self.watcher.start()
        self.import_journal_archive(automatic=True)

    def _repair_latest_position_gap(self, session):
        if not session or session.get("commander_id") is None:
            return False
        commander_id = int(session["commander_id"])
        if not self.database.commander_state_repair_needed(
            commander_id, "position_gap"
        ):
            return False
        path = Path(session["journal_file"])
        limit = int(session.get("last_read_offset") or 0)
        latest = None
        try:
            with path.open("rb") as handle:
                raw = handle.read(limit)
            for line in raw.splitlines():
                try:
                    event = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if event.get("event") in ("Location", "FSDJump", "CarrierJump", "Docked"):
                    latest = event
        except OSError as exc:
            logger.warning("Positionsreparatur konnte Journal nicht lesen: %s", exc)
            return False
        return self.database.repair_commander_position_gap(
            commander_id, path, latest or {},
            enqueue_inara=self._inara_identity_matches(commander_id),
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

    def _saved_viewed_commander_id(self):
        value = self.settings.value("commander_view/viewed_commander_id", None)
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def resolve_viewed_commander(self, commanders=None):
        """Bestimmt die Ansicht, ohne die Live-Identität zu verändern."""
        commanders = commanders if commanders is not None else self.database.list_commanders()
        known_ids = {int(item["id"]) for item in commanders}
        previous = self.viewed_commander_id

        if not self._viewed_commander_user_selected and self.commander_id in known_ids:
            self.viewed_commander_id = int(self.commander_id)
        elif self.viewed_commander_id not in known_ids:
            saved = self._saved_viewed_commander_id()
            self.viewed_commander_id = (
                saved if saved in known_ids
                else (int(commanders[0]["id"]) if commanders else None)
            )

        if self.viewed_commander_id != previous:
            self.viewedCommanderChanged.emit(self.viewed_commander_id)
        return self.viewed_commander_id

    def select_viewed_commander(self, commander_id):
        """Setzt nur die UI-Ansicht; Live-ID und DB-Schreibziel bleiben unberührt."""
        commander_id = int(commander_id)
        if not any(item["id"] == commander_id for item in self.database.list_commanders()):
            raise ValueError("Commander existiert nicht")
        previous = self.viewed_commander_id
        self.viewed_commander_id = commander_id
        self._viewed_commander_user_selected = True
        self.settings.setValue("commander_view/viewed_commander_id", commander_id)
        if previous != commander_id:
            self.viewedCommanderChanged.emit(commander_id)

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
        #
        # Wichtig: Nach einer Datenbank-Migration kann beim Programmstart
        # bereits ein automatischer Archivimport laufen. Klickt der Benutzer
        # dann auf "Journal-Archiv importieren", darf die Oberfläche nicht
        # auf "Vorbereitung …" hängen bleiben. Der manuelle Aufruf hängt
        # sich deshalb an den bereits laufenden Import an und bekommt dessen
        # Fortschritt/Abschluss mitgeteilt.
        if self._database_import_running:
            if not automatic:
                self._database_import_manual_waiting = True

                if self._database_import_last_progress is not None:
                    current, total, name = (
                        self._database_import_last_progress
                    )
                    self.databaseImportProgress.emit(
                        int(current),
                        int(total),
                        str(name),
                    )
                else:
                    self.databaseImportProgress.emit(
                        0,
                        0,
                        "Automatischer Archivabgleich läuft bereits …",
                    )
            return

        self._database_import_running = True
        logger.info(
            "Journal-Archivimport gestartet (%s)",
            "automatisch" if automatic else "manuell",
        )
        self._database_import_manual_waiting = (
            not automatic
        )
        self._database_import_last_progress = None
        folder = Path(self.journal_folder)

        def progress(current, total, name):
            current = int(current)
            total = int(total)
            name = str(name)

            self._database_import_last_progress = (
                current,
                total,
                name,
            )

            # Normalerweise bleibt der automatische Startabgleich still.
            # Hat der Benutzer währenddessen jedoch manuell auf Import
            # geklickt, zeigen wir ab diesem Moment den laufenden Fortschritt.
            if (
                not automatic
                or self._database_import_manual_waiting
                or self._initialization_visible
            ):
                self.databaseImportProgress.emit(
                    current,
                    total,
                    name,
                )
                if automatic and self._initialization_visible:
                    display_name = name
                    if ":" in display_name:
                        display_name = display_name.split(":", 1)[1].strip()
                    if not display_name.lower().endswith(".log"):
                        display_name = ""
                    self.initializationProgress.emit(
                        current, total, "startup.phase.history", display_name
                    )

        def worker():
            try:
                stats = self.database.import_journal_archive(
                    folder,
                    progress_callback=progress,
                )

                # Der Archivimport ist der vorgesehene vollständige Abgleich.
                # Hier bleiben beide Lernroutinen unabhängig vom letzten
                # Live-Event aktiv, damit historische Verkaufsdaten erhalten
                # beziehungsweise neu übernommen werden.
                self._run_journal_learning("", force=True, folder=folder)

                logger.info(
                    "Journal-Archivimport beendet: importiert=%s, übersprungen=%s",
                    stats.get("imported_journals", 0),
                    stats.get("skipped_journals", 0),
                )

                if (
                    not automatic
                    or self._database_import_manual_waiting
                ):
                    self.databaseImportFinished.emit(
                        stats,
                        ""
                    )
                if automatic:
                    self.initializationFinished.emit("")
            except Exception as exc:
                error_text = str(exc)

                if automatic:
                    logger.exception(
                        "Automatischer Archivabgleich fehlgeschlagen"
                    )

                # Auch beim automatischen Startimport an die Oberfläche
                # melden. So ist sofort sichtbar, in welcher Datei/Zeile
                # ein altes oder ungewöhnliches Journal klemmt.
                self.databaseImportFinished.emit(
                    None,
                    error_text
                )
                if automatic:
                    self.initializationFinished.emit(error_text)
            finally:
                self._database_import_running = False
                self._database_import_manual_waiting = False
                self._database_import_last_progress = None

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
        logger.info("Journalordner geändert: %s", self.journal_folder)

        self.settings.setValue(
            "journal_folder",
            str(folder)
        )

        self.watcher.set_folder(
            self.journal_folder
        )
        self._journal_index_sessions = None
        self._journal_index_current = None
        self._start_initial_journal_index()

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
        fid=None,
    ):
        fid = str(fid or self.commander_fid or "").strip()
        if not fid:
            raise ValueError("EDSM-Einstellungen benötigen eine eindeutige FID")
        prefix = f"edsm/commanders/{fid}"
        if commander is not None:
            self.settings.setValue(f"{prefix}/commander_name", commander.strip())

        if api_key is not None:
            self.settings.setValue(f"{prefix}/api_key", api_key.strip())

        if enabled is not None:
            self.settings.setValue(f"{prefix}/enabled", bool(enabled))

        if fid != self.commander_fid:
            return
        self._invalidate_edsm_worker()
        self._load_live_edsm_settings()
        if not self.edsm_enabled:
            self.edsm_upload_status = "disabled"
            self.edsm_upload_message = "EDSM deaktiviert"
        elif self.edsm_upload_status == "disabled":
            self.edsm_upload_status = "waiting"
            self.edsm_upload_message = "Warte auf Übertragung"

    def edsm_settings_for_fid(self, fid):
        fid = str(fid or "").strip()
        prefix = f"edsm/commanders/{fid}"
        return {
            "fid": fid,
            "commander": str(self.settings.value(f"{prefix}/commander_name", "") or ""),
            "api_key": str(self.settings.value(f"{prefix}/api_key", "") or ""),
            "enabled": str(self.settings.value(f"{prefix}/enabled", "false")).lower()
                       in ("1", "true", "yes", "on"),
            "last_test_status": str(
                self.settings.value(f"{prefix}/last_test_status", "") or ""
            ),
        }

    def set_edsm_test_status(self, fid, ok, text):
        fid = str(fid or "").strip()
        if fid:
            self.settings.setValue(
                f"edsm/commanders/{fid}/last_test_status",
                f"{'ok' if ok else 'error'}|{str(text or '')}",
            )

    def _load_live_edsm_settings(self):
        config = self.edsm_settings_for_fid(self.commander_fid)
        self.edsm_commander = config["commander"]
        self.edsm_api_key = config["api_key"]
        self.edsm_enabled = config["enabled"]
        runtime = getattr(self, "_edsm_runtime_by_fid", {}).get(self.commander_fid)
        if runtime:
            self.edsm_upload_status, self.edsm_upload_message = runtime
        else:
            self.edsm_upload_status = "waiting" if self.edsm_enabled else "disabled"
            self.edsm_upload_message = (
                "Warte auf Übertragung" if self.edsm_enabled else "EDSM deaktiviert"
            )

    def _migrate_legacy_edsm_settings(self):
        if not self.commander_fid or not self.commander:
            return False
        sessions = getattr(self, "_journal_index_sessions", None)
        if sessions:
            live_session = sessions[-1]
            if (
                live_session.get("attribution_status") != "identified"
                or str(live_session.get("fid_seen") or "").strip()
                != self.commander_fid
            ):
                return False
        old_keys = ("edsm/commander", "edsm/api_key", "edsm/enabled")
        if not any(self.settings.contains(key) for key in old_keys):
            return False
        legacy_name = str(self.settings.value("edsm/commander", "") or "").strip()
        if not legacy_name or legacy_name.casefold() != self.commander.strip().casefold():
            return False
        prefix = f"edsm/commanders/{self.commander_fid}"
        if not self.settings.contains(f"{prefix}/enabled"):
            mapping = (("edsm/commander", "commander_name"),
                       ("edsm/api_key", "api_key"), ("edsm/enabled", "enabled"))
            for old_key, new_name in mapping:
                if self.settings.contains(old_key):
                    self.settings.setValue(f"{prefix}/{new_name}", self.settings.value(old_key))
        upload_prefix = f"edsm_upload/commanders/{self.commander_fid}"
        if (
            self.settings.contains("edsm_upload/initialized")
            and not self.settings.contains(f"{upload_prefix}/initialized")
        ):
            self.settings.setValue(
                f"{upload_prefix}/initialized",
                self.settings.value("edsm_upload/initialized"),
            )
            for key in self.settings.allKeys():
                if key.startswith("edsm_upload/positions/"):
                    suffix = key.removeprefix("edsm_upload/positions/")
                    self.settings.setValue(
                        f"{upload_prefix}/positions/{suffix}",
                        self.settings.value(key),
                    )
        for key in old_keys:
            self.settings.remove(key)
        self.settings.remove("edsm_upload/initialized")
        self.settings.remove("edsm_upload/positions")
        self._load_live_edsm_settings()
        return True

    def _invalidate_edsm_worker(self):
        fid = str(getattr(self, "commander_fid", "") or "")
        if fid and hasattr(self, "_edsm_runtime_by_fid"):
            self._edsm_runtime_by_fid[fid] = (
                getattr(self, "edsm_upload_status", "disabled"),
                getattr(self, "edsm_upload_message", "EDSM deaktiviert"),
            )
        self._edsm_upload_token = None
        self._edsm_upload_running = False

    def set_inara_settings(
        self,
        commander=None,
        api_key=None,
        enabled=None,
        fid=None,
    ):
        fid = str(fid or self.commander_fid or "").strip()
        if not fid:
            raise ValueError("Inara-Einstellungen benötigen eine eindeutige FID")
        prefix = f"inara/commanders/{fid}"
        if commander is not None:
            self.settings.setValue(f"{prefix}/commander", commander.strip())

        if api_key is not None:
            self.settings.setValue(f"{prefix}/api_key", api_key.strip())

        if enabled is not None:
            self.settings.setValue(f"{prefix}/enabled", bool(enabled))
        if fid == self.commander_fid:
            if any(value is not None for value in (commander, api_key, enabled)):
                getattr(self, "_inara_runtime_by_fid", {}).pop(fid, None)
            self._load_live_inara_settings()

    def inara_settings_for_fid(self, fid):
        fid = str(fid or "").strip()
        prefix = f"inara/commanders/{fid}"
        return {
            "fid": fid,
            "commander": str(self.settings.value(f"{prefix}/commander", "") or ""),
            "api_key": str(self.settings.value(f"{prefix}/api_key", "") or ""),
            "enabled": str(self.settings.value(f"{prefix}/enabled", "false")).lower()
                       in ("1", "true", "yes", "on"),
            "last_test_status": str(
                self.settings.value(f"{prefix}/last_test_status", "") or ""
            ),
        }

    def set_inara_test_status(self, fid, ok, text):
        fid = str(fid or "").strip()
        if not fid:
            return
        self.settings.setValue(
            f"inara/commanders/{fid}/last_test_status",
            f"{'ok' if ok else 'error'}|{str(text or '')}",
        )

    def _load_live_inara_settings(self):
        config = self.inara_settings_for_fid(self.commander_fid)
        self.inara_commander = config["commander"]
        self.inara_api_key = config["api_key"]
        self.inara_enabled = config["enabled"]
        runtime = getattr(self, "_inara_runtime_by_fid", {}).get(self.commander_fid)
        if not self.inara_enabled:
            self.inara_upload_status = "disabled"
            self.inara_upload_message = "Inara deaktiviert"
        elif runtime:
            self.inara_upload_status, self.inara_upload_message = runtime
        else:
            self.inara_upload_status = "waiting"
            self.inara_upload_message = "Warte auf Inara-Übertragung"

    def _migrate_legacy_inara_settings(self):
        if not hasattr(self.settings, "contains") or not hasattr(
            self.settings, "remove"
        ):
            return
        migrated = str(
            self.settings.value("inara/commander_settings_migrated", "false") or "false"
        ).lower() in ("1", "true", "yes", "on")
        if not self.commander_fid or migrated:
            return
        prefix = f"inara/commanders/{self.commander_fid}"
        if not self.settings.contains(f"{prefix}/enabled"):
            for old, new in (("commander", "commander"), ("api_key", "api_key"),
                             ("enabled", "enabled")):
                old_key = f"inara/{old}"
                if self.settings.contains(old_key):
                    self.settings.setValue(f"{prefix}/{new}", self.settings.value(old_key))
        self.settings.setValue("inara/commander_settings_migrated", True)
        for key in ("inara/commander", "inara/api_key", "inara/enabled",
                    "inara/commander_fid"):
            self.settings.remove(key)
        self._load_live_inara_settings()

    def _inara_identity_matches(self, commander_id=None):
        return bool(
            getattr(self, "inara_enabled", False)
            and getattr(self, "inara_api_key", "") and self.commander_fid
            and (commander_id is None or int(commander_id) == int(self.commander_id or -1))
        )

    def _invalidate_inara_worker(self):
        """Detach a worker as soon as the active journal identity changes."""
        fid = str(getattr(self, "commander_fid", "") or "")
        status = getattr(self, "inara_upload_status", "disabled")
        if fid and status != "uploading":
            runtime = getattr(self, "_inara_runtime_by_fid", None)
            if runtime is None:
                runtime = self._inara_runtime_by_fid = {}
            runtime[fid] = (
                status, getattr(self, "inara_upload_message", "")
            )
        self._inara_upload_token = None
        self._inara_upload_running = False

    def _upload_pending_to_inara(self):
        if not self._inara_identity_matches():
            return
        commander_id = int(self.commander_id)
        commander_name = str(self.commander or "")
        commander_fid = str(self.commander_fid or "")
        api_key = str(self.inara_api_key or "")
        active_token = getattr(self, "_inara_upload_token", None)
        if (
            self._inara_upload_running
            and active_token is not None
            and active_token[:3] == (commander_id, commander_fid, api_key)
        ):
            return
        rows = self.database.inara_pending(commander_id, INARA_BATCH_SIZE)
        if not rows:
            return
        token = (commander_id, commander_fid, api_key, object())
        self._inara_upload_token = token
        self._inara_upload_running = True
        self.inara_upload_status = "uploading"
        self.inara_upload_message = f"{len(rows)} Inara-Event(s) werden übertragen"
        self.changed.emit()

        def worker():
            try:
                if (
                    self._inara_upload_token is not token
                    or not self._inara_identity_matches(commander_id)
                    or self.commander_fid != commander_fid
                    or self.inara_api_key != api_key
                ):
                    return
                sent, failed = upload_batch(api_key, commander_name, commander_fid, rows)
                if self._inara_upload_token is not token:
                    return
                self.database.update_inara_outbox(sent, failed)
                if failed:
                    self.inara_upload_status = "error"
                    self.inara_upload_message = next(iter(failed.values()))
                else:
                    self.inara_upload_status = "ok"
                    self.inara_upload_message = f"Letzte Inara-Übertragung erfolgreich: {len(sent)} Event(s)"
                self._inara_runtime_by_fid[commander_fid] = (
                    self.inara_upload_status, self.inara_upload_message
                )
            except Exception as exc:
                if self._inara_upload_token is not token:
                    return
                message = str(exc)
                self.database.update_inara_outbox(
                    errors={row["id"]: message for row in rows}
                )
                if commander_fid == self.commander_fid:
                    self.inara_upload_status = "error"
                    self.inara_upload_message = message
                    self._inara_runtime_by_fid[commander_fid] = (
                        self.inara_upload_status, self.inara_upload_message
                    )
                logger.warning("Inara-Upload pausiert: %s", message)
            finally:
                if self._inara_upload_token is token:
                    self._inara_upload_token = None
                    self._inara_upload_running = False
                    self.changed.emit()

        threading.Thread(target=worker, daemon=True,
                         name="CMDRHelper-Inara-Upload").start()

    def _upload_journal_to_edsm(self):
        if (
            not self.edsm_enabled
            or not self.commander_fid
            or not self.edsm_commander
            or not self.edsm_api_key
            or not self.journal_folder
            or self._edsm_upload_running
        ):
            return

        self._edsm_upload_running = True
        folder = Path(self.journal_folder)
        fid = str(self.commander_fid or "")
        commander = str(self.edsm_commander or "")
        api_key = str(self.edsm_api_key or "")
        token = (fid, commander, api_key, object())
        self._edsm_upload_token = token
        uploader = EDSMJournalUploader(
            commander, api_key, settings=self.settings, fid=fid,
            is_current=lambda: self._edsm_upload_token is token,
        )
        self.edsm_uploader = uploader

        def worker():
            try:
                result = uploader.process_folder(folder)

                if self._edsm_upload_token is not token or result.get("cancelled"):
                    return

                if result.get("initialized"):
                    logger.info(
                        "EDSM-Uploader initialisiert; vorhandene "
                        "Journaldaten werden nicht erneut übertragen."
                    )

                error = result.get("error") or ""
                if error == "__cancelled__":
                    return
                if error:
                    self.edsm_upload_status = "error"
                    self.edsm_upload_message = str(error)
                    logger.warning(
                        "EDSM-Upload pausiert: %s",
                        error,
                    )
                else:
                    sent = int(result.get("events_sent") or 0)
                    discarded = int(result.get("events_skipped") or 0)

                    self.edsm_upload_status = "ok"
                    if sent:
                        self.edsm_upload_message = (
                            f"Letzte Übertragung erfolgreich: "
                            f"{sent} Event(s)"
                        )
                    elif discarded:
                        self.edsm_upload_message = (
                            "EDSM aktiv · Journal verarbeitet"
                        )
                    else:
                        self.edsm_upload_message = (
                            "EDSM aktiv · keine neuen Daten"
                        )

            except Exception as exc:
                if self._edsm_upload_token is not token:
                    return
                self.edsm_upload_status = "error"
                self.edsm_upload_message = str(exc)
                logger.exception("EDSM-Upload fehlgeschlagen")
            finally:
                if self._edsm_upload_token is token:
                    self._edsm_upload_token = None
                    self._edsm_upload_running = False
                    self.changed.emit()

        threading.Thread(
            target=worker,
            daemon=True,
            name="CMDRHelper-EDSM-Upload",
        ).start()

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
                factor = self.database.learned_cartography_factor(
                    new_body.get("planet_class") or "",
                    new_body.get("terraformable"),
                )
                apply_values(
                    new_body,
                    correction_factor=factor,
                )
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

    def _refresh_from_watcher(self):
        success = False
        try:
            success = self.refresh()
        except Exception:
            logger.exception("Journalaktualisierung unerwartet fehlgeschlagen")
        finally:
            self.watcher.refresh_finished(success)

    def _run_journal_learning(self, latest_event, force=False, folder=None):
        """Startet teure Lernläufe nur bei passenden Verkaufsevents."""
        folder = Path(folder or self.journal_folder)

        if force or latest_event == "SellOrganicData":
            try:
                learn_result = self.database.learn_bio_values_from_journals(folder)
                if int(learn_result.get("values_changed") or 0):
                    logger.info(
                        "BIO-Wertetabelle aktualisiert: %s neue/geänderte Werte",
                        int(learn_result.get("values_changed") or 0),
                    )
            except Exception:
                logger.exception(
                    "BIO-Verkaufswerte konnten nicht aus dem Journal gelernt werden"
                )

        if force or latest_event in (
            "SellExplorationData",
            "MultiSellExplorationData",
        ):
            try:
                result = self.database.learn_cartography_values_from_journals(
                    folder,
                    valuation_func=calculate_body_values,
                )
                if int(result.get("sales_stored") or 0):
                    logger.info(
                        "Kartographie-Lerndaten aktualisiert: %s Verkauf/Verkäufe, "
                        "%s Körper",
                        int(result.get("sales_stored") or 0),
                        int(result.get("bodies_stored") or 0),
                    )
            except Exception:
                logger.exception(
                    "Kartographie-Verkaufswerte konnten nicht aus dem Journal gelernt werden"
                )

    def reset_commander_runtime_state(self):
        """Leert ausschließlich persönliche, flüchtige Commander-Zustände."""
        self.commander = ""
        self.system = ""
        self.system_address = None
        self.body = ""
        self.station = ""
        self.ship = ""
        self.ship_loadout = ShipLoadoutData()
        self.cargo_snapshot = None
        cargo_signal = getattr(self, "cargoSnapshotChanged", None)
        if cargo_signal is not None:
            cargo_signal.emit(None)
        self.last_timestamp = ""
        self.missions = []

        self.system_bodies = []
        self.system_body_count = 0
        self.system_signals_count = 0
        self.system_all_bodies_found = False
        self.system_scan_value = 0
        self.system_mapped_value = 0
        self.system_current_value = 0
        self.system_high_value_count = 0

        self.system_bio_completed_count = 0
        self.system_bio_value = 0
        self.system_bio_first_logged_value = 0
        self.system_bio_unknown = []

        self.unsold_cartography_value = 0
        self.unsold_cartography_count = 0
        self.unsold_bio_value = 0
        self.unsold_bio_first_logged_value = 0
        self.unsold_bio_count = 0
        self.unsold_bio_unknown = []

        self.edsm_body_count = 0
        self.edsm_added_count = 0
        self.edsm_source_status = ""
        self._edsm_request_system = ""

    def _latest_identified_index_session(self):
        """Returns the chronologically newest indexed, identified session."""
        for session in reversed(self._journal_index_sessions or []):
            if not isinstance(session, dict):
                continue
            if (
                session.get("attribution_status") == "identified"
                and session.get("commander_id") is not None
                and str(session.get("fid_seen") or "").strip()
            ):
                return session
        return None

    @staticmethod
    def _stored_ship_loadout(stored_ship):
        return ShipLoadoutData(
            ship_id=stored_ship.get("ship_id"),
            ship_type=stored_ship.get("ship_type"),
            ship_name=stored_ship.get("ship_name"),
            ship_ident=stored_ship.get("ship_ident"),
            max_jump_range=stored_ship.get("max_jump_range"),
            unladen_mass=stored_ship.get("unladen_mass"),
            cargo_capacity=stored_ship.get("cargo_capacity"),
            main_tank_capacity=stored_ship.get("main_tank_capacity"),
            reserve_tank_capacity=stored_ship.get("reserve_tank_capacity"),
            fsd_item=stored_ship.get("fsd_item"),
            guardian_fsd_boosters=tuple(
                GuardianFsdBooster(item.get("item") or "", item.get("on"))
                for item in (stored_ship.get("guardian_fsd_boosters") or [])
                if isinstance(item, dict)
            ),
            modules=tuple(stored_ship.get("modules") or ()),
            loadout_timestamp=stored_ship.get("loadout_timestamp"),
            loadout_complete=bool(stored_ship.get("loadout_complete")),
            loadout_stale=bool(stored_ship.get("loadout_stale", True)),
        )

    def _restore_persistent_commander_state(self, summary):
        """Restores the fast-start fields that do not require journal replay."""
        if not summary:
            return
        self.commander = summary.get("current_name") or self.commander
        location = summary.get("persistent_location") or {}
        if location:
            self.system = location.get("system_name") or ""
            self.system_address = location.get("system_address")
            self.station = location.get("station_name") or ""
            self.body = location.get("body_name") or ""
            self.last_timestamp = location.get("event_timestamp") or self.last_timestamp
        stored_ship = summary.get("ship") or {}
        if stored_ship:
            self.ship = stored_ship.get("ship_name") or stored_ship.get("ship_type") or ""
            self.ship_loadout = self._stored_ship_loadout(stored_ship)
        self.missions = normalize_missions([
            mission
            for mission in self.database.commander_missions(self.commander_id)
            if mission.get("is_open")
        ])
        persistent_cart = summary.get("unsold_cartography") or {}
        self.unsold_cartography_value = int(
            persistent_cart.get("estimated_value") or 0
        )
        self.unsold_cartography_count = int(persistent_cart.get("bodies") or 0)
        persistent_bio = summary.get("unsold_biology") or {}
        self.unsold_bio_count = int(persistent_bio.get("findings") or 0)
        self.unsold_bio_value = int(persistent_bio.get("estimated_value") or 0)
        self.unsold_bio_first_logged_value = self.unsold_bio_value * 5
        self.unsold_bio_unknown = ["Unbekannte BIO-Art"] * int(
            persistent_bio.get("unknown_values") or 0
        )

    def _prepare_indexed_live_state(self, emit_identity=False):
        """Adopts index facts before processing bytes after the journal offset."""
        self.journal_files = len(self._journal_index_sessions or [])
        self.connected = self.journal_files > 0
        session = self._latest_identified_index_session()
        if session is None:
            return None

        commander_id = int(session["commander_id"])
        fid = str(session.get("fid_seen") or "").strip()
        name = str(session.get("commander_name_seen") or "").strip()
        previous_fid = self.commander_fid
        if previous_fid and previous_fid != fid:
            AppState._invalidate_inara_worker(self)
            AppState._invalidate_edsm_worker(self)
        self.database.set_active_commander(commander_id)
        self.commander_id = commander_id
        self.commander_fid = fid
        if name:
            self.commander = name
        if hasattr(self, "settings"):
            if (self._journal_index_sessions or [None])[-1] is session:
                AppState._migrate_legacy_inara_settings(self)
                AppState._migrate_legacy_edsm_settings(self)
            AppState._load_live_inara_settings(self)
            AppState._load_live_edsm_settings(self)
        if not getattr(self, "_viewed_commander_user_selected", False):
            previous_viewed = getattr(self, "viewed_commander_id", None)
            self.viewed_commander_id = commander_id
            if previous_viewed != commander_id:
                self.viewedCommanderChanged.emit(commander_id)

        self._restore_persistent_commander_state(
            self.database.commander_summary(commander_id)
        )
        if emit_identity and previous_fid != fid:
            self.commanderIdentityChanged.emit(commander_id, fid, self.commander)
        return session

    def _apply_commander_identity(self, data, emit_signal=True):
        """Übernimmt ausschließlich eine durch FID belegte Journalidentität."""
        fid = str(data.get("commander_fid") or "").strip()
        if not fid:
            return False

        name = str(
            data.get("commander_identity_name") or data.get("commander") or ""
        ).strip()
        commander_id = self.database.upsert_commander(
            fid,
            name,
            data.get("commander_identity_timestamp") or "",
        )
        if commander_id is None:
            return False

        self.database.ensure_schema_v3()
        self.database.ensure_schema_v4()
        self.database.ensure_schema_v5()
        self.database.set_active_commander(commander_id)

        previous_fid = self.commander_fid
        if previous_fid and previous_fid != fid:
            AppState._invalidate_inara_worker(self)
            AppState._invalidate_edsm_worker(self)
        self.commander_id = commander_id
        self.commander_fid = fid
        if hasattr(self, "settings"):
            AppState._migrate_legacy_inara_settings(self)
            AppState._load_live_inara_settings(self)
            AppState._migrate_legacy_edsm_settings(self)
            AppState._load_live_edsm_settings(self)

        if not getattr(self, "_viewed_commander_user_selected", False):
            previous_viewed = getattr(self, "viewed_commander_id", None)
            self.viewed_commander_id = commander_id
            if previous_viewed != commander_id and hasattr(self, "viewedCommanderChanged"):
                self.viewedCommanderChanged.emit(commander_id)

        changed = previous_fid != fid
        if changed and emit_signal:
            self.commanderIdentityChanged.emit(commander_id, fid, name)
        return changed

    def _store_latest_journal_session(self, data):
        """Persistiert nur die aktuelle Datei, nicht rückwirkend das Archiv."""
        session = data.get("latest_journal_session")
        if not isinstance(session, dict):
            return
        self.database.store_journal_session(session)

    def refresh(self):
        self._last_refresh_error = ""
        if not self.journal_folder:
            self.connected = False
            self.changed.emit()
            return True

        try:
            watcher_current = getattr(self.watcher, "_current", None)
            if (
                self._journal_index_sessions is None
                or (watcher_current is not None
                    and str(watcher_current) != self._journal_index_current)
            ):
                from cmdrhelper.journal_index import scan_journal_folder
                self._journal_index_sessions = scan_journal_folder(
                    self.database, self.journal_folder
                )
                self._journal_index_current = (
                    str(Path(self._journal_index_sessions[-1]["journal_file"]))
                    if self._journal_index_sessions else None
                )
            self._prepare_indexed_live_state(emit_identity=False)
            data = read_latest_state(
                self.journal_folder,
                mission_reset_at=self.mission_reset_at,
                indexed_sessions=self._journal_index_sessions,
            )
        except JournalReadError as exc:
            logger.warning("Temporärer Journal-Lesefehler: %s", exc)
            return False
        except OSError as exc:
            # Auch ein Fehler während der Iteration (nach erfolgreichem open)
            # darf die Watcher-Signatur nicht bestätigen.
            logger.warning(
                "Journal konnte nicht vollständig gelesen werden: %s",
                exc,
            )
            return False

        previous_system = self.system
        previous_system_address = self.system_address
        previous_loadout = self.ship_loadout

        incoming_fid = str(data.get("commander_fid") or "").strip()
        if (
            self.commander_fid
            and incoming_fid
            and incoming_fid != self.commander_fid
        ):
            self.reset_commander_runtime_state()

        if data.get("commander_fid"):
            self.commander = (
                data.get("commander_identity_name")
                or data.get("commander")
                or self.commander
            )
        identity_changed = self._apply_commander_identity(
            data,
            emit_signal=False,
        )
        current_session = ((self._journal_index_sessions or [None])[-1])
        if (
            current_session
            and data.get("latest_journal_session") is current_session
            and str(current_session.get("fid_seen") or "").strip()
            == self.commander_fid
        ):
            current_session["commander_id"] = self.commander_id
        if current_session and current_session.get("commander_id") is not None:
            from cmdrhelper.journal_reader import read_journal_delta
            committed_offset = int(current_session.get("last_read_offset") or 0)
            delta_events, safe_offset = read_journal_delta(
                Path(current_session["journal_file"]), committed_offset,
            )
            if safe_offset > committed_offset:
                try:
                    self.database.apply_commander_journal_delta(
                        int(current_session["commander_id"]),
                        current_session["journal_file"], delta_events, safe_offset,
                        enqueue_inara=self._inara_identity_matches(
                            current_session["commander_id"]
                        ),
                    )
                except (sqlite3.Error, RuntimeError, ValueError) as exc:
                    logger.exception("Commander-Journaldelta konnte nicht gespeichert werden")
                    self._last_refresh_error = (
                        "Journaldelta konnte nicht gespeichert werden: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    self.changed.emit()
                    return False
                current_session["last_read_offset"] = safe_offset
        persistent_summary = (
            self.database.commander_summary(self.commander_id)
            if self.commander_id is not None else None
        ) or {}
        stored_location = persistent_summary.get("persistent_location") or {}
        if not data.get("system") and stored_location:
            data["system"] = stored_location.get("system_name") or ""
            data["system_address"] = stored_location.get("system_address")
            data["station"] = stored_location.get("station_name") or ""
            data["body"] = stored_location.get("body_name") or ""
            data["last_position"] = dict(stored_location)
        if getattr(data.get("ship_loadout"), "ship_id", None) is None:
            stored_ship = persistent_summary.get("ship") or {}
            if stored_ship:
                data["ship"] = stored_ship.get("ship_name") or stored_ship.get("ship_type") or ""
                data["ship_loadout"] = ShipLoadoutData(
                    ship_id=stored_ship.get("ship_id"),
                    ship_type=stored_ship.get("ship_type"),
                    ship_name=stored_ship.get("ship_name"),
                    ship_ident=stored_ship.get("ship_ident"),
                    max_jump_range=stored_ship.get("max_jump_range"),
                    unladen_mass=stored_ship.get("unladen_mass"),
                    cargo_capacity=stored_ship.get("cargo_capacity"),
                    main_tank_capacity=stored_ship.get("main_tank_capacity"),
                    reserve_tank_capacity=stored_ship.get("reserve_tank_capacity"),
                    fsd_item=stored_ship.get("fsd_item"),
                    guardian_fsd_boosters=tuple(
                        GuardianFsdBooster(item.get("item") or "", item.get("on"))
                        for item in (stored_ship.get("guardian_fsd_boosters") or [])
                        if isinstance(item, dict)
                    ),
                    modules=tuple(stored_ship.get("modules") or ()),
                    loadout_timestamp=stored_ship.get("loadout_timestamp"),
                    loadout_complete=bool(stored_ship.get("loadout_complete")),
                    loadout_stale=bool(stored_ship.get("loadout_stale", True)),
                )
        self._store_latest_journal_session(data)
        self.system = data["system"]
        self.system_address = data.get("system_address")
        self.body = data["body"]
        self.station = data["station"]
        self.ship = data["ship"]
        self.ship_loadout = data.get("ship_loadout") or ShipLoadoutData()
        self.last_timestamp = data["last_timestamp"]
        self.journal_files = data["journal_files"]

        self._apply_live_cargo_snapshot(data, current_session)

        if (
            identity_changed
            or self._ship_loadout_signature(previous_loadout)
            != self._ship_loadout_signature(self.ship_loadout)
        ):
            self.shipLoadoutChanged.emit(self.ship_loadout)

        if (
            identity_changed
            or self._ship_route_inputs_signature(previous_loadout)
            != self._ship_route_inputs_signature(self.ship_loadout)
        ):
            self.shipRouteInputsChanged.emit(self.ship_loadout)

        if (
            self.system
            and (
                self.system != previous_system
                or self.system_address != previous_system_address
            )
        ):
            event_type = str(data.get("last_system_event") or "")
            if event_type in ("FSDJump", "CarrierJump", "Location"):
                self.positionChanged.emit(
                    self.system,
                    self.system_address,
                    event_type,
                )

        self.missions = normalize_missions(data["missions"])
        if self.commander_id is not None:
            self.missions = normalize_missions([
                mission for mission in self.database.commander_missions(self.commander_id)
                if mission.get("is_open")
            ])

        self.system_bodies = data.get("system_bodies", [])

        # Phase 1: Journaldaten zusätzlich dauerhaft speichern.
        # Die bestehende Anzeige liest weiterhin wie bisher aus dem Journal.
        try:
            # Live-Snapshot speichern, aber die Journaldatei hier NICHT
            # als vollständig archiv-importiert markieren. Das erledigt
            # ausschließlich der Archivimport selbst.
            self.database.store_snapshot(data, commander_id=self.commander_id)
        except Exception:
            logger.exception("Commander-Livezustand konnte nicht gespeichert werden")

        latest_event = str(data.get("last_event") or "")

        self._run_journal_learning(latest_event)

        # Gelernte Korrektur auf die aktuell sichtbaren Journal-Körper
        # anwenden. Ohne Lerndaten liefert die Datenbank exakt Faktor 1.0.
        for body in self.system_bodies:
            try:
                factor = self.database.learned_cartography_factor(
                    body.get("planet_class") or "",
                    body.get("terraformable"),
                )
            except Exception:
                factor = 1.0

            try:
                apply_values(
                    body,
                    correction_factor=factor,
                )
            except Exception:
                logger.exception(
                    "Gelernter Kartographiewert konnte für %s nicht angewendet werden",
                    body.get("name") or "?",
                )

        for body in self.system_bodies:
            body["journal_scanned"] = True
            body["edsm_known"] = False
            body["source"] = "Journal"

        self.system_body_count = data.get("system_body_count", 0)
        self.system_signals_count = data.get("system_signals_count", 0)
        self.system_all_bodies_found = data.get("system_all_bodies_found", False)

        # Werte beziehen sich weiterhin ausschließlich auf
        # die tatsächlich im eigenen Journal vorhandenen Körper.
        totals = system_totals(
            self.system_bodies,
            correction_factor_func=lambda body: (
                self.database.learned_cartography_factor(
                    body.get("planet_class") or "",
                    body.get("terraformable"),
                )
            ),
        )
        self.system_scan_value = totals["scan_total"]
        self.system_mapped_value = totals["mapped_total"]
        self.system_current_value = totals["current_total"]
        self.system_high_value_count = totals["high_value_count"]

        # BIO-Werte stammen aus den dauerhaft gespeicherten ScanOrganic-
        # Ereignissen. Nur vollständig analysierte Proben (ScanType=Analyse)
        # werden gezählt.
        try:
            bio_entries = [
                entry
                for body in self.system_bodies
                for entry in (body.get("biology") or [])
            ]
            learned_values = self.database.learned_bio_values()

            bio_totals = biology_totals(
                bio_entries,
                learned_values=learned_values,
            )
        except Exception:
            logger.exception(
                "BIO-Werte für aktuelles System konnten nicht berechnet werden"
            )
            bio_totals = {
                "completed_count": 0,
                "base_total": 0,
                "first_logged_total": 0,
                "unknown": [],
            }

        self.system_bio_completed_count = int(
            bio_totals["completed_count"]
        )
        self.system_bio_value = int(
            bio_totals["base_total"]
        )
        self.system_bio_first_logged_value = int(
            bio_totals["first_logged_total"]
        )
        self.system_bio_unknown = list(
            bio_totals["unknown"]
        )

        persistent = (
            self.database.commander_summary(self.commander_id)
            if self.commander_id is not None else None
        ) or {}
        persistent_cart = persistent.get("unsold_cartography") or {}
        self.unsold_cartography_value = int(persistent_cart.get("estimated_value") or 0)
        self.unsold_cartography_count = int(persistent_cart.get("bodies") or 0)
        persistent_bio = persistent.get("unsold_biology") or {}
        self.unsold_bio_count = int(persistent_bio.get("findings") or 0)
        self.unsold_bio_value = int(persistent_bio.get("estimated_value") or 0)
        self.unsold_bio_first_logged_value = self.unsold_bio_value * 5
        self.unsold_bio_unknown = ["Unbekannte BIO-Art"] * int(
            persistent_bio.get("unknown_values") or 0
        )

        self.connected = (
            self.journal_files > 0
        )

        self._load_edsm_cache_for_current_system()

        if identity_changed:
            self.commanderIdentityChanged.emit(
                self.commander_id,
                self.commander_fid,
                self.commander,
            )

        self.changed.emit()

        self._upload_journal_to_edsm()
        self._upload_pending_to_inara()
        self._request_edsm_for_current_system()
        return True

    def _apply_live_cargo_snapshot(self, data, current_session):
        """Bind Cargo.json only to the uniquely identified live journal FID."""
        identified = (
            current_session
            and current_session.get("attribution_status") == "identified"
            and current_session.get("commander_id") is not None
            and str(current_session.get("fid_seen") or "").strip()
            == str(self.commander_fid or "").strip()
        )
        if not identified:
            if self.cargo_snapshot is not None:
                self.cargo_snapshot = None
                self.cargoSnapshotChanged.emit(None)
            return
        current_loadout = self.ship_loadout or ShipLoadoutData()
        if (
            isinstance(self.cargo_snapshot, dict)
            and self.cargo_snapshot.get("vessel") == "Ship"
            and self.cargo_snapshot.get("ship_id") is not None
            and current_loadout.ship_id is not None
            and self.cargo_snapshot.get("ship_id") != current_loadout.ship_id
        ):
            self.cargo_snapshot = None
            self.cargoSnapshotChanged.emit(None)
        trigger = data.get("last_cargo_event") if identified else None
        if not isinstance(trigger, dict):
            return

        vessel = str(trigger.get("Vessel") or "").strip().casefold()
        if vessel not in ("ship", "srv"):
            return
        previous = self.cargo_snapshot
        if (
            isinstance(previous, dict)
            and previous.get("fid") == self.commander_fid
            and str(previous.get("vessel") or "").casefold() == vessel
            and previous.get("timestamp") == str(trigger.get("timestamp") or "")
            and previous.get("count") == trigger.get("Count")
        ):
            return

        loadout = current_loadout
        snapshot = read_cargo_snapshot(
            Path(self.journal_folder) / "Cargo.json",
            trigger,
            fid=self.commander_fid,
            ship_id=loadout.ship_id,
            cargo_capacity=loadout.cargo_capacity,
            srv_type=data.get("active_srv_type") or "",
            attempts=5,
            retry_delay=0.04,
        )
        if snapshot != previous:
            self.cargo_snapshot = snapshot
            self.cargoSnapshotChanged.emit(snapshot)

    @staticmethod
    def _ship_loadout_signature(loadout):
        if loadout is None:
            return None
        return (
            loadout.ship_id,
            loadout.ship_type,
            loadout.ship_name,
            loadout.ship_ident,
            loadout.unladen_mass,
            loadout.cargo_capacity,
            loadout.max_jump_range,
            loadout.main_tank_capacity,
            loadout.reserve_tank_capacity,
            loadout.fsd_item,
            loadout.fsd_on,
            loadout.fsd_blueprint,
            loadout.fsd_engineering_level,
            loadout.fsd_engineering_quality,
            loadout.fsd_experimental_effect,
            loadout.fsd_engineering_modifiers,
            loadout.fsd_optimal_mass,
            loadout.fsd_max_fuel_per_jump,
            loadout.guardian_fsd_boosters,
            loadout.modules,
            loadout.loadout_timestamp,
            loadout.loadout_complete,
            loadout.loadout_stale,
        )

    @staticmethod
    def _ship_route_inputs_signature(loadout):
        if loadout is None:
            return None
        return (
            loadout.cargo,
            loadout.main_fuel,
            loadout.reserve_fuel,
        )
