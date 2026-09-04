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
from cmdrhelper.python_support import is_supported, supported_description


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

UPDATE_LOG_RELATIVE = Path("backup") / "update.log"
UPDATE_STATUS_RELATIVE = Path("backup") / "update_status.json"
UPDATE_REPAIR_RELATIVE = Path("backup") / "update_repair_required.json"


def _expected_venv_python(install_dir: Path) -> Path:
    relative = Path("venv/Scripts/python.exe") if os.name == "nt" else Path("venv/bin/python")
    return Path(install_dir) / relative


def _local_script_names() -> tuple[str, str]:
    return ("install.bat", "start.bat") if os.name == "nt" else ("install.sh", "start.sh")


def _require_local_venv_interpreter(
    install_dir: Path, executable: str | Path | None = None,
) -> Path:
    """Verhindert Updates über System-Python oder ein fremdes Projekt-venv."""
    expected = _expected_venv_python(Path(install_dir))
    install_root = Path(install_dir).resolve()
    venv_root = Path(install_dir) / "venv"
    install_script, start_script = _local_script_names()
    if venv_root.is_symlink() or (
        venv_root.exists() and venv_root.resolve().parent != install_root
    ):
        raise RuntimeError(
            "Update abgebrochen: Das lokale venv ist auf ein fremdes "
            "Verzeichnis verknüpft. Bitte die Installation manuell prüfen."
        )
    actual = Path(executable or sys.executable)
    normalized_expected = os.path.normcase(os.path.abspath(str(expected)))
    normalized_actual = os.path.normcase(os.path.abspath(str(actual)))
    # Unter Linux zeigen die python-Dateien verschiedener venvs häufig alle
    # auf denselben Systeminterpreter. samefile() wäre dort kein Herkunftsnachweis.
    same_interpreter = normalized_actual == normalized_expected
    if os.name != "nt" and not same_interpreter:
        actual_path = Path(normalized_actual)
        expected_path = Path(normalized_expected)
        same_interpreter = (
            actual_path.parent == expected_path.parent
            and actual_path.name in {
                "python", "python3",
                f"python{sys.version_info.major}.{sys.version_info.minor}",
            }
        )
    if os.name == "nt" and not same_interpreter:
        try:
            same_interpreter = os.path.samefile(actual, expected)
        except OSError:
            pass
    if not same_interpreter:
        raise RuntimeError(
            "Update abgebrochen: CMDRHelper läuft nicht mit dem lokalen venv. "
            f"Erwartet: {expected}; verwendet: {actual}. Bitte {install_script} "
            f"zur Reparatur und anschließend {start_script} dieser Installation verwenden."
        )
    if not expected.exists() or not is_supported():
        raise RuntimeError(
            "Das lokale CMDRHelper-venv fehlt oder verwendet eine nicht "
            f"unterstützte Python-Version ({supported_description()}). "
            f"Bitte {install_script} ausführen."
        )
    return expected


