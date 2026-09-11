"""Short, localized release highlights for the update confirmation and GitHub release."""
from __future__ import annotations

import json
import re

from cmdrhelper.i18n import get_language, tr

RELEASE_SUMMARIES = {
    "3.3": (
        "release.3_3.analysis",
        "release.3_3.game_mode",
        "release.3_3.copy_system",
        "release.3_3.experience",
        "release.3_3.archive_import",
    ),
    "3.2.1": (
        "release.3_2_1.windows_update",
        "release.3_2_1.restart",
        "release.3_2_1.single_instance",
        "release.3_2_1.line_breaks",
    ),
    "3.2": (
        "release.3_2.materials",
        "release.3_2.traders",
        "release.3_2.overview",
        "release.3_2.belts",
        "release.3_2.routes",
        "release.3_2.cartography",
    ),
}


def release_summary(version: str, release_notes: str = "") -> list[str]:
    """Prefer an explicit summary in the existing GitHub release body.

    Ordinary Markdown/changelog text is deliberately not displayed. Malformed
    or untranslated metadata falls back to the bundled, version-specific list.
    """
    match = re.search(
        r"<!--\s*cmdrhelper-update-summary\s+(.*?)-->",
        release_notes or "", re.DOTALL,
    )
    if match:
        try:
            payload = json.loads(match.group(1))
            items = payload.get(get_language()) if isinstance(payload, dict) else None
            if isinstance(items, list) and items and all(
                isinstance(item, str) and item.strip() for item in items
            ):
                return [item.strip() for item in items[:6]]
        except (ValueError, RecursionError):
            pass
    normalized = str(version).strip().removeprefix("v").removeprefix("V")
    return [tr(key) for key in RELEASE_SUMMARIES.get(normalized, ())][:6]
