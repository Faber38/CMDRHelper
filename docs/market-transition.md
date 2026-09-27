# Markt-DB-Übergang abgeschlossen

Aktueller Folgestand: [gemeinsame lokale Märkte, Schema 2 und Mining](shared-markets-mining.md).
Die früheren Phasenmessungen und FID-Verträge unten sind historische Dokumentation;
für aktuelle Lese-APIs, Migration und Aufbewahrung gilt der verlinkte Folgestand.

## Produktive JSON-Abhängigkeiten: vorher / nachher

Vor diesem Abschluss las die Statusanzeige die Dateigröße von
`observed_markets.json`; der Observer lud JSON auch vor einem DB-Neustart ein.
Kaufen, Verkaufen und Empfehlungen lasen bereits MarketStore. Die Produktion
verwendete bereits Header, der Writer unterstützte aber weiterhin optional eine
vollständige Warenprojektion (`headers_only=False`, `install_projection`,
`apply_committed`). Ein fehlgeschlagenes Initialisierungs-Future ließ den
gewünschten frühen JSON-Handelsfallback noch nicht zu.

Jetzt dienen JSON-Inhalte ausschließlich der einmaligen Migration und dem
Lesefallback vor DB-Veröffentlichung. Nach Aktivierung wird JSON beim App-Start
nicht geladen. Es gibt keinen produktiven weiteren JSON-Preisleser. Der verbleibende
`ObservedMarketCache` hält nach Aktivierung ausschließlich kleine Header für die
Kontext-/Altersprüfung des angedockten Empfehlungsausgangspunkts; die vollständige
Writer-Projektion und ihre Auswahloption sind entfernt. Gemeinsame
Snapshot-Validierung, Uhr und Altersprüfung bleiben in diesem Modul.

Die Originaldatei bleibt unverändert. Der produktive Observer schreibt weiterhin
über den geordneten SQLite-Writer, bestätigt erst COMMIT und wiederholt
fehlgeschlagene Aufträge. Der Legacy-Observer-Modus dient den vorhandenen
isolierten Cache-/Observer-Tests; er ist nicht der AppState-Produktionspfad.
Mining wurde nicht umgestellt.

## Status und Aktivierung

`MarketStore.storage_stats()` zählt `COUNT(DISTINCT market_id)` über den vorhandenen
Index von `current_markets`. Der Writer veröffentlicht die globale Zahl bei
Initialisierung und COMMIT. Alle FIDs zählen zusammen; dieselbe MarketID einmal;
Alter und Spansh spielen keine Rolle. Cleanup erhält sämtliche aktuellen Stände.

Die GUI verwendet den veröffentlichten Integer und drei Dateisystem-Stat-Abfragen:
`markets.db` + `markets.db-wal` + `markets.db-shm`. WAL-Inhalte werden auch vor
Checkpoint berücksichtigt; SHM ist als tatsächlich vorhandener Index enthalten.
Die Summe ist die tatsächliche Dateilänge, keine Summe logischer Nutzdaten oder
Schätzung aus SQL-Zeilenzahlen. Einzelne `stat()`-Aufrufe sind kein atomarer
Dateisystem-Snapshot während eines gleichzeitig laufenden Checkpoints; das nächste
Commit-/Cleanup-/Ansichtsupdate liest die aktuellen Längen erneut. Kein SQL und
keine vollständigen Warenlisten laufen für diese Anzeige im GUI-Thread.

Nach erfolgreicher Veröffentlichung/Validierung wird `markets.db.activated`
dauerhaft gespeichert. Bestehende DB oder Marker sperren den JSON-Rückfall.
Eine beschädigte/unmarkierte bestehende DB wird geprüft und niemals ersetzt;
eine fehlende aktivierte DB erfordert Wiederherstellung. Der Marker bleibt auch
bei späteren DB-Fehlern maßgeblich. Initialisierungs-/Writerfehler stehen in Futures
und Logs, nach Aktivierung außerdem in der Speicherstatuszeile. Handelslesefehler
führen zu Fehler-/Teilresultatstatus plus Logging, nicht zu alten JSON-Angeboten.
Vor Veröffentlichung darf ein Initialisierungsfehler dagegen den bisherigen
JSON-Lesebestand nutzen; erneute erfolgreiche Initialisierung schaltet auf DB um.

Die Aktivierungsprüfung liest nur drei Migrationsschlüssel aus `store_meta`.
Sie lädt insbesondere nicht die pro Station gespeicherten Warenreihenfolgen.

## Prüfung und Messverfahren

Alle Daten sind synthetisch in temporären Verzeichnissen. Keine produktiven Daten,
keine Netzabfragen. Die gemeinsame Regression lief mit gesperrtem `socket.connect`
und `connect_ex` sowie isolierten XDG-Daten-/Konfigurationsverzeichnissen.
576 Tests bestanden: MarketStore/Migration/Writer, Kaufen/Verkaufen, Empfehlungen,
Observer/Cache/Status, kombinierte Handelsansicht, Warenidentität/-lokalisierung,
Spansh-Mocks und Startup. Nach der abschließenden Begrenzung der Migrationsmetadaten
bestanden erneut 126 Markt-Tests (einschließlich acht neuer Übergangstests) und
neun RecommendationStore-Tests.

