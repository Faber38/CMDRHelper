from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PySide6.QtCore import QSettings

from cmdrhelper.journal_files import journal_files
from cmdrhelper.journal_reader import classify_journal_file
from cmdrhelper.version import __version__
from cmdrhelper.logging_config import log_event


logger = logging.getLogger(__name__)

EDSM_JOURNAL_URL = "https://www.edsm.net/api-journal-v1"
EDSM_DISCARD_URL = "https://www.edsm.net/api-journal-v1/discard"

# Kleine Batches halten Requests überschaubar und erleichtern Wiederholungen.
BATCH_SIZE = 50

# EDSM: 1xx = erfolgreich / bereits vorhanden / Duplikat.
# 5xx wird von der Journal-API ebenfalls als angenommen/gespeichert behandelt.
SUCCESS_CLASSES = (1, 5)


def _read_json_response(response):
    raw = response.read().decode("utf-8", errors="replace")
    if not raw.strip():
        raise ValueError("EDSM hat keine Daten zurückgegeben.")
    return json.loads(raw)


def fetch_discarded_events(timeout: int = 15) -> tuple[bool, set[str], str]:
    request = Request(
        EDSM_DISCARD_URL,
        headers={
            "User-Agent": f"CMDRHelper/{__version__}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            data = _read_json_response(response)
    except HTTPError as exc:
        return False, set(), f"EDSM HTTP-Fehler {exc.code}."
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return False, set(), f"EDSM nicht erreichbar: {reason}"
    except TimeoutError:
        return False, set(), "Zeitüberschreitung bei EDSM."
    except Exception as exc:
        return False, set(), f"Discard-Liste konnte nicht geladen werden: {exc}"

    if not isinstance(data, list):
        return False, set(), "EDSM lieferte eine unerwartete Discard-Liste."

    discarded = {str(item) for item in data if item}
    logger.info("EDSM Discard-Liste geladen: %s Eventtyp(en)", len(discarded))
    return True, discarded, ""


def _journal_header(journal: Path) -> tuple[str, str]:
    try:
        with journal.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if isinstance(event, dict) and event.get("event") == "Fileheader":
                    return (
                        str(event.get("gameversion") or ""),
                        str(event.get("build") or ""),
                    )
    except OSError:
        pass

    return "", ""


def _encode_post_data(
    commander: str,
    api_key: str,
    game_version: str,
    game_build: str,
    events: list[dict],
) -> bytes:
    payload = {
        "commanderName": commander,
        "apiKey": api_key,
        "fromSoftware": "CMDRHelper",
        "fromSoftwareVersion": __version__,
        "fromGameVersion": game_version,
        "fromGameBuild": game_build,
        "message": json.dumps(
            events,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    return urlencode(payload).encode("utf-8")


def _log_upload_response(http_status, prepared, ok, reply, *, transport_error=False):
    """Diagnostics only: never infer individual acknowledgements from HTTP success.

    Missing, malformed or differently sized event replies cannot establish a count.
    Count all explicit acknowledgements, not just the resumable consecutive prefix.
    """
    code = reply.get("msgnum") if isinstance(reply, dict) else None
    replies = reply.get("events") if isinstance(reply, dict) else None
    confirmed = "unknown"
    if (type(code) is int and code // 100 in SUCCESS_CLASSES
            and isinstance(replies, list) and len(replies) == prepared
            and all(isinstance(item, dict) and type(item.get("msgnum")) is int
                    and 100 <= item["msgnum"] <= 599 for item in replies)):
        confirmed = sum(item["msgnum"] // 100 in SUCCESS_CLASSES for item in replies)
    check = "transport_error" if transport_error else "accepted" if ok else "rejected"
    if not transport_error and not ok:
        if type(confirmed) is int and confirmed > 0:
            check = "partial"
        elif type(code) is not int or not 100 <= code <= 599:
            check = "unknown"
    log_event(logger, "EDSM upload response checked", http_status=http_status,
              edsm_code=code if type(code) is int and 100 <= code <= 599 else "unknown",
              prepared_events=prepared, confirmed_events=confirmed, response_check=check)


def upload_events(
    commander: str,
    api_key: str,
    game_version: str,
    game_build: str,
    events: list[dict],
    timeout: int = 20,
) -> tuple[bool, dict | None, str]:
    commander = (commander or "").strip()
    api_key = (api_key or "").strip()
    game_version = (game_version or "").strip()
    game_build = (game_build or "").strip()

    if not commander:
        return False, None, "Commander-Name fehlt."
    if not api_key:
        return False, None, "EDSM API-Schlüssel fehlt."
    if not game_version:
        return False, None, "Elite-Spielversion fehlt."
    if not game_build:
        return False, None, "Elite-Build fehlt."
    if not events:
        return True, {"msgnum": 100, "msg": "Nothing to send"}, ""

    request = Request(
        EDSM_JOURNAL_URL,
        data=_encode_post_data(
            commander,
            api_key,
            game_version,
            game_build,
            events,
        ),
        headers={
            "User-Agent": f"CMDRHelper/{__version__}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )

    http_status = "unknown"

    def finish(ok, reply, error, *, transport_error=False):
        _log_upload_response(http_status, len(events), ok, reply, transport_error=transport_error)
        return ok, reply, error

    try:
        with urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if type(status) is int and 100 <= status <= 599:
                http_status = status
            reply = _read_json_response(response)
    except HTTPError as exc:
        http_status = exc.code
        delay = 120.0
        value = (exc.headers or {}).get("Retry-After", "")
        try:
            delay = max(delay, float(value))
        except (TypeError, ValueError):
            try:
                delay = max(delay, (parsedate_to_datetime(value)
                                   - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                pass
        return finish(False, {"retry_after_seconds": delay}, f"EDSM HTTP-Fehler {exc.code}.", transport_error=True)
    except URLError as exc:
        return finish(False, None, "EDSM nicht erreichbar.", transport_error=True)
    except TimeoutError:
        return finish(False, None, "Zeitüberschreitung beim EDSM-Upload.", transport_error=True)
    except Exception as exc:
        return finish(False, None, "EDSM-Upload fehlgeschlagen.")

    if not isinstance(reply, dict):
        return finish(False, None, "EDSM lieferte eine unerwartete Antwort.")

    try:
        msgnum = int(reply.get("msgnum"))
    except (TypeError, ValueError):
        msgnum = 0

    if msgnum and (msgnum // 100) in SUCCESS_CLASSES:
        replies = reply.get("events")
        if replies is not None:
            try:
                accepted = (isinstance(replies, list) and len(replies) == len(events)
                            and all(int(item.get("msgnum", 0)) // 100 in SUCCESS_CLASSES
                                    for item in replies))
            except (TypeError, ValueError, AttributeError):
                accepted = False
            if not accepted:
                return finish(False, reply, "EDSM hat nicht alle Ereignisse bestätigt.")
        return finish(True, reply, "")

    return finish(
        False,
        reply,
        f"EDSM: Upload abgelehnt (Code {msgnum})",
    )


class EDSMJournalUploader:
    """
    Inkrementeller EDSM-Journal-Uploader.

    - merkt Byte-Position pro Journaldatei in QSettings
    - lädt EDSM-Discard-Liste dynamisch
    - sendet nur neue, von EDSM gewünschte Events
    - setzt die Position erst nach erfolgreichem Batch weiter
    - bei erster Aktivierung werden vorhandene Journale auf EOF markiert,
      damit nicht versehentlich das gesamte Archiv erneut hochgeladen wird
    """

    _locks = {}
    _retry_after = {}
    _discard_cache = {}

    def __init__(
        self,
        commander: str,
        api_key: str,
        settings: QSettings | None = None,
        fid: str = "",
        is_current=None,
        source_id: str = "",
        legacy_folder=None,
        source_folders=(),
    ):
        self.commander = (commander or "").strip()
        self.api_key = (api_key or "").strip()
        self.settings = settings or QSettings("CMDRHelper", "CMDRHelper")
        self.fid = str(fid or "").strip()
        self.is_current = is_current
        self.source_id = source_id
        self.legacy_folder = Path(legacy_folder) if legacy_folder else None
        self.source_folders = tuple(Path(p) for p in source_folders)

        self._identity = (self.settings.fileName(), self.fid)
        self._retry_delay = 120.0
        self._lock = self._locks.setdefault(self._identity, threading.Lock())
        self._discarded: set[str] | None = self._discard_cache.get(self._identity)
        upload_prefix = (
            f"edsm_upload/commanders/{self.fid}"
            if self.fid else "edsm_upload"
        )
        self._legacy_upload_prefix = upload_prefix
        if source_id:
            upload_prefix += f"/sources/{source_id}"
        self._upload_prefix = upload_prefix
        self._initialized_key = f"{upload_prefix}/initialized"

    def update_credentials(self, commander: str, api_key: str):
        self.commander = (commander or "").strip()
        self.api_key = (api_key or "").strip()

    @staticmethod
    def _safe_key(path: Path) -> str:
        # QSettings-Gruppen vertragen Dateinamen besser als komplette Pfade.
        return path.name.replace("/", "_").replace("\\", "_")

    def _position_key(self, journal: Path) -> str:
        if self.source_id:
            import hashlib
            # Canonical full path distinguishes file aliases as well as names.
            key = hashlib.sha256(str(journal.resolve()).encode()).hexdigest()
            return f"{self._upload_prefix}/positions/{key}"
        return f"{self._upload_prefix}/positions/{self._safe_key(journal)}"

    def _still_current(self) -> bool:
        return self.is_current is None or bool(self.is_current())

    def _stored_position(self, journal: Path) -> int:
        try:
            return int(self.settings.value(self._position_key(journal), 0) or 0)
        except (TypeError, ValueError):
            return 0

    def _set_position(self, journal: Path, position: int):
        self.settings.setValue(
            self._position_key(journal),
            int(position),
        )

    def _is_initialized(self) -> bool:
        return str(
            self.settings.value(self._initialized_key, "false")
        ).lower() in ("1", "true", "yes", "on")

    def _belongs_to_commander(self, journal):
        if not self.fid:
            return False
        try:
            identity = classify_journal_file(journal)
        except (OSError, AttributeError, TypeError):
            return False
        return (identity["attribution_status"] == "identified"
                and identity["fid_seen"] == self.fid)

    def _baseline_existing_files(self, folder: Path) -> int:
        count = 0

        for journal in journal_files(folder):
            if not self._belongs_to_commander(journal):
                continue
            if self.settings.contains(self._position_key(journal)):
                continue
            try:
                size = int(journal.stat().st_size)
            except OSError:
                continue

            if self.source_id:
                suffix = '/positions/' + self._position_key(journal).rsplit('/', 1)[1]
                previous = {int(self.settings.value(key, 0)) for key in self.settings.allKeys()
                    if key.startswith(self._legacy_upload_prefix + '/sources/') and key.endswith(suffix)}
                if previous:
                    # Re-adding a removed source must retain its pending tail.
                    # Full canonical path keys provide unambiguous provenance.
                    if len(previous) != 1 or not 0 <= next(iter(previous)) <= size:
                        raise ValueError('edsm_source_position_conflict')
                    self._set_position(journal, next(iter(previous)))
                    count += 1
                    continue
                legacy_key = f"{self._legacy_upload_prefix}/positions/{self._safe_key(journal)}"
                if self.settings.contains(legacy_key):
                    matches = {str((p / journal.name).resolve()) for p in self.source_folders
                               if (p / journal.name).is_file() and self._belongs_to_commander(p / journal.name)}
                    if ((self.legacy_folder is not None and folder.resolve() != self.legacy_folder.resolve())
                            or matches != {str(journal.resolve())}):
                        raise ValueError('edsm_legacy_position_ambiguous')
                    position = int(self.settings.value(legacy_key, 0))
                    if position < 0 or position > size:
                        raise ValueError('edsm_legacy_position_invalid')
                    self._set_position(journal, position)
                else:
                    from .journal_index import _complete_line_offset
                    self._set_position(journal, _complete_line_offset(journal))
            else:
                self._set_position(journal, size)
            count += 1

        self.settings.setValue(self._initialized_key, True)
        self.settings.sync()

        logger.info(
            "EDSM Upload initialisiert: %s vorhandene Journaldatei(en) "
            "als bereits verarbeitet markiert",
            count,
        )
        return count

    def _ensure_discard_list(self) -> tuple[bool, str]:
        if self._discarded is not None:
            return True, ""

        ok, discarded, error = fetch_discarded_events()

        if not ok:
            return False, error

        self._discarded = discarded
        self._discard_cache[self._identity] = discarded
        return True, ""

    def process_folder(self, folder: Path) -> dict:
        folder = Path(folder)
        if self.source_id:
            import hashlib
            folder_key = hashlib.sha256(str(folder.resolve()).encode()).hexdigest()
            self._initialized_key = f"{self._upload_prefix}/initialized/{folder_key}"

        result = {
            "initialized": False,
            "files": 0,
            "events_sent": 0,
            "events_skipped": 0,
            "error": "",
        }

        if not self.fid or not self.commander or not self.api_key:
            result["error"] = "EDSM-Zugangsdaten fehlen."
            return result

        if not self._still_current():
            result["cancelled"] = True
            return result

        if not folder.exists():
            result["error"] = f"Journalordner nicht gefunden: {folder}"
            return result

        # Verhindert parallele Uploads bei schnellen JournalChanged-Signalen.
        if not self._lock.acquire(blocking=False):
            return result

        try:
            if time.monotonic() < self._retry_after.get(self._identity, 0):
                result["retry_paused"] = True
                result["error"] = "EDSM-Wiederholung pausiert (Netzwerk/Rate-Limit)."
                return result
            if not self._is_initialized():
                self._baseline_existing_files(folder)
                result["initialized"] = True
                return result

            ok, error = self._ensure_discard_list()
            if not ok:
                result["error"] = error
                logger.warning("EDSM Upload pausiert: %s", error)
                return result

            for journal in journal_files(folder):
                if not self._still_current():
                    result["cancelled"] = True
                    break
                if not self._belongs_to_commander(journal):
                    continue
                try:
                    file_size = int(journal.stat().st_size)
                except OSError:
                    continue

                position = self._stored_position(journal)

                # Never reset confirmed progress for a replaced/truncated file.
                if position > file_size:
                    result["error"] = f"Journaldatei gekürzt: {journal.name}"
                    break

                if position == file_size:
                    continue

                sent, skipped, error = self._process_journal(
                    journal,
                    position,
                )

                log_event(logger, "EDSM journal processing finished",
                          skipped_events=skipped,
                          position_advanced=self._stored_position(journal) > position,
                          success=not bool(error))

                result["files"] += 1
                result["events_sent"] += sent
                result["events_skipped"] += skipped

                if error:
                    result["error"] = error
                    break

            if result["events_sent"]:
                logger.info(
                    "EDSM Uploadlauf: %s Event(s) gesendet, %s verworfen",
                    result["events_sent"],
                    result["events_skipped"],
                )
            elif result["events_skipped"]:
                logger.debug(
                    "EDSM Uploadlauf: 0 Event(s) gesendet, %s verworfen",
                    result["events_skipped"],
                )

            return result

        finally:
            if result["error"] and not result.get("retry_paused"):
                self._retry_after[self._identity] = time.monotonic() + self._retry_delay
            self.settings.sync()
            self._lock.release()

    def _confirm_prefix(self, journal, positions, reply):
        """Retain consecutive individual confirmations in a partially rejected batch."""
        if isinstance(reply, dict):
            self._retry_delay = max(120.0, float(reply.get("retry_after_seconds", 120)))
        if not isinstance(reply, dict) or not isinstance(reply.get("events"), list):
            return 0
        if len(reply["events"]) != len(positions):
            return 0
        count = 0
        for position, event_reply in zip(positions, reply["events"]):
            try:
                accepted = int(event_reply.get("msgnum", 0)) // 100 in SUCCESS_CLASSES
            except (AttributeError, TypeError, ValueError):
                break
            if not accepted:
                break
            self._set_position(journal, position)
            count += 1
        return count

    def _process_journal(
        self,
        journal: Path,
        start_position: int,
    ) -> tuple[int, int, str]:
        game_version, game_build = _journal_header(journal)

        if not game_version or not game_build:
            error = (
                f"Spielversion/Build fehlen in {journal.name}"
            )
            logger.warning("EDSM: %s", error)
            return 0, 0, error

        sent_count = 0
        skipped_count = 0
        batch_events: list[dict] = []
        batch_positions: list[int] = []
        batch_end_position = start_position

        try:
            handle = journal.open("rb")
        except OSError as exc:
            return 0, 0, f"{journal.name} kann nicht gelesen werden: {exc}"

        with handle:
            handle.seek(start_position)

            while True:
                line_start = handle.tell()
                raw = handle.readline()

                if not raw:
                    break

                line_end = handle.tell()

                # Unvollständige letzte Zeile noch nicht als verarbeitet markieren.
                if not raw.endswith(b"\n"):
                    handle.seek(line_start)
                    break

                try:
                    text = raw.decode("utf-8", errors="replace").strip()
                    event = json.loads(text)
                    if not isinstance(event, dict):
                        raise ValueError("Journal event is not an object")
                except (json.JSONDecodeError, ValueError):
                    # Defekte vollständige Zeile überspringen, damit der Upload
                    # nicht dauerhaft an derselben Stelle hängen bleibt.
                    batch_end_position = line_end
                    if not batch_events:
                        self._set_position(journal, line_end)
                    skipped_count += 1
                    logger.warning(
                        "EDSM: ungültige JSON-Zeile übersprungen in %s bei Byte %s",
                        journal.name,
                        line_start,
                    )
                    continue

                event_name = str(event.get("event") or "")

                if not event_name or event_name in (self._discarded or set()):
                    batch_end_position = line_end
                    if not batch_events:
                        self._set_position(journal, line_end)
                    skipped_count += 1
                    continue

                batch_events.append(event)
                batch_positions.append(line_end)
                batch_end_position = line_end

                if len(batch_events) >= BATCH_SIZE:
                    if not self._still_current():
                        return sent_count, skipped_count, "__cancelled__"
                    ok, _reply, error = upload_events(
                        self.commander,
                        self.api_key,
                        game_version,
                        game_build,
                        batch_events,
                    )

                    if not ok:
                        sent_count += self._confirm_prefix(journal, batch_positions, _reply)
                        logger.warning(
                            "EDSM Batch fehlgeschlagen in %s: %s",
                            journal.name,
                            error,
                        )
                        return sent_count, skipped_count, error

                    self._set_position(journal, batch_end_position)
                    sent_count += len(batch_events)
                    logger.info(
                        "EDSM: %s Event(s) aus %s übertragen",
                        len(batch_events),
                        journal.name,
                    )
                    batch_events = []
                    batch_positions = []

            if batch_events:
                if not self._still_current():
                    return sent_count, skipped_count, "__cancelled__"
                ok, _reply, error = upload_events(
                    self.commander,
                    self.api_key,
                    game_version,
                    game_build,
                    batch_events,
                )

                if not ok:
                    sent_count += self._confirm_prefix(journal, batch_positions, _reply)
                    logger.warning(
                        "EDSM Rest-Batch fehlgeschlagen in %s: %s",
                        journal.name,
                        error,
                    )
                    return sent_count, skipped_count, error

                self._set_position(journal, batch_end_position)
                sent_count += len(batch_events)

                logger.info(
                    "EDSM: %s Event(s) aus %s übertragen",
                    len(batch_events),
                    journal.name,
                )

        self.settings.sync()
        return sent_count, skipped_count, ""
