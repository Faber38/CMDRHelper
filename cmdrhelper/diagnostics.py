"""User-requested, local-only diagnostic packages with an explicit allowlist."""
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import platform
import re
import sqlite3
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

import PySide6
from PySide6.QtCore import qVersion

from cmdrhelper.logging_config import LOG_BACKUP_COUNT, LOG_MAX_BYTES, PRIVACY_MARKER, log_folder, sanitize, logged_operation
from cmdrhelper.version import __version__

logger = logging.getLogger(__name__)


def system_info(database=None, journals=None):
    info = dict(version=__version__, os=platform.system(), platform=platform.system(),
                python=platform.python_version(), pyside=PySide6.__version__, qt=qVersion(),
                architecture=platform.machine(), created_at=datetime.now(timezone.utc).isoformat(),
                installation_mode='venv' if sys.prefix != sys.base_prefix else 'python',
                installation_path='<installation>', database_path='<database>',
                journal_path='<journals>', database_reachable=False, database_size=None,
                journal_folder_reachable=False, journal_files=0)
    if database:
        try:
            path = Path(database)
            info['database_size'] = path.stat().st_size
            # Read-only probe: no schema initialization, repair, checkpoint or data query.
            con = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=0)
            try:
                con.execute('PRAGMA schema_version').fetchone()
                info['database_reachable'] = True
            finally:
                con.close()
        except (OSError, sqlite3.Error):
            pass
    if journals:
        try:
            path = Path(journals)
            with os.scandir(path) as entries:
                info['journal_files'] = sum(1 for entry in entries if entry.name.startswith('Journal.')
                                            and entry.name.endswith('.log') and entry.is_file(follow_symlinks=False))
            info['journal_folder_reachable'] = True
        except OSError:
            pass
    return info


def suggested_name():
    return datetime.now().strftime('CMDRHelper_Diagnose_%Y-%m-%d_%H%M.zip')


def _log_text(path):
    if path.is_symlink():
        return None
    try:
        with path.open('rb') as stream:
            data = stream.read(LOG_MAX_BYTES + 65536)
    except FileNotFoundError:  # Rotation may remove a file during collection.
        return None
    lines = []
    for line in data.decode('utf-8', errors='replace').splitlines():
        # Old logs predate the privacy boundary. Never copy their payloads.
        if re.match(r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d (?:DEBUG|INFO|WARNING|ERROR|CRITICAL) +\[privacy-v1\] ', line):
            # The formatter already redacts; apply fallback rules once more.
            lines.append(sanitize(line))
        elif line.startswith(PRIVACY_MARKER + ' '):
            lines.append(sanitize(line))
        elif re.match(r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d ', line):
            lines.append(line[:19] + ' [legacy log content omitted]')
    return '\n'.join(lines) + '\n'


@logged_operation("Diagnostic package")
def create_package(target, *, database=None, journals=None, folder=None, overwrite=False):
    import json
    target = Path(target)
    if target.suffix.lower() != '.zip':
        raise ValueError('ZIP extension required')
    folder = Path(folder) if folder is not None else log_folder()
    info = system_info(database, journals)
    logs = {}
    # Do not scan arbitrary files or follow symlinks. DBs, journals, exports and
    # screenshots are excluded by construction, regardless of their location.
    for number in range(LOG_BACKUP_COUNT + 1):
        name = 'cmdrhelper.log' + (f'.{number}' if number else '')
        content = _log_text(folder / name)
        if content is not None:
            logs[name] = content
    timestamps = sorted(re.findall(r'(?m)^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d', '\n'.join(logs.values())))
    warnings = []
    for text in logs.values():
        for line in text.splitlines():
            if re.match(r'^\d{4}.* (?:WARNING|ERROR|CRITICAL) +', line):
                warnings.append(line)
    from cmdrhelper.i18n import tr
    summary = tr('diagnostics.summary', version=info['version'], platform=info['os'],
                 count=len(logs), period=(timestamps[0] + ' — ' + timestamps[-1] if timestamps else '–'),
                 warnings='\n'.join(sorted(warnings)[-10:]) or '–')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.cmdrhelper-diagnose-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            with ZipFile(stream, 'w', ZIP_DEFLATED) as archive:
                for name, content in logs.items():
                    archive.writestr(name, content.encode('utf-8'))
                archive.writestr('system_info.json', json.dumps(info, indent=2).encode('utf-8'))
                archive.writestr('diagnose_summary.txt', summary.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        if overwrite:
            os.replace(temporary, target)
        else:
            os.link(temporary, target)  # Atomic publication, never clobber a file.
        return target
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
