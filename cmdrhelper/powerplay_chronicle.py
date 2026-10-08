"""Ephemeral PP2 display groups; proximity never proves a cause."""
from dataclasses import dataclass, field
from datetime import datetime


def is_rare_sale(event):
    """Recognize a journal sale using offline commodity identity, not its label."""
    from .commodity_master import lookup_by_symbol
    from .powerplay import amount, timestamp
    if event.get("event") != "MarketSell":
        return False
    count = amount(event.get("Count"))
    commodity = lookup_by_symbol(event.get("Type"))
    return (count is not None and count > 0 and commodity is not None
            and commodity.rare and timestamp(event.get("timestamp")) is not None)


def local_today():
    return datetime.now().astimezone().date()


def local_event_day(value, zone=None):
    from .powerplay import timestamp
    at = timestamp(value)
    # Convert each instant separately: the current UTC offset is not a timezone
    # and must not be reused for timestamps on the other side of a DST change.
    return at.astimezone(zone).date() if at else None


def today_groups(chronicle, day=None, zone=None):
    from .powerplay import timestamp
    day = day or local_today()
    return sorted((g for g in chronicle.groups
                   if local_event_day(g.action.get("timestamp"), zone) == day),
                  key=lambda g: timestamp(g.action["timestamp"]), reverse=True)


def chronicle_for_day(events, day, zone=None):
    """Replay the same correlations, keeping pre-midnight location context only."""
    from .powerplay import PowerplayState
    state = PowerplayState()
    chronicle = PowerplayChronicle()
    for event in events:
        state._apply(event)
        if local_event_day(event.get("timestamp"), zone) == day:
            chronicle.apply(event, system=state.system.get("StarSystem", ""),
                            station=state.station, power=state.power)
        else:
            # A day boundary cannot leave a stale candidate/block open.
            chronicle.pending = chronicle.active = None
            chronicle.ambiguous = False
    return chronicle


@dataclass
class ChronicleGroup:
    action: dict
    certainty: str
    system: str = ""
    station: str = ""
    power: str = ""
    credits: list[dict] = field(default_factory=list)


@dataclass
class PowerplayChronicle:
    groups: list[ChronicleGroup] = field(default_factory=list)
    pending: ChronicleGroup | None = None
    active: ChronicleGroup | None = None
    ambiguous: bool = False

    def _append(self, group):
        self.groups.append(group)
        self.active = group

    @staticmethod
    def _gap(first, second):
        from .powerplay import timestamp
        a, b = timestamp(first.get("timestamp")), timestamp(second.get("timestamp"))
        return (b - a).total_seconds() if a is not None and b is not None else None

    @staticmethod
    def _window(group):
        return 3 if group.action.get("event") == "ShipTargeted" else 1

    def apply(self, event, *, system="", station="", power=""):
        from .powerplay import amount
        kind = event.get("event")
        if kind == "MarketSell":
            # Every sale remains a barrier, including ordinary/invalid sales.
            # A proven rare sale is visible but never a merit candidate.
            self.pending = self.active = None
            self.ambiguous = False
            if is_rare_sale(event):
                self.groups.append(ChronicleGroup(dict(event), "explicit", system, station, power))
            return
        if kind in ("Music", "Friends", "ReceiveText"):
            return
        # Target loss is part of the observed Bounty sequence, not another scan.
        if (kind == "ShipTargeted" and event.get("TargetLocked") is False
                and self.pending and self.pending.action["event"] == "Bounty"):
            return
        explicit = kind in ("PowerplayCollect", "PowerplayDeliver")
        candidate = kind in ("Bounty", "SearchAndRescue") or (
            kind == "ShipTargeted" and event.get("TargetLocked") is True
            and type(event.get("ScanStage")) is int and event["ScanStage"] == 3)
        if explicit or candidate:
            previous = self.pending or (self.active if self.active and not self.active.credits else None)
            gap = self._gap(previous.action, event) if previous else None
            self.ambiguous = bool(previous and gap is not None
                                  and 0 <= gap <= self._window(previous))
            self.pending = self.active = None
            if explicit and (not isinstance(event.get("Power"), str) or not event["Power"].strip()
                             or not isinstance(event.get("Type"), str) or not event["Type"].strip()
                             or amount(event.get("Count")) is None):
                return
            group = ChronicleGroup(dict(event), "explicit" if explicit else "temporal",
                                   system, station, event.get("Power", power))
            if explicit:
                self.ambiguous = False
                self._append(group)
            else:
                self.pending = group
            return
        if kind != "PowerplayMerits":
            # Unknown events, movements, cargo changes and other actions are
            # barriers. Do not grow a permissive list of ignored gameplay events.
            self.pending = self.active = None
            self.ambiguous = False
            return
        if (amount(event.get("MeritsGained")) is None
                or not isinstance(event.get("Power"), str) or not event["Power"].strip()):
            self.pending = self.active = None
            return
        group = self.pending or self.active
        matched = False
        if group and not self.ambiguous and group.power in ("", event["Power"]):
            gap = self._gap(group.action, event)
            action = group.action.get("event")
            if gap is not None:
                if action == "PowerplayDeliver":
                    matched = gap == 0
                elif action in ("Bounty", "SearchAndRescue", "ShipTargeted"):
                    matched = 0 <= gap <= self._window(group)
                    if action == "ShipTargeted":
                        matched = matched and event["MeritsGained"] == 10 and not group.credits
                elif group.certainty == "unknown" and group.credits:
                    last_gap = self._gap(group.credits[-1], event)
                    matched = 0 <= gap <= 10 and last_gap is not None and 0 <= last_gap <= 3
        if matched:
            if self.pending is not None:
                self._append(group)
            group.power = event["Power"]
            group.credits.append(dict(event))
        else:
            group = ChronicleGroup(dict(event), "unknown", system, station, event["Power"], [dict(event)])
            self._append(group)
        self.pending = None
        self.ambiguous = False
