from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from cmdrhelper.version import __version__


GITHUB_OWNER = "Faber38"
GITHUB_REPO = "CMDRHelper"

LATEST_RELEASE_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)

# Diese Pfade gehören dem Benutzer bzw. der lokalen Installation und
# dürfen bei einem Update weder überschrieben noch beim Rollback gelöscht
# werden.
PROTECTED_NAMES = {
    "data",
    "backup",
    "release",
    "build",
    ".git",
    ".github",
    ".venv",
    "venv",
}

PROTECTED_SUFFIXES = {
    ".db",
    ".db-wal",
    ".db-shm",
}


def _log_update(
    install_dir: Path,
    message: str,
) -> None:
    """Schreibt eine dauerhafte Diagnose des Update-Ablaufs."""
    try:
        log_dir = install_dir / "backup"
        log_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        log_path = log_dir / "update.log"

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        with log_path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                f"[{timestamp}] {message}\n"
            )
    except Exception:
        pass


def _version_tuple(value: str) -> tuple[int, ...]:
    raw = str(value or "").strip()

    if raw.lower().startswith("v"):
        raw = raw[1:]

    parts = []

    for part in raw.split("."):
        digits = ""

        for char in part:
            if char.isdigit():
                digits += char
            else:
                break

        parts.append(
            int(digits)
            if digits
            else 0
        )

    return tuple(parts or [0])


def is_newer_version(
    candidate: str,
    current: str,
) -> bool:
    candidate_tuple = _version_tuple(
        candidate
    )
    current_tuple = _version_tuple(
        current
    )

    length = max(
        len(candidate_tuple),
        len(current_tuple),
    )

    candidate_tuple += (
        0,
    ) * (length - len(candidate_tuple))

    current_tuple += (
        0,
    ) * (length - len(current_tuple))

    return candidate_tuple > current_tuple


def _request(
    url: str,
    current_version: str = __version__,
) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"CMDRHelper/{current_version}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )


def check_latest_release(
    owner: str = GITHUB_OWNER,
    repository: str = GITHUB_REPO,
    current_version: str = __version__,
    timeout: float = 6.0,
) -> dict:
    url = (
        "https://api.github.com/repos/"
        f"{owner}/{repository}/releases/latest"
    )

    try:
        with urllib.request.urlopen(
            _request(url, current_version),
            timeout=timeout,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {
                "ok": False,
                "error": "Noch kein GitHub-Release gefunden.",
                "status": 404,
            }

        return {
            "ok": False,
            "error": f"GitHub HTTP-Fehler {exc.code}.",
            "status": exc.code,
        }

    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)

        return {
            "ok": False,
            "error": f"GitHub nicht erreichbar: {reason}",
        }

    except TimeoutError:
        return {
            "ok": False,
            "error": (
                "Zeitüberschreitung bei der "
                "GitHub-Updateprüfung."
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": f"Updateprüfung fehlgeschlagen: {exc}",
        }

    tag = str(
        payload.get("tag_name")
        or ""
    ).strip()

    version = (
        tag[1:]
        if tag.lower().startswith("v")
        else tag
    )

    expected_asset = (
        f"CMDRHelper_v{version}.zip"
    )

    assets = []
    asset_name = ""
    asset_url = ""
    asset_size = 0

    for asset in payload.get("assets") or []:
        if not isinstance(asset, dict):
            continue

        name = str(
            asset.get("name")
            or ""
        ).strip()

        url_value = str(
            asset.get("browser_download_url")
            or ""
        ).strip()

        size_value = int(
            asset.get("size")
            or 0
        )

        assets.append(
            {
                "name": name,
                "url": url_value,
                "size": size_value,
            }
        )

        if name == expected_asset:
            asset_name = name
            asset_url = url_value
            asset_size = size_value

    # Fallback: genau ein passendes CMDRHelper-ZIP vorhanden.
    if not asset_url:
        zip_assets = [
            asset
            for asset in assets
            if asset["name"].lower().startswith(
                "cmdrhelper_"
            )
            and asset["name"].lower().endswith(
                ".zip"
            )
        ]

        if len(zip_assets) == 1:
            asset_name = zip_assets[0]["name"]
            asset_url = zip_assets[0]["url"]
            asset_size = zip_assets[0]["size"]

    return {
        "ok": True,
        "version": version,
        "tag": tag,
        "name": payload.get("name") or tag,
        "html_url": payload.get("html_url") or "",
        "published_at": payload.get("published_at") or "",
        "release_notes": payload.get("body") or "",
        "assets": assets,
        "asset_name": asset_name,
        "asset_url": asset_url,
        "asset_size": asset_size,
        "newer": is_newer_version(
            version,
            current_version,
        ),
    }


class UpdateCheckSignals(QObject):
    finished = Signal(object)


class UpdateCheckWorker(QRunnable):
    def __init__(
        self,
        owner: str,
        repository: str,
        current_version: str,
    ):
        super().__init__()

        self.owner = owner
        self.repository = repository
        self.current_version = current_version
        self.signals = UpdateCheckSignals()

        # MainWindow hält den Worker bis zum finished-Signal.
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        result = check_latest_release(
            self.owner,
            self.repository,
            self.current_version,
        )

        self.signals.finished.emit(
            result
        )


def _is_protected(
    relative_path: Path,
) -> bool:
    if not relative_path.parts:
        return True

    first = relative_path.parts[0]

    if first in PROTECTED_NAMES:
        return True

    if relative_path.suffix.lower() in PROTECTED_SUFFIXES:
        return True

    return False


def _backup_managed_files(
    install_dir: Path,
    backup_dir: Path,
) -> None:
    backup_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    for source in install_dir.iterdir():
        relative = Path(
            source.name
        )

        if _is_protected(relative):
            continue

        destination = (
            backup_dir
            / source.name
        )

        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                ),
            )
        else:
            shutil.copy2(
                source,
                destination,
            )


