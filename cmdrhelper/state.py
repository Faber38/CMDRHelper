from __future__ import annotations

from pathlib import Path
import logging
import threading
from datetime import datetime, timezone

from PySide6.QtCore import QObject, QSettings, Signal

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
from cmdrhelper.bio_valuation import biology_totals
from cmdrhelper.route_planner.models import ShipLoadoutData

logger = logging.getLogger(__name__)


class AppState(QObject):
    changed = Signal()
    commanderIdentityChanged = Signal(object, str, str)
    positionChanged = Signal(str, object, str)
    shipLoadoutChanged = Signal(object)
    shipRouteInputsChanged = Signal(object)
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
        self._database_import_manual_waiting = False
        self._database_import_last_progress = None

        self.commander = ""
        self.commander_id = None
        self.commander_fid = ""
        self.system = ""
        self.system_address = None
        self.body = ""
        self.station = ""
        self.ship = ""
        self.ship_loadout = ShipLoadoutData()
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

        self.edsm_uploader = EDSMJournalUploader(
            self.edsm_commander,
            self.edsm_api_key,
            settings=self.settings,
        )
        self._edsm_upload_running = False
        self.edsm_upload_status = (
            "disabled" if not self.edsm_enabled else "waiting"
        )
        self.edsm_upload_message = (
            "EDSM deaktiviert"
            if not self.edsm_enabled
            else "Warte auf Übertragung"
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
            self.watcher.start()
            self.watcher.check_now()
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
            ):
                self.databaseImportProgress.emit(
                    current,
                    total,
                    name,
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
        self.watcher.start()
        self.watcher.check_now()
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

        self.edsm_uploader.update_credentials(
            self.edsm_commander,
            self.edsm_api_key,
        )

        if not self.edsm_enabled:
            self.edsm_upload_status = "disabled"
            self.edsm_upload_message = "EDSM deaktiviert"
        elif self.edsm_upload_status == "disabled":
            self.edsm_upload_status = "waiting"
            self.edsm_upload_message = "Warte auf Übertragung"

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

    def _upload_journal_to_edsm(self):
        if (
            not self.edsm_enabled
            or not self.journal_folder
            or self._edsm_upload_running
        ):
            return

        self._edsm_upload_running = True
        folder = Path(self.journal_folder)

        def worker():
            try:
                result = self.edsm_uploader.process_folder(folder)

                if result.get("initialized"):
                    logger.info(
                        "EDSM-Uploader initialisiert; vorhandene "
                        "Journaldaten werden nicht erneut übertragen."
                    )

                error = result.get("error") or ""
                if error:
                    self.edsm_upload_status = "error"
                    self.edsm_upload_message = str(error)
                    logger.warning(
                        "EDSM-Upload pausiert: %s",
                        error,
                    )
                else:
                    sent = int(result.get("sent") or 0)
                    discarded = int(result.get("discarded") or 0)

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
                self.edsm_upload_status = "error"
                self.edsm_upload_message = str(exc)
                logger.exception("EDSM-Upload fehlgeschlagen")
            finally:
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

    def _apply_commander_identity(self, data):
        """Übernimmt ausschließlich eine durch FID belegte Journalidentität."""
        fid = str(data.get("commander_fid") or "").strip()
        if not fid:
            return

        name = str(
            data.get("commander_identity_name") or data.get("commander") or ""
        ).strip()
        commander_id = self.database.upsert_commander(
            fid,
            name,
            data.get("commander_identity_timestamp") or "",
        )
        if commander_id is None:
            return

        previous_fid = self.commander_fid
        self.commander_id = commander_id
        self.commander_fid = fid

        if previous_fid != fid:
            self.commanderIdentityChanged.emit(commander_id, fid, name)

    def refresh(self):
        if not self.journal_folder:
            self.connected = False
            self.changed.emit()
            return True

        try:
            data = read_latest_state(
                self.journal_folder,
                mission_reset_at=self.mission_reset_at,
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

        self.commander = data["commander"]
        self._apply_commander_identity(data)
        self.system = data["system"]
        self.system_address = data.get("system_address")
        self.body = data["body"]
        self.station = data["station"]
        self.ship = data["ship"]
        self.ship_loadout = data.get("ship_loadout") or ShipLoadoutData()
        self.last_timestamp = data["last_timestamp"]
        self.journal_files = data["journal_files"]

        if self._ship_loadout_signature(previous_loadout) != self._ship_loadout_signature(
            self.ship_loadout
        ):
            self.shipLoadoutChanged.emit(self.ship_loadout)

        if self._ship_route_inputs_signature(
            previous_loadout
        ) != self._ship_route_inputs_signature(self.ship_loadout):
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
        except Exception:
            logger.exception("Live-Snapshot konnte nicht gespeichert werden")

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
            bio_entries = self.database.biology_for_system(
                self.system_address
            )
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

        raw_unsold_cartography = int(
            data.get("unsold_cartography_value", 0)
            or 0
        )

        try:
            unsold_cartography_factor = self.database.learned_cartography_factor()
        except Exception:
            unsold_cartography_factor = 1.0

        self.unsold_cartography_value = int(
            round(
                raw_unsold_cartography
                * float(unsold_cartography_factor or 1.0)
            )
        )
        self.unsold_cartography_count = int(
            data.get("unsold_cartography_count", 0)
            or 0
        )

        try:
            unsold_bio_totals = biology_totals(
                data.get("unsold_biology", []),
                learned_values=self.database.learned_bio_values(),
            )
        except Exception:
            logger.exception("Offene BIO-Werte konnten nicht berechnet werden")
            unsold_bio_totals = {
                "completed_count": 0, "base_total": 0,
                "first_logged_total": 0, "unknown": [],
            }

        self.unsold_bio_count = int(unsold_bio_totals["completed_count"])
        self.unsold_bio_value = int(unsold_bio_totals["base_total"])
        self.unsold_bio_first_logged_value = int(unsold_bio_totals["first_logged_total"])
        self.unsold_bio_unknown = list(unsold_bio_totals["unknown"])

        self.connected = (
            self.journal_files > 0
        )

        self._load_edsm_cache_for_current_system()

        self.changed.emit()

        self._upload_journal_to_edsm()
        self._request_edsm_for_current_system()
        return True

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
