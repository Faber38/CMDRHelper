from __future__ import annotations

from .de import TRANSLATIONS as DE
from .en import TRANSLATIONS as EN
from .fr import TRANSLATIONS as FR
from .it import TRANSLATIONS as IT
from .no import TRANSLATIONS as NO
from .sv import TRANSLATIONS as SV
from .fi import TRANSLATIONS as FI
from .pl import TRANSLATIONS as PL
from .nl import TRANSLATIONS as NL
from .es import TRANSLATIONS as ES
from .tr import TRANSLATIONS as TR
from .el import TRANSLATIONS as EL

_TRANSLATIONS = {
    "de": DE,
    "en": EN,
    "fr": FR,
    "it": IT,
    "no": NO,
    "sv": SV,
    "fi": FI,
    "pl": PL,
    "nl": NL,
    "es": ES,
    "tr": TR,
    "el": EL,
}

_current_language = "de"


def normalize_language(language: str) -> str:
    language = str(language or "de").strip().lower()
    return language if language in _TRANSLATIONS else "de"


def set_language(language: str, settings=None) -> str:
    global _current_language
    _current_language = normalize_language(language)

    if settings is not None:
        settings.setValue("ui_language", _current_language)
        settings.sync()

    return _current_language


def get_language() -> str:
    return _current_language


def tr(key: str, **values) -> str:
    key = str(key)
    language_table = _TRANSLATIONS.get(_current_language, DE)

    # Fallback-Reihenfolge:
    # 1. gewählte Sprache
    # 2. Englisch
    # 3. Deutsch
    # 4. Übersetzungsschlüssel selbst
    text = language_table.get(key)
    if text is None:
        text = EN.get(key)
    if text is None:
        text = DE.get(key, key)

    if values:
        try:
            return text.format(**values)
        except (KeyError, ValueError):
            return text

    return text
