"""Compact value-list presentation of the existing exploration status."""
from cmdrhelper.i18n import tr


def mapping_status_presentation(status, *, light=False):
    """Return text, tooltip, foreground and ascending rank; retain unknowns."""
    own, previous = status["self_mapped"], status["was_mapped_at_scan"]
    if own is True:
        kind, rank = "self", 0
    elif previous is True:
        kind, rank = "already", 1
    elif own is False and previous is False:
        kind, rank = "not", 2
    else:
        kind, rank = "unknown", 3
    # Dark palette follows existing body/status accents; darker light variants
    # keep the same meaning with readable contrast on light table backgrounds.
    colors = ("#17679b", "#28752c", "#856000", "#536574") if light else (
        "#68c7ff", "#65d067", "#ffb000", "#9ba9b7")
    prefix = "explorer.mapping_status_"
    return ("?" if kind == "unknown" else tr(prefix + kind),
            tr(prefix + kind + "_tip"), colors[rank], rank)
