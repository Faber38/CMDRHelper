"""Windows process waiting for the external updater; never starts the GUI."""
from __future__ import annotations

import ctypes
from ctypes import wintypes


def _kernel32():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def wait_for_process_exit(pid: int, timeout: float = 30.0) -> None:
    """Wait on one process handle, with no signal/termination rights.

    A missing PID is already finished. Access/API errors fail closed: they
    must never be interpreted as permission to overwrite a running app.
    Keeping the handle also avoids polling a subsequently reused PID.
    """
    if pid <= 0 or timeout < 0:
        raise ValueError("Ungültige Eltern-PID oder Wartezeit.")
    kernel = _kernel32()
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: PID no longer exists
            return
        raise OSError(error, "Elternprozess konnte nicht geöffnet werden.")
    try:
        result = kernel.WaitForSingleObject(handle, min(int(timeout * 1000), 0xFFFFFFFE))
        if result == 0:  # WAIT_OBJECT_0: process has terminated
            return
        if result == 258:  # WAIT_TIMEOUT
            raise RuntimeError(
                "CMDRHelper wurde nicht rechtzeitig beendet. Update abgebrochen."
            )
        raise OSError(ctypes.get_last_error(), "Warten auf Elternprozess fehlgeschlagen.")
    finally:
        kernel.CloseHandle(handle)
