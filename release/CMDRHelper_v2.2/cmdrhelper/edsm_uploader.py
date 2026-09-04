from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PySide6.QtCore import QSettings

from cmdrhelper.journal_files import journal_files
from cmdrhelper.version import __version__


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

                if event.get("event") == "Fileheader":
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

    try:
        with urlopen(request, timeout=timeout) as response:
            reply = _read_json_response(response)
    except HTTPError as exc:
        return False, None, f"EDSM HTTP-Fehler {exc.code}."
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return False, None, f"EDSM nicht erreichbar: {reason}"
    except TimeoutError:
        return False, None, "Zeitüberschreitung beim EDSM-Upload."
    except Exception as exc:
        return False, None, f"EDSM-Upload fehlgeschlagen: {exc}"

    if not isinstance(reply, dict):
        return False, None, "EDSM lieferte eine unerwartete Antwort."

    try:
        msgnum = int(reply.get("msgnum"))
    except (TypeError, ValueError):
        msgnum = 0

    if msgnum and (msgnum // 100) in SUCCESS_CLASSES:
        return True, reply, ""

    return (
        False,
        reply,
        f"EDSM: {reply.get('msg') or 'Upload abgelehnt'} (Code {msgnum})",
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

    def __init__(
        self,
        commander: str,
        api_key: str,
        settings: QSettings | None = None,
        fid: str = "",
        is_current=None,
    ):
        self.commander = (commander or "").strip()
        self.api_key = (api_key or "").strip()
        self.settings = settings or QSettings("CMDRHelper", "CMDRHelper")
        self.fid = str(fid or "").strip()
        self.is_current = is_current

        self._lock = threading.Lock()
        self._discarded: set[str] | None = None
        upload_prefix = (
            f"edsm_upload/commanders/{self.fid}"
            if self.fid else "edsm_upload"
        )
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

    def _baseline_existing_files(self, folder: Path) -> int:
        count = 0

        for journal in journal_files(folder):
            try:
                size = int(journal.stat().st_size)
            except OSError:
                continue

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
        return True, ""

    def process_folder(self, folder: Path) -> dict:
        folder = Path(folder)

        result = {
            "initialized": False,
            "files": 0,
            "events_sent": 0,
            "events_skipped": 0,
            "error": "",
        }

        if not self.commander or not self.api_key:
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
                try:
                    file_size = int(journal.stat().st_size)
                except OSError:
                    continue

                position = self._stored_position(journal)

                # Datei wurde ersetzt/gekürzt.
                if position > file_size:
                    logger.warning(
                        "EDSM Journalposition größer als Datei; setze zurück: %s",
                        journal.name,
                    )
                    position = 0

                if position == file_size:
                    continue

                sent, skipped, error = self._process_journal(
                    journal,
                    position,
                )

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
            self._lock.release()

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
                except json.JSONDecodeError:
                    # Defekte vollständige Zeile überspringen, damit der Upload
                    # nicht dauerhaft an derselben Stelle hängen bleibt.
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
                    self._set_position(journal, line_end)
                    skipped_count += 1
                    continue

                batch_events.append(event)
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