def _write_update_state(install_dir: Path, relative: Path, payload: dict) -> None:
    target = Path(install_dir) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def consume_update_status(install_dir: Path) -> dict | None:
    """Liest eine einmalige Rollbackmeldung für den nächsten GUI-Start."""
    target = Path(install_dir) / UPDATE_STATUS_RELATIVE
    if not target.exists():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        target.unlink()
    except OSError:
        pass
    return payload if isinstance(payload, dict) else None


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

    first = relative_path.parts[0].casefold()

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

        if source.is_symlink():
            shutil.copy2(source, destination, follow_symlinks=False)
        elif source.is_dir():
            shutil.copytree(
                source,
                destination,
                symlinks=True,
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


def _managed_file_manifest(root: Path) -> set[str]:
    result = set()
    root = Path(root)
    for current, directories, files in os.walk(root):
        current_path = Path(current)
        kept_directories = []
        for name in directories:
            candidate = current_path / name
            relative = candidate.relative_to(root)
            if _is_protected(relative):
                continue
            if candidate.is_symlink():
                result.add(relative.as_posix())
            else:
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in files:
            path = current_path / name
            relative = path.relative_to(root)
            if not _is_protected(relative) and (path.is_file() or path.is_symlink()):
                result.add(relative.as_posix())
    return result


def _remove_new_managed_files(install_dir: Path, previous: set[str]) -> None:
    """Entfernt nur Dateien, die vor dem Update nicht vorhanden waren."""
    root = Path(install_dir)
    current = _managed_file_manifest(root)
    for relative_text in sorted(current - previous, reverse=True):
        path = root / Path(relative_text)
        if path.is_file() or path.is_symlink():
            path.unlink()
    directories = []
    for current, names, _files in os.walk(root):
        current_path = Path(current)
        names[:] = [
            name for name in names
            if not _is_protected((current_path / name).relative_to(root))
        ]
        directories.extend(current_path / name for name in names)
    directories.sort(key=lambda p: len(p.parts), reverse=True)
    for directory in directories:
        relative = directory.relative_to(root)
        if _is_protected(relative):
            continue
        try:
            directory.rmdir()
        except OSError:
            pass


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

        if source.is_symlink():
            raise RuntimeError(
                f"Release enthält einen nicht erlaubten symbolischen Link: {relative}"
            )

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

        if source.is_symlink():
            if destination.exists() or destination.is_symlink():
                if destination.is_dir() and not destination.is_symlink():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            shutil.copy2(source, destination, follow_symlinks=False)
        elif source.is_dir():
            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True,
                symlinks=True,
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
    _require_local_venv_interpreter(install_dir)
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


def _install_requirements(
    install_dir: Path,
) -> None:
    """Installiert die neuen Requirements ausschließlich im aktiven venv."""
    requirements = install_dir / "requirements.txt"
    if not requirements.exists():
        raise RuntimeError(
            "requirements.txt fehlt; Abhängigkeitsprüfung kann nicht sicher erfolgen."
        )
    _log_update(
        install_dir, f"Prüfe Python-Abhängigkeiten aus: {requirements}"
    )
    _log_update(
        install_dir, f"Verwendeter Python-Interpreter: {sys.executable}"
    )
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements),
        ],
        cwd=str(install_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = str(process.stdout or "").strip()
    if output:
        for line in output.splitlines():
            _log_update(
                install_dir,
                f"pip: {line}"
            )

    if process.returncode:
        raise RuntimeError(
            "Die Python-Abhängigkeiten konnten nicht installiert werden "
            f"(pip Exit-Code {process.returncode})."
        )

    _log_update(
        install_dir,
        "Python-Abhängigkeiten erfolgreich geprüft/installiert."
    )


def _installed_version(install_dir: Path) -> str:
    process = subprocess.run(
        [
            sys.executable, "-c",
            "from cmdrhelper.version import __version__; print(__version__)",
        ],
        cwd=str(install_dir), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if process.returncode:
        raise RuntimeError(
            f"Zielversion konnte nicht geladen werden: {process.stderr.strip()}"
        )
    return process.stdout.strip()


def _restart_cmdrhelper(
    install_dir: Path,
) -> subprocess.Popen:
    main_file = (
        install_dir
        / "main.py"
    )

    if not main_file.exists():
        raise RuntimeError(
            "main.py wurde nach dem Update nicht gefunden."
        )

    return _spawn(
        [
            sys.executable,
            str(main_file),
        ],
        cwd=install_dir,
    )


def _verify_restart(process: subprocess.Popen, timeout: float = 2.0) -> None:
    """Kleiner Handshake: Ein sofort beendeter GUI-Prozess gilt als Fehler."""
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return
    raise RuntimeError(
        "Die neue CMDRHelper-Version wurde sofort wieder beendet "
        f"(Exit-Code {returncode})."
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

    try:
        _require_local_venv_interpreter(install_dir)
    except Exception as exc:
        _log_update(install_dir, f"ABBRUCH Interpreterprüfung: {exc}")
        return 5

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
    previous_manifest: set[str] = set()
    dependency_phase_started = False
    phase = "Vorbereitung"

    try:
        phase = "Backup"
        _log_update(
            install_dir,
            f"Erstelle Backup: {backup_dir}"
        )

        previous_manifest = _managed_file_manifest(install_dir)
        _backup_managed_files(
            install_dir,
            backup_dir,
        )

        backup_created = True

        phase = "Release entpacken"
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
        phase = "Programmdateien kopieren"
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

        # requirements.txt gehört zum neuen Release. Vor dem Neustart
        # sicherstellen, dass das vorhandene venv/Python alle benötigten
        # Pakete besitzt.
        phase = "Python-Abhängigkeiten installieren"
        dependency_phase_started = True
        _install_requirements(
            install_dir
        )

        phase = "Zielversion prüfen"
        installed_version = _installed_version(install_dir)
        if _version_tuple(installed_version) != _version_tuple(latest_version):
            raise RuntimeError(
                f"Installierte Zielversion {installed_version!r} stimmt nicht "
                f"mit {latest_version!r} überein."
            )

        _log_update(
            install_dir,
            "Starte CMDRHelper neu ..."
        )

        phase = "Neustart prüfen"
        restarted = _restart_cmdrhelper(
            install_dir
        )
        _verify_restart(restarted)

        _log_update(
            install_dir,
            "Update erfolgreich abgeschlossen."
        )

        return 0

    except Exception as exc:
        _log_update(
            install_dir,
            (
                f"UPDATE-FEHLER in Phase '{phase}': "
                f"{type(exc).__name__}: {exc}"
            )
        )

        if backup_created:
            try:
                _log_update(
                    install_dir,
                    "Rollback wird gestartet ..."
                )

                _remove_new_managed_files(install_dir, previous_manifest)
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

                status = {
                    "kind": "rollback",
                    "message": "Update fehlgeschlagen. Die vorherige Version wurde wiederhergestellt.",
                    "phase": phase,
                    "error": str(exc),
                    "log": str(install_dir / UPDATE_LOG_RELATIVE),
                }
                _write_update_state(install_dir, UPDATE_STATUS_RELATIVE, status)

                if dependency_phase_started:
                    repair_script, _start_script = _local_script_names()
                    _write_update_state(
                        install_dir, UPDATE_REPAIR_RELATIVE,
                        {**status, "repair": repair_script},
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
                failure_status = {
                    "kind": "rollback",
                    "message": "Update und automatische Wiederherstellung fehlgeschlagen.",
                    "phase": "Rollback",
                    "error": str(rollback_exc),
                    "log": str(install_dir / UPDATE_LOG_RELATIVE),
                    "repair": _local_script_names()[0],
                }
                _write_update_state(
                    install_dir, UPDATE_STATUS_RELATIVE, failure_status
                )
                _write_update_state(
                    install_dir, UPDATE_REPAIR_RELATIVE, failure_status
                )
                return 3

        if not backup_created:
            _write_update_state(
                install_dir, UPDATE_STATUS_RELATIVE,
                {
                    "kind": "rollback",
                    "message": "Update vor Änderung der Installation abgebrochen.",
                    "phase": phase,
                    "error": str(exc),
                    "log": str(install_dir / UPDATE_LOG_RELATIVE),
                },
            )

        if dependency_phase_started:
            repair_script, _start_script = _local_script_names()
            _log_update(
                install_dir,
                f"venv kann verändert sein; Reparatur über {repair_script} erforderlich."
            )
            return 2

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