def _copy_release(
    source_root: Path,
    install_dir: Path,
) -> None:
    for source in source_root.rglob("*"):
        relative = source.relative_to(
            source_root
        )

        if _is_protected(relative):
            continue

        destination = (
            install_dir
            / relative
        )

        if source.is_dir():
            destination.mkdir(
                parents=True,
                exist_ok=True,
            )
        else:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                source,
                destination,
            )


def _restore_backup(
    backup_dir: Path,
    install_dir: Path,
) -> None:
    """
    Stellt die gesicherte Programmversion durch Überschreiben wieder her.

    Auch beim Rollback werden vorhandene Dateien nicht pauschal gelöscht.
    Dadurch bleiben data/, Entwicklerdateien und andere lokale Dateien
    unangetastet.
    """
    for source in backup_dir.iterdir():
        destination = (
            install_dir
            / source.name
        )

        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True,
            )
        else:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            shutil.copy2(
                source,
                destination,
            )


def _extract_release_root(
    zip_path: Path,
    temp_dir: Path,
) -> Path:
    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:
        archive.extractall(
            temp_dir
        )

    entries = [
        p
        for p in temp_dir.iterdir()
        if p.name != "__MACOSX"
    ]

    if (
        len(entries) == 1
        and entries[0].is_dir()
    ):
        return entries[0]

    return temp_dir


