# Persistenter Journalindex

Schema 10 erweitert `journal_sessions`; `journal_imports` bleibt der getrennte,
commanderbezogene Fachimportmarker. Der Index speichert zusätzlich `sha256`,
`last_read_offset`, `last_complete_line_offset`, `fully_imported` und
`last_indexed_at`. Pfad, Größe, `mtime_ns`, FID/Name, Ereignisgrenzen und
Zuordnungsstatus werden nicht doppelt gehalten.

Ein Ordnerscan verwendet genau einen `scandir`-Durchlauf. Stimmen Pfad, Größe
und `mtime_ns` mit einem Eintrag samt Hash überein, wird die Datei nicht
geöffnet. Neue/geänderte Dateien und migrierte Einträge ohne Hash werden einmal
gelesen und mit SHA-256 abgesichert. Ändert sich nur die `mtime`, bestätigt ein
identischer Hash den alten Inhalt ohne erneuten Fachimport. Ein anderer Hash
setzt `fully_imported` zurück; der bestehende idempotente Archivimport prüft die
Datei erneut. Seine Unique Keys verhindern doppelte persönliche Datensätze.

Im Livebetrieb wird nur die jüngste Sitzung fachlich ausgewertet. Nach dem
ersten Lesen hält der Reader deren vollständige Zeilen im Speicher und liest
bei Wachstum ausschließlich Bytes ab dem letzten sicheren Offset. Ein Rest
ohne `\n` verändert den Offset nicht und wird beim nächsten Refresh erneut
gelesen. Nach einem Prozessneustart wird die aktuelle Sitzung einmal gelesen;
historische Sitzungen werden aus dem Index übernommen.

Persistiert und beim Archivimport commanderbezogen fortgeschrieben sind
Missionen, Position, Flotte/Loadouts, Carrier, Vermögen, offene Bio- und
Kartographiedaten sowie Exploration, Visits, Bio/Geo/Codex. Nur flüchtige
Details der aktuellen Sitzung werden weiterhin aus dem jüngsten Journal
gebildet: letztes Event, aktueller Body/Station, momentaner Treibstoff/Cargo,
Mission-Terminal-Zwischenupdates sowie die Live-Systemzähler und das aktuelle
Body-Snapshot. Ihre Semantik bleibt unverändert; es werden lediglich keine
historischen Dateien mehr dafür erneut gelesen.

Der Watcher prüft die gecachte aktuelle Datei jede Sekunde mit `stat()` und
sucht alle zehn Sekunden mit einem einzelnen `scandir` nach einer neuen Datei.
Die Auswahl verwendet weiterhin `journal_sort_key` für beide unterstützten
Dateinamensformate.
