from __future__ import annotations

from dataclasses import dataclass, field


# Interne CMDRHelper-Missionszustände.
# Diese Werte sind bewusst sprachunabhängig von der in Elite Dangerous
# eingestellten Sprache: Sie werden ausschließlich von CMDRHelper erzeugt.
# Die Übersetzung für die Oberfläche erfolgt zentral über mission_manager.
STATUS_ACCEPTED = "Angenommen"
STATUS_EN_ROUTE = "Unterwegs"
STATUS_IN_TARGET_SYSTEM = "Im Zielsystem"
STATUS_AT_DESTINATION = "Am Missionsziel"
STATUS_REDIRECTED = "Ziel geändert"
STATUS_CARGO_COLLECTED = "Ware aufgenommen"
STATUS_DELIVERING = "Lieferung läuft"
STATUS_COMPLETED = "Aufgabe erledigt"
STATUS_DATA_RECEIVED = "Daten erhalten"
STATUS_FAILED = "Fehlgeschlagen"
STATUS_ABANDONED = "Abgebrochen"
STATUS_INACTIVE = "Nicht mehr aktiv"


@dataclass
class Mission:
    mission_id: int | None = None
    name: str = ""
    internal_name: str = ""
    mission_type: str = ""
    faction: str = ""
    destination_system: str = ""
    destination_station: str = ""
    destination_body: str = ""
    target: str = ""
    commodity: str = ""
    count: int = 0
    reward: int = 0
    expiry: str = ""
    status: str = STATUS_ACCEPTED
    next_step: str = "Mission prüfen"
    summary: str = ""
    progress_text: str = ""
    accepted_at: str = ""
    last_update: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class SystemBody:
    body_id: int = -1
    name: str = ""
    short_name: str = ""
    body_type: str = ""
    star_type: str = ""
    planet_class: str = ""
    parent_id: int | None = None
    parent_star_id: int | None = None
    radius_m: float | None = None
    surface_temperature: float | None = None
    surface_pressure: float | None = None
    atmosphere_composition: str = ""
    gravity_g: float | None = None
    distance_ls: float | None = None
    landable: bool = False
    terraformable: bool = False
    was_discovered: bool | None = None
    was_mapped: bool | None = None
    atmosphere: str = ""
    volcanism: str = ""
    biological_signals: int = 0
    planetary_mining_signals: int | None = None
