"""Preserve metadata from an own DSS completion independently of Scan flags."""


def mapping_metadata(event):
    """Only supplied, valid journal values may update mapping metadata."""
    values = {}
    if isinstance(event.get("timestamp"), str) and event["timestamp"]:
        values["mapped_at"] = event["timestamp"]
    for journal_key, key in (("ProbesUsed", "probes_used"),
                             ("EfficiencyTarget", "efficiency_target")):
        value = event.get(journal_key)
        if type(value) is int and value >= 0:
            values[key] = value
    return values


def apply_mapping_metadata(body, event):
    values = mapping_metadata(event)
    # Keep the first recorded own mapping time, as commander_bodies already does.
    if body.get("mapped_at"):
        values.pop("mapped_at", None)
    body.update(values)
