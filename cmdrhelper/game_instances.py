"""Read-only process evidence. Unavailable evidence never means 'no game'."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path

from .journal_sources import canonical


@dataclass(frozen=True)
class GameInstance:
    pid: int
    started: float
    prefixes: tuple = ()
    journals: tuple = ()


@dataclass
class ProcessSnapshot:
    available: bool
    instances: list = field(default_factory=list)


def inspect_instances(proc=Path('/proc')):
    # Windows cannot establish a prefix/source relationship through tasklist.
    # Report unavailable rather than making a window/title-based guess.
    if os.name != 'posix' or not proc.is_dir():
        return ProcessSnapshot(False)
    instances = []
    available = True
    try:
        uptime = float((proc/'uptime').read_text().split()[0])
        boot = datetime.now(timezone.utc).timestamp() - uptime
        ticks = os.sysconf('SC_CLK_TCK')
        entries = list(proc.iterdir())
    except (OSError, ValueError):
        return ProcessSnapshot(False)
    for entry in entries:
        if not entry.name.isdecimal():
            continue
        try:
            args = (entry/'cmdline').read_bytes().split(b'\0')
            # A launcher/proton command can mention the game as a later
            # argument. That does not make the wrapper another game instance.
            names = {Path(args[0].decode(errors='replace').replace('\\', '/')).name.casefold()}
            if not names.intersection({'elitedangerous64.exe', 'elitedangerous.exe', 'elitedangerous64', 'elitedangerous'}):
                continue
            stat = (entry/'stat').read_text()
            start_ticks = stat.rsplit(')', 1)[1].split()[19]
            started = boot + int(start_ticks) / ticks
            prefixes, journals = set(), set()
            try:
                for item in (entry/'environ').read_bytes().split(b'\0'):
                    key, sep, value = item.partition(b'=')
                    if sep and key in (b'WINEPREFIX', b'STEAM_COMPAT_DATA_PATH'):
                        prefix = Path(os.fsdecode(value))
                        if key == b'STEAM_COMPAT_DATA_PATH':
                            prefix = prefix/'pfx'
                        prefixes.add(canonical(prefix))
            except (PermissionError, FileNotFoundError):
                pass
            try:
                for fd in (entry/'fd').iterdir():
                    try:
                        target = fd.resolve(strict=True)
                        if target.name.startswith('Journal.') and target.suffix == '.log':
                            journals.add(str(target))
                    except OSError:
                        continue
            except (PermissionError, FileNotFoundError):
                pass
            # PID recycling/exit during inspection invalidates the evidence.
            if (entry/'stat').read_text().rsplit(')', 1)[1].split()[19] != start_ticks:
                available = False
                continue
            instances.append(GameInstance(int(entry.name), started, tuple(prefixes), tuple(journals)))
        except FileNotFoundError:
            continue
        except (OSError, ValueError, IndexError):
            available = False
    return ProcessSnapshot(available, instances)


def confirmed_selection(snapshot, runtimes):
    """Return (source ID, commander ID, FID) only for one proved instance."""
    if not snapshot.available or len(snapshot.instances) != 1:
        return None
    instance = snapshot.instances[0]
    matches = []
    for runtime in runtimes:
        source, sessions = runtime.source, runtime.processor.sessions
        if not source.enabled or not sessions or source.status != 'ready':
            continue
        session = sessions[-1]
        if session.get('attribution_status') != 'identified' or not session.get('fid_seen') or session.get('commander_id') is None:
            continue
        path = Path(session['journal_file'])
        direct = canonical(path) in instance.journals
        prefix_match = any(Path(canonical(source.path)).is_relative_to(Path(prefix)/'drive_c/users')
                           for prefix in instance.prefixes)
        try:
            first = datetime.fromisoformat(session['first_event_at'].replace('Z', '+00:00')).timestamp()
        except (TypeError, ValueError, KeyError):
            first = 0
        # A prefix alone must never bind a previous login to this process.
        if direct or (prefix_match and instance.started <= first <= datetime.now(timezone.utc).timestamp()):
            matches.append((source.id, session['commander_id'], session['fid_seen']))
    return matches[0] if len(matches) == 1 else None
