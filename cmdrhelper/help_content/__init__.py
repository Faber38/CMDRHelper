"""Sprachabhängiger Zugriff auf zentral gepflegte Hilfetexte."""

from dataclasses import dataclass

from cmdrhelper.help_content import de


@dataclass(frozen=True)
class HelpTopic:
    area: str
    text: str
    dialog_title: str
    close_label: str


_LANGUAGES = {"de": de}


def help_topic(context: str, language: str = "de") -> HelpTopic:
    """Liefert ein Hilfethema; bis weitere Texte existieren, gilt Deutsch."""
    catalog = _LANGUAGES.get(language, de)
    area, text = catalog.HELP_TOPICS[context]
    return HelpTopic(
        area=area,
        text=text,
        dialog_title=catalog.DIALOG_TITLE.format(area=area),
        close_label=catalog.CLOSE_LABEL,
    )
