"""A Lat/Lon compass driven solely by the current complete Status.json.

Journal metadata helps name bodies; it never authorizes or blocks navigation.
"""
from dataclasses import dataclass, replace
from datetime import datetime
import json
import math
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

from cmdrhelper.journal_files import journal_files
from cmdrhelper.planet_geometry import SurfaceSolution, solve
from cmdrhelper.status_reader import StatusError, StatusSnapshot, read_status, unique_object


@dataclass(frozen=True)
class BodyBinding:
    fid: str
    system_address: int | None
    body_id: int | None
    body_name: str


@dataclass(frozen=True)
class SurfaceTarget:
    binding: BodyBinding
    latitude: float
    longitude: float
    system_name: str = ""
    name: str = ""


@dataclass(frozen=True)
class NavigationState:
    target: SurfaceTarget | None = None
    snapshot: StatusSnapshot | None = None
    solution: SurfaceSolution | None = None
    reason: str = "waiting_planetary_position"
    last_confirmed_at: datetime | None = None


class LiveBodyContext:
    """Journal metadata for target input and artwork, never an activation gate."""
    def __init__(self):
        self.fid = ""
        self.running = False
        self.system_address = None
        self.system_name = ""
        self.known_bodies = {}
        self.binding = None

    def feed(self, event):
        et = event.get("event")
        if et in ("Commander", "LoadGame"):
            fid = event.get("FID")
            if not isinstance(fid, str) or not fid.strip():
                self.running = False
                self.binding = None
                return
            if fid != self.fid or et == "LoadGame":
                self.binding = None
                self.system_address = None
                self.system_name = ""
                self.known_bodies.clear()
            self.fid = fid
            if et == "LoadGame":
                self.running = True
            return
        if et in ("Shutdown", "Died"):
            self.running = False
            self.binding = None
            return
        if et == "LeaveBody":
            self.binding = None
            return
        if event.get("FID", self.fid) != self.fid:
            return
        if et in ("Location", "FSDJump", "CarrierJump", "SupercruiseEntry", "SupercruiseExit"):
            address = event.get("SystemAddress")
            name = event.get("StarSystem")
            if type(address) is int and address >= 0:
                self.system_address = address
                self.system_name = name if isinstance(name, str) else ""
                self.binding = None
        if et not in ("Location", "ApproachBody", "SupercruiseExit", "Touchdown", "Scan",
                      "Disembark", "Embark"):
            return
        if event.get("PlayerControlled") is False:
            return
        planet = (et in ("ApproachBody", "Touchdown") or event.get("OnPlanet") is True
                  or event.get("BodyType") == "Planet" or bool(event.get("PlanetClass")))
        address = event.get("SystemAddress", self.system_address)
        body_id = event.get("BodyID")
        name = event.get("BodyName") or event.get("Body")
        if (not planet or (address is not None and (type(address) is not int or address < 0))
                or (body_id is not None and (type(body_id) is not int or body_id < 0))
                or not isinstance(name, str) or not name.strip()):
            return
        binding = BodyBinding(self.fid, address, body_id, name)
        self.known_bodies[address, name] = binding
        if et != "Scan":
            self.binding = binding
            self.system_address = address
            if isinstance(event.get("StarSystem"), str):
                self.system_name = event["StarSystem"]


class LiveJournalTail:
    """Bounded reads, complete JSON lines only; handles session parts and truncation."""
    def __init__(self):
        self.folder = None
        self.session = None
        self.path = None
        self.offset = 0
        self.file_id = None
        self.context = LiveBodyContext()

    def reset(self, folder):
        self.folder = folder
        self.session = self.path = self.file_id = None
        self.offset = 0
        self.context = LiveBodyContext()

    def poll(self, folder):
        folder = Path(folder) if folder else None
        if folder != self.folder:
            self.reset(folder)
        if folder is None:
            raise StatusError("journal_invalid")
        files = journal_files(folder)
        if not files:
            self.context.binding = None
            raise StatusError("journal_invalid")
        session = files[-1].name.rsplit(".", 2)[0]
        if session != self.session:
            self.reset(folder)
            self.session = session
        parts = [p for p in files if p.name.rsplit(".", 2)[0] == session]
        if self.path is not None and self.path not in parts:
            self.reset(folder)
            self.session = session
        budget = 2 * 1024 * 1024
        for path in parts:
            if self.path is not None and parts.index(path) < parts.index(self.path):
                continue
            if path != self.path:
                self.path, self.offset, self.file_id = path, 0, None
            stat = path.stat()
            file_id = (stat.st_dev, stat.st_ino)
            if (self.file_id is not None and file_id != self.file_id) or stat.st_size < self.offset:
                self.reset(folder)
                raise StatusError("journal_invalid")
            self.file_id = file_id
            with path.open("rb") as handle:
                handle.seek(self.offset)
                while budget > 0:
                    line = handle.readline(min(budget, 1024 * 1024))
                    if not line:
                        break
                    if not line.endswith(b"\n"):
                        raise StatusError("journal_pending")
                    budget -= len(line)
                    self.offset = handle.tell()
                    try:
                        event = json.loads(line, object_pairs_hook=unique_object)
                        if not isinstance(event, dict):
                            raise ValueError("Journal object required")
                    except ValueError:
                        self.context.binding = None
                        continue
                    self.context.feed(event)
            if budget <= 0:
                raise StatusError("journal_pending")