Neue Abdeckung: globale Stationszahl, mehrere FIDs/gleiche MarketID, DB/WAL/SHM,
Cleanup und Checkpoint beim Schließen, GUI ohne SQL, JSON-Fallback vor Migration,
Recovery trotz altem fehlgeschlagenem Future, ausschließlich DB nach Aktivierung,
veraltete JSON ohne Ergebniseinfluss, Lese-/Neustartfehler ohne Rückfall,
Neustart ohne JSON-/Warenprojektion, begrenzte Aktivierungsmetadaten sowie
unveränderte Quelle und COMMIT-Headerbenachrichtigung.

Reproduzierbar mit:

```sh
QT_QPA_PLATFORM=offscreen venv/bin/python tools/benchmark_market_transition.py
```

Je Größe ein frischer Prozess, 350 Waren je Station. Status: 1.000 Wiederholungen;
SQL-Statusaggregat: 100; read-only Store-Öffnen: 30. AppState-Konstruktion mit leerer,
temporärer Commander-DB, isolierten Einstellungen und deaktiviertem Journalstart;
das ist kein vollständiger GUI-Kaltstart. Observer-Aktivierung umfasst Worker,
Headeraufbau und Startup-Cleanup einer bereits migrierten DB, mit `tracemalloc`.
Vollständige DB-Payload-Lader sind dabei gesperrt. RAM der früheren vollständigen
Projektion wird ausschließlich aus 100 generierten synthetischen Warenlisten
hochgerechnet, nicht durch Laden einer vollständigen DB gemessen.

## Messergebnisse

| Stationen | Status Median / Maximum (ms) | SQL-Status Median (ms) | Store öffnen Median (ms) | AppState-Konstruktor (ms) | Observer bereit (ms) | Header (MiB) | Python-Peak (MiB) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0.019 / 0.117 | 0.024 | 0.244 | 3.78 | 19.43 | 0.075 | 0.307 |
| 1000 | 0.018 / 0.120 | 0.079 | 0.240 | 7.93 | 28.74 | 0.742 | 1.205 |
| 5000 | 0.018 / 0.124 | 0.316 | 0.240 | 3.43 | 85.05 | 3.678 | 4.142 |

Observer-Dispatch im GUI: 2,16 / 1,99 / 1,90 ms. Die AppState-Messung verwendet eine
vorab erstellte leere Commander-DB; deren Schemaerstellung und spätere Journaljobs
sind nicht enthalten. SQLite-Öffnen wurde separat gemessen. Die Bereitschaftszeiten
sind Einzelmessungen unter laufendem `tracemalloc`, keine p95-Latenzen.

Bei 5.000 Stationen bleiben etwa 4,03 MiB getraceter Python-Speicher für den
Observer-/Worker-Pfad, davon 3,68 MiB Header. Prozess-RSS stieg im Messabschnitt
von 106,19 auf 120,36 MiB (einschließlich SQLite/Allocator/native Bibliotheken).
Die frühere optionale vollständige Projektion entspräche anhand der synthetischen
100-Stationen-Stichprobe etwa 12,08 / 120,84 / 604,20 MiB. Diese Werte sind
Hochrechnungen, keine behauptete RAM-Ersparnis gegenüber dem bereits zuvor
produktiven Header-Modus.

Der zusätzliche Startup-Peak durch unbeschränktes Lesen von `store_meta` sank
bei 5.000 Stationen im gemessenen Vorher/Nachher-Lauf von 53,74 auf 4,14 MiB.
Keine vollständige Datenbank wurde dafür in Python geladen.

## In diesem Abschluss bearbeitete Dateien

- `cmdrhelper/market_store.py`, `market_migration.py`, `market_writer.py`
- `cmdrhelper/observed_market_cache.py`, `observed_market_observer.py`
- `cmdrhelper/trade_market_source.py`, `recommendation_market_source.py`
- `cmdrhelper/ui/observed_market_status.py`, `trade_view.py`, `recommendations_view.py`
- `cmdrhelper/i18n/{de,el,en,es,fi,fr,it,nl,no,pl,sv,tr}.py` (Speicher-Tooltip)
- `tests/test_market_transition.py`, `test_market_migration.py`, `test_recommendation_store.py`
- `tools/benchmark_market_transition.py`
- `docs/market-transition.md`, `market-migration.md`, `observed-market-cache.md`,
  `recommendations-market-store.md`, `trade-market-store.md`

Die übrigen bereits zuvor vorhandenen Working-Tree-Änderungen bleiben erhalten.
Version, Mining und `cmdrhelper.db`-Schema wurden in diesem Abschluss nicht geändert.
