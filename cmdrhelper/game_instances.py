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
    windows_started: int | None = None  # Exact FILETIME, also guards PID reuse.


@dataclass
class ProcessSnapshot:
    available: bool
    instances: list = field(default_factory=list)


class _WindowsProcesses:
    """Read-only Toolhelp/Restart Manager bindings; no shutdown/restart calls."""

    def __init__(self):
        import ctypes as c
        self.c = c
        dword, boolean, handle = c.c_uint32, c.c_int32, c.c_void_p

        class FileTime(c.Structure):
            _fields_ = [('low', dword), ('high', dword)]

            def ticks(self):
                return self.low | (self.high << 32)

        class ProcessEntry(c.Structure):
            _fields_ = [('size', dword), ('usage', dword), ('pid', dword),
                        ('heap', c.c_size_t), ('module', dword), ('threads', dword),
                        ('parent', dword), ('priority', c.c_int32), ('flags', dword),
                        ('exe', c.c_wchar * 260)]

        class UniqueProcess(c.Structure):
            _fields_ = [('pid', dword), ('started', FileTime)]

        class ProcessInfo(c.Structure):
            _fields_ = [('process', UniqueProcess), ('app_name', c.c_wchar * 256),
                        ('service_name', c.c_wchar * 64), ('app_type', c.c_int32),
                        ('status', dword), ('session', dword), ('restartable', boolean)]

        self.FileTime, self.ProcessEntry, self.ProcessInfo = FileTime, ProcessEntry, ProcessInfo
        self.kernel = c.WinDLL('kernel32', use_last_error=True)
        self.rm = c.WinDLL('rstrtmgr', use_last_error=True)
        declarations = [
            (self.kernel.CreateToolhelp32Snapshot, [dword, dword], handle),
            (self.kernel.Process32FirstW, [handle, c.POINTER(ProcessEntry)], boolean),
            (self.kernel.Process32NextW, [handle, c.POINTER(ProcessEntry)], boolean),
            (self.kernel.OpenProcess, [dword, boolean, dword], handle),
            (self.kernel.GetProcessTimes, [handle] + [c.POINTER(FileTime)] * 4, boolean),
            (self.kernel.GetExitCodeProcess, [handle, c.POINTER(dword)], boolean),
            (self.kernel.CloseHandle, [handle], boolean),
            (self.rm.RmStartSession, [c.POINTER(dword), dword, c.c_wchar_p], dword),
            (self.rm.RmRegisterResources, [dword, dword, c.POINTER(c.c_wchar_p),
                dword, c.POINTER(UniqueProcess), dword, c.POINTER(c.c_wchar_p)], dword),
            (self.rm.RmGetList, [dword, c.POINTER(dword), c.POINTER(dword),
                c.POINTER(ProcessInfo), c.POINTER(dword)], dword),
            (self.rm.RmEndSession, [dword], dword),
        ]
        for function, args, result in declarations:
            function.argtypes, function.restype = args, result

    def instances(self):
        c, kernel = self.c, self.kernel
        snapshot = kernel.CreateToolhelp32Snapshot(2, 0)  # TH32CS_SNAPPROCESS
        if snapshot in (None, c.c_void_p(-1).value):
            raise OSError('Windows process snapshot unavailable')
        instances = []
        try:
            entry = self.ProcessEntry()
            entry.size = c.sizeof(entry)
            more = kernel.Process32FirstW(snapshot, c.byref(entry))
            while more:
                if entry.exe.casefold() in ('elitedangerous64.exe', 'elitedangerous.exe'):
                    process = kernel.OpenProcess(0x1000, False, entry.pid)  # QUERY_LIMITED_INFORMATION
                    if not process:
                        raise OSError('Elite process identity unavailable')
                    try:
                        created, exited, system, user = (self.FileTime() for _ in range(4))
                        status = c.c_uint32()
                        if (not kernel.GetProcessTimes(process, c.byref(created), c.byref(exited),
                                c.byref(system), c.byref(user))
                                or not kernel.GetExitCodeProcess(process, c.byref(status))
                                or status.value != 259):  # STILL_ACTIVE
                            raise OSError('Elite process exited during inspection')
                        ticks = created.ticks()
                        instances.append(GameInstance(entry.pid, ticks / 10_000_000 - 11644473600,
                                                      windows_started=ticks))
                    finally:
                        kernel.CloseHandle(process)
                more = kernel.Process32NextW(snapshot, c.byref(entry))
            if c.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                raise OSError('Windows process enumeration incomplete')
        finally:
            kernel.CloseHandle(snapshot)
        return instances

    def file_users(self, path):
        c, rm = self.c, self.rm
        session = c.c_uint32()
        if rm.RmStartSession(c.byref(session), 0, c.create_unicode_buffer(33)):
            raise OSError('Windows resource session unavailable')
        try:
            files = (c.c_wchar_p * 1)(str(path))
            if rm.RmRegisterResources(session, 1, files, 0, None, 0, None):
                raise OSError('Windows journal resource unavailable')
            needed, count, reasons = c.c_uint32(), c.c_uint32(), c.c_uint32()
            result = rm.RmGetList(session, c.byref(needed), c.byref(count), None, c.byref(reasons))
            if result == 0:
                return set()
            if result != 234:  # ERROR_MORE_DATA
                raise OSError('Windows journal users unavailable')
            rows = (self.ProcessInfo * needed.value)()
            count.value = len(rows)
            if rm.RmGetList(session, c.byref(needed), c.byref(count), rows, c.byref(reasons)):
                # A changing list is retried by the existing source timer.
                raise OSError('Windows journal users changed during inspection')
            return {(row.process.pid, row.process.started.ticks()) for row in rows[:count.value]}
        finally:
            rm.RmEndSession(session)


def inspect_instances(proc=Path('/proc')):
    if os.name == 'nt':
        try:
            return ProcessSnapshot(True, _WindowsProcesses().instances())
        except (OSError, AttributeError):
            return ProcessSnapshot(False)
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
    windows = None
    if instance.windows_started is not None:
        try:
            windows = _WindowsProcesses()
        except (OSError, AttributeError):
            return None
    matches = []
    for runtime in runtimes:
        source, sessions = runtime.source, runtime.processor.sessions
        if not source.enabled or not sessions or source.status != 'ready':
            continue
        session = sessions[-1]
        if session.get('attribution_status') != 'identified' or not session.get('fid_seen') or session.get('commander_id') is None:
            continue
        path = Path(session['journal_file'])
        if windows is not None:
            try:
                # Process name/time alone is never a journal or FID witness.
                # Query only this source's latest verified journal, not history.
                users = windows.file_users(canonical(path))
            except OSError:
                return None
            if (instance.pid, instance.windows_started) in users:
                matches.append((source.id, session['commander_id'], session['fid_seen']))
            continue
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
    if len(matches) != 1:
        return None
    if windows is not None:
        try:
            # Resource lookup may outlive the source timer's process snapshot.
            # Recheck immediately before handing a selection to the caller.
            current = windows.instances()
        except OSError:
            return None
        if [(p.pid, p.windows_started) for p in current] != [(instance.pid, instance.windows_started)]:
            return None
    return matches[0]
