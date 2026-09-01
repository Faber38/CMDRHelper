from __future__ import annotations

import sqlite3
import logging
import json
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 4

PERSONAL_TABLES = (
    "system_visits",
    "biology",
    "geology",
    "codex_entries",
    "cartography_sales",
    "journal_imports",
    "bio_value_journal_scans",
    "cartography_value_journal_scans",
)


class CommanderMigrationError(RuntimeError):
    pass

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
        self.active_commander_id = None
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
                # Der Indexstand ist nur Metadatum. Ein Schema-Start darf
                # bestehende persönliche Daten niemals als Nebeneffekt
                # verwerfen; ein gewünschter Neuimport muss explizit erfolgen.
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
                con.execute("PRAGMA user_version = 1")

            if schema_version < 2:
                # Version 2 ergänzt ausschließlich die Zuordnung einzelner
                # Journaldateien. Bestehende Importmarker bleiben unberührt.
                con.execute(
                    """
                    CREATE TABLE IF NOT EXISTS journal_sessions (
                        id INTEGER PRIMARY KEY,
                        journal_file TEXT NOT NULL UNIQUE,
                        commander_id INTEGER,
                        fid_seen TEXT,
                        commander_name_seen TEXT,
                        first_event_at TEXT,
                        last_event_at TEXT,
                        file_size INTEGER,
                        modified_ns INTEGER,
                        attribution_status TEXT NOT NULL CHECK (
                            attribution_status IN ('identified', 'unknown', 'ambiguous')
                        ),
                        FOREIGN KEY (commander_id) REFERENCES commanders(id)
                    )
                    """
                )
                con.execute("PRAGMA user_version = 2")

        self._maybe_migrate_v3()
        self._maybe_migrate_v4()

    def _personal_row_counts(self, con):
        return {
            table: int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in PERSONAL_TABLES
        }

    def _legacy_commander_for_v3(self, con, require=False):
        counts = self._personal_row_counts(con)
        if not any(counts.values()):
            row = con.execute("SELECT id FROM commanders ORDER BY id LIMIT 1").fetchone()
            return (int(row[0]) if row else None), counts

        commanders = con.execute("SELECT id FROM commanders ORDER BY id").fetchall()
        if len(commanders) == 1:
            return int(commanders[0][0]), counts

        if not commanders and not require:
            return None, counts

        raise CommanderMigrationError(
            "Die bestehenden persönlichen Daten können nicht eindeutig einem "
            "Commander zugeordnet werden. Migration auf Schema-Version 3 "
            "wurde ohne Änderungen abgebrochen."
        )

    def _create_migration_backup(self, target_version=3) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = self.path.with_name(
            f"{self.path.name}.pre-v{int(target_version)}-{stamp}.bak"
        )
        try:
            source = sqlite3.connect(self.path)
            target = sqlite3.connect(backup_path)
            try:
                source.backup(target)
                if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise sqlite3.DatabaseError("Backup-Integritätsprüfung fehlgeschlagen")
            finally:
                target.close()
                source.close()
        except Exception as exc:
            try:
                backup_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise CommanderMigrationError(
                f"Datenbanksicherung vor Migration fehlgeschlagen: {exc}"
            ) from exc
        return backup_path

    def _maybe_migrate_v3(self, require=False):
        with self._connect() as con:
            version = int(con.execute("PRAGMA user_version").fetchone()[0])
            if version >= 3:
                return None
            legacy_commander_id, before_counts = self._legacy_commander_for_v3(
                con, require=require
            )
            if legacy_commander_id is None and any(before_counts.values()):
                return None
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CommanderMigrationError(
                    "Integritätsprüfung vor Migration fehlgeschlagen."
                )
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise CommanderMigrationError(
                    "Foreign-Key-Prüfung vor Migration fehlgeschlagen."
                )

        backup_path = self._create_migration_backup(3)
        logger.info("Datenbanksicherung vor v3-Migration: %s", backup_path)
        self._migrate_personal_tables_v3(legacy_commander_id, before_counts)
        return backup_path

    def ensure_schema_v3(self):
        return self._maybe_migrate_v3(require=True)

    def _legacy_commander_for_v4(self, con, require=False):
        system_count = int(con.execute("SELECT COUNT(*) FROM systems").fetchone()[0])
        body_count = int(con.execute("SELECT COUNT(*) FROM bodies").fetchone()[0])
        if not (system_count or body_count):
            return None, system_count, body_count

        commanders = con.execute("SELECT id, fid FROM commanders ORDER BY id").fetchall()
        if len(commanders) == 1 and str(commanders[0][1] or "").strip():
            return int(commanders[0][0]), system_count, body_count
        if not commanders and not require:
            return None, system_count, body_count
        raise CommanderMigrationError(
            "Die persönlichen Explorer-Zustände in systems/bodies können nicht "
            "eindeutig einem Commander zugeordnet werden. Migration auf "
            "Schema-Version 4 wurde ohne Änderungen abgebrochen; bei mehreren "
            "FIDs ist ein kontrollierter Neuaufbau aus identified Journals nötig."
        )

    def _maybe_migrate_v4(self, require=False):
        with self._connect() as con:
            version = int(con.execute("PRAGMA user_version").fetchone()[0])
            if version >= 4:
                return None
            if version < 3:
                return None
            system_columns = {
                row[1] for row in con.execute("PRAGMA table_info(systems)").fetchall()
            }
            existing_tables = {
                row[0] for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if (
                "first_seen" not in system_columns
                and {"commander_systems", "commander_bodies"} <= existing_tables
            ):
                if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise CommanderMigrationError("Vorhandenes v4-Schema ist beschädigt")
                if con.execute("PRAGMA foreign_key_check").fetchall():
                    raise CommanderMigrationError("Vorhandenes v4-Schema hat Foreign-Key-Fehler")
                con.execute("PRAGMA user_version=4")
                return None
            commander_id, system_count, body_count = self._legacy_commander_for_v4(
                con, require=require
            )
            if commander_id is None and (system_count or body_count):
                return None
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CommanderMigrationError("Integritätsprüfung vor v4-Migration fehlgeschlagen.")
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise CommanderMigrationError("Foreign-Key-Prüfung vor v4-Migration fehlgeschlagen.")

        backup_path = self._create_migration_backup(4)
        logger.info("Datenbanksicherung vor v4-Migration: %s", backup_path)
        self._migrate_exploration_tables_v4(commander_id, system_count, body_count)
        return backup_path

    def ensure_schema_v4(self):
        return self._maybe_migrate_v4(require=True)

    def _migrate_exploration_tables_v4(self, commander_id, system_count, body_count):
        con = sqlite3.connect(self.path)
        try:
            con.execute("PRAGMA foreign_keys=OFF")
            con.execute("BEGIN IMMEDIATE")
            material_count = int(con.execute("SELECT COUNT(*) FROM materials").fetchone()[0])
            con.executescript("""
                CREATE TABLE systems_v4 (
                    system_address INTEGER PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    body_count INTEGER NOT NULL DEFAULT 0,
                    x REAL, y REAL, z REAL
                );
                CREATE TABLE bodies_v4 (
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
                    radius_m REAL,
                    gravity_g REAL,
                    distance_ls REAL,
                    landable INTEGER NOT NULL DEFAULT 0,
                    terraformable INTEGER NOT NULL DEFAULT 0,
                    atmosphere TEXT NOT NULL DEFAULT '',
                    volcanism TEXT NOT NULL DEFAULT '',
                    biological_signals INTEGER NOT NULL DEFAULT 0,
                    geological_signals INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(system_address, body_id),
                    FOREIGN KEY(system_address) REFERENCES systems_v4(system_address)
                );
                CREATE TABLE commander_systems (
                    commander_id INTEGER NOT NULL,
                    system_address INTEGER NOT NULL,
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    body_count_seen INTEGER NOT NULL DEFAULT 0,
                    fss_discovery_scan_seen INTEGER NOT NULL DEFAULT 0,
                    all_bodies_found INTEGER NOT NULL DEFAULT 0,
                    all_bodies_found_at TEXT,
                    PRIMARY KEY(commander_id, system_address),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id),
                    FOREIGN KEY(system_address) REFERENCES systems_v4(system_address)
                );
                CREATE TABLE commander_bodies (
                    commander_id INTEGER NOT NULL,
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    scanned INTEGER NOT NULL DEFAULT 0,
                    was_discovered_at_scan INTEGER,
                    was_mapped_at_scan INTEGER,
                    was_footfalled_at_scan INTEGER,
                    self_mapped INTEGER NOT NULL DEFAULT 0,
                    mapped_at TEXT,
                    efficient_mapping INTEGER NOT NULL DEFAULT 0,
                    probes_used INTEGER,
                    efficiency_target INTEGER,
                    first_footfall INTEGER NOT NULL DEFAULT 0,
                    first_footfall_at TEXT,
                    biological_signals_seen INTEGER NOT NULL DEFAULT 0,
                    geological_signals_seen INTEGER NOT NULL DEFAULT 0,
                    scan_value_cached INTEGER NOT NULL DEFAULT 0,
                    mapped_value_cached INTEGER NOT NULL DEFAULT 0,
                    current_value_cached INTEGER NOT NULL DEFAULT 0,
                    high_value_cached INTEGER NOT NULL DEFAULT 0,
                    valuation_version INTEGER NOT NULL DEFAULT 1,
                    PRIMARY KEY(commander_id, system_address, body_id),
                    FOREIGN KEY(commander_id, system_address)
                        REFERENCES commander_systems(commander_id, system_address),
                    FOREIGN KEY(system_address, body_id)
                        REFERENCES bodies_v4(system_address, body_id)
                );
            """)
            con.execute("""INSERT INTO systems_v4(system_address,name,body_count,x,y,z)
                           SELECT system_address,name,body_count,x,y,z FROM systems""")
            con.execute("""INSERT INTO bodies_v4(
                    system_address,body_id,name,short_name,body_type,star_type,planet_class,
                    parent_id,mass_em,stellar_mass,radius_m,gravity_g,distance_ls,landable,
                    terraformable,atmosphere,volcanism,biological_signals,geological_signals)
                SELECT system_address,body_id,name,short_name,body_type,star_type,planet_class,
                    parent_id,mass_em,stellar_mass,NULL,gravity_g,distance_ls,landable,
                    terraformable,atmosphere,volcanism,biological_signals,geological_signals
                FROM bodies""")
            if commander_id is not None:
                con.execute("""INSERT INTO commander_systems(
                        commander_id,system_address,first_seen,last_seen,body_count_seen,
                        fss_discovery_scan_seen,all_bodies_found,all_bodies_found_at)
                    SELECT ?,system_address,first_seen,last_seen,body_count,
                        CASE WHEN body_count>0 THEN 1 ELSE 0 END,
                        all_bodies_found,CASE WHEN all_bodies_found<>0 THEN last_seen ELSE NULL END
                    FROM systems""", (commander_id,))
                con.execute("""INSERT INTO commander_bodies(
                        commander_id,system_address,body_id,first_seen,last_seen,scanned,
                        was_discovered_at_scan,was_mapped_at_scan,self_mapped,efficient_mapping,
                        biological_signals_seen,geological_signals_seen,scan_value_cached,
                        mapped_value_cached,current_value_cached,high_value_cached)
                    SELECT ?,system_address,body_id,first_seen,last_seen,1,
                        was_discovered,was_mapped,self_mapped,efficient_mapping,
                        biological_signals,geological_signals,scan_value,mapped_value,
                        current_value,high_value FROM bodies""", (commander_id,))

            if int(con.execute("SELECT COUNT(*) FROM systems_v4").fetchone()[0]) != system_count:
                raise CommanderMigrationError("System-Zeilenzahl nach v4-Migration abweichend")
            if int(con.execute("SELECT COUNT(*) FROM bodies_v4").fetchone()[0]) != body_count:
                raise CommanderMigrationError("Body-Zeilenzahl nach v4-Migration abweichend")
            if int(con.execute("SELECT COUNT(*) FROM materials").fetchone()[0]) != material_count:
                raise CommanderMigrationError("Materialdaten wurden bei v4-Migration verändert")

            con.execute("DROP TABLE bodies")
            con.execute("DROP TABLE systems")
            con.execute("ALTER TABLE systems_v4 RENAME TO systems")
            con.execute("ALTER TABLE bodies_v4 RENAME TO bodies")
            con.execute("CREATE INDEX idx_commander_systems_last_seen ON commander_systems(commander_id,last_seen)")
            con.execute("CREATE INDEX idx_commander_bodies_last_seen ON commander_bodies(commander_id,last_seen)")
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise CommanderMigrationError("Foreign-Key-Prüfung nach v4-Migration fehlgeschlagen")
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CommanderMigrationError("Integritätsprüfung nach v4-Migration fehlgeschlagen")
            con.execute("PRAGMA user_version=4")
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def set_active_commander(self, commander_id):
        self.active_commander_id = (
            int(commander_id) if commander_id is not None else None
        )

    def _require_commander_id(self, commander_id=None) -> int:
        value = self.active_commander_id if commander_id is None else commander_id
        if value is None:
            raise ValueError("Aktiver Commander ist nicht eindeutig gesetzt")
        return int(value)

    def _commander_fid(self, commander_id) -> str:
        with self._connect() as con:
            row = con.execute(
                "SELECT fid FROM commanders WHERE id=?", (int(commander_id),)
            ).fetchone()
        if row is None:
            raise ValueError("Commander existiert nicht")
        return str(row[0])

    def list_commanders(self) -> list[dict]:
        """Liefert alle bekannten Commanderprofile ohne aktiven Fallback."""
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT id, fid, current_name, first_seen, last_seen
                FROM commanders
                ORDER BY current_name COLLATE NOCASE, fid COLLATE NOCASE, id
                """
            ).fetchall()

        name_counts = {}
        for row in rows:
            name = str(row[2] or "").strip()
            name_counts[name.casefold()] = name_counts.get(name.casefold(), 0) + 1

        result = []
        for row in rows:
            name = str(row[2] or "").strip()
            fid = str(row[1] or "")
            base = name or fid
            display_name = (
                f"{base} ({fid})"
                if name and name_counts.get(name.casefold(), 0) > 1
                else base
            )
            result.append({
                "id": int(row[0]),
                "fid": fid,
                "current_name": name,
                "display_name": display_name,
                "first_seen": row[3] or "",
                "last_seen": row[4] or "",
            })
        return result

    def commander_summary(self, commander_id) -> dict | None:
        """Aggregiert ausschließlich persistente Daten der expliziten ID."""
        if commander_id is None:
            return None
        commander_id = int(commander_id)
        with self._connect() as con:
            commander = con.execute(
                """
                SELECT id, fid, current_name, first_seen, last_seen
                FROM commanders WHERE id=?
                """,
                (commander_id,),
            ).fetchone()
            if commander is None:
                return None

            counts = {}
            for key, table in (
                ("visited_systems", "system_visits"),
                ("biology_findings", "biology"),
                ("geology_findings", "geology"),
                ("codex_entries", "codex_entries"),
                ("cartography_sales", "cartography_sales"),
            ):
                expression = (
                    "COUNT(DISTINCT system_address)"
                    if table == "system_visits" else "COUNT(*)"
                )
                counts[key] = int(con.execute(
                    f"SELECT {expression} FROM {table} WHERE commander_id=?",
                    (commander_id,),
                ).fetchone()[0])

            location = con.execute(
                """
                SELECT system_name, system_address, visited_at, x, y, z
                FROM system_visits
                WHERE commander_id=?
                ORDER BY visited_at DESC, id DESC
                LIMIT 1
                """,
                (commander_id,),
            ).fetchone()

        return {
            "id": int(commander[0]),
            "fid": str(commander[1] or ""),
            "current_name": str(commander[2] or ""),
            "first_seen": commander[3] or "",
            "last_seen": commander[4] or "",
            **counts,
            "last_location": None if location is None else {
                "system_name": str(location[0] or ""),
                "system_address": location[1],
                "visited_at": location[2] or "",
                "x": location[3], "y": location[4], "z": location[5],
            },
        }

    def resolve_session_commander(self, session: dict) -> int | None:
        if session.get("attribution_status") != "identified":
            return None
        fid = str(session.get("fid_seen") or "").strip()
        if not fid:
            return None
        return self.upsert_commander(
            fid,
            session.get("commander_name_seen") or "",
            session.get("last_event_at") or session.get("first_event_at") or "",
        )

    def _migrate_personal_tables_v3(self, commander_id, before_counts):
        definitions = {
            "system_visits": """
                CREATE TABLE system_visits_v3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commander_id INTEGER NOT NULL,
                    system_address INTEGER NOT NULL,
                    system_name TEXT NOT NULL DEFAULT '', visited_at TEXT NOT NULL DEFAULT '',
                    x REAL, y REAL, z REAL,
                    UNIQUE(commander_id, system_address, visited_at),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "biology": """
                CREATE TABLE biology_v3 (
                    commander_id INTEGER NOT NULL, system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL, genus TEXT NOT NULL DEFAULT '',
                    species TEXT NOT NULL DEFAULT '', variant TEXT NOT NULL DEFAULT '',
                    scan_type TEXT NOT NULL DEFAULT '', first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, system_address, body_id, genus, species, variant),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "geology": """
                CREATE TABLE geology_v3 (
                    commander_id INTEGER NOT NULL, system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL, name TEXT NOT NULL DEFAULT '',
                    raw_name TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL DEFAULT '', last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, system_address, body_id, name, source),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "codex_entries": """
                CREATE TABLE codex_entries_v3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, commander_id INTEGER NOT NULL,
                    system_address INTEGER, system_name TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL DEFAULT '', subcategory TEXT NOT NULL DEFAULT '',
                    name TEXT NOT NULL DEFAULT '', raw_name TEXT NOT NULL DEFAULT '',
                    nearest_destination TEXT NOT NULL DEFAULT '', region TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL DEFAULT '', first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    UNIQUE(commander_id, system_address, category, subcategory, name,
                           nearest_destination, event_type),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "cartography_sales": """
                CREATE TABLE cartography_sales_v3 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, commander_id INTEGER NOT NULL,
                    journal_file TEXT NOT NULL DEFAULT '', event_timestamp TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL DEFAULT '', base_value INTEGER NOT NULL DEFAULT 0,
                    bonus INTEGER NOT NULL DEFAULT 0, total_earnings INTEGER NOT NULL DEFAULT 0,
                    estimated_total INTEGER NOT NULL DEFAULT 0, correction_factor REAL,
                    body_count INTEGER NOT NULL DEFAULT 0, first_seen TEXT NOT NULL DEFAULT '',
                    UNIQUE(commander_id, journal_file, event_timestamp, event_type),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "journal_imports": """
                CREATE TABLE journal_imports_v3 (
                    commander_id INTEGER NOT NULL, journal_file TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0, modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_import TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, journal_file),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "bio_value_journal_scans": """
                CREATE TABLE bio_value_journal_scans_v3 (
                    commander_id INTEGER NOT NULL, journal_file TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0, modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_scan TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, journal_file),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
            "cartography_value_journal_scans": """
                CREATE TABLE cartography_value_journal_scans_v3 (
                    commander_id INTEGER NOT NULL, journal_file TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0, modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_scan TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, journal_file),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                )""",
        }
        columns = {
            "system_visits": "id, system_address, system_name, visited_at, x, y, z",
            "biology": "system_address, body_id, genus, species, variant, scan_type, first_seen, last_seen",
            "geology": "system_address, body_id, name, raw_name, source, first_seen, last_seen",
            "codex_entries": "id, system_address, system_name, category, subcategory, name, raw_name, nearest_destination, region, event_type, first_seen, last_seen",
            "cartography_sales": "id, journal_file, event_timestamp, event_type, base_value, bonus, total_earnings, estimated_total, correction_factor, body_count, first_seen",
            "journal_imports": "journal_file, file_size, modified_ns, last_import",
            "bio_value_journal_scans": "journal_file, file_size, modified_ns, last_scan",
            "cartography_value_journal_scans": "journal_file, file_size, modified_ns, last_scan",
        }

        con = sqlite3.connect(self.path)
        try:
            con.execute("PRAGMA foreign_keys = OFF")
            con.execute("BEGIN IMMEDIATE")
            sale_body_count = int(con.execute(
                "SELECT COUNT(*) FROM cartography_sale_bodies"
            ).fetchone()[0])
            for table in PERSONAL_TABLES:
                con.execute(definitions[table])
                old_columns = columns[table]
                new_columns = old_columns.split(", ")
                insert_columns = list(new_columns)
                id_position = 1 if table in ("system_visits", "codex_entries", "cartography_sales") else 0
                insert_columns.insert(id_position, "commander_id")
                select_columns = list(new_columns)
                select_columns.insert(id_position, "?")
                if before_counts[table]:
                    con.execute(
                        f"INSERT INTO {table}_v3 ({', '.join(insert_columns)}) "
                        f"SELECT {', '.join(select_columns)} FROM {table}",
                        (commander_id,),
                    )
                con.execute(f"DROP TABLE {table}")
                con.execute(f"ALTER TABLE {table}_v3 RENAME TO {table}")

            con.execute(
                "CREATE INDEX idx_system_visits_time ON system_visits(commander_id, visited_at)"
            )
            con.execute(
                "CREATE INDEX idx_geology_body ON geology(commander_id, system_address, body_id)"
            )
            con.execute(
                "CREATE INDEX idx_codex_system ON codex_entries(commander_id, system_address)"
            )
            con.execute(
                "CREATE INDEX idx_codex_name ON codex_entries(commander_id, name)"
            )

            after_counts = self._personal_row_counts(con)
            if after_counts != before_counts:
                raise CommanderMigrationError(
                    f"Zeilenzahlen nach Migration abweichend: {before_counts} -> {after_counts}"
                )
            if int(con.execute(
                "SELECT COUNT(*) FROM cartography_sale_bodies"
            ).fetchone()[0]) != sale_body_count:
                raise CommanderMigrationError(
                    "Kartographie-Verkaufskörper wurden bei der Migration verändert"
                )
            if commander_id is not None:
                for table in PERSONAL_TABLES:
                    wrong = int(con.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE commander_id<>?",
                        (int(commander_id),),
                    ).fetchone()[0])
                    if wrong:
                        raise CommanderMigrationError(
                            f"Commander-Zuordnung in {table} ist unvollständig"
                        )
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise CommanderMigrationError("Foreign-Key-Prüfung nach Migration fehlgeschlagen")
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise CommanderMigrationError("Integritätsprüfung nach Migration fehlgeschlagen")
            con.execute("PRAGMA user_version = 3")
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

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

    def store_journal_session(self, session: dict) -> int:
        """Speichert eine bereits dateilokal ermittelte Journalzuordnung."""
        status = str(session.get("attribution_status") or "unknown").strip()
        if status not in ("identified", "unknown", "ambiguous"):
            raise ValueError(f"Ungültiger Zuordnungsstatus: {status}")

        journal_file = str(session.get("journal_file") or "").strip()
        if not journal_file:
            raise ValueError("Journaldatei fehlt")

        fid = str(session.get("fid_seen") or "").strip()
        name = str(session.get("commander_name_seen") or "").strip()
        commander_id = None

        if status == "identified" and fid:
            commander_id = self.upsert_commander(
                fid,
                name,
                session.get("last_event_at") or session.get("first_event_at") or "",
            )
        else:
            # Unknown/ambiguous dürfen auch bei versehentlich mitgelieferten
            # Identitätswerten niemals automatisch zugeordnet werden.
            fid = ""
            name = ""

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO journal_sessions (
                    journal_file, commander_id, fid_seen,
                    commander_name_seen, first_event_at, last_event_at,
                    file_size, modified_ns, attribution_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(journal_file) DO UPDATE SET
                    commander_id=excluded.commander_id,
                    fid_seen=excluded.fid_seen,
                    commander_name_seen=excluded.commander_name_seen,
                    first_event_at=excluded.first_event_at,
                    last_event_at=excluded.last_event_at,
                    file_size=excluded.file_size,
                    modified_ns=excluded.modified_ns,
                    attribution_status=excluded.attribution_status
                """,
                (
                    journal_file, commander_id, fid or None, name or None,
                    session.get("first_event_at") or None,
                    session.get("last_event_at") or None,
                    session.get("file_size"), session.get("modified_ns"), status,
                ),
            )
            row = con.execute(
                "SELECT id FROM journal_sessions WHERE journal_file = ?",
                (journal_file,),
            ).fetchone()

        return int(row[0])

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

    def store_snapshot(self, data, commander_id=None):
        address = data.get("system_address")
        if address is None:
            return

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        seen = data.get("last_timestamp") or now
        bodies = data.get("system_bodies") or []

        with self._connect() as con:
            con.execute("""
                INSERT INTO systems (
                    system_address, name, body_count, x, y, z
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address) DO UPDATE SET
                    name=CASE WHEN excluded.name <> '' THEN excluded.name ELSE systems.name END,
                    body_count=MAX(systems.body_count, excluded.body_count),
                    x=COALESCE(excluded.x, systems.x),
                    y=COALESCE(excluded.y, systems.y),
                    z=COALESCE(excluded.z, systems.z)
            """, (
                int(address), data.get("system") or "",
                int(data.get("system_body_count") or len(bodies)),
                (data.get("star_pos") or [None, None, None])[0],
                (data.get("star_pos") or [None, None, None])[1],
                (data.get("star_pos") or [None, None, None])[2],
            ))

            if commander_id is not None:
                commander_id = int(commander_id)
                con.execute("""
                    INSERT INTO commander_systems(
                        commander_id, system_address, first_seen, last_seen,
                        body_count_seen, fss_discovery_scan_seen,
                        all_bodies_found, all_bodies_found_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(commander_id, system_address) DO UPDATE SET
                        last_seen=excluded.last_seen,
                        body_count_seen=MAX(commander_systems.body_count_seen,
                                            excluded.body_count_seen),
                        fss_discovery_scan_seen=MAX(
                            commander_systems.fss_discovery_scan_seen,
                            excluded.fss_discovery_scan_seen),
                        all_bodies_found=MAX(commander_systems.all_bodies_found,
                                             excluded.all_bodies_found),
                        all_bodies_found_at=COALESCE(
                            commander_systems.all_bodies_found_at,
                            excluded.all_bodies_found_at)
                """, (
                    commander_id, int(address), seen, seen,
                    int(data.get("system_body_count") or len(bodies)),
                    self._bool_db(data.get("fss_discovery_scan_seen")) or 0,
                    self._bool_db(data.get("system_all_bodies_found")) or 0,
                    data.get("all_bodies_found_at") or (
                        seen if data.get("system_all_bodies_found") else None
                    ),
                ))

            for body in bodies:
                body_id = body.get("body_id")
                if body_id is None:
                    continue

                con.execute("""
                    INSERT INTO bodies (
                        system_address, body_id, name, short_name, body_type,
                        star_type, planet_class, parent_id, mass_em, stellar_mass,
                        radius_m, gravity_g, distance_ls, landable, terraformable,
                        atmosphere, volcanism, biological_signals, geological_signals
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(system_address, body_id) DO UPDATE SET
                        name=excluded.name,
                        short_name=excluded.short_name,
                        body_type=excluded.body_type,
                        star_type=excluded.star_type,
                        planet_class=excluded.planet_class,
                        parent_id=excluded.parent_id,
                        mass_em=COALESCE(excluded.mass_em, bodies.mass_em),
                        stellar_mass=COALESCE(excluded.stellar_mass, bodies.stellar_mass),
                        radius_m=COALESCE(excluded.radius_m, bodies.radius_m),
                        gravity_g=COALESCE(excluded.gravity_g, bodies.gravity_g),
                        distance_ls=COALESCE(excluded.distance_ls, bodies.distance_ls),
                        landable=excluded.landable,
                        terraformable=excluded.terraformable,
                        atmosphere=CASE WHEN excluded.atmosphere <> '' THEN excluded.atmosphere ELSE bodies.atmosphere END,
                        volcanism=CASE WHEN excluded.volcanism <> '' THEN excluded.volcanism ELSE bodies.volcanism END,
                        biological_signals=MAX(bodies.biological_signals, excluded.biological_signals),
                        geological_signals=MAX(bodies.geological_signals, excluded.geological_signals)
                """, (
                    int(address), int(body_id), body.get("name") or "",
                    body.get("short_name") or "", body.get("body_type") or "",
                    body.get("star_type") or "", body.get("planet_class") or "",
                    body.get("parent_id"), body.get("mass_em"), body.get("stellar_mass"),
                    body.get("radius_m"), body.get("gravity_g"), body.get("distance_ls"),
                    self._bool_db(body.get("landable")) or 0,
                    self._bool_db(body.get("terraformable")) or 0,
                    body.get("atmosphere") or "", body.get("volcanism") or "",
                    int(body.get("biological_signals") or 0),
                    int(body.get("geological_signals") or 0),
                ))

                if commander_id is not None:
                    con.execute("""
                        INSERT INTO commander_bodies(
                            commander_id,system_address,body_id,first_seen,last_seen,scanned,
                            was_discovered_at_scan,was_mapped_at_scan,was_footfalled_at_scan,
                            self_mapped,mapped_at,efficient_mapping,probes_used,efficiency_target,
                            first_footfall,first_footfall_at,biological_signals_seen,
                            geological_signals_seen,scan_value_cached,mapped_value_cached,
                            current_value_cached,high_value_cached
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(commander_id,system_address,body_id) DO UPDATE SET
                            last_seen=excluded.last_seen,
                            scanned=MAX(commander_bodies.scanned,excluded.scanned),
                            was_discovered_at_scan=COALESCE(excluded.was_discovered_at_scan,
                                commander_bodies.was_discovered_at_scan),
                            was_mapped_at_scan=COALESCE(excluded.was_mapped_at_scan,
                                commander_bodies.was_mapped_at_scan),
                            was_footfalled_at_scan=COALESCE(excluded.was_footfalled_at_scan,
                                commander_bodies.was_footfalled_at_scan),
                            self_mapped=MAX(commander_bodies.self_mapped,excluded.self_mapped),
                            mapped_at=COALESCE(commander_bodies.mapped_at,excluded.mapped_at),
                            efficient_mapping=MAX(commander_bodies.efficient_mapping,
                                excluded.efficient_mapping),
                            probes_used=COALESCE(excluded.probes_used,commander_bodies.probes_used),
                            efficiency_target=COALESCE(excluded.efficiency_target,
                                commander_bodies.efficiency_target),
                            first_footfall=MAX(commander_bodies.first_footfall,
                                excluded.first_footfall),
                            first_footfall_at=COALESCE(commander_bodies.first_footfall_at,
                                excluded.first_footfall_at),
                            biological_signals_seen=MAX(commander_bodies.biological_signals_seen,
                                excluded.biological_signals_seen),
                            geological_signals_seen=MAX(commander_bodies.geological_signals_seen,
                                excluded.geological_signals_seen),
                            scan_value_cached=excluded.scan_value_cached,
                            mapped_value_cached=excluded.mapped_value_cached,
                            current_value_cached=excluded.current_value_cached,
                            high_value_cached=excluded.high_value_cached
                    """, (
                        commander_id,int(address),int(body_id),seen,seen,1,
                        self._bool_db(body.get("was_discovered")),
                        self._bool_db(body.get("was_mapped")),
                        self._bool_db(body.get("was_footfalled")),
                        self._bool_db(body.get("self_mapped")) or 0,
                        body.get("mapped_at"),
                        self._bool_db(body.get("efficient_mapping")) or 0,
                        body.get("probes_used"),body.get("efficiency_target"),
                        self._bool_db(body.get("first_footfall")) or 0,
                        body.get("first_footfall_at"),
                        int(body.get("biological_signals") or 0),
                        int(body.get("geological_signals") or 0),
                        int(body.get("scan_value") or 0),int(body.get("mapped_value") or 0),
                        int(body.get("current_value") or 0),
                        self._bool_db(body.get("high_value")) or 0,
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
                      variant="", scan_type="", timestamp="", commander_id=None):
        if system_address is None or body_id is None:
            return
        if not (genus or species or variant):
            return
        seen = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            con.execute("""
                INSERT INTO biology (
                    commander_id, system_address, body_id, genus, species, variant,
                    scan_type, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(commander_id, system_address, body_id, genus, species, variant)
                DO UPDATE SET
                    scan_type=CASE WHEN excluded.scan_type <> ''
                                   THEN excluded.scan_type ELSE biology.scan_type END,
                    last_seen=excluded.last_seen
            """, (commander_id, int(system_address), int(body_id), str(genus or ""),
                  str(species or ""), str(variant or ""), str(scan_type or ""),
                  seen, seen))

    def biology_for_body(self, system_address, body_id, commander_id=None):
        if system_address is None or body_id is None:
            return []
        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            rows = con.execute("""
                SELECT genus, species, variant, scan_type, first_seen, last_seen
                FROM biology
                WHERE commander_id=? AND system_address=? AND body_id=?
                ORDER BY variant COLLATE NOCASE, species COLLATE NOCASE,
                         genus COLLATE NOCASE
            """, (commander_id, int(system_address), int(body_id))).fetchall()
        return [
            {"genus": r[0], "species": r[1], "variant": r[2],
             "scan_type": r[3], "first_seen": r[4], "last_seen": r[5]}
            for r in rows
        ]

    def biology_for_system(self, system_address, commander_id=None):
        if system_address is None:
            return []

        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT body_id, genus, species, variant,
                       scan_type, first_seen, last_seen
                FROM biology
                WHERE commander_id=? AND system_address=?
                ORDER BY body_id,
                         species COLLATE NOCASE,
                         variant COLLATE NOCASE
                """,
                (commander_id, int(system_address)),
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

    def learn_bio_values_from_journals(self, folder, commander_id=None):
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
        commander_id = self._require_commander_id(commander_id)
        commander_fid = self._commander_fid(commander_id)

        result = {
            "files_scanned": 0,
            "sales_found": 0,
            "values_changed": 0,
        }

        if not folder.is_dir():
            return result

        from cmdrhelper.journal_reader import classify_journal_file

        journals = []
        for journal in sorted(folder.glob("Journal.*.log")):
            try:
                session = classify_journal_file(journal)
            except OSError:
                continue
            if (
                session.get("attribution_status") == "identified"
                and session.get("fid_seen") == commander_fid
            ):
                journals.append(journal)

        if not journals:
            return result

        with self._connect() as con:
            scan_rows = con.execute(
                """
                SELECT journal_file, file_size, modified_ns
                FROM bio_value_journal_scans
                WHERE commander_id=?
                """
                , (commander_id,)
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
                        commander_id, journal_file, file_size,
                        modified_ns, last_scan
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(commander_id, journal_file)
                    DO UPDATE SET
                        file_size=excluded.file_size,
                        modified_ns=excluded.modified_ns,
                        last_scan=excluded.last_scan
                    """,
                    (
                        commander_id,
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

    def cartography_learning_stats(self, commander_id=None):
        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            sales = int(
                con.execute(
                    "SELECT COUNT(*) FROM cartography_sales WHERE commander_id=?",
                    (commander_id,),
                ).fetchone()[0]
            )
            bodies = int(
                con.execute(
                    """SELECT COUNT(*) FROM cartography_sale_bodies b
                       JOIN cartography_sales s ON s.id=b.sale_id
                       WHERE s.commander_id=?""",
                    (commander_id,),
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
                WHERE commander_id=? AND estimated_total > 0
                  AND (base_value > 0 OR total_earnings > 0)
                """,
                (commander_id,),
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
        commander_id=None,
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
        commander_id = self._require_commander_id(commander_id)

        with self._connect() as con:
            params = [commander_id]
            where = [
                "s.commander_id = ?",
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
                    WHERE commander_id=? AND estimated_total > 0
                      AND (base_value > 0 OR total_earnings > 0)
                    """,
                    (commander_id,),
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
        commander_id=None,
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
        commander_id = self._require_commander_id(commander_id)
        commander_fid = self._commander_fid(commander_id)

        result = {
            "files_scanned": 0,
            "sales_found": 0,
            "sales_stored": 0,
            "bodies_stored": 0,
        }

        if not folder.is_dir():
            return result

        from cmdrhelper.journal_reader import classify_journal_file

        journals = []
        for journal in sorted(folder.glob("Journal.*.log")):
            try:
                session = classify_journal_file(journal)
            except OSError:
                continue
            if (
                session.get("attribution_status") == "identified"
                and session.get("fid_seen") == commander_fid
            ):
                journals.append(journal)
        if not journals:
            return result

        with self._connect() as con:
            scan_rows = con.execute(
                """
                SELECT journal_file, file_size, modified_ns
                FROM cartography_value_journal_scans
                WHERE commander_id=?
                """
                , (commander_id,)
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
                                    commander_id,
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
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    commander_id,
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
                        commander_id,
                        journal_file,
                        file_size,
                        modified_ns,
                        last_scan
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(commander_id, journal_file)
                    DO UPDATE SET
                        file_size=excluded.file_size,
                        modified_ns=excluded.modified_ns,
                        last_scan=excluded.last_scan
                    """,
                    (
                        commander_id,
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
        commander_id=None,
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

        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO geology (
                    commander_id, system_address, body_id,
                    name, raw_name, source,
                    first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    commander_id,
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
                    commander_id,
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
        commander_id=None,
    ):
        if system_address is None or body_id is None:
            return []

        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT name, raw_name, source,
                       first_seen, last_seen
                FROM geology
                WHERE commander_id=?
                  AND system_address=?
                  AND body_id=?
                ORDER BY name COLLATE NOCASE
                """,
                (
                    commander_id,
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
        commander_id=None,
    ):
        display_name = str(name or raw_name or "").strip()
        if not display_name:
            return

        seen = (
            timestamp
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        address = int(system_address) if isinstance(system_address, int) else None

        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO codex_entries (
                    commander_id, system_address, system_name,
                    category, subcategory,
                    name, raw_name,
                    nearest_destination, region,
                    event_type, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    commander_id,
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
                    commander_id,
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

    def search_chronicle(self, query, commander_id=None):
        text = str(query or "").strip()
        if not text:
            return []

        pattern = f"%{text}%"
        results = []
        commander_id = self._require_commander_id(commander_id)

        with self._connect() as con:
            for row in con.execute(
                """
                SELECT s.system_address, s.name, s.x, s.y, s.z,
                       cs.first_seen, cs.last_seen, s.body_count
                FROM systems s
                JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=?
                WHERE s.name LIKE ? COLLATE NOCASE
                ORDER BY name COLLATE NOCASE
                LIMIT 500
                """,
                (commander_id, pattern),
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
                    cs.first_seen, cs.last_seen, s.body_count,
                    p.body_id, p.name, p.short_name,
                    p.body_type, p.star_type, p.planet_class,
                    p.atmosphere, p.volcanism, p.terraformable,
                    cb.biological_signals_seen, cb.geological_signals_seen
                FROM bodies p
                JOIN systems s ON s.system_address=p.system_address
                JOIN commander_bodies cb
                  ON cb.system_address=p.system_address AND cb.body_id=p.body_id
                 AND cb.commander_id=?
                JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=?
                WHERE (p.name LIKE ? COLLATE NOCASE
                   OR p.short_name LIKE ? COLLATE NOCASE
                   OR p.body_type LIKE ? COLLATE NOCASE
                   OR p.star_type LIKE ? COLLATE NOCASE
                   OR p.planet_class LIKE ? COLLATE NOCASE
                   OR p.atmosphere LIKE ? COLLATE NOCASE
                   OR p.volcanism LIKE ? COLLATE NOCASE
                   OR (? LIKE '%terraform%' AND p.terraformable=1)
                   OR (? LIKE '%bio%' AND cb.biological_signals_seen>0)
                   OR (? LIKE '%geo%' AND cb.geological_signals_seen>0))
                ORDER BY s.name COLLATE NOCASE, p.body_id
                LIMIT 1000
                """,
                (
                    commander_id, commander_id,
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
                    cs.first_seen, cs.last_seen, s.body_count,
                    bio.body_id, p.name, p.short_name,
                    bio.genus, bio.species, bio.variant
                FROM biology bio
                JOIN systems s ON s.system_address=bio.system_address
                JOIN bodies p
                  ON p.system_address=bio.system_address
                 AND p.body_id=bio.body_id
                JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=bio.commander_id
                WHERE bio.commander_id=? AND (
                      bio.genus LIKE ? COLLATE NOCASE
                   OR bio.species LIKE ? COLLATE NOCASE
                   OR bio.variant LIKE ? COLLATE NOCASE)
                ORDER BY s.name COLLATE NOCASE, p.body_id
                LIMIT 1000
                """,
                (commander_id, pattern, pattern, pattern),
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
                    cs.first_seen, cs.last_seen, s.body_count,
                    m.body_id, p.name, p.short_name,
                    m.material_name, m.percentage
                FROM materials m
                JOIN systems s ON s.system_address=m.system_address
                JOIN bodies p
                  ON p.system_address=m.system_address
                 AND p.body_id=m.body_id
                JOIN commander_bodies cb
                  ON cb.system_address=p.system_address AND cb.body_id=p.body_id
                 AND cb.commander_id=?
                JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=?
                WHERE m.material_name LIKE ? COLLATE NOCASE
                ORDER BY s.name COLLATE NOCASE, p.body_id
                LIMIT 1000
                """,
                (commander_id, commander_id, pattern),
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
                    cs.first_seen, cs.last_seen, s.body_count,
                    c.category, c.subcategory, c.name,
                    c.nearest_destination, c.region, c.event_type
                FROM codex_entries c
                LEFT JOIN systems s ON s.system_address=c.system_address
                LEFT JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=c.commander_id
                WHERE c.commander_id=? AND (
                      c.name LIKE ? COLLATE NOCASE
                   OR c.raw_name LIKE ? COLLATE NOCASE
                   OR c.category LIKE ? COLLATE NOCASE
                   OR c.subcategory LIKE ? COLLATE NOCASE
                   OR c.nearest_destination LIKE ? COLLATE NOCASE
                   OR c.region LIKE ? COLLATE NOCASE
                   OR c.event_type LIKE ? COLLATE NOCASE)
                ORDER BY 2 COLLATE NOCASE, c.name COLLATE NOCASE
                LIMIT 1000
                """,
                (commander_id, pattern, pattern, pattern, pattern, pattern, pattern, pattern),
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

    def chronicle_search_terms(self, commander_id=None):
        result = {
            "BIO": [],
            "Körper": [],
            "Materialien": [],
            "Codex / Phänomene": [],
        }

        commander_id = self._require_commander_id(commander_id)
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
                    WHERE commander_id=?
                      AND (genus <> '' OR species <> '' OR variant <> '')
                    ORDER BY 1 COLLATE NOCASE
                    """
                , (commander_id,)).fetchall()
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
                    WHERE commander_id=? AND name <> ''
                    ORDER BY name COLLATE NOCASE
                    """
                , (commander_id,)).fetchall()
                if row[0]
            ]

        return result

    def mark_journal_files(self, folder, commander_id=None):
        folder = Path(folder)
        if not folder.exists():
            return
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        commander_id = self._require_commander_id(commander_id)
        commander_fid = self._commander_fid(commander_id)
        from cmdrhelper.journal_reader import classify_journal_file
        with self._connect() as con:
            for journal in sorted(folder.glob("Journal.*.log")):
                try:
                    session = classify_journal_file(journal)
                    stat = journal.stat()
                except OSError:
                    continue
                if not (
                    session.get("attribution_status") == "identified"
                    and session.get("fid_seen") == commander_fid
                ):
                    continue
                con.execute("""
                    INSERT INTO journal_imports (
                        commander_id, journal_file, file_size, modified_ns, last_import
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(commander_id, journal_file) DO UPDATE SET
                        file_size=excluded.file_size,
                        modified_ns=excluded.modified_ns,
                        last_import=excluded.last_import
                """, (commander_id, str(journal), int(stat.st_size), int(stat.st_mtime_ns), now))



    def store_visit(self, system_address, system_name="", timestamp="", star_pos=None,
                    commander_id=None):
        if system_address is None:
            return
        pos = list(star_pos or [])
        x = pos[0] if len(pos) > 0 else None
        y = pos[1] if len(pos) > 1 else None
        z = pos[2] if len(pos) > 2 else None
        seen = timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            con.execute("""
                INSERT OR IGNORE INTO system_visits
                    (commander_id, system_address, system_name, visited_at, x, y, z)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (commander_id, int(system_address), str(system_name or ""), seen, x, y, z))

    def chronicle_systems(self, commander_id=None):
        commander_id = self._require_commander_id(commander_id)
        with self._connect() as con:
            rows = con.execute("""
                SELECT s.system_address, s.name, s.x, s.y, s.z,
                       cs.first_seen, cs.last_seen, s.body_count,
                       COUNT(v.id)
                FROM systems s
                JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=?
                JOIN system_visits v ON v.system_address=s.system_address
                                    AND v.commander_id=?
                WHERE s.x IS NOT NULL AND s.y IS NOT NULL AND s.z IS NOT NULL
                GROUP BY s.system_address
                ORDER BY cs.first_seen, s.name COLLATE NOCASE
            """, (commander_id, commander_id)).fetchall()
        return [
            {
                "system_address": r[0], "name": r[1],
                "x": r[2], "y": r[3], "z": r[4],
                "first_seen": r[5], "last_seen": r[6],
                "body_count": r[7], "visits": r[8],
            }
            for r in rows
        ]


    def recent_system_visits(self, limit=10, commander_id=None):
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
        commander_id = self._require_commander_id(commander_id)

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    system_address,
                    system_name,
                    visited_at,
                    x, y, z
                FROM system_visits
                WHERE commander_id=?
                ORDER BY visited_at DESC, id DESC
                LIMIT ?
                """,
                (commander_id, limit),
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


    def chronicle_system_details(self, system_address, commander_id=None):
        """
        Lädt ein bereits besuchtes System vollständig aus der lokalen
        CMDRHelper-Datenbank für die Chronik-/Explorer-Darstellung.
        """
        if system_address is None:
            return {"system": "", "bodies": []}

        address = int(system_address)
        commander_id = self._require_commander_id(commander_id)

        with self._connect() as con:
            system_row = con.execute(
                """
                SELECT s.name, s.body_count, cs.all_bodies_found,
                       cs.first_seen, cs.last_seen
                FROM systems s
                JOIN commander_systems cs
                  ON cs.system_address=s.system_address AND cs.commander_id=?
                WHERE s.system_address = ?
                """,
                (commander_id, address),
            ).fetchone()

            if system_row is None:
                return {"system": "", "bodies": []}

            rows = con.execute(
                """
                SELECT
                    b.body_id, b.name, b.short_name, b.body_type,
                    b.star_type, b.planet_class, b.parent_id,
                    b.mass_em, b.stellar_mass, b.radius_m, b.gravity_g, b.distance_ls,
                    b.landable, b.terraformable,
                    cb.was_discovered_at_scan, cb.was_mapped_at_scan,
                    cb.was_footfalled_at_scan, cb.self_mapped, cb.efficient_mapping,
                    cb.first_footfall, cb.first_footfall_at,
                    b.atmosphere, b.volcanism,
                    cb.biological_signals_seen, cb.geological_signals_seen,
                    cb.scan_value_cached, cb.mapped_value_cached,
                    cb.current_value_cached, cb.high_value_cached,
                    cb.first_seen, cb.last_seen
                FROM bodies b
                JOIN commander_bodies cb
                  ON cb.system_address=b.system_address AND cb.body_id=b.body_id
                 AND cb.commander_id=?
                WHERE b.system_address = ?
                ORDER BY b.body_id
                """,
                (commander_id, address),
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
                    WHERE commander_id=? AND system_address = ? AND body_id = ?
                    ORDER BY variant COLLATE NOCASE,
                             species COLLATE NOCASE,
                             genus COLLATE NOCASE
                    """,
                    (commander_id, address, body_id),
                ).fetchall()

                geology_rows = con.execute(
                    """
                    SELECT name, raw_name, source,
                           first_seen, last_seen
                    FROM geology
                    WHERE commander_id=? AND system_address = ? AND body_id = ?
                    ORDER BY name COLLATE NOCASE
                    """,
                    (commander_id, address, body_id),
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
                        "radius_m": row[9],
                        "gravity_g": row[10],
                        "distance_ls": row[11],
                        "landable": bool(row[12]),
                        "terraformable": bool(row[13]),
                        "was_discovered": (
                            None if row[14] is None else bool(row[14])
                        ),
                        "was_mapped": (
                            None if row[15] is None else bool(row[15])
                        ),
                        "was_footfalled": None if row[16] is None else bool(row[16]),
                        "self_mapped": bool(row[17]),
                        "efficient_mapping": bool(row[18]),
                        "first_footfall": bool(row[19]),
                        "first_footfall_at": row[20],
                        "atmosphere": row[21] or "",
                        "volcanism": row[22] or "",
                        "biological_signals": int(row[23] or 0),
                        "geological_signals": int(row[24] or 0),
                        "scan_value": int(row[25] or 0),
                        "mapped_value": int(row[26] or 0),
                        "current_value": int(row[27] or 0),
                        "high_value": bool(row[28]),
                        "first_seen": row[29] or "",
                        "last_seen": row[30] or "",
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


    def search_biology(self, query, commander_id=None):
        """
        Durchsucht die lokal gespeicherten biologischen Funde nach
        Gattung, Art oder Variante und liefert System + Körper zurück.
        """
        text = str(query or "").strip()
        if not text:
            return []

        pattern = f"%{text}%"
        commander_id = self._require_commander_id(commander_id)

        with self._connect() as con:
            rows = con.execute(
                """
                SELECT
                    bio.system_address,
                    systems.name,
                    systems.x,
                    systems.y,
                    systems.z,
                    commander_systems.first_seen,
                    commander_systems.last_seen,
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
                JOIN commander_systems
                  ON commander_systems.system_address=bio.system_address
                 AND commander_systems.commander_id=bio.commander_id
                WHERE bio.commander_id=? AND (
                      bio.genus LIKE ? COLLATE NOCASE
                   OR bio.species LIKE ? COLLATE NOCASE
                   OR bio.variant LIKE ? COLLATE NOCASE)
                ORDER BY
                    systems.name COLLATE NOCASE,
                    bodies.body_id,
                    bio.variant COLLATE NOCASE,
                    bio.species COLLATE NOCASE,
                    bio.genus COLLATE NOCASE
                """,
                (
                    commander_id,
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
        commander_id = self.active_commander_id

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
                if table in PERSONAL_TABLES or table == "cartography_sale_bodies":
                    if commander_id is None:
                        result[table] = 0
                    elif table == "cartography_sale_bodies":
                        result[table] = int(con.execute(
                            """SELECT COUNT(*) FROM cartography_sale_bodies b
                               JOIN cartography_sales s ON s.id=b.sale_id
                               WHERE s.commander_id=?""",
                            (int(commander_id),),
                        ).fetchone()[0])
                    else:
                        result[table] = int(con.execute(
                            f"SELECT COUNT(*) FROM {table} WHERE commander_id=?",
                            (int(commander_id),),
                        ).fetchone()[0])
                else:
                    result[table] = int(
                        con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
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

    def _journal_needs_import(self, journal: Path, commander_id=None) -> bool:
        commander_id = self._require_commander_id(commander_id)
        try:
            stat = journal.stat()
        except OSError:
            return False

        with self._connect() as con:
            row = con.execute(
                """
                SELECT file_size, modified_ns
                FROM journal_imports
                WHERE commander_id = ? AND journal_file = ?
                """,
                (commander_id, str(journal)),
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

        from cmdrhelper.journal_reader import classify_journal_file

        # Vor dem ersten Zugriff auf die v3-Importmarker alle Dateien strikt
        # einzeln klassifizieren. Dadurch kann ein v2-Altbestand erst dann
        # migriert werden, wenn die belegten FIDs vollständig bekannt sind.
        classified = {}
        for journal in all_journals:
            try:
                session = classify_journal_file(journal)
                self.store_journal_session(session)
                commander_id = self.resolve_session_commander(session)
            except OSError:
                session = {"attribution_status": "unknown"}
                commander_id = None
            classified[journal] = (session, commander_id)

        self.ensure_schema_v3()
        self.ensure_schema_v4()

        # Importstatus aller eindeutig zugeordneten Journale einmalig laden.
        with self._connect() as con:
            imported_rows = con.execute(
                """
                SELECT commander_id, journal_file, file_size, modified_ns
                FROM journal_imports
                """
            ).fetchall()

        imported_files = {
            (int(row[0]), str(row[1])): (
                int(row[2]),
                int(row[3]),
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
            commander_id = None

            session, commander_id = classified[journal]

            try:
                stat = journal.stat()
            except OSError:
                stat = None

            if stat is not None:
                previous = (
                    imported_files.get((commander_id, str(journal)))
                    if commander_id is not None
                    else None
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
                journals.append((journal, commander_id))

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

        # -------------------------------------------------------------
        # Temporärer Importzustand
        # -------------------------------------------------------------
        systems = {}
        bodies = {}
        commander_systems = {}
        commander_bodies = {}
        first_footfall_disembarks = set()
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

        file_commander_id = None

        def ensure_commander_system(address, timestamp=""):
            if file_commander_id is None or address is None:
                return None
            key = (int(file_commander_id), int(address))
            entry = commander_systems.setdefault(key, {
                "first_seen": timestamp or "", "last_seen": timestamp or "",
                "body_count_seen": 0, "fss_discovery_scan_seen": False,
                "all_bodies_found": False, "all_bodies_found_at": None,
            })
            if timestamp:
                if not entry["first_seen"]:
                    entry["first_seen"] = timestamp
                entry["last_seen"] = timestamp
            return entry

        def ensure_commander_body(address, body_id, timestamp=""):
            if file_commander_id is None or address is None or body_id is None:
                return None
            ensure_commander_system(address, timestamp)
            key = (int(file_commander_id), int(address), int(body_id))
            entry = commander_bodies.setdefault(key, {
                "first_seen": timestamp or "", "last_seen": timestamp or "",
                "scanned": False, "was_discovered_at_scan": None,
                "was_mapped_at_scan": None, "was_footfalled_at_scan": None,
                "self_mapped": False, "mapped_at": None,
                "efficient_mapping": False, "probes_used": None,
                "efficiency_target": None, "first_footfall": False,
                "first_footfall_at": None, "biological_signals_seen": 0,
                "geological_signals_seen": 0, "scan_value_cached": 0,
                "mapped_value_cached": 0, "current_value_cached": 0,
                "high_value_cached": False,
            })
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
            if system_address is None or file_commander_id is None:
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
                int(file_commander_id),
                int(system_address),
                seen,
            )

            visits[key] = (
                int(file_commander_id),
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
            if (
                file_commander_id is None
                or system_address is None
                or body_id is None
            ):
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
                int(file_commander_id),
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
            if (
                file_commander_id is None
                or system_address is None
                or body_id is None
            ):
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
                int(file_commander_id),
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
            if file_commander_id is None:
                return

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
                int(file_commander_id),
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
        for index, journal_item in enumerate(
            journals,
            start=1,
        ):
            journal, file_commander_id = journal_item
            # Dateigrenzen sind harte Grenzen: weder Identität noch Position
            # werden aus dem vorherigen Journal übernommen.
            current_system = ""
            current_address = None
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
                            ensure_commander_system(current_address, ts)

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

                        elif et == "Disembark" and event.get("OnPlanet"):
                            address = self._system_address_from_event(event, current_address)
                            body_id = event.get("BodyID")
                            if file_commander_id is None or address is None or body_id is None:
                                continue
                            try:
                                footfall_key = (
                                    int(file_commander_id), int(address), int(body_id)
                                )
                            except (TypeError, ValueError):
                                continue
                            first_footfall_disembarks.add(footfall_key)
                            personal_body = commander_bodies.get(footfall_key)
                            if (personal_body is not None
                                    and personal_body.get("was_footfalled_at_scan") is False):
                                personal_body["first_footfall"] = True
                                personal_body["first_footfall_at"] = ts

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
                            personal_system = ensure_commander_system(address, ts)

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
                                if personal_system is not None:
                                    personal_system["body_count_seen"] = max(
                                        int(personal_system["body_count_seen"]),
                                        int(event["BodyCount"]),
                                    )
                                    personal_system["fss_discovery_scan_seen"] = True

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
                            personal_system = ensure_commander_system(address, ts)

                            if entry is not None:
                                if isinstance(
                                    event.get("Count"),
                                    int,
                                ):
                                    entry["body_count"] = max(
                                        int(entry["body_count"]),
                                        int(event["Count"]),
                                    )
                            if personal_system is not None:
                                personal_system["all_bodies_found"] = True
                                personal_system["all_bodies_found_at"] = ts
                                if isinstance(event.get("Count"), int):
                                    personal_system["body_count_seen"] = max(
                                        int(personal_system["body_count_seen"]),
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
                                "radius_m": event.get("Radius"),
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
                            personal_body = ensure_commander_body(address, body_id, ts)
                            if personal_body is not None:
                                personal_body.update({
                                    "scanned": True,
                                    "was_discovered_at_scan": event.get("WasDiscovered"),
                                    "was_mapped_at_scan": event.get("WasMapped"),
                                    "was_footfalled_at_scan": event.get("WasFootfalled"),
                                    "biological_signals_seen": int(body.get("biological_signals") or 0),
                                    "geological_signals_seen": int(body.get("geological_signals") or 0),
                                    "scan_value_cached": int(body.get("scan_value") or 0),
                                    "mapped_value_cached": int(body.get("mapped_value") or 0),
                                    "current_value_cached": int(body.get("current_value") or 0),
                                    "high_value_cached": bool(body.get("high_value")),
                                })
                                footfall_key = (int(file_commander_id), int(address), int(body_id))
                                if (footfall_key in first_footfall_disembarks
                                        and event.get("WasFootfalled") is False):
                                    personal_body["first_footfall"] = True
                                    personal_body["first_footfall_at"] = ts

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
                            personal_body = ensure_commander_body(address, body_id, ts)

                            if body:
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
                                    efficient = probes_used <= efficiency_target
                                else:
                                    efficient = False
                                if personal_body is not None:
                                    personal_body["self_mapped"] = True
                                    personal_body["mapped_at"] = ts
                                    personal_body["efficient_mapping"] = efficient
                                    personal_body["probes_used"] = probes_used
                                    personal_body["efficiency_target"] = efficiency_target

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
                            personal_body = ensure_commander_body(address, body_id, ts)

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
                            if personal_body is not None:
                                personal_body["biological_signals_seen"] = max(
                                    int(personal_body["biological_signals_seen"]), bio)
                                personal_body["geological_signals_seen"] = max(
                                    int(personal_body["geological_signals_seen"]), geo)

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

            if stat is not None and file_commander_id is not None:
                now = (
                    datetime.now(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )

                journal_marks.append(
                    (
                        int(file_commander_id),
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
                        body_count,
                        x, y, z
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(system_address)
                    DO UPDATE SET
                        name=CASE
                            WHEN excluded.name <> ''
                            THEN excluded.name
                            ELSE systems.name
                        END,
                        body_count=MAX(
                            systems.body_count,
                            excluded.body_count
                        ),
                        x=COALESCE(excluded.x, systems.x),
                        y=COALESCE(excluded.y, systems.y),
                        z=COALESCE(excluded.z, systems.z)
                    """,
                    (
                        int(address),
                        system.get("name") or "",
                        max(
                            int(
                                system.get(
                                    "body_count",
                                    0,
                                )
                            ),
                            len(system_bodies),
                        ),
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
                        radius_m, gravity_g, distance_ls,
                        landable, terraformable,
                        atmosphere, volcanism,
                        biological_signals,
                        geological_signals
                    )
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                        radius_m=COALESCE(
                            excluded.radius_m,
                            bodies.radius_m
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
                        )
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
                        body.get("radius_m"),
                        body.get("gravity_g"),
                        body.get("distance_ls"),
                        self._bool_db(
                            body.get("landable")
                        ) or 0,
                        self._bool_db(
                            body.get("terraformable")
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

            commander_system_rows = [
                (
                    commander_id, address, values["first_seen"], values["last_seen"],
                    int(values["body_count_seen"]),
                    self._bool_db(values["fss_discovery_scan_seen"]) or 0,
                    self._bool_db(values["all_bodies_found"]) or 0,
                    values["all_bodies_found_at"],
                )
                for (commander_id, address), values in commander_systems.items()
            ]
            con.executemany("""
                INSERT INTO commander_systems(
                    commander_id,system_address,first_seen,last_seen,body_count_seen,
                    fss_discovery_scan_seen,all_bodies_found,all_bodies_found_at)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(commander_id,system_address) DO UPDATE SET
                    last_seen=excluded.last_seen,
                    body_count_seen=MAX(commander_systems.body_count_seen,excluded.body_count_seen),
                    fss_discovery_scan_seen=MAX(commander_systems.fss_discovery_scan_seen,
                                                excluded.fss_discovery_scan_seen),
                    all_bodies_found=MAX(commander_systems.all_bodies_found,
                                         excluded.all_bodies_found),
                    all_bodies_found_at=COALESCE(commander_systems.all_bodies_found_at,
                                                 excluded.all_bodies_found_at)
            """, commander_system_rows)

            commander_body_rows = [
                (
                    commander_id,address,body_id,values["first_seen"],values["last_seen"],
                    self._bool_db(values["scanned"]) or 0,
                    self._bool_db(values["was_discovered_at_scan"]),
                    self._bool_db(values["was_mapped_at_scan"]),
                    self._bool_db(values["was_footfalled_at_scan"]),
                    self._bool_db(values["self_mapped"]) or 0,values["mapped_at"],
                    self._bool_db(values["efficient_mapping"]) or 0,
                    values["probes_used"],values["efficiency_target"],
                    self._bool_db(values["first_footfall"]) or 0,
                    values["first_footfall_at"],int(values["biological_signals_seen"]),
                    int(values["geological_signals_seen"]),int(values["scan_value_cached"]),
                    int(values["mapped_value_cached"]),int(values["current_value_cached"]),
                    self._bool_db(values["high_value_cached"]) or 0,
                )
                for (commander_id,address,body_id), values in commander_bodies.items()
            ]
            con.executemany("""
                INSERT INTO commander_bodies(
                    commander_id,system_address,body_id,first_seen,last_seen,scanned,
                    was_discovered_at_scan,was_mapped_at_scan,was_footfalled_at_scan,
                    self_mapped,mapped_at,efficient_mapping,probes_used,efficiency_target,
                    first_footfall,first_footfall_at,biological_signals_seen,
                    geological_signals_seen,scan_value_cached,mapped_value_cached,
                    current_value_cached,high_value_cached)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(commander_id,system_address,body_id) DO UPDATE SET
                    last_seen=excluded.last_seen,
                    scanned=MAX(commander_bodies.scanned,excluded.scanned),
                    was_discovered_at_scan=COALESCE(excluded.was_discovered_at_scan,
                        commander_bodies.was_discovered_at_scan),
                    was_mapped_at_scan=COALESCE(excluded.was_mapped_at_scan,
                        commander_bodies.was_mapped_at_scan),
                    was_footfalled_at_scan=COALESCE(excluded.was_footfalled_at_scan,
                        commander_bodies.was_footfalled_at_scan),
                    self_mapped=MAX(commander_bodies.self_mapped,excluded.self_mapped),
                    mapped_at=COALESCE(commander_bodies.mapped_at,excluded.mapped_at),
                    efficient_mapping=MAX(commander_bodies.efficient_mapping,
                        excluded.efficient_mapping),
                    probes_used=COALESCE(excluded.probes_used,commander_bodies.probes_used),
                    efficiency_target=COALESCE(excluded.efficiency_target,
                        commander_bodies.efficiency_target),
                    first_footfall=MAX(commander_bodies.first_footfall,excluded.first_footfall),
                    first_footfall_at=COALESCE(commander_bodies.first_footfall_at,
                        excluded.first_footfall_at),
                    biological_signals_seen=MAX(commander_bodies.biological_signals_seen,
                        excluded.biological_signals_seen),
                    geological_signals_seen=MAX(commander_bodies.geological_signals_seen,
                        excluded.geological_signals_seen),
                    scan_value_cached=excluded.scan_value_cached,
                    mapped_value_cached=excluded.mapped_value_cached,
                    current_value_cached=excluded.current_value_cached,
                    high_value_cached=excluded.high_value_cached
            """, commander_body_rows)

            # Besuche
            con.executemany(
                """
                INSERT OR IGNORE INTO system_visits (
                    commander_id,
                    system_address,
                    system_name,
                    visited_at,
                    x, y, z
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                list(visits.values()),
            )

            # Biologie
            biology_rows = []
            for key, values in biology_entries.items():
                commander_id, address, body_id, genus, species, variant = key
                biology_rows.append(
                    (
                        commander_id,
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
                    commander_id,
                    system_address, body_id,
                    genus, species, variant,
                    scan_type, first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    commander_id,
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
                commander_id, address, body_id, name, source = key
                geology_rows.append(
                    (
                        commander_id,
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
                    commander_id,
                    system_address, body_id,
                    name, raw_name, source,
                    first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    commander_id,
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
                    commander_id,
                    address,
                    category,
                    subcategory,
                    name,
                    nearest_destination,
                    event_type,
                ) = key

                codex_rows.append(
                    (
                        commander_id,
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
                    commander_id,
                    system_address, system_name,
                    category, subcategory,
                    name, raw_name,
                    nearest_destination, region,
                    event_type, first_seen, last_seen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(
                    commander_id,
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
                    commander_id,
                    journal_file,
                    file_size,
                    modified_ns,
                    last_import
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(commander_id, journal_file)
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