def download_release(
    info: dict,
    timeout: float = 120.0,
) -> Path:
    asset_url = str(
        info.get("asset_url")
        or ""
    ).strip()

    version = str(
        info.get("version")
        or ""
    ).strip()

    asset_name = str(
        info.get("asset_name")
        or ""
    ).strip()

    if not asset_url:
        raise RuntimeError(
            f"Im Release v{version} wurde kein "
            "CMDRHelper-ZIP gefunden."
        )

    temp_root = Path(
        tempfile.mkdtemp(
            prefix="cmdrhelper_update_"
        )
    )

    zip_path = (
        temp_root
        / (
            asset_name
            or f"CMDRHelper_v{version}.zip"
        )
    )

    request = urllib.request.Request(
        asset_url,
        headers={
            "User-Agent": (
                f"CMDRHelper/{__version__}"
            )
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=timeout,
    ) as response:
        with zip_path.open(
            "wb"
        ) as target:
            shutil.copyfileobj(
                response,
                target,
            )

    if not zipfile.is_zipfile(
        zip_path
    ):
        raise RuntimeError(
            "Die heruntergeladene Datei ist "
            "kein gültiges ZIP-Archiv."
        )

    return zip_path


def _spawn(
    args: list[str],
    *,
    cwd: Path,
) -> subprocess.Popen:
    kwargs = {
        "cwd": str(cwd),
    }

    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(
        args,
        **kwargs,
    )


def launch_installer(
    *,
    zip_path: Path,
    install_dir: Path,
    current_version: str,
    latest_version: str,
    parent_pid: int,
) -> None:
    # update.py liegt im Python-Paket cmdrhelper.
    # Deshalb nicht als einzelne Datei starten, sondern als Modul.
    # So bleibt der Projektordner im Python-Suchpfad und
    # "from cmdrhelper..." funktioniert auch im separaten Updater-Prozess.
    _spawn(
        [
            sys.executable,
            "-m",
            "cmdrhelper.update",
            "--apply",
            str(zip_path),
            "--install-dir",
            str(install_dir),
            "--current-version",
            current_version,
            "--latest-version",
            latest_version,
            "--parent-pid",
            str(parent_pid),
        ],
        cwd=install_dir,
    )


def _pid_exists(
    pid: int,
) -> bool:
    if pid <= 0:
        return False

    try:
        os.kill(
            pid,
            0,
        )
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        # Unter Windows kann os.kill(pid, 0) je nach Python/Prozessart
        # einen OSError liefern. Dann behandeln wir den Prozess als beendet.
        return False

    return True


def _wait_for_parent_exit(
    pid: int,
    timeout: float = 30.0,
) -> None:
    deadline = (
        time.monotonic()
        + timeout
    )

    while (
        _pid_exists(pid)
        and time.monotonic() < deadline
    ):
        time.sleep(0.25)

    if _pid_exists(pid):
        raise RuntimeError(
            "CMDRHelper wurde nicht rechtzeitig beendet. "
            "Update abgebrochen."
        )


def _ensure_script_permissions(
    install_dir: Path,
) -> None:
    if os.name == "nt":
        return

    for script_name in (
        "start.sh",
        "install.sh",
        "create_release.sh",
        "github.sh",
    ):
        script = (
            install_dir
            / script_name
        )

        if not script.exists():
            continue

        current_mode = (
            script.stat().st_mode
        )

        script.chmod(
            current_mode
            | 0o111
        )


def _restart_cmdrhelper(
    install_dir: Path,
) -> None:
    main_file = (
        install_dir
        / "main.py"
    )

    if not main_file.exists():
        raise RuntimeError(
            "main.py wurde nach dem Update nicht gefunden."
        )

    _spawn(
        [
            sys.executable,
            str(main_file),
        ],
        cwd=install_dir,
    )


def apply_update(
    *,
    zip_path: Path,
    install_dir: Path,
    current_version: str,
    latest_version: str,
    parent_pid: int,
) -> int:
    install_dir = install_dir.resolve()
    zip_path = zip_path.resolve()

    _log_update(
        install_dir,
        (
            "============================================================"
        )
    )
    _log_update(
        install_dir,
        (
            f"Update gestartet: {current_version} -> {latest_version}"
        )
    )
    _log_update(
        install_dir,
        f"Installationsordner: {install_dir}"
    )
    _log_update(
        install_dir,
        f"ZIP: {zip_path}"
    )
    _log_update(
        install_dir,
        f"Elternprozess PID: {parent_pid}"
    )

    try:
        _log_update(
            install_dir,
            "Warte auf das Beenden von CMDRHelper ..."
        )
        _wait_for_parent_exit(
            parent_pid
        )
        _log_update(
            install_dir,
            "CMDRHelper ist beendet."
        )
    except Exception as exc:
        _log_update(
            install_dir,
            f"ABBRUCH beim Warten auf Elternprozess: {exc}"
        )
        return 4

    backup_root = (
        install_dir
        / "backup"
    )

    backup_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    backup_dir = (
        backup_root
        / (
            f"CMDRHelper_v{current_version}_"
            f"{timestamp}"
        )
    )

    temp_extract = Path(
        tempfile.mkdtemp(
            prefix="cmdrhelper_extract_"
        )
    )

    backup_created = False

    try:
        _log_update(
            install_dir,
            f"Erstelle Backup: {backup_dir}"
        )

        _backup_managed_files(
            install_dir,
            backup_dir,
        )

        backup_created = True

        _log_update(
            install_dir,
            "Backup erfolgreich erstellt."
        )

        _log_update(
            install_dir,
            f"Entpacke Release nach: {temp_extract}"
        )

        release_root = _extract_release_root(
            zip_path,
            temp_extract,
        )

        _log_update(
            install_dir,
            f"Release-Wurzel: {release_root}"
        )

        if not (
            release_root
            / "main.py"
        ).exists():
            raise RuntimeError(
                "Release-ZIP enthält keine main.py."
            )

        if not (
            release_root
            / "cmdrhelper"
        ).is_dir():
            raise RuntimeError(
                "Release-ZIP enthält keinen "
                "cmdrhelper-Ordner."
            )

        _log_update(
            install_dir,
            "Release-Struktur ist gültig."
        )

        _log_update(
            install_dir,
            (
                "Kopiere neue Release-Dateien über die "
                "bestehende Installation ..."
            )
        )

        # WICHTIG:
        # Vor einem normalen Update werden keine vorhandenen Dateien
        # pauschal gelöscht. Dateien aus dem Release werden lediglich
        # ergänzt bzw. überschrieben. Dadurch bleiben lokale Dateien,
        # die nicht Bestandteil des Release-ZIPs sind, erhalten.
        _copy_release(
            release_root,
            install_dir,
        )

        _ensure_script_permissions(
            install_dir
        )

        _log_update(
            install_dir,
            "Neue Programmdateien wurden installiert."
        )

        _log_update(
            install_dir,
            "Starte CMDRHelper neu ..."
        )

        _restart_cmdrhelper(
            install_dir
        )

        _log_update(
            install_dir,
            "Update erfolgreich abgeschlossen."
        )

        return 0

    except Exception as exc:
        _log_update(
            install_dir,
            (
                f"UPDATE-FEHLER: "
                f"{type(exc).__name__}: {exc}"
            )
        )

        if backup_created:
            try:
                _log_update(
                    install_dir,
                    "Rollback wird gestartet ..."
                )

                _restore_backup(
                    backup_dir,
                    install_dir,
                )

                _ensure_script_permissions(
                    install_dir
                )

                _log_update(
                    install_dir,
                    "Rollback erfolgreich."
                )

            except Exception as rollback_exc:
                _log_update(
                    install_dir,
                    (
                        "ROLLBACK-FEHLER: "
                        f"{type(rollback_exc).__name__}: "
                        f"{rollback_exc}"
                    )
                )

                return 3

        try:
            _log_update(
                install_dir,
                "Starte die wiederhergestellte Version ..."
            )

            _restart_cmdrhelper(
                install_dir
            )

        except Exception as restart_exc:
            _log_update(
                install_dir,
                (
                    "Neustart nach Fehler ebenfalls "
                    f"fehlgeschlagen: {restart_exc}"
                )
            )

        return 2

    finally:
        shutil.rmtree(
            temp_extract,
            ignore_errors=True,
        )

        # Download-Verzeichnis erst ganz am Ende entfernen.
        shutil.rmtree(
            zip_path.parent,
            ignore_errors=True,
        )

        _log_update(
            install_dir,
            "Temporäre Update-Dateien wurden aufgeräumt."
        )



def _main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply"
    )
    parser.add_argument(
        "--install-dir"
    )
    parser.add_argument(
        "--current-version"
    )
    parser.add_argument(
        "--latest-version"
    )
    parser.add_argument(
        "--parent-pid",
        type=int,
        default=0,
    )

    args = parser.parse_args()

    if not args.apply:
        return 0

    return apply_update(
        zip_path=Path(args.apply),
        install_dir=Path(args.install_dir),
        current_version=str(
            args.current_version
        ),
        latest_version=str(
            args.latest_version
        ),
        parent_pid=int(
            args.parent_pid
        ),
    )


if __name__ == "__main__":
    raise SystemExit(
        _main()
    )
