from __future__ import annotations

import sqlite3
import logging
import json
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

def _direct_parent_id(parents) -> int | None:
    """
    Ermittelt aus Elite-Dangerous-Parents den für CMDRHelper sinnvollsten
    direkten darstellbaren Elternkörper.

    Frontier liefert die Hierarchie vom nahen zum weiter entfernten Parent.
    Planet/Star sind für unsere Systemkarte darstellbar; Null (Barycentre)
    und Ring werden übersprungen.
    """
    if not isinstance(parents, list):
        return None

    for parent in parents:
        if not isinstance(parent, dict):
            continue

        for parent_type, value in parent.items():
            if parent_type not in ("Planet", "Star"):
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

    return None



def default_database_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "cmdrhelper.db"


class CMDRDatabase:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Datenbank: %s", self.path)
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
                    all_bodies_found INTEGER NOT NULL DEFAULT 0,
                    x REAL,
                    y REAL,
                    z REAL
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

                CREATE TABLE IF NOT EXISTS biology (
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    genus TEXT NOT NULL DEFAULT '',
                    species TEXT NOT NULL DEFAULT '',
                    variant TEXT NOT NULL DEFAULT '',
                    scan_type TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (system_address, body_id, genus, species, variant)
                );

                CREATE TABLE IF NOT EXISTS geology (
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    name TEXT NOT NULL DEFAULT '',
                    raw_name TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (
                        system_address,
                        body_id,
                        name,
                        source
                    )
                );

                CREATE INDEX IF NOT EXISTS idx_geology_body
                    ON geology(system_address, body_id);

                CREATE TABLE IF NOT EXISTS codex_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_address INTEGER,
                    system_name TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT '',
                    subcategory TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL DEFAULT '',
                    raw_name TEXT NOT NULL DEFAULT '',
                    nearest_destination TEXT NOT NULL DEFAULT '',
                    region TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    UNIQUE(
                        system_address,
                        category,
                        subcategory,
                        name,
                        nearest_destination,
                        event_type
                    )
                );

                CREATE INDEX IF NOT EXISTS idx_codex_system
                    ON codex_entries(system_address);

                CREATE INDEX IF NOT EXISTS idx_codex_name
                    ON codex_entries(name);

                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS system_visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_address INTEGER NOT NULL,
                    system_name TEXT NOT NULL DEFAULT '',
                    visited_at TEXT NOT NULL DEFAULT '',
                    x REAL,
                    y REAL,
                    z REAL,
                    UNIQUE(system_address, visited_at)
                );

                CREATE INDEX IF NOT EXISTS idx_system_visits_time
                    ON system_visits(visited_at);

                CREATE TABLE IF NOT EXISTS journal_imports (
                    journal_file TEXT PRIMARY KEY,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_import TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS learned_bio_values (
                    species TEXT PRIMARY KEY COLLATE NOCASE,
                    genus TEXT NOT NULL DEFAULT '',
                    base_value INTEGER NOT NULL DEFAULT 0,
                    last_bonus INTEGER NOT NULL DEFAULT 0,
                    last_total INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT 'SellOrganicData'
                );

                CREATE TABLE IF NOT EXISTS bio_value_journal_scans (
                    journal_file TEXT PRIMARY KEY,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_scan TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS cartography_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_file TEXT NOT NULL DEFAULT '',
                    event_timestamp TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL DEFAULT '',
                    base_value INTEGER NOT NULL DEFAULT 0,
                    bonus INTEGER NOT NULL DEFAULT 0,
                    total_earnings INTEGER NOT NULL DEFAULT 0,
                    estimated_total INTEGER NOT NULL DEFAULT 0,
                    correction_factor REAL,
                    body_count INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL DEFAULT '',
                    UNIQUE(journal_file, event_timestamp, event_type)
                );

                CREATE TABLE IF NOT EXISTS cartography_sale_bodies (
                    sale_id INTEGER NOT NULL,
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    body_name TEXT NOT NULL DEFAULT '',
                    body_type TEXT NOT NULL DEFAULT '',
                    star_type TEXT NOT NULL DEFAULT '',
                    planet_class TEXT NOT NULL DEFAULT '',
                    mass_em REAL,
                    stellar_mass REAL,
                    terraformable INTEGER NOT NULL DEFAULT 0,
                    was_discovered INTEGER,
                    was_mapped INTEGER,
                    self_mapped INTEGER NOT NULL DEFAULT 0,
                    efficient_mapping INTEGER NOT NULL DEFAULT 0,
                    estimated_value INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (sale_id, system_address, body_id),
                    FOREIGN KEY (sale_id) REFERENCES cartography_sales(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_cartography_sale_bodies_class
                    ON cartography_sale_bodies(planet_class);

                CREATE TABLE IF NOT EXISTS cartography_value_journal_scans (
                    journal_file TEXT PRIMARY KEY,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_scan TEXT NOT NULL DEFAULT ''
                );
            """)

            columns = {
                row[1] for row in con.execute("PRAGMA table_info(systems)").fetchall()
            }
            for column in ("x", "y", "z"):
                if column not in columns:
                    con.execute(f"ALTER TABLE systems ADD COLUMN {column} REAL")

            discovery_index = con.execute(
                "SELECT value FROM app_meta WHERE key=?",
                ("discovery_index_version",),
            ).fetchone()

            if discovery_index is None or discovery_index[0] != "3":
                con.execute("DELETE FROM journal_imports")
                con.execute("DELETE FROM geology")
                con.execute(
                    """
                    INSERT INTO app_meta (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                    """,
                    ("discovery_index_version", "3"),
                )

            schema_version = int(
                con.execute("PRAGMA user_version").fetchone()[0]
            )

            if schema_version < 1:
                # Version 1 ist bewusst rein additiv: Die vorhandenen
                # fachlichen Tabellen und deren Daten bleiben unverändert.
                con.execute(
                    """
                    CREATE TABLE IF NOT EXISTS commanders (
                        id INTEGER PRIMARY KEY,
                        fid TEXT NOT NULL UNIQUE,
                        current_name TEXT,
                        first_seen TEXT,
                        last_seen TEXT
                    )
                    """
                )
                con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def upsert_commander(self, fid, current_name="", timestamp="") -> int | None:
        """Legt eine per Frontier-FID identifizierte Identität an/aktualisiert sie."""
        fid = str(fid or "").strip()
        if not fid:
            return None

        current_name = str(current_name or "").strip()
        seen = str(timestamp or "").strip() or (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO commanders (
                    fid, current_name, first_seen, last_seen
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(fid) DO UPDATE SET
                    current_name=CASE
                        WHEN excluded.current_name <> ''
                        THEN excluded.current_name
                        ELSE commanders.current_name
                    END,
                    last_seen=excluded.last_seen
                """,
                (fid, current_name, seen, seen),
            )
            row = con.execute(
                "SELECT id FROM commanders WHERE fid = ?",
                (fid,),
            ).fetchone()

        return int(row[0]) if row is not None else None

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
                    body_count, all_bodies_found, x, y, z
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address) DO UPDATE SET
                    name=CASE WHEN excluded.name <> '' THEN excluded.name ELSE systems.name END,
                    last_seen=excluded.last_seen,
                    body_count=MAX(systems.body_count, excluded.body_count),
                    all_bodies_found=MAX(systems.all_bodies_found, excluded.all_bodies_found),
                    x=COALESCE(excluded.x, systems.x),
                    y=COALESCE(excluded.y, systems.y),
                    z=COALESCE(excluded.z, systems.z)
            """, (
                int(address), data.get("system") or "", seen, seen,
                int(data.get("system_body_count") or len(bodies)),
                self._bool_db(data.get("system_all_bodies_found")) or 0,
                (data.get("star_pos") or [None, None, None])[0],
                (data.get("star_pos") or [None, None, None])[1],
                (data.get("star_pos") or [None, None, None])[2],
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

    def store_biology(self, system_address, body_id, genus="", species="",
                      variant="", scan_type="", timestamp=""):
        if system_address is None or body_id is None:
            return
        if not (genus or species or variant):
            return
        seen = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connect() as con:
            con.execute("""
                INSERT INTO biology (
                    system_address, body_id, genus, species, variant,
                    scan_type, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address, body_id, genus, species, variant)
                DO UPDATE SET
                    scan_type=CASE WHEN excluded.scan_type <> ''
                                   THEN excluded.scan_type ELSE biology.scan_type END,
                    last_seen=excluded.last_seen
            """, (int(system_address), int(body_id), str(genus or ""),
                  str(species or ""), str(variant or ""), str(scan_type or ""),
                  seen, seen))

    def biology_for_body(self, system_address, body_id):
        if system_address is None or body_id is None:
            return []
        with self._connect() as con:
            rows = con.execute("""
                SELECT genus, species, variant, scan_type, first_seen, last_seen
                FROM biology
                WHERE system_address=? AND body_id=?
                ORDER BY variant COLLATE NOCASE, species COLLATE NOCASE,
                         genus COLLATE NOCASE
            """, (int(system_address), int(body_id))).fetchall()
        return [
            {"genus": r[0], "species": r[1], "variant": r[2],
             "scan_type": r[3], "first_seen": r[4], "last_seen": r[5]}
            for r in rows
        ]

    def biology_for_system(self, system_address):
        if system_address is None:
            return []

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT body_id, genus, species, variant,
                       scan_type, first_seen, last_seen
                FROM biology
                WHERE system_address=?
                ORDER BY body_id,
                         species COLLATE NOCASE,
                         variant COLLATE NOCASE
                """,
                (int(system_address),),
            ).fetchall()

        return [
            {
                "body_id": row[0],
                "genus": row[1],
                "species": row[2],
                "variant": row[3],
                "scan_type": row[4],
                "first_seen": row[5],
                "last_seen": row[6],
            }
            for row in rows
        ]

    @staticmethod
    def _bio_sale_name(item):
        if not isinstance(item, dict):
            return "", ""

        genus = (
            item.get("Genus_Localised")
            or item.get("Genus")
            or item.get("genus")
            or ""
        )

        species = (
            item.get("Species_Localised")
            or item.get("Species")
            or item.get("species")
            or item.get("Variant_Localised")
            or item.get("Variant")
            or item.get("variant")
            or ""
        )

        return str(genus or "").strip(), str(species or "").strip()

    def learned_bio_values(self):
        """
        Liefert vom eigenen Commander tatsächlich verkaufte BIO-Basiswerte.

        Diese Werte stammen direkt aus SellOrganicData und haben bei der
        Schätzung Vorrang vor der statischen Referenztabelle.
        """
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT species, base_value
                FROM learned_bio_values
                WHERE species <> '' AND base_value > 0
                ORDER BY species COLLATE NOCASE
                """
            ).fetchall()

        return {
            str(species): int(value or 0)
            for species, value in rows
        }

    def learned_bio_value_details(self):
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT species, genus, base_value,
                       last_bonus, last_total,
                       first_seen, last_seen, source
                FROM learned_bio_values
                ORDER BY species COLLATE NOCASE
                """
            ).fetchall()

        return [
            {
                "species": row[0],
                "genus": row[1],
                "base_value": int(row[2] or 0),
                "last_bonus": int(row[3] or 0),
                "last_total": int(row[4] or 0),
                "first_seen": row[5] or "",
                "last_seen": row[6] or "",
                "source": row[7] or "",
            }
            for row in rows
        ]

    def learn_bio_values_from_journals(self, folder):
        """
        Lernt Vista-Genomics-Basiswerte direkt aus SellOrganicData.

        Es werden nur neue/geänderte Journaldateien eingelesen. Dadurch kann
        die Methode bei jedem normalen State-Refresh aufgerufen werden, ohne
        jedes Mal das komplette Journalarchiv erneut zu parsen.

        Rückgabe:
            {
                "files_scanned": int,
                "sales_found": int,
                "values_changed": int,
            }
        """
        folder = Path(folder)

        result = {
            "files_scanned": 0,
            "sales_found": 0,
            "values_changed": 0,
        }

        if not folder.is_dir():
            return result

        journals = sorted(
            folder.glob("Journal.*.log")
        )

        if not journals:
            return result

        with self._connect() as con:
            scan_rows = con.execute(
                """
                SELECT journal_file, file_size, modified_ns
                FROM bio_value_journal_scans
                """
            ).fetchall()

        scanned = {
            str(row[0]): (
                int(row[1]),
                int(row[2]),
            )
            for row in scan_rows
        }

        changed_files = []

        for journal in journals:
            try:
                stat = journal.stat()
            except OSError:
                continue

            previous = scanned.get(
                str(journal)
            )

            if previous is not None:
                old_size, old_modified_ns = previous

                if (
                    int(old_size) == int(stat.st_size)
                    and int(old_modified_ns) == int(stat.st_mtime_ns)
                ):
                    continue

            changed_files.append(
                (
                    journal,
                    int(stat.st_size),
                    int(stat.st_mtime_ns),
                )
            )

        if not changed_files:
            return result

        now = (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        learned = []

        for journal, file_size, modified_ns in changed_files:
            result["files_scanned"] += 1

            try:
                handle = journal.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                continue

            with handle:
                for line in handle:
                    # Billiger Vorfilter: die meisten Journalzeilen müssen
                    # nicht durch json.loads().
                    if '"event":"SellOrganicData"' not in line:
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if event.get("event") != "SellOrganicData":
                        continue

                    timestamp = (
                        event.get("timestamp")
                        or now
                    )

                    items = (
                        event.get("BioData")
                        or event.get("Data")
                        or event.get("OrganicData")
                        or []
                    )

                    if not isinstance(items, list):
                        continue

                    for item in items:
                        genus, species = self._bio_sale_name(
                            item
                        )

                        if not species:
                            continue

                        try:
                            value = int(
                                item.get("Value")
                                or item.get("value")
                                or 0
                            )
                        except (TypeError, ValueError):
                            value = 0

                        try:
                            bonus = int(
                                item.get("Bonus")
                                or item.get("bonus")
                                or 0
                            )
                        except (TypeError, ValueError):
                            bonus = 0

                        if value <= 0:
                            continue

                        result["sales_found"] += 1

                        learned.append(
                            (
                                species,
                                genus,
                                value,
                                bonus,
                                value + bonus,
                                timestamp,
                                timestamp,
                                "SellOrganicData",
                            )
                        )

            # Datei erst nach erfolgreichem Lesen markieren.
            with self._connect() as con:
                con.execute(
                    """
                    INSERT INTO bio_value_journal_scans (
                        journal_file, file_size,
                        modified_ns, last_scan
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(journal_file)
                    DO UPDATE SET
                        file_size=excluded.file_size,
                        modified_ns=excluded.modified_ns,
                        last_scan=excluded.last_scan
                    """,
                    (
                        str(journal),
                        file_size,
                        modified_ns,
                        now,
                    ),
                )

        if not learned:
            return result

        with self._connect() as con:
            for row in learned:
                (
                    species,
                    genus,
                    value,
                    bonus,
                    total,
                    first_seen,
                    last_seen,
                    source,
                ) = row

                previous = con.execute(
                    """
                    SELECT base_value
                    FROM learned_bio_values
                    WHERE species = ? COLLATE NOCASE
                    """,
                    (species,),
                ).fetchone()

                previous_value = (
                    int(previous[0])
                    if previous is not None
                    else None
                )

                con.execute(
                    """
                    INSERT INTO learned_bio_values (
                        species, genus, base_value,
                        last_bonus, last_total,
                        first_seen, last_seen, source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(species)
                    DO UPDATE SET
                        genus=CASE
                            WHEN excluded.genus <> ''
                            THEN excluded.genus
                            ELSE learned_bio_values.genus
                        END,
                        base_value=excluded.base_value,
                        last_bonus=excluded.last_bonus,
                        last_total=excluded.last_total,
                        last_seen=excluded.last_seen,
                        source=excluded.source
                    """,
                    row,
                )

                if (
                    previous_value is None
                    or previous_value != value
                ):
                    result["values_changed"] += 1

        if result["sales_found"]:
            logger.info(
                "BIO-Werte gelernt: %s Verkaufseinträge, "
                "%s neue/geänderte Artwerte aus %s Journaldatei(en)",
                result["sales_found"],
                result["values_changed"],
                result["files_scanned"],
            )

        return result

    @staticmethod
    def _cartography_sale_amounts(event):
        def _int_value(*names):
            for name in names:
                value = event.get(name)
                if value is None:
                    continue
                try:
                    return int(value)
                except (TypeError, ValueError):
                    continue
            return 0

        base_value = max(0, _int_value("BaseValue", "Value"))
        bonus = max(0, _int_value("Bonus"))
        total_earnings = max(
            0,
            _int_value("TotalEarnings", "TotalValue", "Total"),
        )

        if total_earnings <= 0:
            total_earnings = max(0, base_value + bonus)

        return base_value, bonus, total_earnings

    def cartography_learning_stats(self):
        with self._connect() as con:
            sales = int(
                con.execute(
                    "SELECT COUNT(*) FROM cartography_sales"
                ).fetchone()[0]
            )
            bodies = int(
                con.execute(
                    "SELECT COUNT(*) FROM cartography_sale_bodies"
                ).fetchone()[0]
            )

            row = con.execute(
                """
                SELECT
                    SUM(
                        CASE
                            WHEN base_value > 0 THEN base_value
                            ELSE total_earnings
                        END
                    ),
                    SUM(estimated_total)
                FROM cartography_sales
                WHERE estimated_total > 0
                  AND (base_value > 0 OR total_earnings > 0)
                """
            ).fetchone()

        actual = int((row or (0, 0))[0] or 0)
        estimated = int((row or (0, 0))[1] or 0)

        return {
            "sales": sales,
            "bodies": bodies,
            "actual_total": actual,
            "estimated_total": estimated,
            "correction_factor": (
                actual / estimated
                if estimated > 0
                else 1.0
            ),
        }

    def learned_cartography_factor(
        self,
        planet_class="",
        terraformable=None,
    ):
        """
        Liefert einen aus echten Universal-Cartographics-Verkäufen
        abgeleiteten Korrekturfaktor.

        Frontier gibt bei MultiSellExplorationData keinen Einzelpreis je
        Körper aus. Deshalb bleibt der Verkauf als Batch die Wahrheit.
        Für Körperklassen verwenden wir den Batch-Faktor nur dann speziell,
        wenn mindestens drei passende Körper in der Lerndatenbank vorhanden
        sind. Ansonsten gilt der globale Faktor. Ohne Lerndaten ist er 1.0.
        """
        planet_class = str(planet_class or "").strip()

        with self._connect() as con:
            params = []
            where = [
                "s.estimated_total > 0",
                "(s.base_value > 0 OR s.total_earnings > 0)",
                "b.estimated_value > 0",
                "b.body_type <> 'Star'",
                "b.star_type = ''",
            ]

            if planet_class:
                where.append("b.planet_class = ? COLLATE NOCASE")
                params.append(planet_class)

            if terraformable is not None:
                where.append("b.terraformable = ?")
                params.append(1 if terraformable else 0)

            row = con.execute(
                f"""
                SELECT
                    COUNT(*),
                    SUM(
                        b.estimated_value
                        * (
                            CASE
                                WHEN s.base_value > 0 THEN s.base_value
                                ELSE s.total_earnings
                            END
                        )
                        / CAST(s.estimated_total AS REAL)
                    ),
                    SUM(b.estimated_value)
                FROM cartography_sale_bodies AS b
                JOIN cartography_sales AS s
                  ON s.id = b.sale_id
                WHERE {' AND '.join(where)}
                """,
                params,
            ).fetchone()

            count = int((row or (0, 0, 0))[0] or 0)
            learned_actual = float((row or (0, 0, 0))[1] or 0.0)
            learned_estimated = float((row or (0, 0, 0))[2] or 0.0)

            if count >= 3 and learned_estimated > 0:
                factor = learned_actual / learned_estimated
            else:
                global_row = con.execute(
                    """
                    SELECT
                        SUM(
                            CASE
                                WHEN base_value > 0 THEN base_value
                                ELSE total_earnings
                            END
                        ),
                        SUM(estimated_total)
                    FROM cartography_sales
                    WHERE estimated_total > 0
                      AND (base_value > 0 OR total_earnings > 0)
                    """
                ).fetchone()

                actual = float((global_row or (0, 0))[0] or 0.0)
                estimated = float((global_row or (0, 0))[1] or 0.0)

                factor = (
                    actual / estimated
                    if estimated > 0
                    else 1.0
                )

        # Gleicher Sicherheitsrahmen wie in valuation.py.
        return min(2.0, max(0.5, float(factor or 1.0)))

    def learn_cartography_values_from_journals(
        self,
        folder,
        valuation_func=None,
    ):
        """
        Rekonstruiert Verkaufs-Batches aus den Journalen und speichert
        Formel-Schätzung + echten Universal-Cartographics-Wert.

        Wichtig:
        MultiSellExplorationData liefert keinen Einzelwert je Körper.
        Deshalb werden keine erfundenen "Ist-Werte" pro Körper gespeichert.
        Die Körperdaten dienen nur als Merkmale des jeweiligen Verkaufs-Batches.
        """
        folder = Path(folder)

        result = {
            "files_scanned": 0,
            "sales_found": 0,
            "sales_stored": 0,
            "bodies_stored": 0,
        }

        if not folder.is_dir():
            return result

        journals = sorted(folder.glob("Journal.*.log"))
        if not journals:
            return result

        with self._connect() as con:
            scan_rows = con.execute(
                """
                SELECT journal_file, file_size, modified_ns
                FROM cartography_value_journal_scans
                """
            ).fetchall()

        scanned = {
            str(row[0]): (int(row[1]), int(row[2]))
            for row in scan_rows
        }

        changed_files = []

        for journal in journals:
            try:
                stat = journal.stat()
            except OSError:
                continue

            signature = (
                int(stat.st_size),
                int(stat.st_mtime_ns),
            )

            if scanned.get(str(journal)) == signature:
                continue

            changed_files.append(
                (
                    journal,
                    signature[0],
                    signature[1],
                )
            )

        if not changed_files:
            return result

        changed_names = {
            str(journal)
            for journal, _size, _modified in changed_files
        }

        # Der offene Verkaufstopf wird bewusst über ALLE Journale
        # rekonstruiert. Sonst könnte ein Verkauf in einer neuen Datei
        # Scans aus einer älteren Datei verlieren.
        open_bodies = {}
        current_address = None

        for journal in journals:
            is_changed = str(journal) in changed_names

            if is_changed:
                result["files_scanned"] += 1

            try:
                handle = journal.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                continue

            with handle:
                for line in handle:
                    if not any(
                        token in line
                        for token in (
                            '"event":"Location"',
                            '"event":"FSDJump"',
                            '"event":"CarrierJump"',
                            '"event":"Scan"',
                            '"event":"SAAScanComplete"',
                            '"event":"SellExplorationData"',
                            '"event":"MultiSellExplorationData"',
                        )
                    ):
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("event")
                    timestamp = event.get("timestamp") or ""

                    if event_type in (
                        "Location",
                        "FSDJump",
                        "CarrierJump",
                    ):
                        address = event.get("SystemAddress")
                        if isinstance(address, int):
                            current_address = address
                        continue

                    if event_type == "Scan":
                        address = event.get("SystemAddress")
                        if not isinstance(address, int):
                            address = current_address

                        body_id = event.get("BodyID")

                        if address is None or body_id is None:
                            continue

                        body_name = str(
                            event.get("BodyName")
                            or ""
                        )

                        # Belt Cluster zahlen nicht wie normale Körper.
                        if "belt cluster" in body_name.lower():
                            continue

                        try:
                            key = (
                                int(address),
                                int(body_id),
                            )
                        except (TypeError, ValueError):
                            continue

                        previous = open_bodies.get(
                            key,
                            {},
                        )

                        body = {
                            "system_address": int(address),
                            "body_id": int(body_id),
                            "name": body_name,
                            "body_type": (
                                "Star"
                                if event.get("StarType")
                                else "Planet"
                            ),
                            "star_type": event.get("StarType") or "",
                            "planet_class": event.get("PlanetClass") or "",
                            "mass_em": event.get("MassEM"),
                            "stellar_mass": event.get("StellarMass"),
                            "terraformable": (
                                event.get("TerraformState")
                                == "Terraformable"
                            ),
                            "was_discovered": event.get("WasDiscovered"),
                            "was_mapped": event.get("WasMapped"),
                            "self_mapped": bool(
                                previous.get("self_mapped")
                            ),
                            "efficient_mapping": bool(
                                previous.get("efficient_mapping")
                            ),
                        }

                        if callable(valuation_func):
                            try:
                                values = valuation_func(
                                    dict(body)
                                )
                            except Exception:
                                values = {}
                        else:
                            values = {}

                        body["estimated_value"] = int(
                            values.get("current_value")
                            or 0
                        )

                        open_bodies[key] = body
                        continue

                    if event_type == "SAAScanComplete":
                        address = event.get("SystemAddress")
                        if not isinstance(address, int):
                            address = current_address

                        body_id = event.get("BodyID")

                        try:
                            key = (
                                int(address),
                                int(body_id),
                            )
                        except (TypeError, ValueError):
                            continue

                        body = open_bodies.get(key)
                        if body is None:
                            continue

                        body["self_mapped"] = True

                        probes_used = event.get("ProbesUsed")
                        efficiency_target = event.get("EfficiencyTarget")

                        body["efficient_mapping"] = bool(
                            isinstance(probes_used, int)
                            and isinstance(efficiency_target, int)
                            and probes_used <= efficiency_target
                        )

                        if callable(valuation_func):
                            try:
                                values = valuation_func(
                                    dict(body)
                                )
                            except Exception:
                                values = {}
                        else:
                            values = {}

                        body["estimated_value"] = int(
                            values.get("current_value")
                            or 0
                        )
                        continue

                    if event_type not in (
                        "SellExplorationData",
                        "MultiSellExplorationData",
                    ):
                        continue

                    result["sales_found"] += 1

                    base_value, bonus, total_earnings = (
                        self._cartography_sale_amounts(event)
                    )

                    estimated_total = sum(
                        max(
                            0,
                            int(
                                body.get("estimated_value")
                                or 0
                            ),
                        )
                        for body in open_bodies.values()
                    )

                    # BaseValue ist für das Lernen bevorzugt, weil
                    # TotalEarnings durch Crew/weitere Mechaniken vom
                    # eigentlichen Kartographie-Bruttowert abweichen kann.
                    learning_value = (
                        base_value
                        if base_value > 0
                        else total_earnings
                    )

                    if (
                        is_changed
                        and learning_value > 0
                        and estimated_total > 0
                    ):
                        with self._connect() as con:
                            cursor = con.execute(
                                """
                                INSERT OR IGNORE INTO cartography_sales (
                                    journal_file,
                                    event_timestamp,
                                    event_type,
                                    base_value,
                                    bonus,
                                    total_earnings,
                                    estimated_total,
                                    correction_factor,
                                    body_count,
                                    first_seen
                                )
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    str(journal),
                                    timestamp,
                                    event_type,
                                    base_value,
                                    bonus,
                                    total_earnings,
                                    estimated_total,
                                    learning_value / estimated_total,
                                    len(open_bodies),
                                    timestamp,
                                ),
                            )

                            if cursor.rowcount:
                                sale_id = int(cursor.lastrowid)

                                rows = []

                                for body in open_bodies.values():
                                    rows.append(
                                        (
                                            sale_id,
                                            int(body["system_address"]),
                                            int(body["body_id"]),
                                            str(body.get("name") or ""),
                                            str(body.get("body_type") or ""),
                                            str(body.get("star_type") or ""),
                                            str(body.get("planet_class") or ""),
                                            body.get("mass_em"),
                                            body.get("stellar_mass"),
                                            self._bool_db(
                                                body.get("terraformable")
                                            ) or 0,
                                            self._bool_db(
                                                body.get("was_discovered")
                                            ),
                                            self._bool_db(
                                                body.get("was_mapped")
                                            ),
                                            self._bool_db(
                                                body.get("self_mapped")
                                            ) or 0,
                                            self._bool_db(
                                                body.get("efficient_mapping")
                                            ) or 0,
                                            int(
                                                body.get("estimated_value")
                                                or 0
                                            ),
                                        )
                                    )

                                con.executemany(
                                    """
                                    INSERT OR REPLACE INTO
                                    cartography_sale_bodies (
                                        sale_id,
                                        system_address,
                                        body_id,
                                        body_name,
                                        body_type,
                                        star_type,
                                        planet_class,
                                        mass_em,
                                        stellar_mass,
                                        terraformable,
                                        was_discovered,
                                        was_mapped,
                                        self_mapped,
                                        efficient_mapping,
                                        estimated_value
                                    )
                                    VALUES (
                                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                                    )
                                    """,
                                    rows,
                                )

                                result["sales_stored"] += 1
                                result["bodies_stored"] += len(rows)

                    # Ein Verkauf schließt immer den bis dahin offenen Topf.
                    open_bodies.clear()

        now = (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        with self._connect() as con:
            for journal, file_size, modified_ns in changed_files:
                con.execute(
                    """
                    INSERT INTO cartography_value_journal_scans (
                        journal_file,
                        file_size,
                        modified_ns,
                        last_scan
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(journal_file)
                    DO UPDATE SET
                        file_size=excluded.file_size,
                        modified_ns=excluded.modified_ns,
                        last_scan=excluded.last_scan
                    """,
                    (
                        str(journal),
                        file_size,
                        modified_ns,
                        now,
                    ),
                )

        if result["sales_stored"]:
            logger.info(
                "Kartographie gelernt: %s Verkauf/Verkäufe, "
                "%s Körper aus %s neuer/geänderter Journaldatei(en)",
                result["sales_stored"],
                result["bodies_stored"],
                result["files_scanned"],
            )

        return result

    @staticmethod
    def _geo_display_name(value):
        raw = str(value or "").strip()
        if not raw:
            return ""

        lower = raw.lower()

        # Generische Signalnamen enthalten keine konkrete GEO-Art.
        generic = {
            "geological",
            "geologisch",
            "$saa_signaltype_geological;",
            "saa_signaltype_geological",
        }
        if lower in generic:
            return ""

        translations = {
            "ice geysers": "Eisgeysire",
            "water geysers": "Wassergeysire",
            "silicate vapour geysers": "Silikatdampf-Geysire",
            "carbon dioxide geysers": "Kohlendioxid-Geysire",
            "fumaroles": "Fumarolen",
            "silicate vapour fumaroles": "Silikatdampf-Fumarolen",
            "sulphur dioxide fumaroles": "Schwefeldioxid-Fumarolen",
            "sulfur dioxide fumaroles": "Schwefeldioxid-Fumarolen",
            "water fumaroles": "Wasser-Fumarolen",
            "gas vents": "Gas-Schlote",
            "steam vents": "Dampf-Schlote",
            "lava spouts": "Lavafontänen",
        }

        for key, translated in translations.items():
            if key in lower:
                return translated

        return raw

    def store_geology(
        self,
        system_address,
        body_id,
        name="",
        raw_name="",
        source="",
        timestamp="",
    ):
        if system_address is None or body_id is None:
            return

        display_name = self._geo_display_name(
            name or raw_name
        )
        if not display_name:
            return

        seen = (
            timestamp
            or datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO geology (
                    system_address, body_id,
                    name, raw_name, source,
                    first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    system_address,
                    body_id,
                    name,
                    source
                )
                DO UPDATE SET
                    raw_name=CASE
                        WHEN excluded.raw_name <> ''
                        THEN excluded.raw_name
                        ELSE geology.raw_name
                    END,
                    last_seen=excluded.last_seen
                """,
                (
                    int(system_address),
                    int(body_id),
                    display_name,
                    str(raw_name or ""),
                    str(source or ""),
                    seen,
                    seen,
                ),
            )

    def geology_for_body(
        self,
        system_address,
        body_id,
    ):
        if system_address is None or body_id is None:
            return []

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT name, raw_name, source,
                       first_seen, last_seen
                FROM geology
                WHERE system_address=?
                  AND body_id=?
                ORDER BY name COLLATE NOCASE
                """,
                (
                    int(system_address),
                    int(body_id),
                ),
            ).fetchall()

        return [
            {
                "name": row[0],
                "raw_name": row[1],
                "source": row[2],
                "first_seen": row[3],
                "last_seen": row[4],
            }
            for row in rows
        ]

    def store_codex_entry(
        self,
        system_address=None,
        system_name="",
        category="",
        subcategory="",
        name="",
        raw_name="",
        nearest_destination="",
        region="",
        event_type="CodexEntry",
        timestamp="",
    ):
        display_name = str(name or raw_name or "").strip()
        if not display_name:
            return

        seen = (
            timestamp
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        address = int(system_address) if isinstance(system_address, int) else None

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO codex_entries (
                    system_address, system_name,
                    category, subcategory,
                    name, raw_name,
                    nearest_destination, region,
                    event_type, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    system_address,
                    category,
                    subcategory,
                    name,
                    nearest_destination,
                    event_type
                )
                DO UPDATE SET
                    system_name=CASE
                        WHEN excluded.system_name <> ''
                        THEN excluded.system_name
                        ELSE codex_entries.system_name
                    END,
                    raw_name=CASE
                        WHEN excluded.raw_name <> ''
                        THEN excluded.raw_name
                        ELSE codex_entries.raw_name
                    END,
                    region=CASE
                        WHEN excluded.region <> ''
                        THEN excluded.region
                        ELSE codex_entries.region
                    END,
                    last_seen=excluded.last_seen
                """,
                (
                    address,
                    str(system_name or ""),
                    str(category or ""),
                    str(subcategory or ""),
                    display_name,
                    str(raw_name or ""),
                    str(nearest_destination or ""),
                    str(region or ""),
                    str(event_type or ""),
                    seen,
                    seen,
                ),
            )

    def search_chronicle(self, query):
        text = str(query or "").strip()
        if not text:
            return []

        pattern = f"%{text}%"
        results = []

        with self._connect() as con:
            for row in con.execute(
                """
                SELECT system_address, name, x, y, z,
                       first_seen, last_seen, body_count
                FROM systems
                WHERE name LIKE ? COLLATE NOCASE
                ORDER BY name COLLATE NOCASE
                LIMIT 500
                """,
                (pattern,),
            ).fetchall():
                results.append({
                    "kind": "System",
                    "system_address": row[0],
                    "system_name": row[1],
                    "x": row[2], "y": row[3], "z": row[4],
                    "system_first_seen": row[5],
                    "system_last_seen": row[6],
                    "body_count": row[7],
                    "body_id": None,
                    "body_name": "",
                    "short_name": "",
                    "match_name": row[1],
                    "detail": "Systemname",
                })

            for row in con.execute(
                """
                SELECT
                    p.system_address, s.name, s.x, s.y, s.z,
                    s.first_seen, s.last_seen, s.body_count,
                    p.body_id, p.name, p.short_name,
                    p.body_type, p.star_type, p.planet_class,
                    p.atmosphere, p.volcanism, p.terraformable,
                    p.biological_signals, p.geological_signals
                FROM bodies p
                JOIN systems s ON s.system_address=p.system_address
                WHERE p.name LIKE ? COLLATE NOCASE
                   OR p.short_name LIKE ? COLLATE NOCASE
                   OR p.body_type LIKE ? COLLATE NOCASE
                   OR p.star_type LIKE ? COLLATE NOCASE
                   OR p.planet_class LIKE ? COLLATE NOCASE
                   OR p.atmosphere LIKE ? COLLATE NOCASE
                   OR p.volcanism LIKE ? COLLATE NOCASE
                   OR (? LIKE '%terraform%' AND p.terraformable=1)
                   OR (? LIKE '%bio%' AND p.biological_signals>0)
                   OR (? LIKE '%geo%' AND p.geological_signals>0)
                ORDER BY s.name COLLATE NOCASE, p.body_id
                LIMIT 1000
                """,
                (
                    pattern, pattern, pattern, pattern, pattern, pattern, pattern,
                    text.lower(), text.lower(), text.lower(),
                ),
            ).fetchall():
                details = [
                    v for v in (row[11], row[12], row[13], row[14], row[15])
                    if v
                ]
                if row[16]:
                    details.append("Terraforming-Kandidat")
                if row[17]:
                    details.append(f"BIO ×{row[17]}")
                if row[18]:
                    details.append(f"GEO ×{row[18]}")

                results.append({
                    "kind": "Körper",
                    "system_address": row[0],
                    "system_name": row[1],
                    "x": row[2], "y": row[3], "z": row[4],
                    "system_first_seen": row[5],
                    "system_last_seen": row[6],
                    "body_count": row[7],
                    "body_id": row[8],
                    "body_name": row[9],
                    "short_name": row[10],
                    "match_name": row[10] or row[9],
                    "detail": " · ".join(map(str, details)),
                })

            for row in con.execute(
                """
                SELECT
                    bio.system_address, s.name, s.x, s.y, s.z,
                    s.first_seen, s.last_seen, s.body_count,
                    bio.body_id, p.name, p.short_name,
                    bio.genus, bio.species, bio.variant
                FROM biology bio
                JOIN systems s ON s.system_address=bio.system_address
                JOIN bodies p
                  ON p.system_address=bio.system_address
                 AND p.body_id=bio.body_id
                WHERE bio.genus LIKE ? COLLATE NOCASE
                   OR bio.species LIKE ? COLLATE NOCASE
                   OR bio.variant LIKE ? COLLATE NOCASE
                ORDER BY s.name COLLATE NOCASE, p.body_id
                LIMIT 1000
                """,
                (pattern, pattern, pattern),
            ).fetchall():
                bio_name = row[13] or row[12] or row[11] or "Biologie"
                results.append({
                    "kind": "BIO",
                    "system_address": row[0],
                    "system_name": row[1],
                    "x": row[2], "y": row[3], "z": row[4],
                    "system_first_seen": row[5],
                    "system_last_seen": row[6],
                    "body_count": row[7],
                    "body_id": row[8],
                    "body_name": row[9],
                    "short_name": row[10],
                    "match_name": bio_name,
                    "detail": bio_name,
                })

            for row in con.execute(
                """
                SELECT
                    m.system_address, s.name, s.x, s.y, s.z,
                    s.first_seen, s.last_seen, s.body_count,
                    m.body_id, p.name, p.short_name,
                    m.material_name, m.percentage
                FROM materials m
                JOIN systems s ON s.system_address=m.system_address
                JOIN bodies p
                  ON p.system_address=m.system_address
                 AND p.body_id=m.body_id
                WHERE m.material_name LIKE ? COLLATE NOCASE
                ORDER BY s.name COLLATE NOCASE, p.body_id
                LIMIT 1000
                """,
                (pattern,),
            ).fetchall():
                pct = f"{float(row[12]):.2f} %" if row[12] is not None else ""
                results.append({
                    "kind": "Material",
                    "system_address": row[0],
                    "system_name": row[1],
                    "x": row[2], "y": row[3], "z": row[4],
                    "system_first_seen": row[5],
                    "system_last_seen": row[6],
                    "body_count": row[7],
                    "body_id": row[8],
                    "body_name": row[9],
                    "short_name": row[10],
                    "match_name": row[11],
                    "detail": f"{row[11]} {pct}".strip(),
                })

            for row in con.execute(
                """
                SELECT
                    c.system_address,
                    COALESCE(NULLIF(c.system_name, ''), s.name, ''),
                    s.x, s.y, s.z,
                    s.first_seen, s.last_seen, s.body_count,
                    c.category, c.subcategory, c.name,
                    c.nearest_destination, c.region, c.event_type
                FROM codex_entries c
                LEFT JOIN systems s ON s.system_address=c.system_address
                WHERE c.name LIKE ? COLLATE NOCASE
                   OR c.raw_name LIKE ? COLLATE NOCASE
                   OR c.category LIKE ? COLLATE NOCASE
                   OR c.subcategory LIKE ? COLLATE NOCASE
                   OR c.nearest_destination LIKE ? COLLATE NOCASE
                   OR c.region LIKE ? COLLATE NOCASE
                   OR c.event_type LIKE ? COLLATE NOCASE
                ORDER BY 2 COLLATE NOCASE, c.name COLLATE NOCASE
                LIMIT 1000
                """,
                (pattern, pattern, pattern, pattern, pattern, pattern, pattern),
            ).fetchall():
                detail = " · ".join(
                    str(v) for v in (row[8], row[9], row[11], row[12]) if v
                )
                results.append({
                    "kind": "Codex",
                    "system_address": row[0],
                    "system_name": row[1],
                    "x": row[2], "y": row[3], "z": row[4],
                    "system_first_seen": row[5] or "",
                    "system_last_seen": row[6] or "",
                    "body_count": int(row[7] or 0),
                    "body_id": None,
                    "body_name": row[11] or "",
                    "short_name": row[11] or "",
                    "match_name": row[10],
                    "detail": detail or row[13],
                })

        unique = []
        seen = set()
        for item in results:
            key = (
                item.get("kind"),
                item.get("system_address"),
                item.get("body_id"),
                item.get("match_name"),
                item.get("detail"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)

        return unique

    def chronicle_search_terms(self):
        result = {
            "BIO": [],
            "Körper": [],
            "Materialien": [],
            "Codex / Phänomene": [],
        }

        with self._connect() as con:
            result["BIO"] = [
                row[0] for row in con.execute(
                    """
                    SELECT DISTINCT
                        CASE
                            WHEN variant <> '' THEN variant
                            WHEN species <> '' THEN species
                            ELSE genus
                        END
                    FROM biology
                    WHERE genus <> '' OR species <> '' OR variant <> ''
                    ORDER BY 1 COLLATE NOCASE
                    """
                ).fetchall()
                if row[0]
            ]

            result["Körper"] = [
                row[0] for row in con.execute(
                    """
                    SELECT DISTINCT planet_class
                    FROM bodies
                    WHERE planet_class <> ''
                    ORDER BY planet_class COLLATE NOCASE
                    """
                ).fetchall()
                if row[0]
            ]

            result["Materialien"] = [
                row[0] for row in con.execute(
                    """
                    SELECT DISTINCT material_name
                    FROM materials
                    WHERE material_name <> ''
                    ORDER BY material_name COLLATE NOCASE
                    """
                ).fetchall()
                if row[0]
            ]

            result["Codex / Phänomene"] = [
                row[0] for row in con.execute(
                    """
                    SELECT DISTINCT name
                    FROM codex_entries
                    WHERE name <> ''
                    ORDER BY name COLLATE NOCASE
                    """
                ).fetchall()
                if row[0]
            ]

        return result

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



    def store_visit(self, system_address, system_name="", timestamp="", star_pos=None):
        if system_address is None:
            return
        pos = list(star_pos or [])
        x = pos[0] if len(pos) > 0 else None
        y = pos[1] if len(pos) > 1 else None
        z = pos[2] if len(pos) > 2 else None
        seen = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connect() as con:
            con.execute("""
                INSERT OR IGNORE INTO system_visits
                    (system_address, system_name, visited_at, x, y, z)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (int(system_address), str(system_name or ""), seen, x, y, z))

    def chronicle_systems(self):
        with self._connect() as con:
            rows = con.execute("""
                SELECT s.system_address, s.name, s.x, s.y, s.z,
                       s.first_seen, s.last_seen, s.body_count,
                       COUNT(v.id)
                FROM systems s
                LEFT JOIN system_visits v ON v.system_address=s.system_address
                WHERE s.x IS NOT NULL AND s.y IS NOT NULL AND s.z IS NOT NULL
                GROUP BY s.system_address
                ORDER BY s.first_seen, s.name COLLATE NOCASE
            """).fetchall()
        return [
            {
                "system_address": r[0], "name": r[1],
                "x": r[2], "y": r[3], "z": r[4],
                "first_seen": r[5], "last_seen": r[6],
                "body_count": r[7], "visits": r[8],
            }
            for r in rows
        ]


    def recent_system_visits(self, limit=10):
        """
        Liefert die letzten tatsächlich protokollierten Systembesuche
        aus system_visits, neuester Besuch zuerst.

        Mehrfache Besuche desselben Systems bleiben bewusst erhalten,
        weil die Liste eine echte Reisehistorie zeigen soll.
        """
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 10

        limit = max(1, min(100, limit))

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    system_address,
                    system_name,
                    visited_at,
                    x, y, z
                FROM system_visits
                ORDER BY visited_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "system_address": row[0],
                "system_name": row[1] or "",
                "visited_at": row[2] or "",
                "x": row[3],
                "y": row[4],
                "z": row[5],
            }
            for row in rows
        ]


    def chronicle_system_details(self, system_address):
        """
        Lädt ein bereits besuchtes System vollständig aus der lokalen
        CMDRHelper-Datenbank für die Chronik-/Explorer-Darstellung.
        """
        if system_address is None:
            return {"system": "", "bodies": []}

        address = int(system_address)

        with self._connect() as con:
            system_row = con.execute(
                """
                SELECT name, body_count, all_bodies_found,
                       first_seen, last_seen
                FROM systems
                WHERE system_address = ?
                """,
                (address,),
            ).fetchone()

            if system_row is None:
                return {"system": "", "bodies": []}

            rows = con.execute(
                """
                SELECT
                    body_id, name, short_name, body_type,
                    star_type, planet_class, parent_id,
                    mass_em, stellar_mass, gravity_g, distance_ls,
                    landable, terraformable,
                    was_discovered, was_mapped,
                    self_mapped, efficient_mapping,
                    atmosphere, volcanism,
                    biological_signals, geological_signals,
                    scan_value, mapped_value, current_value,
                    high_value, first_seen, last_seen
                FROM bodies
                WHERE system_address = ?
                ORDER BY body_id
                """,
                (address,),
            ).fetchall()

            bodies = []

            for row in rows:
                body_id = row[0]

                materials_rows = con.execute(
                    """
                    SELECT material_name, percentage
                    FROM materials
                    WHERE system_address = ? AND body_id = ?
                    ORDER BY material_name COLLATE NOCASE
                    """,
                    (address, body_id),
                ).fetchall()

                biology_rows = con.execute(
                    """
                    SELECT genus, species, variant, scan_type,
                           first_seen, last_seen
                    FROM biology
                    WHERE system_address = ? AND body_id = ?
                    ORDER BY variant COLLATE NOCASE,
                             species COLLATE NOCASE,
                             genus COLLATE NOCASE
                    """,
                    (address, body_id),
                ).fetchall()

                geology_rows = con.execute(
                    """
                    SELECT name, raw_name, source,
                           first_seen, last_seen
                    FROM geology
                    WHERE system_address = ? AND body_id = ?
                    ORDER BY name COLLATE NOCASE
                    """,
                    (address, body_id),
                ).fetchall()

                materials = {
                    item[0]: item[1]
                    for item in materials_rows
                }

                biology = [
                    {
                        "genus": item[0],
                        "species": item[1],
                        "variant": item[2],
                        "scan_type": item[3],
                        "first_seen": item[4],
                        "last_seen": item[5],
                    }
                    for item in biology_rows
                ]

                geology = [
                    {
                        "name": item[0],
                        "raw_name": item[1],
                        "source": item[2],
                        "first_seen": item[3],
                        "last_seen": item[4],
                    }
                    for item in geology_rows
                ]

                bodies.append(
                    {
                        "body_id": row[0],
                        "name": row[1],
                        "short_name": row[2],
                        "body_type": row[3],
                        "star_type": row[4],
                        "planet_class": row[5],
                        "parent_id": row[6],
                        "mass_em": row[7],
                        "stellar_mass": row[8],
                        "gravity_g": row[9],
                        "distance_ls": row[10],
                        "landable": bool(row[11]),
                        "terraformable": bool(row[12]),
                        "was_discovered": (
                            None if row[13] is None else bool(row[13])
                        ),
                        "was_mapped": (
                            None if row[14] is None else bool(row[14])
                        ),
                        "self_mapped": bool(row[15]),
                        "efficient_mapping": bool(row[16]),
                        "atmosphere": row[17] or "",
                        "volcanism": row[18] or "",
                        "biological_signals": int(row[19] or 0),
                        "geological_signals": int(row[20] or 0),
                        "scan_value": int(row[21] or 0),
                        "mapped_value": int(row[22] or 0),
                        "current_value": int(row[23] or 0),
                        "high_value": bool(row[24]),
                        "first_seen": row[25] or "",
                        "last_seen": row[26] or "",
                        "materials": materials,
                        "biology": biology,
                        "geology": geology,
                        "journal_scanned": True,
                        "edsm_known": False,
                        "source": "Journal",
                    }
                )

        return {
            "system_address": address,
            "system": system_row[0] or "",
            "body_count": int(system_row[1] or 0),
            "all_bodies_found": bool(system_row[2]),
            "first_seen": system_row[3] or "",
            "last_seen": system_row[4] or "",
            "bodies": bodies,
        }


    def search_biology(self, query):
        """
        Durchsucht die lokal gespeicherten biologischen Funde nach
        Gattung, Art oder Variante und liefert System + Körper zurück.
        """
        text = str(query or "").strip()
        if not text:
            return []

        pattern = f"%{text}%"

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    bio.system_address,
                    systems.name,
                    systems.x,
                    systems.y,
                    systems.z,
                    systems.first_seen,
                    systems.last_seen,
                    systems.body_count,
                    bodies.body_id,
                    bodies.name,
                    bodies.short_name,
                    bio.genus,
                    bio.species,
                    bio.variant,
                    bio.first_seen,
                    bio.last_seen
                FROM biology AS bio
                JOIN systems
                  ON systems.system_address = bio.system_address
                JOIN bodies
                  ON bodies.system_address = bio.system_address
                 AND bodies.body_id = bio.body_id
                WHERE bio.genus LIKE ? COLLATE NOCASE
                   OR bio.species LIKE ? COLLATE NOCASE
                   OR bio.variant LIKE ? COLLATE NOCASE
                ORDER BY
                    systems.name COLLATE NOCASE,
                    bodies.body_id,
                    bio.variant COLLATE NOCASE,
                    bio.species COLLATE NOCASE,
                    bio.genus COLLATE NOCASE
                """,
                (
                    pattern,
                    pattern,
                    pattern,
                ),
            ).fetchall()

        return [
            {
                "system_address": row[0],
                "system_name": row[1],
                "x": row[2],
                "y": row[3],
                "z": row[4],
                "system_first_seen": row[5],
                "system_last_seen": row[6],
                "body_count": row[7],
                "body_id": row[8],
                "body_name": row[9],
                "short_name": row[10],
                "genus": row[11],
                "species": row[12],
                "variant": row[13],
                "first_seen": row[14],
                "last_seen": row[15],
            }
            for row in rows
        ]

    def stats(self) -> dict:
        result = {}

        with self._connect() as con:
            for table in (
                "systems",
                "bodies",
                "materials",
                "biology",
                "learned_bio_values",
                "cartography_sales",
                "cartography_sale_bodies",
                "geology",
                "codex_entries",
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

        Performance:
        Während des Parsens werden Änderungen zunächst im Speicher gesammelt.
        Erst am Ende wird alles in EINER SQLite-Verbindung und EINER
        Transaktion geschrieben. Das vermeidet tausende einzelne
        Verbindungen/Commits – besonders wichtig bei sehr großen
        Windows-Journalarchiven.
        """
        folder = Path(folder)

        if not folder.exists():
            raise FileNotFoundError(
                f"Journalordner nicht gefunden: {folder}"
            )

        all_journals = sorted(
            folder.glob("Journal.*.log")
        )

        # Importstatus aller Journale einmalig laden.
        with self._connect() as con:
            imported_rows = con.execute(
                """
                SELECT journal_file, file_size, modified_ns
                FROM journal_imports
                """
            ).fetchall()

        imported_files = {
            str(row[0]): (
                int(row[1]),
                int(row[2]),
            )
            for row in imported_rows
        }

        journals = []
        total_files = len(all_journals)

        if progress_callback and total_files:
            progress_callback(
                0,
                total_files,
                "Prüfe Journaldateien …",
            )

        for check_index, journal in enumerate(
            all_journals,
            start=1,
        ):
            needs_import = False

            try:
                stat = journal.stat()
            except OSError:
                stat = None

            if stat is not None:
                previous = imported_files.get(
                    str(journal)
                )

                if previous is None:
                    needs_import = True
                else:
                    old_size, old_modified_ns = previous
                    needs_import = not (
                        int(old_size) == int(stat.st_size)
                        and int(old_modified_ns) == int(stat.st_mtime_ns)
                    )

            if needs_import:
                journals.append(journal)

            if progress_callback:
                progress_callback(
                    check_index,
                    total_files,
                    f"Prüfe: {journal.name}",
                )

        skipped_count = (
            len(all_journals)
            - len(journals)
        )

        if progress_callback and journals:
            progress_callback(
                0,
                len(journals),
                f"Import startet: {len(journals)} Journaldatei(en)",
            )

        total = len(journals)

        if total == 0:
            logger.info(
                "Journalarchiv aktuell: %s Datei(en) geprüft, kein Import nötig",
                total_files,
            )
            stats = self.stats()
            stats["imported_journals"] = 0
            stats["skipped_journals"] = skipped_count
            return stats

        logger.info(
            "Journalarchiv: %s Datei(en) werden importiert, %s übersprungen",
            total,
            skipped_count,
        )

        current_system = ""
        current_address = None

        # -------------------------------------------------------------
        # Temporärer Importzustand
        # -------------------------------------------------------------
        systems = {}
        bodies = {}
        pending_bio = {}
        pending_geo = {}

        # Alle Tabellen, die bisher während des Parsens einzeln
        # geschrieben wurden, werden jetzt im Speicher gesammelt.
        visits = {}
        biology_entries = {}
        geology_entries = {}
        codex_entries = {}
        journal_marks = []

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
                    "star_pos": None,
                },
            )

            if name:
                entry["name"] = name

            if timestamp:
                if not entry["first_seen"]:
                    entry["first_seen"] = timestamp
                entry["last_seen"] = timestamp

            return entry

        def remember_visit(
            system_address,
            system_name="",
            timestamp="",
            star_pos=None,
        ):
            if system_address is None:
                return

            pos = list(star_pos or [])
            x = pos[0] if len(pos) > 0 else None
            y = pos[1] if len(pos) > 1 else None
            z = pos[2] if len(pos) > 2 else None

            seen = (
                timestamp
                or datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )

            key = (
                int(system_address),
                seen,
            )

            visits[key] = (
                int(system_address),
                str(system_name or ""),
                seen,
                x,
                y,
                z,
            )

        def remember_biology(
            system_address,
            body_id,
            genus="",
            species="",
            variant="",
            scan_type="",
            timestamp="",
        ):
            if system_address is None or body_id is None:
                return

            if not (genus or species or variant):
                return

            seen = (
                timestamp
                or datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )

            key = (
                int(system_address),
                int(body_id),
                str(genus or ""),
                str(species or ""),
                str(variant or ""),
            )

            previous = biology_entries.get(key)

            if previous is None:
                biology_entries[key] = {
                    "scan_type": str(scan_type or ""),
                    "first_seen": seen,
                    "last_seen": seen,
                }
            else:
                if scan_type:
                    previous["scan_type"] = str(scan_type)
                previous["last_seen"] = seen

        def remember_geology(
            system_address,
            body_id,
            name="",
            raw_name="",
            source="",
            timestamp="",
        ):
            if system_address is None or body_id is None:
                return

            display_name = self._geo_display_name(
                name or raw_name
            )

            if not display_name:
                return

            seen = (
                timestamp
                or datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )

            key = (
                int(system_address),
                int(body_id),
                display_name,
                str(source or ""),
            )

            previous = geology_entries.get(key)

            if previous is None:
                geology_entries[key] = {
                    "raw_name": str(raw_name or ""),
                    "first_seen": seen,
                    "last_seen": seen,
                }
            else:
                if raw_name:
                    previous["raw_name"] = str(raw_name)
                previous["last_seen"] = seen

        def remember_codex(
            system_address=None,
            system_name="",
            category="",
            subcategory="",
            name="",
            raw_name="",
            nearest_destination="",
            region="",
            event_type="CodexEntry",
            timestamp="",
        ):
            display_name = str(
                name or raw_name or ""
            ).strip()

            if not display_name:
                return

            seen = (
                timestamp
                or datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )

            address = (
                int(system_address)
                if isinstance(system_address, int)
                else None
            )

            key = (
                address,
                str(category or ""),
                str(subcategory or ""),
                display_name,
                str(nearest_destination or ""),
                str(event_type or ""),
            )

            previous = codex_entries.get(key)

            if previous is None:
                codex_entries[key] = {
                    "system_name": str(system_name or ""),
                    "raw_name": str(raw_name or ""),
                    "region": str(region or ""),
                    "first_seen": seen,
                    "last_seen": seen,
                }
            else:
                if system_name:
                    previous["system_name"] = str(system_name)
                if raw_name:
                    previous["raw_name"] = str(raw_name)
                if region:
                    previous["region"] = str(region)
                previous["last_seen"] = seen

        # -------------------------------------------------------------
        # Journale parsen – KEINE SQLite-Schreibzugriffe in dieser Schleife
        # -------------------------------------------------------------
        for index, journal in enumerate(
            journals,
            start=1,
        ):
            current_line_number = 0
            current_event_name = ""

            if progress_callback:
                progress_callback(
                    index,
                    total,
                    f"Importiere: {journal.name}",
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

                            current_system = (
                                name or current_system
                            )

                            entry = ensure_system(
                                current_address,
                                current_system,
                                ts,
                            )

                            star_pos = event.get("StarPos")

                            if (
                                entry is not None
                                and isinstance(
                                    star_pos,
                                    (list, tuple),
                                )
                                and len(star_pos) >= 3
                            ):
                                entry["star_pos"] = [
                                    float(star_pos[0]),
                                    float(star_pos[1]),
                                    float(star_pos[2]),
                                ]

                            if et in (
                                "Location",
                                "FSDJump",
                                "CarrierJump",
                            ):
                                remember_visit(
                                    current_address,
                                    current_system,
                                    ts,
                                    (
                                        entry.get("star_pos")
                                        if entry
                                        else None
                                    ),
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
                            parent_id = _direct_parent_id(parents)

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
                                "scan_value": previous.get(
                                    "scan_value",
                                    0,
                                ),
                                "mapped_value": previous.get(
                                    "mapped_value",
                                    0,
                                ),
                                "current_value": previous.get(
                                    "current_value",
                                    0,
                                ),
                                "high_value": previous.get(
                                    "high_value",
                                    False,
                                ),
                            }

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

                            for signal in event.get(
                                "Signals"
                            ) or []:
                                if not isinstance(signal, dict):
                                    continue

                                signal_type = (
                                    signal.get("Type_Localised")
                                    or signal.get("Type")
                                    or ""
                                )

                                signal_lower = str(
                                    signal_type
                                ).lower()

                                if (
                                    "geological" in signal_lower
                                    or "geologisch" in signal_lower
                                    or "saa_signaltype_geological"
                                    in signal_lower
                                ):
                                    specific_name = (
                                        signal.get("Name_Localised")
                                        or signal.get("Name")
                                        or signal.get("Type_Localised")
                                        or signal.get("Type")
                                        or ""
                                    )

                                    remember_geology(
                                        address,
                                        body_id,
                                        name=specific_name,
                                        raw_name=(
                                            signal.get("Name")
                                            or signal.get("Type")
                                            or ""
                                        ),
                                        source=et,
                                        timestamp=ts,
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

                        elif et == "CodexEntry":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )

                            codex_category = (
                                event.get("Category_Localised")
                                or event.get("Category")
                                or ""
                            )
                            codex_subcategory = (
                                event.get("SubCategory_Localised")
                                or event.get("SubCategory")
                                or ""
                            )
                            codex_name = (
                                event.get("Name_Localised")
                                or event.get("Name")
                                or ""
                            )

                            codex_body_id = event.get("BodyID")

                            if (
                                codex_body_id is None
                                and isinstance(
                                    event.get("Body"),
                                    int,
                                )
                            ):
                                codex_body_id = event.get("Body")

                            category_raw = str(
                                event.get("Category")
                                or ""
                            ).lower()
                            subcategory_raw = str(
                                event.get("SubCategory")
                                or ""
                            ).lower()
                            name_raw = str(
                                event.get("Name")
                                or ""
                            ).lower()
                            name_local = str(
                                codex_name or ""
                            ).lower()

                            is_biology = (
                                "category_biology"
                                in category_raw
                                or "organic"
                                in subcategory_raw
                                or "organische strukturen"
                                in codex_subcategory.lower()
                            )

                            is_specific_geology = (
                                "category_geology"
                                in category_raw
                                or "geolog"
                                in subcategory_raw
                                or "fumar" in name_raw
                                or "fumar" in name_local
                                or "geyser" in name_raw
                                or "geyser" in name_local
                                or "geysir" in name_local
                                or "vent" in name_raw
                                or "vent" in name_local
                                or "lava" in name_raw
                                or "lava" in name_local
                            )

                            if (
                                address is not None
                                and codex_body_id is not None
                                and is_specific_geology
                                and not is_biology
                            ):
                                remember_geology(
                                    address,
                                    codex_body_id,
                                    name=codex_name,
                                    raw_name=(
                                        event.get("Name")
                                        or ""
                                    ),
                                    source="CodexEntry",
                                    timestamp=ts,
                                )

                            remember_codex(
                                system_address=address,
                                system_name=(
                                    event.get("System")
                                    or event.get("StarSystem")
                                    or current_system
                                    or ""
                                ),
                                category=codex_category,
                                subcategory=codex_subcategory,
                                name=codex_name,
                                raw_name=(
                                    event.get("Name")
                                    or ""
                                ),
                                nearest_destination=(
                                    event.get(
                                        "NearestDestination"
                                    )
                                    or ""
                                ),
                                region=(
                                    event.get("Region_Localised")
                                    or event.get("Region")
                                    or ""
                                ),
                                event_type="CodexEntry",
                                timestamp=ts,
                            )

                        elif et == "FSSSignalDiscovered":
                            if event.get("IsStation") is True:
                                continue

                            signal_name = (
                                event.get("SignalName_Localised")
                                or event.get("SignalName")
                                or ""
                            )

                            if not signal_name:
                                continue

                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )

                            fss_body_id = event.get("BodyID")

                            if (
                                fss_body_id is None
                                and isinstance(
                                    event.get("Body"),
                                    int,
                                )
                            ):
                                fss_body_id = event.get("Body")

                            signal_lower = str(
                                signal_name
                            ).lower()

                            if (
                                address is not None
                                and fss_body_id is not None
                                and (
                                    "fumar" in signal_lower
                                    or "geyser" in signal_lower
                                    or "geysir" in signal_lower
                                    or "vent" in signal_lower
                                    or "lava" in signal_lower
                                )
                            ):
                                remember_geology(
                                    address,
                                    fss_body_id,
                                    name=signal_name,
                                    raw_name=(
                                        event.get("SignalName")
                                        or ""
                                    ),
                                    source=(
                                        "FSSSignalDiscovered"
                                    ),
                                    timestamp=ts,
                                )

                            remember_codex(
                                system_address=address,
                                system_name=current_system,
                                category="FSS-Signal",
                                subcategory="",
                                name=signal_name,
                                raw_name=(
                                    event.get("SignalName")
                                    or ""
                                ),
                                event_type=(
                                    "FSSSignalDiscovered"
                                ),
                                timestamp=ts,
                            )

                        elif et == "ScanOrganic":
                            address = self._system_address_from_event(
                                event,
                                current_address,
                            )
                            body_id = event.get("BodyID")

                            if (
                                body_id is None
                                and isinstance(
                                    event.get("Body"),
                                    int,
                                )
                            ):
                                body_id = event.get("Body")

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

                            remember_biology(
                                address,
                                body_id,
                                genus=(
                                    event.get("Genus_Localised")
                                    or event.get("Genus")
                                    or ""
                                ),
                                species=(
                                    event.get("Species_Localised")
                                    or event.get("Species")
                                    or ""
                                ),
                                variant=(
                                    event.get("Variant_Localised")
                                    or event.get("Variant")
                                    or ""
                                ),
                                scan_type=(
                                    event.get("ScanType")
                                    or ""
                                ),
                                timestamp=ts,
                            )

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

            # Journal erst nach erfolgreichem Parsen als importiert vormerken.
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

                journal_marks.append(
                    (
                        str(journal),
                        int(stat.st_size),
                        int(stat.st_mtime_ns),
                        now,
                    )
                )

        # -------------------------------------------------------------
        # EINMALIGER SQLite-Schreibblock
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback(
                total,
                total,
                "Schreibe Datenbank …",
            )

        with self._connect() as con:
            # Systeme
            for address, system in systems.items():
                system_bodies = [
                    body
                    for (
                        body_address,
                        _body_id,
                    ), body in bodies.items()
                    if body_address == address
                ]

                seen = (
                    system.get("last_seen")
                    or datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

                first_seen = (
                    system.get("first_seen")
                    or seen
                )

                star_pos = (
                    system.get("star_pos")
                    or [None, None, None]
                )

                con.execute(
                    """
                    INSERT INTO systems (
                        system_address, name,
                        first_seen, last_seen,
                        body_count, all_bodies_found,
                        x, y, z
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(system_address)
                    DO UPDATE SET
                        name=CASE
                            WHEN excluded.name <> ''
                            THEN excluded.name
                            ELSE systems.name
                        END,
                        last_seen=excluded.last_seen,
                        body_count=MAX(
                            systems.body_count,
                            excluded.body_count
                        ),
                        all_bodies_found=MAX(
                            systems.all_bodies_found,
                            excluded.all_bodies_found
                        ),
                        x=COALESCE(excluded.x, systems.x),
                        y=COALESCE(excluded.y, systems.y),
                        z=COALESCE(excluded.z, systems.z)
                    """,
                    (
                        int(address),
                        system.get("name") or "",
                        first_seen,
                        seen,
                        max(
                            int(
                                system.get(
                                    "body_count",
                                    0,
                                )
                            ),
                            len(system_bodies),
                        ),
                        self._bool_db(
                            system.get(
                                "all_bodies_found",
                                False,
                            )
                        ) or 0,
                        (
                            star_pos[0]
                            if len(star_pos) > 0
                            else None
                        ),
                        (
                            star_pos[1]
                            if len(star_pos) > 1
                            else None
                        ),
                        (
                            star_pos[2]
                            if len(star_pos) > 2
                            else None
                        ),
                    ),
                )

            # Körper + Materialien
            for (address, body_id), body in bodies.items():
                seen = (
                    body.get("last_seen")
                    or datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
                first_seen = (
                    body.get("first_seen")
                    or seen
                )

                con.execute(
                    """
                    INSERT INTO bodies (
                        system_address, body_id,
                        name, short_name, body_type,
                        star_type, planet_class,
                        parent_id, mass_em, stellar_mass,
                        gravity_g, distance_ls,
                        landable, terraformable,
                        was_discovered, was_mapped,
                        self_mapped, efficient_mapping,
                        atmosphere, volcanism,
                        biological_signals,
                        geological_signals,
                        scan_value, mapped_value,
                        current_value, high_value,
                        first_seen, last_seen
                    )
                    VALUES (
                        ?,?,?,?,?,?,?,?,?,?,
                        ?,?,?,?,?,?,?,?,?,?,
                        ?,?,?,?,?,?,?,?
                    )
                    ON CONFLICT(system_address, body_id)
                    DO UPDATE SET
                        name=excluded.name,
                        short_name=excluded.short_name,
                        body_type=excluded.body_type,
                        star_type=excluded.star_type,
                        planet_class=excluded.planet_class,
                        parent_id=excluded.parent_id,
                        mass_em=COALESCE(
                            excluded.mass_em,
                            bodies.mass_em
                        ),
                        stellar_mass=COALESCE(
                            excluded.stellar_mass,
                            bodies.stellar_mass
                        ),
                        gravity_g=COALESCE(
                            excluded.gravity_g,
                            bodies.gravity_g
                        ),
                        distance_ls=COALESCE(
                            excluded.distance_ls,
                            bodies.distance_ls
                        ),
                        landable=excluded.landable,
                        terraformable=excluded.terraformable,
                        was_discovered=COALESCE(
                            excluded.was_discovered,
                            bodies.was_discovered
                        ),
                        was_mapped=COALESCE(
                            excluded.was_mapped,
                            bodies.was_mapped
                        ),
                        self_mapped=MAX(
                            bodies.self_mapped,
                            excluded.self_mapped
                        ),
                        efficient_mapping=MAX(
                            bodies.efficient_mapping,
                            excluded.efficient_mapping
                        ),
                        atmosphere=CASE
                            WHEN excluded.atmosphere <> ''
                            THEN excluded.atmosphere
                            ELSE bodies.atmosphere
                        END,
                        volcanism=CASE
                            WHEN excluded.volcanism <> ''
                            THEN excluded.volcanism
                            ELSE bodies.volcanism
                        END,
                        biological_signals=MAX(
                            bodies.biological_signals,
                            excluded.biological_signals
                        ),
                        geological_signals=MAX(
                            bodies.geological_signals,
                            excluded.geological_signals
                        ),
                        scan_value=excluded.scan_value,
                        mapped_value=excluded.mapped_value,
                        current_value=excluded.current_value,
                        high_value=excluded.high_value,
                        last_seen=excluded.last_seen
                    """,
                    (
                        int(address),
                        int(body_id),
                        body.get("name") or "",
                        body.get("short_name") or "",
                        body.get("body_type") or "",
                        body.get("star_type") or "",
                        body.get("planet_class") or "",
                        body.get("parent_id"),
                        body.get("mass_em"),
                        body.get("stellar_mass"),
                        body.get("gravity_g"),
                        body.get("distance_ls"),
                        self._bool_db(
                            body.get("landable")
                        ) or 0,
                        self._bool_db(
                            body.get("terraformable")
                        ) or 0,
                        self._bool_db(
                            body.get("was_discovered")
                        ),
                        self._bool_db(
                            body.get("was_mapped")
                        ),
                        self._bool_db(
                            body.get("self_mapped")
                        ) or 0,
                        self._bool_db(
                            body.get("efficient_mapping")
                        ) or 0,
                        body.get("atmosphere") or "",
                        body.get("volcanism") or "",
                        int(
                            body.get(
                                "biological_signals"
                            )
                            or 0
                        ),
                        int(
                            body.get(
                                "geological_signals"
                            )
                            or 0
                        ),
                        int(
                            body.get("scan_value")
                            or 0
                        ),
                        int(
                            body.get("mapped_value")
                            or 0
                        ),
                        int(
                            body.get("current_value")
                            or 0
                        ),
                        self._bool_db(
                            body.get("high_value")
                        ) or 0,
                        first_seen,
                        seen,
                    ),
                )

                for name, percentage in self._materials(
                    body
                ):
                    try:
                        percentage = (
                            float(percentage)
                            if percentage is not None
                            else None
                        )
                    except (TypeError, ValueError):
                        percentage = None

                    con.execute(
                        """
                        INSERT INTO materials (
                            system_address,
                            body_id,
                            material_name,
                            percentage
                        )
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(
                            system_address,
                            body_id,
                            material_name
                        )
                        DO UPDATE SET
                            percentage=excluded.percentage
                        """,
                        (
                            int(address),
                            int(body_id),
                            str(name),
                            percentage,
                        ),
                    )

            # Besuche
            con.executemany(
                """
                INSERT OR IGNORE INTO system_visits (
                    system_address,
                    system_name,
                    visited_at,
                    x, y, z
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                list(visits.values()),
            )

            # Biologie
            biology_rows = []
            for key, values in biology_entries.items():
                address, body_id, genus, species, variant = key
                biology_rows.append(
                    (
                        address,
                        body_id,
                        genus,
                        species,
                        variant,
                        values["scan_type"],
                        values["first_seen"],
                        values["last_seen"],
                    )
                )

            con.executemany(
                """
                INSERT INTO biology (
                    system_address, body_id,
                    genus, species, variant,
                    scan_type, first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    system_address,
                    body_id,
                    genus,
                    species,
                    variant
                )
                DO UPDATE SET
                    scan_type=CASE
                        WHEN excluded.scan_type <> ''
                        THEN excluded.scan_type
                        ELSE biology.scan_type
                    END,
                    last_seen=excluded.last_seen
                """,
                biology_rows,
            )

            # Geologie
            geology_rows = []
            for key, values in geology_entries.items():
                address, body_id, name, source = key
                geology_rows.append(
                    (
                        address,
                        body_id,
                        name,
                        values["raw_name"],
                        source,
                        values["first_seen"],
                        values["last_seen"],
                    )
                )

            con.executemany(
                """
                INSERT INTO geology (
                    system_address, body_id,
                    name, raw_name, source,
                    first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    system_address,
                    body_id,
                    name,
                    source
                )
                DO UPDATE SET
                    raw_name=CASE
                        WHEN excluded.raw_name <> ''
                        THEN excluded.raw_name
                        ELSE geology.raw_name
                    END,
                    last_seen=excluded.last_seen
                """,
                geology_rows,
            )

            # Codex / Phänomene
            codex_rows = []
            for key, values in codex_entries.items():
                (
                    address,
                    category,
                    subcategory,
                    name,
                    nearest_destination,
                    event_type,
                ) = key

                codex_rows.append(
                    (
                        address,
                        values["system_name"],
                        category,
                        subcategory,
                        name,
                        values["raw_name"],
                        nearest_destination,
                        values["region"],
                        event_type,
                        values["first_seen"],
                        values["last_seen"],
                    )
                )

            con.executemany(
                """
                INSERT INTO codex_entries (
                    system_address, system_name,
                    category, subcategory,
                    name, raw_name,
                    nearest_destination, region,
                    event_type, first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    system_address,
                    category,
                    subcategory,
                    name,
                    nearest_destination,
                    event_type
                )
                DO UPDATE SET
                    system_name=CASE
                        WHEN excluded.system_name <> ''
                        THEN excluded.system_name
                        ELSE codex_entries.system_name
                    END,
                    raw_name=CASE
                        WHEN excluded.raw_name <> ''
                        THEN excluded.raw_name
                        ELSE codex_entries.raw_name
                    END,
                    region=CASE
                        WHEN excluded.region <> ''
                        THEN excluded.region
                        ELSE codex_entries.region
                    END,
                    last_seen=excluded.last_seen
                """,
                codex_rows,
            )

            # Erst NACH erfolgreichem Datenbank-Schreibblock die Journale
            # als verarbeitet markieren.
            con.executemany(
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
                journal_marks,
            )

        stats = self.stats()
        logger.info(
            "Datenbankimport abgeschlossen: %s Journaldatei(en)",
            total,
        )
        stats["imported_journals"] = total
        stats["skipped_journals"] = skipped_count
        return stats
