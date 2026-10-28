"""Read-only, session-bound evidence for mission arrival presentation."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .game_instances import confirmed_selection, inspect_instances
from .journal_reader import read_journal_delta
from .journal_files import journal_files
from .status_reader import read_status_data, utc_timestamp


@dataclass
class ArrivalPosition:
    system: str = ''
    address: int | None = None
    body: str = ''
    body_id: int | None = None
    station: str = ''
    market_id: int | None = None
    kind: str = ''
    evidence: tuple = ()

    def clear_arrival(self):
        self.station = ''
        self.market_id = None
        self.kind = ''
        self.evidence = ()

    def feed(self, event, sequence):
        et = event.get('event')
        if et in ('Commander', 'LoadGame', 'Shutdown', 'Died'):
            self.__dict__.update(ArrivalPosition().__dict__)
            return
        location_events = {'Location', 'FSDJump', 'CarrierJump', 'SupercruiseEntry',
                           'SupercruiseExit', 'ApproachBody', 'ApproachSettlement',
                           'Docked', 'Disembark', 'Embark', 'Touchdown', 'Liftoff', 'LeaveBody'}
        if et not in location_events:
            return
        if et in ('Touchdown', 'Liftoff') and event.get('PlayerControlled') is not True:
            return
        system = event.get('StarSystem')
        address = event.get('SystemAddress')
        body = event.get('BodyName') or event.get('Body')
        body_id = event.get('BodyID')
        station = event.get('StationName')
        if et == 'ApproachSettlement':
            station = event.get('Name')
        same_dock = (self.evidence if self.kind == 'station' and station == self.station
                     and system == self.system and (address is None or self.address is None
                                                   or address == self.address) else ())
        same_landing = self.evidence if self.kind == 'body' else ()
        if (system and system == self.system and address is not None
                and self.address is not None and address != self.address):
            self.clear_arrival()
            return
        if ((system and self.system and system != self.system)
                or (address is not None and self.address is not None and address != self.address)):
            self.__dict__.update(ArrivalPosition().__dict__)
        if et in ('Location', 'FSDJump', 'CarrierJump', 'SupercruiseEntry'):
            self.__dict__.update(ArrivalPosition().__dict__)
        if system:
            self.system = system
        if address is not None:
            self.address = address
        if et == 'LeaveBody':
            self.clear_arrival()
            self.body, self.body_id = '', None
            return
        # Only position events may change the player's context (never Scan,
        # navigation Destination, ship recall Touchdown, or mission payloads).
        body_matches = bool(body and self.body == body and
                            (body_id is None or self.body_id is None or body_id == self.body_id))
        if ((body and self.body and body != self.body)
                or (body_id is not None and self.body_id is not None and body_id != self.body_id)):
            self.clear_arrival()
        if body:
            if body != self.body:
                self.body_id = None
            self.body = body
        if body_id is not None:
            self.body_id = body_id
        if (self.station and station == self.station and self.market_id is not None
                and event.get('MarketID') is not None and event['MarketID'] != self.market_id):
            self.clear_arrival()
            return
        if self.station and station and station != self.station:
            self.clear_arrival()
        if et == 'Docked' or (et == 'Location' and event.get('Docked') is True):
            self.clear_arrival()
            if system and station:
                self.station, self.market_id = station, event.get('MarketID')
                self.kind = 'station'
                self.evidence = same_dock or (sequence, event.get('timestamp'), et)
        elif et == 'Touchdown':
            self.clear_arrival()
            if self.system and body_matches:
                self.kind = 'body'
                self.evidence = same_landing or (sequence, event.get('timestamp'), et)
        elif et == 'ApproachSettlement' and station:
            # Remember identity evidence for a later Docked, never arrival.
            self.station, self.market_id = station, event.get('MarketID')

    def matches(self, mission):
        if (not self.kind or mission.mission_id is None or mission.extra.get('pending_offer')
                or not mission.destination_system or mission.destination_system != self.system):
            return False
        if mission.destination_station:
            return (self.kind == 'station' and mission.destination_station == self.station
                    and (not mission.destination_body or mission.destination_body == self.body))
        return bool(self.kind == 'body' and mission.destination_body
                    and mission.destination_body == self.body)


class ArrivalSource:
    """Never use the GUI's last position as live evidence. No DB writes/poller."""
    def __init__(self):
        self.cache = None
        self.confirmed = None

    def snapshot(self, state):
        result = self._snapshot(state)
        if result is None:
            self.confirmed = None
        return result

    def _snapshot(self, state):
        manager = getattr(state, 'sources', None)
        if manager is None:
            return None
        processes = inspect_instances()
        selected = confirmed_selection(processes, manager.runtimes.values())
        if selected is None:
            return None
        source_id, cid, fid = selected
        if (cid != getattr(state, 'commander_id', None)
                or fid != getattr(state, 'commander_fid', None)
                or getattr(state, 'viewed_commander_id', cid) != cid):
            return None
        runtime = manager.runtimes[source_id]
        session = runtime.processor.sessions[-1]
        rows = [s for s in runtime.processor.sessions if s.get('commander_id') == cid
                and s.get('fid_seen') == fid and s.get('attribution_status') == 'identified']
        projection = runtime.processor.projection_for(rows)
        if not projection or projection.get('commander_fid') != fid:
            return None
        path = Path(session['journal_file'])
        try:
            current = projection.get('latest_journal_session') or {}
            if (current.get('journal_file') != str(path) or current.get('fid_seen') != fid
                    or current.get('commander_id') != cid
                    or current.get('attribution_status') != 'identified'
                    or path.parent.resolve() != Path(runtime.source.path).resolve()):
                return None
            files = journal_files(path.parent)
            if not files or files[-1] != path:
                return None
            stat = path.stat()
            signature = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            if stat.st_size != session.get('last_read_offset') or stat.st_size != session.get('last_complete_line_offset'):
                return None
            instance = processes.instances[0]
            identity = (source_id, runtime.generation, cid, fid, str(path),
                        session.get('first_event_at'), stat.st_dev, stat.st_ino,
                        instance.pid, instance.started)
            if self.cache is None or self.cache[:2] != (identity, signature):
                events, offset = read_journal_delta(path, 0)
                after = path.stat()
                if offset != stat.st_size or signature != (
                        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    return None
                identities = {e.get('FID') for e in events if e.get('event') in ('Commander', 'LoadGame')}
                if identities != {fid}:
                    return None
                position = ArrivalPosition()
                closed = set()
                login = None
                for n, event in enumerate(events):
                    position.feed(event, n)
                    if event.get('event') == 'LoadGame':
                        login = (n, event.get('timestamp'))
                    if event.get('event') in ('MissionCompleted', 'MissionAbandoned', 'MissionFailed'):
                        closed.add(event.get('MissionID'))
                self.cache = (identity, signature, position, closed, login)
            _, _, position, closed, login = self.cache
            identity = identity + (login,)
            status, _ = read_status_data(path.parent / 'Status.json')
            flags = status.get('Flags')
            stamp = utc_timestamp(status.get('timestamp'))
            if (status.get('event') != 'Status' or type(flags) is not int or flags < 0
                    or stamp < utc_timestamp(session['first_event_at'])
                    or (login and stamp < utc_timestamp(login[1]))
                    or (stamp - datetime.now(timezone.utc)).total_seconds() > 5):
                return None
            contradiction = bool(flags & ((1 << 4) | (1 << 30)))
            contradiction |= bool(status.get('BodyName') and position.body and status['BodyName'] != position.body)
            contradiction |= position.kind == 'body' and status.get('BodyName') != position.body
            proof = (identity, position.evidence)
            # A new binding must be confirmed NOW, not merely by a historical
            # Docked/Touchdown. Afterwards explicit Undocked/Liftoff may retain
            # the known vicinity until an actual departure/contradiction.
            physical = bool(flags & (1 if position.kind == 'station' else 2))
            pending = bool(position.evidence and stamp < utc_timestamp(position.evidence[1]))
            pending = pending or bool(position.kind and self.confirmed != proof and not physical)
            # Revalidate bytes after the sidecar read; no pending journal tail.
            after = path.stat()
            if signature != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                return None
            if pending or contradiction:
                self.confirmed = None
                return identity, ArrivalPosition(), closed
            self.confirmed = proof if position.kind else None
            return identity, position, closed
        except (OSError, ValueError, TypeError, KeyError, IndexError):
            return None
