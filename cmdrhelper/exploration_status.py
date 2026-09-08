"""Interpret own journal observations, never current Elite ownership.

The existing was_* fields are observations at a scan (possibly a saved scan
from an earlier visit). Candidates below refer ONLY to that observation, not
an unsold claim or today's availability. self_mapped is a separate cumulative
record; it does not establish who mapped first or the order relative to a scan.
Sales estimates and EDSM records cannot confirm official first ownership.
"""
from cmdrhelper.i18n import tr


def journal_flag(body, name):
    if body.get("journal_scanned") is False or body.get("source") == "EDSM":
        return None
    value = body.get(name)
    return value if isinstance(value, bool) else None


def exploration_status(body):
    discovered = journal_flag(body, "was_discovered")
    mapped = journal_flag(body, "was_mapped")
    mappable = not (body.get("star_type") or body.get("body_type") in ("Star", "BeltCluster"))
    own_mapping = body.get("self_mapped")
    if body.get("source") == "EDSM":
        own_mapping = None
    elif own_mapping is not True and body.get("journal_scanned") is False:
        own_mapping = None
    elif not isinstance(own_mapping, bool):
        own_mapping = None
    return {
        "was_discovered_at_scan": discovered,
        "was_mapped_at_scan": mapped,
        "self_mapped": own_mapping,
        "edsm_known": body.get("edsm_known") if isinstance(body.get("edsm_known"), bool) else None,
        "first_discovery_candidate": discovered is False,
        "first_mapping_candidate": bool(mappable and mapped is False),
    }


def truth_text(value):
    return tr("common.yes") if value is True else tr("common.no") if value is False else tr("common.unknown")


def status_rows(body):
    """Shared compact wording for map, value-list tooltips and body details."""
    status = exploration_status(body)
    rows = [(tr("body_detail.already_discovered"), truth_text(status["was_discovered_at_scan"]))]
    rows.append((tr("body_detail.first_discovery"),
                 tr("body_detail.first_discovery_possible") if status["first_discovery_candidate"]
                 else tr("body_detail.no_already_discovered") if status["was_discovered_at_scan"] is True
                 else tr("common.unknown")))
    if not (body.get("star_type") or body.get("body_type") in ("Star", "BeltCluster")):
        rows.extend([
            (tr("body_detail.already_mapped"), truth_text(status["was_mapped_at_scan"])),
            (tr("body_detail.mapped_by_you_label"), truth_text(status["self_mapped"])),
            (tr("body_detail.first_mapping"),
             tr("body_detail.first_mapping_claimed") if status["first_mapping_candidate"] and status["self_mapped"] is True
             else tr("body_detail.first_mapping_possible") if status["first_mapping_candidate"]
             else tr("body_detail.no_already_mapped") if status["was_mapped_at_scan"] is True
             else tr("common.unknown")),
        ])
    # False can mean "no body returned/EDSM disabled" in the existing data path,
    # not a verified negative API result. Do not label that as not known to EDSM.
    if status["edsm_known"] is True:
        rows.append(("EDSM", tr("exploration.edsm_body_known")))
    return rows


def status_tooltip(body):
    return "\n".join(f"{label}: {value}" for label, value in status_rows(body)) + "\n" + tr("exploration.historical_notice")
