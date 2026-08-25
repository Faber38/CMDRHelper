from __future__ import annotations

from cmdrhelper.models import Mission


def mission_kind(name: str) -> str:
    n = (name or "").lower()

    groups = [
        ("delivery", ("delivery", "deliver", "courier", "transport", "cargo")),
        ("data", ("data", "datalink", "hack", "scan", "download", "upload")),
        ("combat", ("assass", "massacre", "kill", "onslaught", "combat", "pirate")),
        ("salvage", ("salvage", "collect", "recovery", "retrieve")),
        ("passenger", ("passenger", "sightseeing", "evacuation")),
        ("mining", ("mining", "mine")),
    ]

    for kind, words in groups:
        if any(word in n for word in words):
            return kind
    return "other"


def default_next_step(raw: dict) -> str:
    kind = mission_kind(
        (raw.get("internal_name") or "") + " " + (raw.get("name") or "")
    )

    system = raw.get("destination_system") or ""
    station = raw.get("destination_station") or ""
    target = raw.get("target") or ""

    if system:
        if station:
            return f"Nach {system} / {station} reisen"
        return f"Nach {system} reisen"

    if kind == "combat" and target:
        return f"Ziel suchen: {target}"

    if kind == "delivery":
        return "Lieferauftrag prüfen"
    if kind == "data":
        return "Missionsziel aufsuchen"
    if kind == "salvage":
        return "Missionsgegenstand beschaffen"
    if kind == "passenger":
        return "Passagierziel anfliegen"
    return "Missionsbeschreibung prüfen"


def build_summary(raw: dict) -> str:
    parts = []

    if raw.get("destination_system"):
        parts.append(f"Zielsystem: {raw['destination_system']}")
    if raw.get("destination_body"):
        parts.append(f"Planet/Körper: {raw['destination_body']}")
    if raw.get("destination_station"):
        parts.append(f"Ort: {raw['destination_station']}")
    if raw.get("target"):
        parts.append(f"Ziel: {raw['target']}")
    if raw.get("commodity"):
        amount = f" ({raw.get('count', 0)}x)" if raw.get("count") else ""
        parts.append(f"Waren: {raw['commodity']}{amount}")

    if not parts:
        return "Das Journal enthält für diese Mission keine weiteren Zielangaben."

    return " · ".join(parts)


def normalize_missions(rows: list[dict]) -> list[Mission]:
    result: list[Mission] = []

    for raw in rows:
        status = raw.get("status") or "Angenommen"
        next_step = raw.get("next_step") or default_next_step(raw)
        summary = raw.get("summary") or build_summary(raw)

        result.append(
            Mission(
                mission_id=raw.get("mission_id"),
                name=raw.get("name", ""),
                internal_name=raw.get("internal_name", ""),
                destination_system=raw.get("destination_system", ""),
                destination_station=raw.get("destination_station", ""),
                destination_body=raw.get("destination_body", ""),
                target=raw.get("target", ""),
                commodity=raw.get("commodity", ""),
                count=int(raw.get("count") or 0),
                reward=int(raw.get("reward") or 0),
                expiry=raw.get("expiry", ""),
                status=status,
                next_step=next_step,
                summary=summary,
                progress_text=raw.get("progress_text", ""),
                accepted_at=raw.get("accepted_at", ""),
                last_update=raw.get("last_update", ""),
                extra=raw.get("extra", {}) or {},
            )
        )

    return result
