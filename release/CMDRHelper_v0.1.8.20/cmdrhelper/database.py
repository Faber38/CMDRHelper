from __future__ import annotations

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path


def default_database_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "cmdrhelper.db"


class CMDRDatabase:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self):
        con = sqlite3.connect(self.path)
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA journal_mode = WAL")
        return con

    def _create_schema(self):
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS systems (
                    system_address INTEGER PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    body_count INTEGER NOT NULL DEFAULT 0,
                    all_bodies_found INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS bodies (
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    name TEXT NOT NULL DEFAULT '',
                    short_name TEXT NOT NULL DEFAULT '',
                    body_type TEXT NOT NULL DEFAULT '',
                    star_type TEXT NOT NULL DEFAULT '',
                    planet_class TEXT NOT NULL DEFAULT '',
                    parent_id INTEGER,
                    mass_em REAL,
                    stellar_mass REAL,
                    gravity_g REAL,
                    distance_ls REAL,
                    landable INTEGER NOT NULL DEFAULT 0,
                    terraformable INTEGER NOT NULL DEFAULT 0,
                    was_discovered INTEGER,
                    was_mapped INTEGER,
                    self_mapped INTEGER NOT NULL DEFAULT 0,
                    efficient_mapping INTEGER NOT NULL DEFAULT 0,
                    atmosphere TEXT NOT NULL DEFAULT '',
                    volcanism TEXT NOT NULL DEFAULT '',
                    biological_signals INTEGER NOT NULL DEFAULT 0,
                    geological_signals INTEGER NOT NULL DEFAULT 0,
                    scan_value INTEGER NOT NULL DEFAULT 0,
                    mapped_value INTEGER NOT NULL DEFAULT 0,
                    current_value INTEGER NOT NULL DEFAULT 0,
                    high_value INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (system_address, body_id)
                );

                CREATE TABLE IF NOT EXISTS materials (
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    material_name TEXT NOT NULL,
                    percentage REAL,
                    PRIMARY KEY (system_address, body_id, material_name)
                );

                CREATE TABLE IF NOT EXISTS journal_imports (
                    journal_file TEXT PRIMARY KEY,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_import TEXT NOT NULL DEFAULT ''
                );
            """)

    @staticmethod
    def _bool_db(value):
        if value is None:
            return None
        return 1 if bool(value) else 0

    @staticmethod
    def _materials(body):
        raw = body.get("materials") or {}
        if isinstance(raw, dict):
            return list(raw.items())
        if isinstance(raw, list):
            result = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                name = item.get("Name_Localised") or item.get("Name") or item.get("name")
                value = item.get("Percent")
                if value is None:
                    value = item.get("percentage")
                if name:
                    result.append((str(name), value))
            return result
        return []

    def store_snapshot(self, data):
        address = data.get("system_address")
        if address is None:
            return

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        seen = data.get("last_timestamp") or now
        bodies = data.get("system_bodies") or []

        with self._connect() as con:
            con.execute("""
                INSERT INTO systems (
                    system_address, name, first_seen, last_seen,
                    body_count, all_bodies_found
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address) DO UPDATE SET
                    name=CASE WHEN excluded.name <> '' THEN excluded.name ELSE systems.name END,
                    last_seen=excluded.last_seen,
                    body_count=MAX(systems.body_count, excluded.body_count),
                    all_bodies_found=MAX(systems.all_bodies_found, excluded.all_bodies_found)
            """, (
                int(address), data.get("system") or "", seen, seen,
                int(data.get("system_body_count") or len(bodies)),
                self._bool_db(data.get("system_all_bodies_found")) or 0,
            ))

            for body in bodies:
                body_id = body.get("body_id")
                if body_id is None:
                    continue

                con.execute("""
                    INSERT INTO bodies (
                        system_address, body_id, name, short_name, body_type,
                        star_type, planet_class, parent_id, mass_em, stellar_mass,
                        gravity_g, distance_ls, landable, terraformable,
                        was_discovered, was_mapped, self_mapped, efficient_mapping,
                        atmosphere, volcanism, biological_signals, geological_signals,
                        scan_value, mapped_value, current_value, high_value,
                        first_seen, last_seen
                    ) VALUES (
                        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                    )
                    ON CONFLICT(system_address, body_id) DO UPDATE SET
                        name=excluded.name,
                        short_name=excluded.short_name,
                        body_type=excluded.body_type,
                        star_type=excluded.star_type,
                        planet_class=excluded.planet_class,
                        parent_id=excluded.parent_id,
                        mass_em=COALESCE(excluded.mass_em, bodies.mass_em),
                        stellar_mass=COALESCE(excluded.stellar_mass, bodies.stellar_mass),
                        gravity_g=COALESCE(excluded.gravity_g, bodies.gravity_g),
                        distance_ls=COALESCE(excluded.distance_ls, bodies.distance_ls),
                        landable=excluded.landable,
                        terraformable=excluded.terraformable,
                        was_discovered=COALESCE(excluded.was_discovered, bodies.was_discovered),
                        was_mapped=COALESCE(excluded.was_mapped, bodies.was_mapped),
                        self_mapped=MAX(bodies.self_mapped, excluded.self_mapped),
                        efficient_mapping=MAX(bodies.efficient_mapping, excluded.efficient_mapping),
                        atmosphere=CASE WHEN excluded.atmosphere <> '' THEN excluded.atmosphere ELSE bodies.atmosphere END,
                        volcanism=CASE WHEN excluded.volcanism <> '' THEN excluded.volcanism ELSE bodies.volcanism END,
                        biological_signals=MAX(bodies.biological_signals, excluded.biological_signals),
                        geological_signals=MAX(bodies.geological_signals, excluded.geological_signals),
                        scan_value=excluded.scan_value,
                        mapped_value=excluded.mapped_value,
                        current_value=excluded.current_value,
                        high_value=excluded.high_value,
                        last_seen=excluded.last_seen
                """, (
                    int(address), int(body_id), body.get("name") or "",
                    body.get("short_name") or "", body.get("body_type") or "",
                    body.get("star_type") or "", body.get("planet_class") or "",
                    body.get("parent_id"), body.get("mass_em"), body.get("stellar_mass"),
                    body.get("gravity_g"), body.get("distance_ls"),
                    self._bool_db(body.get("landable")) or 0,
                    self._bool_db(body.get("terraformable")) or 0,
                    self._bool_db(body.get("was_discovered")),
                    self._bool_db(body.get("was_mapped")),
                    self._bool_db(body.get("self_mapped")) or 0,
                    self._bool_db(body.get("efficient_mapping")) or 0,
                    body.get("atmosphere") or "", body.get("volcanism") or "",
                    int(body.get("biological_signals") or 0),
                    int(body.get("geological_signals") or 0),
                    int(body.get("scan_value") or 0), int(body.get("mapped_value") or 0),
                    int(body.get("current_value") or 0),
                    self._bool_db(body.get("high_value")) or 0, seen, seen
                ))

                for name, percentage in self._materials(body):
                    try:
                        percentage = float(percentage) if percentage is not None else None
                    except (TypeError, ValueError):
                        percentage = None
                    con.execute("""
                        INSERT INTO materials (
                            system_address, body_id, material_name, percentage
                        ) VALUES (?, ?, ?, ?)
                        ON CONFLICT(system_address, body_id, material_name)
                        DO UPDATE SET percentage=excluded.percentage
                    """, (int(address), int(body_id), str(name), percentage))

    def mark_journal_files(self, folder):
        folder = Path(folder)
        if not folder.exists():
            return
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connect() as con:
            for journal in sorted(folder.glob("Journal.*.log")):
                try:
                    stat = journal.stat()
                except OSError:
                    continue
                con.execute("""
                    INSERT INTO journal_imports (
                        journal_file, file_size, modified_ns, last_import
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(journal_file) DO UPDATE SET
                        file_size=excluded.file_size,
                        modified_ns=excluded.modified_ns,
                        last_import=excluded.last_import
                """, (str(journal), int(stat.st_size), int(stat.st_mtime_ns), now))


    def stats(self) -> dict:
        result = {}

        with self._connect() as con:
            for table in (
                "systems",
                "bodies",
                "materials",
                "journal_imports",
            ):
                result[table] = int(
                    con.execute(
                        f"SELECT COUNT(*) FROM {table}"
                    ).fetchone()[0]
                )

        return result

    @staticmethod
    def _system_address_from_event(event, current_address):
        value = event.get("SystemAddress")

        if isinstance(value, int):
            return value

        return current_address

    @staticmethod
    def _bio_geo_counts(event):
        bio = 0
        geo = 0

        for signal in event.get("Signals") or []:
            if not isinstance(signal, dict):
                continue

            signal_type = (
                signal.get("Type_Localised")
                or signal.get("Type")
                or ""
            ).lower()

            try:
                count = int(signal.get("Count") or 0)
            except Exception:
                count = 0

            if (
                "biological" in signal_type
                or "biologisch" in signal_type
                or "saa_signaltype_biological" in signal_type
            ):
                bio += count

            if (
                "geological" in signal_type
                or "geologisch" in signal_type
                or "saa_signaltype_geological" in signal_type
            ):
                geo += count

        if bio == 0 and event.get("Genuses"):
            bio = len(event.get("Genuses") or [])

        return bio, geo

    def _journal_needs_import(self, journal: Path) -> bool:
        try:
            stat = journal.stat()
        except OSError:
            return False

        with self._connect() as con:
            row = con.execute(
                """
                SELECT file_size, modified_ns
                FROM journal_imports
                WHERE journal_file = ?
                """,
                (str(journal),),
            ).fetchone()

        if row is None:
            return True

        old_size, old_modified_ns = row

        return not (
            int(old_size) == int(stat.st_size)
            and int(old_modified_ns) == int(stat.st_mtime_ns)
        )

    def import_journal_archive(
        self,
        folder,
        progress_callback=None,
    ) -> dict:
        """
        Liest das vorhandene Journalarchiv chronologisch und baut
        das persönliche System-/Körperarchiv auf.

        Bestehende Datensätze werden per UPSERT ergänzt.
        Der aktuelle Live-Betrieb bleibt davon unabhängig.
        """
        folder = Path(folder)

        if not folder.exists():
            raise FileNotFoundError(
                f"Journalordner nicht gefunden: {folder}"
            )

        all_journals = sorted(
            folder.glob("Journal.*.log")
        )

        journals = [
            journal
            for journal in all_journals
            if self._journal_needs_import(journal)
        ]

        skipped_count = (
            len(all_journals)
            - len(journals)
        )

        current_system = ""
        current_address = None

        # Temporärer Importzustand
        systems = {}
        bodies = {}
        pending_bio = {}
        pending_geo = {}

        def ensure_system(address, name="", timestamp=""):
            if address is None:
                return None

            entry = systems.setdefault(
                int(address),
                {
                    "name": name or "",
                    "first_seen": timestamp or "",
                    "last_seen": timestamp or "",
                    "body_count": 0,
                    "all_bodies_found": False,
                },
            )

            if name:
                entry["name"] = name

            if timestamp:
                if not entry["first_seen"]:
                    entry["first_seen"] = timestamp
                entry["last_seen"] = timestamp

            return entry

        total = len(journals)

        if total == 0:
            stats = self.stats()
            stats["imported_journals"] = 0
            stats["skipped_journals"] = skipped_count
            return stats

        for index, journal in enumerate(journals, start=1):
            current_line_number = 0
            current_event_name = ""

            if progress_callback:
                progress_callback(
                    index,
                    total,
                    journal.name,
                )

            try:
                handle = journal.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                continue

            try:
                with handle:
                    for current_line_number, line in enumerate(
                        handle,
                        start=1,
                    ):
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            # Einzelne beschädigte JSON-Zeilen bleiben wie bisher
                            # toleriert und stoppen den Archivimport nicht.
                            continue

                        et = event.get("event")
                        current_event_name = str(et or "")
                        ts = event.get("timestamp") or ""

                        if et in (
                            "Location",
                            "FSDJump",
                            "CarrierJump",
                            "Docked",
                        ):
                            name = (
                                event.get("StarSystem")
                                or current_system
                            )

                            address = event.get(
                                "SystemAddress"
                            )

                            if isinstance(address, int):
                                current_address = address

                            current_system = name or current_system

                            ensure_system(
                                current_address,
                                current_system,
                                ts,
                            )

                        elif et == "FSSDiscoveryScan":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )

                            entry = ensure_system(
                                address,
                                current_system,
                                ts,
                            )

                            if (
                                entry is not None
                                and isinstance(
                                    event.get("BodyCount"),
                                    int,
                                )
                            ):
                                entry["body_count"] = max(
                                    int(entry["body_count"]),
                                    int(event["BodyCount"]),
                                )

                        elif et == "FSSAllBodiesFound":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )

                            entry = ensure_system(
                                address,
                                current_system,
                                ts,
                            )

                            if entry is not None:
                                entry["all_bodies_found"] = True

                                if isinstance(
                                    event.get("Count"),
                                    int,
                                ):
                                    entry["body_count"] = max(
                                        int(entry["body_count"]),
                                        int(event["Count"]),
                                    )

                        elif et == "Scan":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )
                            body_id = event.get("BodyID")

                            if (
                                address is None
                                or body_id is None
                            ):
                                continue

                            try:
                                body_id = int(body_id)
                            except Exception:
                                continue

                            ensure_system(
                                address,
                                current_system,
                                ts,
                            )

                            parents = event.get("Parents") or []
                            parent_id = None

                            if parents:
                                try:
                                    parent_id = int(
                                        next(
                                            iter(
                                                parents[-1].values()
                                            )
                                        )
                                    )
                                except Exception:
                                    parent_id = None

                            raw_gravity = event.get(
                                "SurfaceGravity"
                            )
                            gravity_g = None

                            if isinstance(
                                raw_gravity,
                                (int, float),
                            ):
                                gravity_g = (
                                    float(raw_gravity)
                                    / 9.80665
                                )

                            body_name = (
                                event.get("BodyName")
                                or ""
                            )

                            short_name = body_name

                            if (
                                current_system
                                and body_name.startswith(
                                    current_system
                                )
                            ):
                                short_name = (
                                    body_name[
                                        len(current_system):
                                    ].strip()
                                    or body_name
                                )

                            key = (
                                int(address),
                                body_id,
                            )

                            previous = bodies.get(
                                key,
                                {},
                            )

                            body = {
                                "body_id": body_id,
                                "name": body_name,
                                "short_name": short_name,
                                "body_type": (
                                    "Star"
                                    if event.get("StarType")
                                    else "Planet"
                                ),
                                "star_type": (
                                    event.get("StarType")
                                    or ""
                                ),
                                "planet_class": (
                                    event.get("PlanetClass")
                                    or ""
                                ),
                                "parent_id": parent_id,
                                "mass_em": event.get(
                                    "MassEM"
                                ),
                                "stellar_mass": event.get(
                                    "StellarMass"
                                ),
                                "gravity_g": gravity_g,
                                "distance_ls": event.get(
                                    "DistanceFromArrivalLS"
                                ),
                                "landable": bool(
                                    event.get(
                                        "Landable",
                                        False,
                                    )
                                ),
                                "terraformable": (
                                    event.get(
                                        "TerraformState"
                                    )
                                    == "Terraformable"
                                ),
                                "was_discovered": event.get(
                                    "WasDiscovered"
                                ),
                                "was_mapped": event.get(
                                    "WasMapped"
                                ),
                                "self_mapped": bool(
                                    previous.get(
                                        "self_mapped"
                                    )
                                ),
                                "efficient_mapping": bool(
                                    previous.get(
                                        "efficient_mapping"
                                    )
                                ),
                                "atmosphere": (
                                    event.get(
                                        "Atmosphere_Localised"
                                    )
                                    or event.get("Atmosphere")
                                    or ""
                                ),
                                "volcanism": (
                                    event.get(
                                        "Volcanism_Localised"
                                    )
                                    or event.get("Volcanism")
                                    or ""
                                ),
                                "materials": (
                                    event.get("Materials")
                                    or previous.get(
                                        "materials",
                                        {},
                                    )
                                    or {}
                                ),
                                "biological_signals": max(
                                    int(
                                        previous.get(
                                            "biological_signals"
                                        )
                                        or 0
                                    ),
                                    int(
                                        pending_bio.get(
                                            key,
                                            0,
                                        )
                                    ),
                                ),
                                "geological_signals": max(
                                    int(
                                        previous.get(
                                            "geological_signals"
                                        )
                                        or 0
                                    ),
                                    int(
                                        pending_geo.get(
                                            key,
                                            0,
                                        )
                                    ),
                                ),
                                "first_seen": (
                                    previous.get(
                                        "first_seen"
                                    )
                                    or ts
                                ),
                                "last_seen": ts,
                            }

                            # Bewertung wird bewusst lokal nachgebildet,
                            # indem die schon gespeicherten Wertfelder
                            # zunächst auf 0 gesetzt werden. Der Live-
                            # Betrieb aktualisiert sie später regulär.
                            body.setdefault(
                                "scan_value",
                                previous.get(
                                    "scan_value",
                                    0,
                                ),
                            )
                            body.setdefault(
                                "mapped_value",
                                previous.get(
                                    "mapped_value",
                                    0,
                                ),
                            )
                            body.setdefault(
                                "current_value",
                                previous.get(
                                    "current_value",
                                    0,
                                ),
                            )
                            body.setdefault(
                                "high_value",
                                previous.get(
                                    "high_value",
                                    False,
                                ),
                            )

                            bodies[key] = body

                        elif et == "SAAScanComplete":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )
                            body_id = event.get("BodyID")

                            if (
                                address is None
                                or body_id is None
                            ):
                                continue

                            try:
                                key = (
                                    int(address),
                                    int(body_id),
                                )
                            except Exception:
                                continue

                            body = bodies.get(key)

                            if body:
                                body["self_mapped"] = True
                                body["last_seen"] = ts

                                probes_used = event.get(
                                    "ProbesUsed"
                                )
                                efficiency_target = event.get(
                                    "EfficiencyTarget"
                                )

                                if (
                                    isinstance(
                                        probes_used,
                                        int,
                                    )
                                    and isinstance(
                                        efficiency_target,
                                        int,
                                    )
                                ):
                                    body[
                                        "efficient_mapping"
                                    ] = (
                                        probes_used
                                        <= efficiency_target
                                    )

                        elif et in (
                            "SAASignalsFound",
                            "FSSBodySignals",
                        ):
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )
                            body_id = event.get("BodyID")

                            if (
                                address is None
                                or body_id is None
                            ):
                                continue

                            try:
                                key = (
                                    int(address),
                                    int(body_id),
                                )
                            except Exception:
                                continue

                            bio, geo = self._bio_geo_counts(
                                event
                            )

                            pending_bio[key] = max(
                                int(
                                    pending_bio.get(
                                        key,
                                        0,
                                    )
                                ),
                                bio,
                            )

                            pending_geo[key] = max(
                                int(
                                    pending_geo.get(
                                        key,
                                        0,
                                    )
                                ),
                                geo,
                            )

                            body = bodies.get(key)

                            if body:
                                body[
                                    "biological_signals"
                                ] = max(
                                    int(
                                        body.get(
                                            "biological_signals"
                                        )
                                        or 0
                                    ),
                                    bio,
                                )

                                body[
                                    "geological_signals"
                                ] = max(
                                    int(
                                        body.get(
                                            "geological_signals"
                                        )
                                        or 0
                                    ),
                                    geo,
                                )

                        elif et == "ScanOrganic":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )
                            body_id = event.get("BodyID")

                            if (
                                address is None
                                or body_id is None
                            ):
                                continue

                            try:
                                key = (
                                    int(address),
                                    int(body_id),
                                )
                            except Exception:
                                continue

                            pending_bio[key] = max(
                                1,
                                int(
                                    pending_bio.get(
                                        key,
                                        0,
                                    )
                                ),
                            )

                            if key in bodies:
                                bodies[key][
                                    "biological_signals"
                                ] = max(
                                    1,
                                    int(
                                        bodies[key].get(
                                            "biological_signals"
                                        )
                                        or 0
                                    ),
                                )

            except Exception as exc:
                event_text = (
                    current_event_name
                    or "unbekannt"
                )
                raise RuntimeError(
                    "Fehler beim Journal-Import\n"
                    f"Datei: {journal.name}\n"
                    f"Zeile: {current_line_number}\n"
                    f"Event: {event_text}\n"
                    f"Fehler: {type(exc).__name__}: {exc}"
                ) from exc

            try:
                stat = journal.stat()
            except OSError:
                stat = None

            if stat is not None:
                now = (
                    datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

                with self._connect() as con:
                    con.execute(
                        """
                        INSERT INTO journal_imports (
                            journal_file,
                            file_size,
                            modified_ns,
                            last_import
                        )
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(journal_file)
                        DO UPDATE SET
                            file_size=excluded.file_size,
                            modified_ns=excluded.modified_ns,
                            last_import=excluded.last_import
                        """,
                        (
                            str(journal),
                            int(stat.st_size),
                            int(stat.st_mtime_ns),
                            now,
                        ),
                    )

        # Persist all collected systems and bodies.
        for address, system in systems.items():
            system_bodies = [
                body
                for (
                    body_address,
                    _body_id,
                ), body in bodies.items()
                if body_address == address
            ]

            snapshot = {
                "system_address": address,
                "system": system.get(
                    "name",
                    "",
                ),
                "last_timestamp": system.get(
                    "last_seen",
                    "",
                ),
                "system_body_count": max(
                    int(
                        system.get(
                            "body_count",
                            0,
                        )
                    ),
                    len(system_bodies),
                ),
                "system_all_bodies_found": bool(
                    system.get(
                        "all_bodies_found",
                        False,
                    )
                ),
                "system_bodies": system_bodies,
            }

            self.store_snapshot(snapshot)

        stats = self.stats()
        stats["imported_journals"] = total
        stats["skipped_journals"] = skipped_count
        return stats
