-- Empty historical CMDRHelper schema 4.
-- Generated from cmdrhelper/database.py at 30a4fa0c9f7f01412777dd6732a5a8edcde37912.
-- No user data; frozen to keep migration tests independent of the current schema.
BEGIN TRANSACTION;
CREATE TABLE app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT ''
                );
INSERT INTO "app_meta" VALUES('discovery_index_version','3');
CREATE TABLE "bio_value_journal_scans" (
                    commander_id INTEGER NOT NULL, journal_file TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0, modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_scan TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, journal_file),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE "biology" (
                    commander_id INTEGER NOT NULL, system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL, genus TEXT NOT NULL DEFAULT '',
                    species TEXT NOT NULL DEFAULT '', variant TEXT NOT NULL DEFAULT '',
                    scan_type TEXT NOT NULL DEFAULT '', first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, system_address, body_id, genus, species, variant),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE "bodies" (
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
                    FOREIGN KEY(system_address) REFERENCES "systems"(system_address)
                );
CREATE TABLE cartography_sale_bodies (
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
CREATE TABLE "cartography_sales" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, commander_id INTEGER NOT NULL,
                    journal_file TEXT NOT NULL DEFAULT '', event_timestamp TEXT NOT NULL DEFAULT '',
                    event_type TEXT NOT NULL DEFAULT '', base_value INTEGER NOT NULL DEFAULT 0,
                    bonus INTEGER NOT NULL DEFAULT 0, total_earnings INTEGER NOT NULL DEFAULT 0,
                    estimated_total INTEGER NOT NULL DEFAULT 0, correction_factor REAL,
                    body_count INTEGER NOT NULL DEFAULT 0, first_seen TEXT NOT NULL DEFAULT '',
                    UNIQUE(commander_id, journal_file, event_timestamp, event_type),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE "cartography_value_journal_scans" (
                    commander_id INTEGER NOT NULL, journal_file TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0, modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_scan TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, journal_file),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE "codex_entries" (
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
                        REFERENCES "bodies"(system_address, body_id)
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
                    FOREIGN KEY(system_address) REFERENCES "systems"(system_address)
                );
CREATE TABLE commanders (
                        id INTEGER PRIMARY KEY,
                        fid TEXT NOT NULL UNIQUE,
                        current_name TEXT,
                        first_seen TEXT,
                        last_seen TEXT
                    );
CREATE TABLE "geology" (
                    commander_id INTEGER NOT NULL, system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL, name TEXT NOT NULL DEFAULT '',
                    raw_name TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '',
                    first_seen TEXT NOT NULL DEFAULT '', last_seen TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, system_address, body_id, name, source),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE "journal_imports" (
                    commander_id INTEGER NOT NULL, journal_file TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0, modified_ns INTEGER NOT NULL DEFAULT 0,
                    last_import TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY(commander_id, journal_file),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE journal_sessions (
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
                    );
CREATE TABLE learned_bio_values (
                    species TEXT PRIMARY KEY COLLATE NOCASE,
                    genus TEXT NOT NULL DEFAULT '',
                    base_value INTEGER NOT NULL DEFAULT 0,
                    last_bonus INTEGER NOT NULL DEFAULT 0,
                    last_total INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT 'SellOrganicData'
                );
CREATE TABLE materials (
                    system_address INTEGER NOT NULL,
                    body_id INTEGER NOT NULL,
                    material_name TEXT NOT NULL,
                    percentage REAL,
                    PRIMARY KEY (system_address, body_id, material_name)
                );
CREATE TABLE "system_visits" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commander_id INTEGER NOT NULL,
                    system_address INTEGER NOT NULL,
                    system_name TEXT NOT NULL DEFAULT '', visited_at TEXT NOT NULL DEFAULT '',
                    x REAL, y REAL, z REAL,
                    UNIQUE(commander_id, system_address, visited_at),
                    FOREIGN KEY(commander_id) REFERENCES commanders(id)
                );
CREATE TABLE "systems" (
                    system_address INTEGER PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    body_count INTEGER NOT NULL DEFAULT 0,
                    x REAL, y REAL, z REAL
                );
CREATE INDEX idx_cartography_sale_bodies_class
                    ON cartography_sale_bodies(planet_class);
CREATE INDEX idx_system_visits_time ON system_visits(commander_id, visited_at);
CREATE INDEX idx_geology_body ON geology(commander_id, system_address, body_id);
CREATE INDEX idx_codex_system ON codex_entries(commander_id, system_address);
CREATE INDEX idx_codex_name ON codex_entries(commander_id, name);
CREATE INDEX idx_commander_systems_last_seen ON commander_systems(commander_id,last_seen);
CREATE INDEX idx_commander_bodies_last_seen ON commander_bodies(commander_id,last_seen);
DELETE FROM "sqlite_sequence";
COMMIT;
PRAGMA user_version = 4;
