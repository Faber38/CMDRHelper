from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Mission:
    mission_id: int | None = None
    name: str = ""
    internal_name: str = ""
    destination_system: str = ""
    destination_station: str = ""
    destination_body: str = ""
    target: str = ""
    commodity: str = ""
    count: int = 0
    reward: int = 0
    expiry: str = ""
    status: str = "Angenommen"
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
    gravity_g: float | None = None
    distance_ls: float | None = None
    landable: bool = False
    terraformable: bool = False
    was_discovered: bool | None = None
    was_mapped: bool | None = None
    atmosphere: str = ""
    volcanism: str = ""
    biological_signals: int = 0
