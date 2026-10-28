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


def screenshot_capture_time(path, *, converted=False):
    """Prefer an explicit capture timestamp; a sequential F10 number is no date."""
    from datetime import datetime
    stem = path.stem
    if not converted:
        stem = re.sub(r'(?i)^(?:Screenshot|HighResScreenshot)[ _-]?', '', stem)
    pattern = r'(\d{4}-\d{2}-\d{2})[_ ](\d{2})[-.](\d{2})[-.](\d{2})'
    match = re.match('^' + pattern + r'(?:_|$)', stem)
    if converted and match is None:
        match = re.search('_' + pattern + r'(?:_\d+)?$', stem)
    if match:
        try:
            return datetime.strptime('-'.join(match.groups()), '%Y-%m-%d-%H-%M-%S').timestamp()
        except ValueError:
            pass
    if converted:
        raise ValueError('invalid_screenshot_name')
    return path.stat().st_mtime


def screenshot_component(value, fallback):
    # Keep the established directory naming rules unchanged.
    return safe_filename_component(re.sub(r'\s+', '_', str(value or '').strip()), fallback)[:70]
