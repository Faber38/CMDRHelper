"""Language-aware access to the centrally maintained help catalogs."""

from dataclasses import dataclass
from importlib import import_module

from cmdrhelper.help_content import de


@dataclass(frozen=True)
class HelpTopic:
    area: str
    text: str
    dialog_title: str
    close_label: str


_LANGUAGES = {"de": de}
for _language in (
    "en", "fr", "it", "no", "sv", "fi", "pl", "nl", "es", "tr", "el",
):
    try:
        _LANGUAGES[_language] = import_module(
            f"cmdrhelper.help_content.{_language}"
        )
    except (ImportError, SyntaxError):
        # A damaged optional catalog must not prevent the German help from opening.
        continue

HELP_LANGUAGES = tuple(_LANGUAGES)


def help_topic(context: str, language: str = "de") -> HelpTopic:
    """Return a localized help topic, falling back to the German master."""
    catalog = _LANGUAGES.get(language, de)
    try:
        area, text = catalog.HELP_TOPICS[context]
    except (AttributeError, KeyError, TypeError, ValueError):
        catalog = de
        area, text = de.HELP_TOPICS[context]
    return HelpTopic(
        area=area,
        text=text,
        dialog_title=catalog.DIALOG_TITLE.format(area=area),
        close_label=catalog.CLOSE_LABEL,
    )
