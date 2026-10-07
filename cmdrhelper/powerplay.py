"""Local PP2 snapshots and a read-only decoder for the game's powers cache.

No assignments, reward attribution, network access or persistent storage.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import re
import struct
from .powerplay_chronicle import PowerplayChronicle


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except (ValueError, TypeError):
        return None


def amount(value):
    return value if type(value) is int and 0 <= value <= 2**63 - 1 else None


def number(value):
    if type(value) is int:
        return value if abs(value) <= 2**63 - 1 else None
    return value if type(value) is float and math.isfinite(value) else None


def system_status(value):
    return str(value or "").removeprefix("POWERPLAY_STATE_").casefold()


@dataclass
class PowerplayActivity:
    event: str
    timestamp: str
    power: str
    commodity: str = ""
    name: str = ""
    count: int | None = None
    gained: int | None = None
    total: int | None = None
    system: str = ""
    station: str = ""


@dataclass
class PowerplayState:
    power: str = ""
    membership_known: bool = False
    rank: int | None = None
    merits: int | None = None
    joined: datetime | None = None
    joined_estimated: bool = False
    recent: list[PowerplayActivity] = field(default_factory=list)
    system: dict = field(default_factory=dict)
    station: str = ""
    transport_items: dict = field(default_factory=dict)
    chronicle: PowerplayChronicle = field(default_factory=PowerplayChronicle)

    def _clear_personal(self):
        self.power = ""
        self.rank = self.merits = self.joined = None
        self.joined_estimated = False
        self.recent = []
        self.transport_items = {}
        self.chronicle = PowerplayChronicle()

    def _remember(self, activity):
        # Preserve journal order, including separate credits in the same second.
        self.recent = (self.recent + [activity])[-24:]

    def apply(self, event):
        self._apply(event)
        self.chronicle.apply(event, system=self.system.get("StarSystem", ""),
                             station=self.station, power=self.power)

    def _apply(self, event):
        kind = event.get("event")
        if kind in ("Fileheader", "LoadGame", "Shutdown"):
            self.system = {}
            self.station = ""
        if kind in ("Location", "FSDJump", "CarrierJump"):
            self.station = (event.get("StationName") or "") if event.get("Docked") is True else ""
            # A new snapshot replaces every old system field, even if absent.
            self.system = {k: event[k] for k in (
                "StarSystem", "SystemAddress", "ControllingPower", "Powers",
                "PowerplayState", "PowerplayStateControlProgress",
                "PowerplayStateReinforcement", "PowerplayStateUndermining",
                "PowerplayConflictProgress", "timestamp",
            ) if k in event}
        elif kind in ("Docked", "SupercruiseExit"):
            self.station = (event.get("StationName") or "") if kind == "Docked" else ""
            if (event.get("StarSystem") and event["StarSystem"] != self.system.get("StarSystem")):
                self.system = {k: event[k] for k in ("StarSystem", "SystemAddress", "timestamp") if k in event}
        elif kind in ("Undocked", "SupercruiseEntry", "StartJump"):
            self.station = ""
        elif kind in ("PowerplayCollect", "PowerplayDeliver"):
            power, commodity = event.get("Power"), event.get("Type")
            count = amount(event.get("Count"))
            if (not isinstance(power, str) or not power.strip()
                    or not isinstance(commodity, str) or not commodity.strip() or count is None):
                return
            name = event.get("Type_Localised")
            name = name if isinstance(name, str) and name.strip() else commodity
            self.transport_items[commodity.casefold()] = dict(power=power, name=name)
            self._remember(PowerplayActivity(
                kind, str(event.get("timestamp") or ""), power,
                commodity=commodity, name=name, count=count,
                system=self.system.get("StarSystem", ""), station=self.station,
            ))
        elif kind in ("PowerplayLeave", "PowerplayDefect"):
            self._clear_personal()
            # A defection requires a subsequent explicit personal snapshot.
            self.membership_known = kind == "PowerplayLeave"
        elif kind in ("PowerplayJoin", "PowerplayRank", "Powerplay", "PowerplayMerits"):
            power = event.get("Power")
            if not isinstance(power, str) or not power.strip():
                if kind == "Powerplay" and power == "":
                    self._clear_personal()
                    self.membership_known = True
                return
            power = power.strip()
            if power != self.power and (self.power or self.membership_known):
                self._clear_personal()
            self.power, self.membership_known = power, True
            if kind in ("PowerplayRank", "Powerplay"):
                self.rank = amount(event.get("Rank"))
            if kind == "Powerplay":
                self.merits = amount(event.get("Merits"))
                pledged = amount(event.get("TimePledged"))
                at = timestamp(event.get("timestamp"))
                if self.joined is None and pledged is not None and at is not None:
                    try:
                        self.joined = at - timedelta(seconds=pledged)
                        self.joined_estimated = True
                    except (OverflowError, ValueError):
                        pass
            elif kind == "PowerplayJoin":
                self.joined = timestamp(event.get("timestamp"))
                self.joined_estimated = False
            elif kind == "PowerplayMerits":
                total = amount(event.get("TotalMerits"))
                if total is not None:
                    self.merits = total
                gained = amount(event.get("MeritsGained"))
                if gained is not None:
                    self._remember(PowerplayActivity(
                        kind, str(event.get("timestamp") or ""), power,
                        gained=gained, total=total,
                    ))


def onboard_articles(state, inventory, powers):
    """Filter confirmed ship inventory by cache IDs or observed PP transport.

    Never turn a Collect/Deliver event into an inventory ledger. Unknown cache
    categories and conflicting mappings cannot imply a use for a commodity.
    """
    if not isinstance(inventory, dict):
        return []
    power_data = (powers or {}).get(state.power, {})
    commodities = power_data.get("commodities", {})
    mapping = {}
    if isinstance(commodities, dict):
        for category in ("acquisition", "reinforcement", "undermining"):
            name = commodities.get(category)
            if isinstance(name, str) and name.strip():
                mapping.setdefault(name.casefold(), []).append(category)
    result = []
    for row in inventory.get("inventory", []):
        name = row.get("frontier_name", "")
        count = amount(row.get("count"))
        if not isinstance(name, str) or not count:
            continue
        key = name.casefold()
        observed = state.transport_items.get(key, {})
        categories = mapping.get(key, [])
        if not categories and not observed:
            continue
        display = row.get("display_name") or name
        if observed.get("name") and observed["name"].casefold() != key:
            display = observed["name"]
        result.append(dict(
            commodity=name, count=count,
            name=display,
            power=state.power if categories else observed.get("power", ""),
            category=categories[0] if len(categories) == 1 else None,
        ))
    return result


def context(state):
    """Return relationship and activity category only from explicit evidence."""
    system = state.system
    status = system_status(system.get("PowerplayState"))
    owner = system.get("ControllingPower")
    if status == "unoccupied" and not owner:
        relationship = "unoccupied"
        powers = system.get("Powers")
        conflicts = system.get("PowerplayConflictProgress")
        candidates = {p for p in powers if isinstance(p, str)} if isinstance(powers, list) else set()
        if isinstance(conflicts, list):
            candidates.update(p["Power"] for p in conflicts if isinstance(p, dict) and isinstance(p.get("Power"), str))
        if state.power and candidates == {state.power}:
            return relationship, "acquisition"
        # Multiple participating powers alone do not establish which cache
        # category applies here. Keep the recommendation explicitly unknown.
        return relationship, None
    if status in ("exploited", "fortified", "stronghold") and isinstance(owner, str) and owner:
        if not state.power:
            return "unknown", None
        own = owner == state.power
        return ("own", "reinforcement") if own else ("opposing", "undermining")
    return "unknown", None


# Revalidated against the local 4.4.1.1 client and the complete real powers file.
# RC4-drop725 wraps a version-3 header and uncompressed UTF-8 JSON.
_CACHE_KEY = b"4%pa#=`yz/7A[VJM63WtFw_ES^=Rx7#_"
MAX_CACHE_BYTES = 4 * 1024 * 1024


def _crypt(data):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + _CACHE_KEY[i % len(_CACHE_KEY)]) & 255
        s[i], s[j] = s[j], s[i]
    i = j = 0
    out = bytearray()
    for n in range(725 + len(data)):
        i = (i + 1) & 255
        j = (j + s[i]) & 255
        s[i], s[j] = s[j], s[i]
        if n >= 725:
            out.append(data[n - 725] ^ s[(s[i] + s[j]) & 255])
    return bytes(out)


class PowerplayCacheError(ValueError):
    pass


class DecodedPowers(dict):
    """Power lookup plus the root-level rank configuration from the same cache."""
    def __init__(self, rank_thresholds=None):
        super().__init__()
        self.rank_thresholds = rank_thresholds


def decode_powers_cache(raw):
    if not 16 <= len(raw) <= MAX_CACHE_BYTES:
        raise PowerplayCacheError("Invalid cache size")
    data = _crypt(raw)
    offset = 5

    def string():
        nonlocal offset
        length = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        if length > 1024 or offset + length > len(data):
            raise PowerplayCacheError("Invalid header string")
        value = data[offset:offset + length].decode("utf-8")
        offset += length
        return value

    try:
        if struct.unpack_from("<I", data)[0] != 3 or data[4] != 1:
            raise PowerplayCacheError("Unsupported powers header")
        if not string() or string() != "api.orerve.net":
            raise PowerplayCacheError("Invalid cache origin/language")
        string()  # Optional server modification date.
        marker, size = struct.unpack_from("<HI", data, offset)
        offset += 6
        if marker != 65535 or size != len(data) - offset:
            raise PowerplayCacheError("Invalid payload length/marker")
        document = json.loads(data[offset:].decode("utf-8"))
        powers = document.get("powers") if isinstance(document, dict) else None
        if not isinstance(powers, list) or not 1 <= len(powers) <= 100:
            raise PowerplayCacheError("Missing powers")
        result = DecodedPowers(document.get("rankThresholds"))
        for power in powers:
            if (not isinstance(power, dict) or not isinstance(power.get("name"), str)
                    or not power["name"].strip() or amount(power.get("id")) is None
                    or not isinstance(power.get("ethos"), dict) or power["name"] in result):
                raise PowerplayCacheError("Invalid power")
            for category, actions in power["ethos"].items():
                if (not isinstance(actions, list) or len(actions) > 100
                        or any(not isinstance(a, str) or len(a) > 512 for a in actions)):
                    raise PowerplayCacheError("Invalid action list")
            result[power["name"]] = power
        return result
    except (ValueError, TypeError, struct.error, RecursionError) as exc:
        raise PowerplayCacheError("Invalid powers cache") from exc


def powers_cache_path(journal_folder):
    if not journal_folder:
        return None
    folder = Path(journal_folder).resolve()
    # Windows Saved Games and Proton profiles share this directory structure.
    if len(folder.parents) >= 3 and folder.parent.parent.name.casefold() == "saved games":
        return folder.parents[2] / "AppData/Local/Frontier Developments/Elite Dangerous/GalacticPoliticsPowers2.cache"
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "Frontier Developments/Elite Dangerous/GalacticPoliticsPowers2.cache"
    return None


class PowersCache:
    """Read/decode once per file signature; never retain stale data on failure."""
    def __init__(self):
        self.signature = None
        self.powers = None

    def load(self, path):
        try:
            if path is None:
                raise OSError("No profile cache")
            path = Path(path)
            stat = path.stat()
            signature = (str(path), stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            if signature != self.signature:
                self.powers = None
                with path.open("rb") as handle:
                    raw = handle.read(MAX_CACHE_BYTES + 1)
                powers = decode_powers_cache(raw)
                after = path.stat()
                if (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != signature[1:]:
                    raise OSError("Cache changed during read")
                self.powers, self.signature = powers, signature
            return self.powers
        except (OSError, PowerplayCacheError):
            self.powers = None
            self.signature = None
            return None


ACTION_TOKENS = (
    "TransportPowerplayCommodities", "TransferClassifiedData", "HandInSalvage",
    "CompleteAidMissions", "ScanShipsWakes", "HandInExplorationData", "BountyHunting",
    "HandInBiologicalData", "HoloscreenHacking", "PowerKills", "RebootMission",
    "SellExoticGoods", "SellLargeProfits", "SellMinedResourcess", "TransferPoliticalData",
    "TransferResearchData", "ScanDatalinks", "RetrieveCommodities", "UploadMalware",
    "CommitCrimes", "FloodLowValueGoods",
)


def action_token(value):
    match = re.match(r"^\$PP2_Action_([A-Za-z]+);", value)
    return match[1] if match and match[1] in ACTION_TOKENS else None
