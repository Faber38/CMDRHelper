from __future__ import annotations

from cmdrhelper.i18n import tr
from cmdrhelper.models import Mission, STATUS_ACCEPTED


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
        status = raw.get("status") or STATUS_ACCEPTED
        next_step = raw.get("next_step") or default_next_step(raw)
        summary = raw.get("summary") or build_summary(raw)

        result.append(
            Mission(
                mission_id=raw.get("mission_id"),
                name=raw.get("name", ""),
                internal_name=raw.get("internal_name", ""),
                mission_type=raw.get("mission_type", ""),
                faction=raw.get("faction", ""),
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


def translate_mission_text(value: str) -> str:
    """
    Übersetzt ausschließlich von CMDRHelper erzeugte Missionstexte.

    Die intern gespeicherten Texte bleiben stabil, damit die Missionslogik
    unabhängig von der in Elite Dangerous eingestellten Sprache arbeitet.
    Journal-Eigennamen und von Frontier gelieferte Texte werden unverändert
    zurückgegeben.
    """
    text = str(value or "")
    if not text:
        return text

    exact = {
        "Angenommen": "mission_state.accepted",
        "Mission angenommen": "mission_state.accepted",
        "Unterwegs": "mission_state.en_route",
        "Im Zielsystem": "mission_state.in_target_system",
        "Am Missionsziel": "mission_state.at_destination",
        "Ziel geändert": "mission_state.redirected",
        "Ware aufgenommen": "mission_state.cargo_collected",
        "Lieferung läuft": "mission_state.delivering",
        "Aufgabe erledigt": "mission_state.completed",
        "Daten erhalten": "mission_state.data_received",
        "Fehlgeschlagen": "mission_state.failed",
        "Abgebrochen": "mission_state.abandoned",
        "Nicht mehr aktiv": "mission_state.inactive",
        "Zurück zum Missionsterminal": "mission_step.return_terminal",
        "Missionsterminal öffnen / Lieferung abgeben": "mission_step.open_terminal_deliver",
        "Missionsziel ausführen / Daten beschaffen": "mission_step.execute_get_data",
        "Missionsziel ausführen": "mission_step.execute",
        "Missionsziel aufsuchen": "mission_step.find_destination",
        "Weitere Missionsware abgeben": "mission_step.deliver_more",
        "Lieferauftrag prüfen": "mission_step.check_delivery",
        "Missionsgegenstand beschaffen": "mission_step.obtain_item",
        "Passagierziel anfliegen": "mission_step.fly_passenger_destination",
        "Missionsbeschreibung prüfen": "mission_step.check_description",
        "Mission prüfen": "mission_step.check_mission",
        "Beschaffungsmission": "mission_name.collect",
        "Das Journal enthält für diese Mission keine weiteren Zielangaben.": "mission_summary.no_details",
    }

    key = exact.get(text)
    if key:
        return tr(key)

    if text.startswith("Nach ") and " / " in text and text.endswith(" reisen"):
        payload = text[5:-7]
        system, station = payload.split(" / ", 1)
        return tr("mission_step.travel_system_station", system=system, station=station)

    if text.startswith("Nach ") and text.endswith(" reisen"):
        return tr("mission_step.travel_system", system=text[5:-7])

    if text.startswith("Ziel suchen: "):
        return tr("mission_step.find_target", target=text[len("Ziel suchen: "):])

    if text.startswith("Zum Zielort ") and text.endswith(" weiterfliegen"):
        station = text[len("Zum Zielort "):-len(" weiterfliegen")]
        return tr("mission_step.continue_to_location", location=station)

    if text.endswith(" aufgenommen") and "/" in text:
        return tr("mission_progress.collected", value=text[:-len(" aufgenommen")])

    if text.endswith(" geliefert") and "/" in text:
        return tr("mission_progress.delivered", value=text[:-len(" geliefert")])

    if text.startswith("Beschaffungsmission: "):
        return tr("mission_name.collect_commodity", commodity=text[len("Beschaffungsmission: "):])

    if " Einheiten besorgen und liefern: " in text:
        count, commodity = text.split(" Einheiten besorgen und liefern: ", 1)
        if count.isdigit():
            return tr("mission_name.collect_count", count=count, commodity=commodity)

    return text