class PlanetNavigationController(QObject):
    changed = Signal(object)

    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.tail = LiveJournalTail()
        self.target = None
        self.state = NavigationState()
        self.last_confirmed_at = None
        self._polling = False
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.poll)

    def start(self):
        self.poll()
        self.timer.start()

    def _publish(self, snapshot=None, solution=None, reason=""):
        state = NavigationState(self.target, snapshot, solution, reason, self.last_confirmed_at)
        if state != self.state:
            self.state = state
            self.changed.emit(state)

    def poll(self):
        if self._polling:
            return
        self._polling = True
        try:
            self._poll()
        finally:
            self._polling = False

    def _poll(self):
        folder = getattr(self.app_state, "journal_folder", None)
        try:
            self.tail.poll(folder)
        except (OSError, StatusError):
            pass  # Optional body metadata; Status.json is authoritative.
        try:
            if not folder:
                raise StatusError("invalid_status")
            snapshot = read_status(Path(folder) / "Status.json")
        except StatusError:
            self._publish(reason="waiting_planetary_position")
            return
        self.last_confirmed_at = snapshot.timestamp
        if self.target is None:
            self._publish(snapshot=snapshot, reason="no_target")
            return
        target_name = self.resolve_body_name(self.target.binding.body_name)
        system = self.tail.context.system_name
        if system and snapshot.body_name.casefold() == (system + " " + target_name).casefold():
            target_name = snapshot.body_name
        if snapshot.body_name.casefold() != target_name.casefold():
            self._publish(snapshot=snapshot, reason="waiting_planetary_position")
            return
        candidate = self.body_binding(snapshot.body_name)
        self.target = replace(self.target, binding=candidate)
        solution = solve(snapshot.latitude, snapshot.longitude, snapshot.heading,
                         self.target.latitude, self.target.longitude, snapshot.radius_m)
        self._publish(snapshot=snapshot, solution=solution)

    def resolve_body_name(self, name):
        """Accept a short body name only with an unambiguous current system prefix."""
        system = self.tail.context.system_name
        if not system:
            system = str(getattr(self.app_state, "system", "") or "")
        if system and not name.casefold().startswith(system.casefold() + " "):
            full_name = system + " " + name
            known = self.body_names()
            # During activation the newly read snapshot is not published yet.
            if any(n.casefold() == full_name.casefold() for n in known):
                return full_name
        return name

    def body_binding(self, name):
        """Resolve optional IDs by exact name; IDs never enter activation rules."""
        context = self.tail.context
        candidates = [b for (address, _), b in context.known_bodies.items()
                      if address == context.system_address and b.body_name.casefold() == name.casefold()]
        if len(candidates) == 1:
            return candidates[0]
        bodies = [b for b in getattr(self.app_state, "system_bodies", ())
                  if str(b.get("name", "")).casefold() == name.casefold()]
        fid = context.fid or str(getattr(self.app_state, "commander_fid", "") or "")
        if len(bodies) == 1:
            return BodyBinding(fid, getattr(self.app_state, "system_address", None),
                               bodies[0].get("body_id"), name)
        return BodyBinding(fid, None, None, name)

    @property
    def current_body(self):
        if self.state.snapshot is not None:
            return self.body_binding(self.state.snapshot.body_name)
        return self.tail.context.binding

    def body_names(self):
        names = {b.body_name for (address, _), b in self.tail.context.known_bodies.items()
                 if address == self.tail.context.system_address}
        names.update(b["name"] for b in getattr(self.app_state, "system_bodies", ())
                     if b.get("body_type") == "Planet" and b.get("name"))
        if self.current_body:
            names.add(self.current_body.body_name)
        return sorted(names)

    def set_target(self, latitude, longitude, body_name=None, name=""):
        """Replace a single in-memory point; body name is the only identity input."""
        self.poll()
        if body_name is None and self.current_body:
            body_name = self.current_body.body_name
        if (not isinstance(body_name, str) or not body_name.strip()
                or not isinstance(name, str)
                or any(type(v) not in (int, float) or not math.isfinite(v)
                       for v in (latitude, longitude))
                or not -90 <= latitude <= 90 or not -180 <= longitude <= 180):
            raise ValueError("invalid_target")
        body_name = self.resolve_body_name(body_name.strip())
        self.target = SurfaceTarget(self.body_binding(body_name), latitude, longitude,
                                    name=name.strip())
        self.poll()

    def stop_target(self):
        self.target = None
        self.poll()
