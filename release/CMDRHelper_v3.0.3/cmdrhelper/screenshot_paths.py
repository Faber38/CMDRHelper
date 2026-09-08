"""Shared naming and commander-folder rules for Elite screenshot copies."""
import re
from pathlib import Path

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def safe_filename_component(value, fallback="UNKNOWN"):
    text = INVALID_FILENAME_CHARS.sub("-", str(value or "").strip())
    text = re.sub(r"\s+", "-", text).strip(" .-")
    if not text:
        text = fallback
    if text.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        text = f"_{text}"
    return text[:120].rstrip(" .") or fallback


def commander_screenshot_folder(target, commander, fid, *, existing=True):
    if target is None:
        return None
    target = Path(target)
    safe_fid = safe_filename_component(fid)
    if existing and target.is_dir():
        suffix = f"_{safe_fid}".casefold()
        candidates = [path for path in target.iterdir()
                      if path.is_dir() and not path.is_symlink()
                      and path.name.casefold().endswith(suffix)]
        if candidates:
            return sorted(candidates, key=lambda path: path.name.casefold())[0]
    desired = target / f"{safe_filename_component(commander)}_{safe_fid}"
    if desired.is_symlink() or (desired.exists() and not desired.is_dir()):
        return None
    return desired
